import Link from 'next/link';
import {api,fmt,RunSummary} from '@/lib/api';
import {Unavailable} from '@/components/shared';
type RunEntry={id:string;model_id:string;status:string;created_at:string;scope:string;demo:boolean;summary:RunSummary|null};
export const metadata={title:'Evaluation Runs'};
export default async function Runs(){
  const runs=await api<RunEntry[]>('/evaluations');
  return <section className="page"><div className="eyebrow">EVALUATION RECORDS</div><h1>Every run leaves evidence.</h1><p className="intro">Completed evaluations, smoke tests and partial runs retain their configuration and captured responses. Only complete benchmark evaluations qualify for rankings.</p>{runs?.length?<div className="tablewrap"><table><thead><tr><th>Model</th><th>Scope</th><th>Status</th><th>Starter score</th><th>Created</th><th>Artifacts</th></tr></thead><tbody>{runs.map(r=><tr key={r.id}><td><Link className="modelname" href={`/models/${encodeURIComponent(r.model_id)}?run=${r.id}`}>{r.model_id}</Link><small>{r.demo?'Demonstration':'Model inference'} · {r.id.slice(0,12)}</small></td><td>{r.scope}</td><td>{r.status}</td><td>{fmt(r.summary?.score?.mean)}</td><td>{r.created_at.slice(0,10)}</td><td><a className="textlink" href={`/api/v1/evaluations/${r.id}/download`}>Download ZIP</a></td></tr>)}</tbody></table></div>:<Unavailable/>}</section>
}
