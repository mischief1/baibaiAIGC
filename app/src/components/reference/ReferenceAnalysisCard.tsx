import type { ReferenceJobStatus } from "../../types/app";

type Props = {
  job: ReferenceJobStatus | null;
  onAnalyze: () => Promise<void>;
  onConfigure: () => Promise<void>;
  targetChineseCount: number;
  targetEnglishCount: number;
  onTargetChineseCountChange: (value: number) => void;
  onTargetEnglishCountChange: (value: number) => void;
  busy: boolean;
};

export function ReferenceAnalysisCard(props: Props) {
  const { job, onAnalyze, onConfigure, targetChineseCount, targetEnglishCount, onTargetChineseCountChange, onTargetEnglishCountChange, busy } = props;
  const summary = job?.analysisSummary;

  return (
    <section className="reference-card">
      <div className="reference-card-head">
        <div>
          <p className="reference-kicker">全文分析</p>
          <h3>引文与数量建议</h3>
        </div>
        <span className="pill">{job?.status ?? "idle"}</span>
      </div>
      <button type="button" className="reference-primary-button" onClick={() => void onAnalyze()} disabled={!job || busy}>
        分析文档
      </button>
      {summary ? (
        <div className="reference-stats-grid">
          <article><strong>{summary.recommendedTotalCount}</strong><span>建议总数</span></article>
          <article><strong>{summary.recommendedChineseCount}</strong><span>中文文献</span></article>
          <article><strong>{summary.recommendedEnglishCount}</strong><span>英文文献</span></article>
          <article><strong>{summary.recommendedCitationPositionsCount}</strong><span>建议插入位置</span></article>
        </div>
      ) : null}
      <div className="reference-inline-form">
        <label>
          <span>中文目标数</span>
          <input type="number" min={0} value={targetChineseCount} onChange={(event) => onTargetChineseCountChange(Number(event.target.value || 0))} />
        </label>
        <label>
          <span>英文目标数</span>
          <input type="number" min={0} value={targetEnglishCount} onChange={(event) => onTargetEnglishCountChange(Number(event.target.value || 0))} />
        </label>
      </div>
      <button type="button" className="reference-secondary-button" onClick={() => void onConfigure()} disabled={!job || !summary || busy}>
        保存目标数量
      </button>
    </section>
  );
}
