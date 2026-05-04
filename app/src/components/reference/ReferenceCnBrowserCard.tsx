import type { ReferenceJobStatus } from "../../types/app";

type Props = {
  job: ReferenceJobStatus | null;
  cnCandidateText: string;
  onCnCandidateTextChange: (value: string) => void;
  onStartSession: () => Promise<void>;
  onSubmitCandidates: () => Promise<void>;
  busy: boolean;
};

export function ReferenceCnBrowserCard(props: Props) {
  const { job, cnCandidateText, onCnCandidateTextChange, onStartSession, onSubmitCandidates, busy } = props;
  const session = job?.cnBrowserSession;
  const candidates = job?.chineseCandidates ?? [];

  return (
    <section className="reference-card">
      <div className="reference-card-head">
        <div>
          <p className="reference-kicker">知网流程</p>
          <h3>中文候选文献确认</h3>
        </div>
        <button type="button" className="reference-secondary-button" onClick={() => void onStartSession()} disabled={!job || busy}>
          准备知网会话
        </button>
      </div>
      <div className="reference-callout">
        <strong>使用边界</strong>
        <p>由用户自行登录知网、查看候选并人工确认。系统只接收你确认后的文献信息，不自动抓取知网内容。</p>
      </div>
      {session ? <p className="reference-muted">当前会话状态：{session.status}。建议处理主题簇数：{session.topicClusters.length}</p> : null}
      <label className="reference-textarea-wrap">
        <span>粘贴已确认的中文候选 JSON 数组</span>
        <textarea value={cnCandidateText} onChange={(event) => onCnCandidateTextChange(event.target.value)} rows={8} placeholder='[{"candidateId":"cn-1","title":"...","authors":["..."],"year":"2022","source":"...","matchedTopicIds":["topic-1"],"userConfirmed":true}]' />
      </label>
      <button type="button" className="reference-primary-button" onClick={() => void onSubmitCandidates()} disabled={!job || busy}>
        提交已确认中文文献
      </button>
      <div className="reference-list">
        {candidates.length ? candidates.map((candidate) => <article key={candidate.candidateId} className="reference-candidate-row"><strong>{candidate.title}</strong><span>{candidate.source} · {candidate.year}</span></article>) : <p className="reference-empty">还没有提交中文候选文献。</p>}
      </div>
    </section>
  );
}
