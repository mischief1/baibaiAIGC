import type { ReferenceJobStatus, ReferencePreviewPayload } from "../../types/app";

type Props = {
  job: ReferenceJobStatus | null;
  preview: ReferencePreviewPayload | null;
  busy: boolean;
  onGenerate: () => Promise<void>;
};

export function ReferenceBindingPreviewCard({ job, preview, busy, onGenerate }: Props) {
  return (
    <section className="reference-card">
      <div className="reference-card-head">
        <div>
          <p className="reference-kicker">句级绑定</p>
          <h3>正文插入预览</h3>
        </div>
        <button type="button" className="reference-primary-button" onClick={() => void onGenerate()} disabled={!job || busy}>
          生成句级绑定
        </button>
      </div>
      <div className="reference-preview-grid">
        <article>
          <h4>插标后的正文</h4>
          <pre>{preview?.annotatedText || "还没有生成预览。"}</pre>
        </article>
        <article>
          <h4>参考文献列表</h4>
          <pre>{preview?.referencesText || "还没有参考文献列表。"}</pre>
        </article>
      </div>
    </section>
  );
}
