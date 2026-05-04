import { useRef } from "react";
import { useReferenceState } from "../../hooks/useReferenceState";
import { referenceWebService } from "../../lib/referenceWebService";
import { ReferenceAnalysisCard } from "./ReferenceAnalysisCard";
import { ReferenceBindingPreviewCard } from "./ReferenceBindingPreviewCard";
import { ReferenceCnBrowserCard } from "./ReferenceCnBrowserCard";
import { ReferenceEnglishCandidatesCard } from "./ReferenceEnglishCandidatesCard";
import { ReferenceExportCard } from "./ReferenceExportCard";

function getStatusLabel(status?: string | null) {
  const labels: Record<string, string> = {
    uploaded: "已上传",
    analyzed: "已分析",
    configured: "已配置",
    english_searched: "已完成英文检索",
    cn_waiting_login: "等待知网登录",
    cn_candidates_confirmed: "已确认中文候选",
    bindings_generated: "已生成绑定",
    applied: "已应用",
    exported: "已导出",
    idle: "未开始",
  };
  return labels[String(status ?? "idle")] ?? String(status ?? "未开始");
}

async function readFilePayload(file: File) {
  if (file.name.toLowerCase().endsWith(".docx")) {
    const contentBase64 = await new Promise<string>((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = () => {
        const result = typeof reader.result === "string" ? reader.result : "";
        const commaIndex = result.indexOf(",");
        resolve(commaIndex >= 0 ? result.slice(commaIndex + 1) : result);
      };
      reader.onerror = () => reject(new Error("Failed to read file."));
      reader.readAsDataURL(file);
    });
    return { filename: file.name, encoding: "base64" as const, contentBase64 };
  }
  return { filename: file.name, encoding: "text" as const, content: await file.text() };
}

export function ReferenceWorkspace() {
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const state = useReferenceState();

  async function refreshHistory() {
    state.setHistory(await referenceWebService.getHistory());
  }

  async function handleUpload(file: File) {
    state.setBusy(true);
    state.setError("");
    try {
      const payload = await readFilePayload(file);
      const job = await referenceWebService.uploadDocument(payload);
      state.setJob(job);
      state.setNotice("已创建参考文献任务。");
      await refreshHistory();
    } catch (error) {
      state.setError(error instanceof Error ? error.message : String(error));
    } finally {
      state.setBusy(false);
    }
  }

  async function handleAnalyze() {
    if (!state.job) return;
    state.setBusy(true);
    state.setError("");
    try {
      const job = await referenceWebService.analyze(state.job.jobId);
      state.setJob(job);
      state.setTargetChineseCount(job.analysisSummary?.recommendedChineseCount ?? 0);
      state.setTargetEnglishCount(job.analysisSummary?.recommendedEnglishCount ?? 0);
      state.setNotice("全文分析完成。");
    } catch (error) {
      state.setError(error instanceof Error ? error.message : String(error));
    } finally {
      state.setBusy(false);
    }
  }

  async function handleConfigure() {
    if (!state.job) return;
    state.setBusy(true);
    state.setError("");
    try {
      const job = await referenceWebService.configure(state.job.jobId, state.targetChineseCount, state.targetEnglishCount);
      state.setJob(job);
      state.setNotice("已保存中英文目标数量。");
    } catch (error) {
      state.setError(error instanceof Error ? error.message : String(error));
    } finally {
      state.setBusy(false);
    }
  }

  async function handleEnglishSearch() {
    if (!state.job) return;
    state.setBusy(true);
    state.setError("");
    try {
      state.setJob(await referenceWebService.searchEnglish(state.job.jobId));
      state.setNotice("英文候选文献已更新。");
    } catch (error) {
      state.setError(error instanceof Error ? error.message : String(error));
    } finally {
      state.setBusy(false);
    }
  }

  async function handleStartCnSession() {
    if (!state.job) return;
    state.setBusy(true);
    state.setError("");
    try {
      await referenceWebService.startCnBrowserSession(state.job.jobId);
      state.setJob(await referenceWebService.getStatus(state.job.jobId));
      state.setNotice("知网会话已准备，请先登录后再确认候选。");
    } catch (error) {
      state.setError(error instanceof Error ? error.message : String(error));
    } finally {
      state.setBusy(false);
    }
  }

  async function handleSubmitCnCandidates() {
    if (!state.job) return;
    state.setBusy(true);
    state.setError("");
    try {
      const parsed = JSON.parse(state.cnCandidateText) as Array<Record<string, unknown>>;
      state.setJob(await referenceWebService.submitCnCandidates(state.job.jobId, parsed));
      state.setNotice("中文候选文献已提交。");
    } catch (error) {
      state.setError(error instanceof Error ? error.message : String(error));
    } finally {
      state.setBusy(false);
    }
  }

  async function handleGenerateBindings() {
    if (!state.job) return;
    state.setBusy(true);
    state.setError("");
    try {
      const result = await referenceWebService.generateBindings(state.job.jobId);
      state.setPreview(result.preview);
      state.setJob(await referenceWebService.getStatus(state.job.jobId));
      state.setNotice("句级绑定预览已生成。");
    } catch (error) {
      state.setError(error instanceof Error ? error.message : String(error));
    } finally {
      state.setBusy(false);
    }
  }

  async function handleApply() {
    if (!state.job) return;
    state.setBusy(true);
    state.setError("");
    try {
      const result = await referenceWebService.apply(state.job.jobId);
      state.setExportResult(result);
      state.setJob(await referenceWebService.getStatus(state.job.jobId));
      state.setNotice("参考文献导出完成。");
    } catch (error) {
      state.setError(error instanceof Error ? error.message : String(error));
    } finally {
      state.setBusy(false);
    }
  }

  return (
    <div className="reference-workspace">
      <section className="reference-hero">
        <div>
          <p className="reference-kicker">独立流程</p>
          <h2>参考文献工作台</h2>
          <p className="reference-muted">这是一条独立于降 AI 轮次状态机的新流程，知网部分保持“用户登录并人工确认，系统只做绑定与插标”。</p>
        </div>
        <div className="reference-hero-actions">
          <input
            ref={fileInputRef}
            type="file"
            accept=".txt,.docx"
            hidden
            onChange={(event) => {
              const file = event.target.files?.[0];
              if (file) {
                void handleUpload(file);
              }
              event.target.value = "";
            }}
          />
          <button type="button" className="reference-primary-button" onClick={() => fileInputRef.current?.click()} disabled={state.busy}>
            上传待处理文档
          </button>
          <button type="button" className="reference-secondary-button" onClick={() => void refreshHistory()} disabled={state.busy}>
            刷新任务历史
          </button>
        </div>
      </section>

      {state.error ? <div className="error-banner">{state.error}</div> : null}
      {state.notice ? <div className="notice-banner">{state.notice}</div> : null}

      <div className="reference-meta-strip">
        <span className="pill">{getStatusLabel(state.job?.status)}</span>
        <span>{state.job?.sourcePath ?? "尚未选择文档"}</span>
      </div>

      <div className="reference-card-row">
        <ReferenceAnalysisCard
          job={state.job}
          onAnalyze={handleAnalyze}
          onConfigure={handleConfigure}
          targetChineseCount={state.targetChineseCount}
          targetEnglishCount={state.targetEnglishCount}
          onTargetChineseCountChange={state.setTargetChineseCount}
          onTargetEnglishCountChange={state.setTargetEnglishCount}
          busy={state.busy}
        />
        <ReferenceEnglishCandidatesCard job={state.job} busy={state.busy} onSearch={handleEnglishSearch} />
        <ReferenceCnBrowserCard
          job={state.job}
          cnCandidateText={state.cnCandidateText}
          onCnCandidateTextChange={state.setCnCandidateText}
          onStartSession={handleStartCnSession}
          onSubmitCandidates={handleSubmitCnCandidates}
          busy={state.busy}
        />
        <ReferenceExportCard job={state.job} exportResult={state.exportResult} busy={state.busy} onApply={handleApply} />
      </div>

      <div className="reference-grid">
        <ReferenceBindingPreviewCard job={state.job} preview={state.preview ?? state.job?.preview ?? null} busy={state.busy} onGenerate={handleGenerateBindings} />
      </div>
    </div>
  );
}
