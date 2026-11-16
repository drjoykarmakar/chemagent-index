# Start here

This is **ChemAgent Index v0.1.0**, a working research infrastructure foundation with 60 synthetic tasks and three clearly labeled demonstration systems. It contains no fabricated commercial-model rankings.

## Launch on your Mac

1. Install and start Docker Desktop.
2. Unzip this archive and open Terminal in the `chemagent-index` folder.
3. Run:

```bash
docker compose up --build
```

4. Open **http://localhost:3000**.
5. Open **http://localhost:8000/docs** for the API.

The startup job creates the database, evaluates all three demo systems and fills the leaderboard. To add another evaluation:

```bash
docker compose exec backend chemagent evaluate --model demo-agent --benchmark chemagentbench-v0.1
```

Inspect a model profile to see its category scores, intervals, task answers, validation failures and run configuration.

## Read next

- `README.md`: installation without Docker, architecture and commands.
- `docs/release-status.md`: what was verified and what remains unverified.
- `docs/scoring.md`: exact formulas and uncertainty.
- `docs/methodology.md`: academic-style methods draft and scientific limits.
- `docs/architecture.md`: phased implementation plan and component boundaries.

Docker execution and browser visual/interaction checks could not be completed in the build environment. Both remain release gates before public deployment. The backend was tested with SQLite and PostgreSQL. No website or GitHub repository has been publicly deployed by this build.

**Next scientific milestone:** independently review the starter tasks, then add one real provider with contract tests and repeated evaluations. Do not advertise the synthetic demo as a validated ranking of AI chemistry capability.
