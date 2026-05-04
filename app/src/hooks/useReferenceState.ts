import { useState } from "react";
import type {
  ReferenceExportResult,
  ReferenceJobStatus,
  ReferencePreviewPayload,
} from "../types/app";

export function useReferenceState() {
  const [job, setJob] = useState<ReferenceJobStatus | null>(null);
  const [history, setHistory] = useState<ReferenceJobStatus[]>([]);
  const [preview, setPreview] = useState<ReferencePreviewPayload | null>(null);
  const [exportResult, setExportResult] = useState<ReferenceExportResult | null>(null);
  const [targetChineseCount, setTargetChineseCount] = useState(0);
  const [targetEnglishCount, setTargetEnglishCount] = useState(0);
  const [cnCandidateText, setCnCandidateText] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  return {
    job,
    history,
    preview,
    exportResult,
    targetChineseCount,
    targetEnglishCount,
    cnCandidateText,
    busy,
    error,
    notice,
    setJob,
    setHistory,
    setPreview,
    setExportResult,
    setTargetChineseCount,
    setTargetEnglishCount,
    setCnCandidateText,
    setBusy,
    setError,
    setNotice,
  };
}
