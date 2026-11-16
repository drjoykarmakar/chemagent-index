import Link from 'next/link';
import {api,categories,fmt,Model,Run,RunSummary,prettyResponse,encodedId} from '@/lib/api';
import {Bars,ResultNotice,Interval,Radar,Unavailable} from '@/components/shared';
export default async function ModelPage({params,searchParams}:{params:Promise<{id:string}>;searchParams:Promise<{run?:string}>}){
  const {id}=await params;
  const selected=await searchParams;
  const profile=await api<{model:Model;runs:{id:string;status:string;cohort:string;created_at:string;summary:RunSummary|null;benchmark_version_id:string}[]}>(`/models/${encodedId(id)}`);
  if(!profile)return <section className="page"><Unavailable/></section>;
  const latest=selected.run?profile.runs.find(r=>r.id===selected.run):profile.runs[0];
  const run=latest?await api<Run>(`/evaluations/${latest.id}`):null;
  return <section className="page"><Link className="breadcrumb" href="/runs">← Evaluation runs</Link>
    <div className="eyebrow">SYSTEM PROFILE / {profile.model.provider.toUpperCase()}</div><h1>{profile.model.display_name}</h1>
    <p className="intro">{profile.model.organization} · Version {profile.model.model_version.slice(0,12)}<br/>{profile.model.demo?'Deterministic software fixture with controlled errors.':'Local model inference on the public development benchmark.'}</p>
    <ResultNotice notice={run?.notice}/>
    {run?<>
      <div className="actions"><span className="pill">{run.status} · {run.tasks.length} tasks captured</span><a className="button secondary" href={`/api/v1/evaluations/${run.id}/download`}>Download run artifacts</a></div>
      {run.summary?.score&&run.summary.cri&&run.summary.reproducibility?<>
        <div className="metricgrid"><div className="metric"><span>STARTER INDEX</span><Interval value={run.summary.score}/></div><div className="metric"><span>RELIABILITY PROXY · CRI</span><Interval value={run.summary.cri}/></div><div className="metric"><span>REPRODUCIBILITY CHECKLIST</span><Interval value={run.summary.reproducibility}/></div><div className="metric"><span>OBSERVED RUN COST</span><strong>{run.summary.usage.cost_usd===null?'Not measured':`$${fmt(run.summary.usage.cost_usd,2)}`}</strong><small>{fmt(run.summary.usage.wall_seconds,1)} s elapsed</small></div></div>
        <div className="profilegrid"><div className="card"><div className="eyebrow">DOMAIN PERFORMANCE</div><h2>Strengths need context.</h2><Bars value={run.summary.score}/></div><div className="card"><Radar value={run.summary.score}/><p className="muted small">{profile.model.demo?'Differences reflect mock error injection.':'Intervals describe variation over this small synthetic collection.'}</p></div></div>
      </>:<p className="callout">This run has no full-benchmark aggregate. Smoke tests and partial evaluations are excluded from rankings.</p>}
      <div className="sectionhead"><div><div className="eyebrow">AUDIT TRAIL</div><h2>Every answer is inspectable.</h2></div></div>
      <div className="tasklist">{run.tasks.map(t=><details key={t.task_id}><summary><span>{t.task_id}<small>{categories[t.score.category]}</small></span><span className={t.score.score===100?'good':'warning'}>{fmt(t.score.score)} / 100 · {t.validation.errors.length?'discrepancy':'passed'}</span></summary><div className="taskdetail"><div><h4>Captured response</h4><pre>{prettyResponse(t.response)}</pre></div><div><h4>Validation and rubric</h4><pre>{JSON.stringify(t.validation,null,2)}</pre></div></div></details>)}</div>
      <div className="profilegrid lower"><div className="card"><h2>Evaluation configuration</h2><pre>{JSON.stringify(run.provenance.config,null,2)}</pre><p className="muted small break">Benchmark: {run.provenance.benchmark_hash}<br/>Scoring: {run.provenance.scoring_hash}</p><details><summary>Model and runtime provenance</summary><pre>{JSON.stringify(run.provenance.provider,null,2)}</pre><pre>{JSON.stringify(run.provenance.environment,null,2)}</pre></details></div>
      <div className="card"><h2>Performance history</h2><p className="muted small">Different cohorts are not treated as comparable improvement.</p>{profile.runs.map(r=><div className="history" key={r.id}><Link href={`/models/${encodedId(id)}?run=${r.id}`}>{r.created_at.slice(0,10)}<small>{r.cohort.slice(0,12)} · {r.status}</small></Link><b>{fmt(r.summary?.score?.mean)}</b></div>)}<h3>Known limitations</h3><p>Small public synthetic tasks with high contamination risk and pending expert review. These tasks do not establish advanced chemistry competence or experimental validity.</p></div></div>
    </>:<Unavailable/>}
  </section>;
}
