import type { ReferenceExportResult, ReferenceJobStatus } from "../../types/app";

type Props = {
  job: ReferenceJobStatus | null;
  exportResult: ReferenceExportResult | null;
  busy: boolean;
  onApply: () => Promise<void>;
};

export function ReferenceExportCard({ job, exportResult, busy, onApply }: Props) {
  return (
    <section className="reference-card">
      <div className="reference-card-head">
        <div>
          <p className="reference-kicker">导出结果</p>
          <h3>生成最终文件</h3>
        </div>
        <button type="button" className="reference-primary-button" onClick={() => void onApply()} disabled={!job || busy}>
          导出带引文文档
        </button>
      </div>
      {exportResult ? (
        <div className="reference-export-result">
          <p><strong>TXT:</strong> {exportResult.outputPath}</p>
          <p><strong>DOCX:</strong> {exportResult.outputDocxPath}</p>
        </div>
      ) : (
        <p className="reference-empty">还没有导出文件。</p>
      )}
    </section>
  );
}
