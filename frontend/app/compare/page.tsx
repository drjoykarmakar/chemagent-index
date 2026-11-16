import {api,Board} from '@/lib/api';
import {DemoNotice,Unavailable} from '@/components/shared';
import ComparePanel from '@/components/compare';
export const metadata={title:'Compare Chemistry AI Systems'};
export default async function Compare(){const board=await api<Board>('/leaderboard');return <section className="page"><div className="eyebrow">MODEL COMPARISON</div><h1>Does the difference hold up?</h1><p className="intro">Compare two systems evaluated on the same tasks, with the same tools, benchmark version and scoring policy. Paired intervals test the difference directly.</p><DemoNotice/>{board&&board.rows.length>=2?<ComparePanel board={board}/>:<Unavailable/>}<div className="callout">This release supports paired comparisons. Multi-system inference, multiple-testing correction and repeated-run uncertainty are future work. No hallucination-frequency claim is inferred from the starter reliability proxy.</div></section>}
