import type { ReferenceCandidate, ReferenceJobStatus } from "../../types/app";

type Props = {
  job: ReferenceJobStatus | null;
  busy: boolean;
  onSearch: () => Promise<void>;
};

function CandidateRow({ candidate }: { candidate: ReferenceCandidate }) {
  return (
    <article className="reference-candidate-row">
      <div>
        <strong>{candidate.title}</strong>
        <p>{candidate.authors.join(", ") || "作者未知"}</p>
      </div>
      <div className="reference-candidate-meta">
        <span>{candidate.source}</span>
        <span>{candidate.year}</span>
        <span className={`pill ${candidate.verified ? "" : "idle"}`}>{candidate.verified ? "已校验" : "未校验"}</span>
      </div>
    </article>
  );
}

export function ReferenceEnglishCandidatesCard({ job, busy, onSearch }: Props) {
  const candidates = job?.englishCandidates ?? [];
  return (
    <section className="reference-card">
      <div className="reference-card-head">
        <div>
          <p className="reference-kicker">英文检索</p>
          <h3>英文候选文献</h3>
        </div>
        <button type="button" className="reference-primary-button" onClick={() => void onSearch()} disabled={!job || busy}>
          检索英文文献
        </button>
      </div>
      <div className="reference-list">
        {candidates.length ? candidates.map((candidate) => <CandidateRow key={candidate.candidateId} candidate={candidate} />) : <p className="reference-empty">还没有英文候选文献。</p>}
      </div>
    </section>
  );
}
