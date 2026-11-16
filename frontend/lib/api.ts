export const categories: Record<string,string> = {chemistry_reasoning:'Chemistry reasoning',medicinal_chemistry:'Medicinal chemistry',molecular_validation:'Molecular validation',synthesis_reasoning:'Synthesis reasoning',literature_reliability:'Literature reliability',stress_tests:'Stress tests'};
export type Estimate = {mean:number;ci95:[number,number]|null;standard_error:number|null;n:number;categories:Record<string,{mean:number;ci95:[number,number]|null;clusters:number;n:number}>};
export type Summary = {score:Estimate;cri:Estimate;reproducibility:Estimate;usage:{cost_usd:number|null;wall_seconds:number;performance_per_dollar:number|null}};
export type Model = {model_id:string;display_name:string;organization:string;provider:string;model_version:string;open_source:boolean;commercial:boolean;demo:boolean;system_type:string};
export type Row = {model:Model;run_id:string;summary:Summary;track:string;cohort:string;evaluated_at:string;benchmark_version_id:string};
export type Board = {notice:string;profile:string;cohort:string|null;available_cohorts:string[];rows:Row[];ranking_note:string};
export type Manifest = {id:string;benchmark_name:string;benchmark_version:string;sample_count:number;public_samples:number;private_samples:number;license:string;description:string;known_limitations:string[];fingerprint:string};
export type Task = {task_id:string;category:string;prompt:string;difficulty:string;inputs:Record<string,unknown>;reference_answer:Record<string,unknown>;rubric:Record<string,unknown>;known_ambiguity:string};
export type Run = {id:string;status:string;model_id:string;summary:Summary|null;cohort:string;provenance:{config:Record<string,unknown>;environment:Record<string,unknown>;benchmark_hash:string;scoring_hash:string;provider:Record<string,unknown>};tasks:{task_id:string;response:string;score:{score:number;category:string};validation:{parse_valid:boolean;errors:string[];fields:unknown[];chemistry:unknown}}[]};
export async function api<T>(path:string):Promise<T|null> { try {const response=await fetch(`${process.env.API_URL || 'http://127.0.0.1:8000'}/api/v1${path}`,{cache:'no-store',signal:AbortSignal.timeout(7000)});if(!response.ok)return null;return await response.json() as T;}catch{return null;} }
export const fmt = (n:number|null|undefined,digits=1) => n==null?'—':n.toFixed(digits);

export function prettyResponse(raw:string):string {try{return JSON.stringify(JSON.parse(raw),null,2);}catch{return raw;}}

// Normalize framework route parameters before encoding them for an upstream URL.
export function encodedId(value:string):string {try{return encodeURIComponent(decodeURIComponent(value));}catch{return encodeURIComponent(value);}}
