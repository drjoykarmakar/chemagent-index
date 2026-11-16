/** Live process smoke test; intentionally does not claim browser or visual validation. */
import { spawn, spawnSync } from 'node:child_process';
import { cpSync, existsSync, mkdtempSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
const root = dirname(dirname(fileURLToPath(import.meta.url)));
const python = process.env.CHEMAGENT_PYTHON || 'python';
const temporary = mkdtempSync(join(tmpdir(), 'chemagent-smoke-'));
const env = { ...process.env, DATABASE_URL: `sqlite:///${join(temporary, 'smoke.db')}`, API_URL:'http://127.0.0.1:8000', HOSTNAME:'127.0.0.1', PORT:'3000', NEXT_TELEMETRY_DISABLED:'1' };
const standalone = join(root, 'frontend/.next/standalone');
if (!existsSync(join(standalone, 'server.js'))) throw new Error('Run npm run build in frontend first');
cpSync(join(root,'frontend/.next/static'),join(standalone,'.next/static'),{recursive:true});
for (const command of ['init-db','seed-demo']) {
  const child = spawnSync(python,['-m','chemagent.cli',command],{cwd:root,env,encoding:'utf8'});
  if(child.status!==0) throw new Error(child.stderr || child.stdout);
}
const smoke = spawnSync(python,['-m','chemagent.cli','evaluate','--model','demo-agent','--sample-size','5'],{cwd:root,env,encoding:'utf8'});
if(smoke.status!==0) throw new Error(smoke.stderr || smoke.stdout);
const backend=spawn(python,['-m','uvicorn','backend.app.main:app','--host','127.0.0.1','--port','8000'],{cwd:root,env,stdio:'ignore'});
const frontend=spawn(process.execPath,[join(standalone,'server.js')],{cwd:standalone,env,stdio:'ignore'});
async function ready(url) {
  for(let i=0;i<100;i++) {
    try {const response=await fetch(url); if(response.ok)return;}catch{}
    await new Promise(resolve=>setTimeout(resolve,100));
  }
  throw new Error(`Service not ready: ${url}`);
}
async function expectPage(path, marker) {
  const response=await fetch(`http://127.0.0.1:3000${path}`);
  const html=await response.text();
  if(response.status!==200 || !html.includes(marker))throw new Error(`Route failed (${response.status}): ${path}`);
  console.log(`PASS ${path}`);
  return html;
}
try {
  await ready('http://127.0.0.1:8000/health');
  await ready('http://127.0.0.1:3000');
  const home=await expectPage('/','DemoChem-A');
  const css=[...home.matchAll(/href="([^\"]+\.css[^\"]*)"/g)];
  if(!css.length)throw new Error('No stylesheet emitted');
  for(const match of css) {
    const response=await fetch(`http://127.0.0.1:3000${match[1].replaceAll('&amp;','&')}`);
    if(!response.ok || !(await response.text()).includes('hero'))throw new Error('Stylesheet not served');
  }
  await expectPage('/leaderboard','DemoChem-C');
  await expectPage('/models/demo-agent','Captured response');
  await expectPage('/compare','Compare paired tasks');
  await expectPage('/methodology','Chemistry Reliability Index');
  await expectPage('/submit','INTAKE NOT OPEN');
  await expectPage('/runs','smoke');
  const runs=await (await fetch('http://127.0.0.1:3000/api/v1/evaluations')).json();
  const sample=runs.find(r=>r.scope==='smoke');
  if(!sample || sample.summary.score!==null)throw new Error('Smoke run must not have an aggregate');
  await expectPage(`/models/demo-agent?run=${sample.id}`,'SMOKE TEST');
  const archive=await fetch(`http://127.0.0.1:3000/api/v1/evaluations/${sample.id}/download`);
  const bytes=new Uint8Array(await archive.arrayBuffer());
  if(!archive.ok || bytes[0]!==80 || bytes[1]!==75)throw new Error('Run artifact download failed');
  const registry=await (await fetch('http://127.0.0.1:8000/api/v1/benchmarks')).json();
  await expectPage('/benchmarks','PUBLIC DEVELOPMENT');
  await expectPage(`/benchmarks/${encodeURIComponent(registry[0].id)}`,'stress_tests_010');
  await expectPage(`/benchmarks/${registry[0].id}`,'stress_tests_010');
  const board=await (await fetch('http://127.0.0.1:3000/api/v1/leaderboard')).json();
  if(board.rows.length!==3)throw new Error('Expected three computed demo systems');
  const comparison=await (await fetch(`http://127.0.0.1:3000/api/v1/compare?left=${board.rows[0].run_id}&right=${board.rows[1].run_id}`)).json();
  if(comparison.wins+comparison.losses+comparison.ties!==60)throw new Error('Paired comparison failed');
  console.log('PASS same-origin API proxy, 60 paired tasks, three computed demos, and CSS assets');
} finally {
  backend.kill('SIGTERM');frontend.kill('SIGTERM');
  await Promise.all([new Promise(r=>backend.once('exit',r)),new Promise(r=>frontend.once('exit',r))]);
  rmSync(temporary,{recursive:true,force:true});
}
