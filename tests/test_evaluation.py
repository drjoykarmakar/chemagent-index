import pytest
from sqlalchemy import select

from chemagent.config import EvaluationConfig
from chemagent.database.models import EvaluationRun, LeaderboardSnapshot, Response
from chemagent.database.queries import comparison, leaderboard, run_detail, snapshot
from chemagent.database.session import sessions
from chemagent.evaluation.runner import run_evaluation
from chemagent.providers.future import (
    AnthropicAdapter,
    GeminiAdapter,
    LocalModelAdapter,
    OpenAIAdapter,
    OpenRouterAdapter,
)
from chemagent.providers.mock import MockAdapter


class InterruptingAdapter(MockAdapter):
    calls = 0
    failing = True

    def generate_structured(self, request, *, seed, timeout):
        self.calls += 1
        if self.calls == 3 and self.failing:
            raise TimeoutError("fixture interruption")
        return super().generate_structured(request, seed=seed, timeout=timeout)


def test_complete_runs_snapshots_and_cohort_comparison(engine):
    left = run_evaluation(engine, EvaluationConfig())
    right = run_evaluation(engine, EvaluationConfig(model="demo-b"))
    with sessions(engine)() as session:
        board = leaderboard(session)
        assert len(board["rows"]) == 2
        detail = run_detail(session, left)
        assert detail["status"] == "completed" and len(detail["tasks"]) == 60
        assert detail["summary"]["usage"]["performance_per_dollar"] is None
        assert (
            comparison(session, left, right)["wins"]
            + comparison(session, left, right)["losses"]
            + comparison(session, left, right)["ties"]
            == 60
        )
        snap_id = snapshot(session)
        frozen = session.get(LeaderboardSnapshot, snap_id).fingerprint
    run_evaluation(engine, EvaluationConfig(model="demo-c", seed=99))
    with sessions(engine)() as session:
        assert session.get(LeaderboardSnapshot, snap_id).fingerprint == frozen
        assert len(leaderboard(session)["rows"]) == 1
        latest = leaderboard(session)["rows"][0]["run_id"]
        with pytest.raises(ValueError, match="Incompatible"):
            comparison(session, left, latest)
    with pytest.raises(ValueError, match="finished"):
        run_evaluation(engine, EvaluationConfig(), resume=left)


def test_resume_keeps_successful_checkpoints(engine):
    adapter = InterruptingAdapter()
    config = EvaluationConfig(retries=0)
    with pytest.raises(TimeoutError):
        run_evaluation(engine, config, adapter=adapter)
    with sessions(engine)() as session:
        run = session.scalar(select(EvaluationRun))
        assert run.status == "partial"
        run_id = run.id
        checkpoints = {r.task_id: r.id for r in session.scalars(select(Response))}
        assert len(checkpoints) == 2
        assert not leaderboard(session)["rows"]
    with pytest.raises(ValueError, match="changed"):
        run_evaluation(engine, EvaluationConfig(seed=2, retries=0), resume=run_id)
    adapter.failing = False
    run_evaluation(engine, config, adapter=adapter, resume=run_id)
    with sessions(engine)() as session:
        assert session.get(EvaluationRun, run_id).status == "completed"
        all_responses = {r.task_id: r.id for r in session.scalars(select(Response))}
        assert len(all_responses) == 60
        assert all(all_responses[key] == value for key, value in checkpoints.items())


def test_provider_boundary_and_tools(engine, dataset):
    with pytest.raises(ValueError, match="Unknown"):
        MockAdapter("real-model")
    adapter = MockAdapter()
    assert adapter.health_check() and adapter.estimate_cost(1, 1) == 0
    with pytest.raises(ValueError, match="unpermitted"):
        run_evaluation(engine, EvaluationConfig(tools=[], track="model_only"))
    with pytest.raises(ValueError, match="mismatch"):
        run_evaluation(engine, EvaluationConfig(model="demo-b"), adapter=adapter)
    from chemagent.providers.base import PublicRequest

    request = PublicRequest.from_task(dataset[1][0])
    assert adapter.generate(request, seed=3, timeout=1) == adapter.generate(
        request, seed=3, timeout=1
    )
    for cls in [
        OpenAIAdapter,
        AnthropicAdapter,
        GeminiAdapter,
        OpenRouterAdapter,
        LocalModelAdapter,
    ]:
        external = cls()
        assert not external.health_check()
        assert external.estimate_cost(1, 1) is None
        assert external.metadata()["implemented"] is False
        with pytest.raises(NotImplementedError):
            external.generate(request, seed=1, timeout=1)


def test_no_empty_snapshot(engine):
    with sessions(engine)() as session, pytest.raises(ValueError, match="empty"):
        snapshot(session)


def test_run_lock_excludes_second_writer(engine):
    from chemagent.evaluation.locking import run_lock

    with run_lock(engine, "fixture-lock"):
        with pytest.raises(ValueError, match="already active"), run_lock(engine, "fixture-lock"):
            pass
    with run_lock(engine, "fixture-lock"):
        pass


def test_private_mock_run_is_rejected(engine, dataset):
    manifest, tasks, fingerprint = dataset

    class PrivateFixture:
        def load(self):
            return (
                manifest,
                [t.model_copy(update={"visibility": "private"}) for t in tasks],
                fingerprint,
            )

    with pytest.raises(ValueError, match="public-development-only"):
        run_evaluation(engine, EvaluationConfig(), store=PrivateFixture())
