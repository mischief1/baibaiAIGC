import { requestJson } from "./webService";
import type {
  ReferenceExportResult,
  ReferenceJobStatus,
  ReferencePreviewPayload,
} from "../types/app";

export type ReferenceUploadPayload = {
  filename: string;
  encoding?: "text" | "base64";
  content?: string;
  contentBase64?: string;
};

export interface ReferenceService {
  uploadDocument(payload: ReferenceUploadPayload): Promise<ReferenceJobStatus>;
  getStatus(jobId: string): Promise<ReferenceJobStatus>;
  getHistory(): Promise<ReferenceJobStatus[]>;
  analyze(jobId: string): Promise<ReferenceJobStatus>;
  configure(jobId: string, targetChineseCount: number, targetEnglishCount: number): Promise<ReferenceJobStatus>;
  searchEnglish(jobId: string): Promise<ReferenceJobStatus>;
  startCnBrowserSession(jobId: string): Promise<{ jobId: string; status: string; topicClusters: Array<Record<string, unknown>> }>;
  submitCnCandidates(jobId: string, candidates: Array<Record<string, unknown>>): Promise<ReferenceJobStatus>;
  generateBindings(jobId: string): Promise<{ jobId: string; preview: ReferencePreviewPayload }>;
  getPreview(jobId: string): Promise<ReferencePreviewPayload>;
  apply(jobId: string): Promise<ReferenceExportResult>;
}

export const referenceWebService: ReferenceService = {
  uploadDocument(payload) {
    return requestJson<ReferenceJobStatus>("/api/reference/upload-document", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },
  getStatus(jobId) {
    return requestJson<ReferenceJobStatus>(`/api/reference/status?jobId=${encodeURIComponent(jobId)}`);
  },
  getHistory() {
    return requestJson<ReferenceJobStatus[]>("/api/reference/history");
  },
  analyze(jobId) {
    return requestJson<ReferenceJobStatus>("/api/reference/analyze", {
      method: "POST",
      body: JSON.stringify({ jobId }),
    });
  },
  configure(jobId, targetChineseCount, targetEnglishCount) {
    return requestJson<ReferenceJobStatus>("/api/reference/configure", {
      method: "POST",
      body: JSON.stringify({ jobId, targetChineseCount, targetEnglishCount }),
    });
  },
  searchEnglish(jobId) {
    return requestJson<ReferenceJobStatus>("/api/reference/search-english", {
      method: "POST",
      body: JSON.stringify({ jobId }),
    });
  },
  startCnBrowserSession(jobId) {
    return requestJson<{ jobId: string; status: string; topicClusters: Array<Record<string, unknown>> }>(
      "/api/reference/start-cn-browser-session",
      {
        method: "POST",
        body: JSON.stringify({ jobId }),
      },
    );
  },
  submitCnCandidates(jobId, candidates) {
    return requestJson<ReferenceJobStatus>("/api/reference/submit-cn-candidates", {
      method: "POST",
      body: JSON.stringify({ jobId, candidates }),
    });
  },
  generateBindings(jobId) {
    return requestJson<{ jobId: string; preview: ReferencePreviewPayload }>("/api/reference/generate-bindings", {
      method: "POST",
      body: JSON.stringify({ jobId }),
    });
  },
  getPreview(jobId) {
    return requestJson<ReferencePreviewPayload>(`/api/reference/preview?jobId=${encodeURIComponent(jobId)}`);
  },
  apply(jobId) {
    return requestJson<ReferenceExportResult>("/api/reference/apply", {
      method: "POST",
      body: JSON.stringify({ jobId }),
    });
  },
};
