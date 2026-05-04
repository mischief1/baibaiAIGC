from __future__ import annotations

import uuid
from pathlib import Path
from typing import Any

from reference_analysis import build_topic_clusters, recommend_reference_counts, score_sentence_candidates
from reference_binding import bind_references_to_sentences
from reference_document import parse_reference_document
from reference_export import build_reference_preview, export_reference_document
from reference_models import ReferenceCandidate, ReferenceDocument, ReferenceJob, SentenceCandidate, TopicCluster
from reference_pipeline import apply_reference_stage
from reference_records import load_reference_records, save_reference_records
from reference_search_cn import submit_confirmed_cn_candidates
from reference_search_english import (
    dedupe_reference_candidates,
    search_openalex_candidates,
    verify_candidates_with_crossref,
)


def _workspace_root(root_dir: Path | None = None) -> Path:
    return Path(root_dir) if root_dir is not None else Path(__file__).resolve().parents[1]


def _load_job_payload(job_id: str, *, root_dir: Path | None = None) -> dict[str, Any]:
    records = load_reference_records(root_dir=root_dir)
    payload = records.get(job_id)
    if not isinstance(payload, dict):
        raise ValueError("Unknown reference job.")
    return payload


def _save_job_payload(job_payload: dict[str, Any], *, root_dir: Path | None = None) -> dict[str, Any]:
    records = load_reference_records(root_dir=root_dir)
    records[str(job_payload["jobId"])] = job_payload
    save_reference_records(records, root_dir=root_dir)
    return job_payload


def list_reference_jobs(*, root_dir: Path | None = None) -> list[dict[str, Any]]:
    records = load_reference_records(root_dir=root_dir)
    return sorted(
        [value for value in records.values() if isinstance(value, dict)],
        key=lambda item: str(item.get("updatedAt", "") or item.get("createdAt", "")),
        reverse=True,
    )


def create_reference_job(source_path: str, *, root_dir: Path | None = None) -> dict[str, Any]:
    job = ReferenceJob(
        job_id=f"ref-{uuid.uuid4().hex}",
        source_path=source_path,
        status="uploaded",
    )
    payload = job.to_dict()
    payload = apply_reference_stage(payload, "uploaded")
    return _save_job_payload(payload, root_dir=root_dir)


def analyze_reference_job(job_id: str, *, root_dir: Path | None = None) -> dict[str, Any]:
    payload = _load_job_payload(job_id, root_dir=root_dir)
    document = parse_reference_document(payload["sourcePath"])
    sentence_candidates = score_sentence_candidates(document)
    clusters = build_topic_clusters(sentence_candidates)
    analysis_summary = recommend_reference_counts(document, clusters, candidate_count=len(sentence_candidates))

    payload["document"] = document.to_dict()
    payload["sentenceCandidates"] = [candidate.to_dict() for candidate in sentence_candidates]
    payload["topicClusters"] = [cluster.to_dict() for cluster in clusters]
    payload["analysisSummary"] = analysis_summary
    payload["analysisStatus"] = "completed"
    payload = apply_reference_stage(payload, "analyzed")
    _save_job_payload(payload, root_dir=root_dir)
    return payload


def configure_reference_job(
    job_id: str,
    *,
    chinese_count: int,
    english_count: int,
    root_dir: Path | None = None,
) -> dict[str, Any]:
    payload = _load_job_payload(job_id, root_dir=root_dir)
    payload["targetChineseCount"] = int(chinese_count)
    payload["targetEnglishCount"] = int(english_count)
    payload = apply_reference_stage(payload, "configured")
    _save_job_payload(payload, root_dir=root_dir)
    return payload


def search_reference_english_candidates(
    job_id: str,
    *,
    root_dir: Path | None = None,
    openalex_get=None,
    crossref_get=None,
) -> dict[str, Any]:
    payload = _load_job_payload(job_id, root_dir=root_dir)
    clusters = [
        TopicCluster.from_dict(item)
        for item in payload.get("topicClusters", [])
        if isinstance(item, dict)
    ]
    target_count = int(payload.get("targetEnglishCount", 5) or 5)
    searched = search_openalex_candidates(clusters, http_get=openalex_get)
    verified = verify_candidates_with_crossref(searched, http_get=crossref_get)
    deduped = dedupe_reference_candidates(verified)[:target_count]

    payload["englishCandidates"] = [candidate.to_dict() for candidate in deduped]
    payload["englishSearchStatus"] = "completed"
    payload = apply_reference_stage(payload, "english_searched")
    _save_job_payload(payload, root_dir=root_dir)
    return payload


def start_cn_browser_session(job_id: str, *, root_dir: Path | None = None) -> dict[str, Any]:
    payload = _load_job_payload(job_id, root_dir=root_dir)
    topic_clusters = payload.get("topicClusters", []) if isinstance(payload.get("topicClusters"), list) else []
    chinese_topics = topic_clusters[:10]
    payload["cnBrowserSession"] = {
        "status": "cn_waiting_login",
        "topicClusters": chinese_topics,
        "limitFlags": {"maxClusterCount": 10},
    }
    payload["chineseSearchStatus"] = "waiting_login"
    payload = apply_reference_stage(payload, "cn_waiting_login")
    _save_job_payload(payload, root_dir=root_dir)
    return {"jobId": job_id, "status": "cn_waiting_login", "topicClusters": chinese_topics}


def submit_reference_cn_candidates(
    job_id: str,
    candidates: list[dict[str, Any]],
    *,
    root_dir: Path | None = None,
) -> dict[str, Any]:
    payload = _load_job_payload(job_id, root_dir=root_dir)
    target_count = int(payload.get("targetChineseCount", 10) or 10)
    accepted = submit_confirmed_cn_candidates(candidates, max_per_job=target_count)
    payload["chineseCandidates"] = [candidate.to_dict() for candidate in accepted]
    payload["chineseSearchStatus"] = "completed"
    payload = apply_reference_stage(payload, "cn_candidates_confirmed")
    _save_job_payload(payload, root_dir=root_dir)
    return payload


def generate_reference_bindings(job_id: str, *, root_dir: Path | None = None) -> dict[str, Any]:
    payload = _load_job_payload(job_id, root_dir=root_dir)
    document = ReferenceDocument.from_dict(payload.get("document", {}))
    sentence_candidates = [
        SentenceCandidate.from_dict(item)
        for item in payload.get("sentenceCandidates", [])
        if isinstance(item, dict)
    ]
    all_candidates = [
        ReferenceCandidate.from_dict(item)
        for item in payload.get("englishCandidates", [])
        if isinstance(item, dict)
    ] + [
        ReferenceCandidate.from_dict(item)
        for item in payload.get("chineseCandidates", [])
        if isinstance(item, dict)
    ]
    bindings = bind_references_to_sentences(sentence_candidates, all_candidates)
    preview = build_reference_preview(document, bindings, all_candidates)

    payload["bindings"] = [binding.to_dict() for binding in bindings]
    payload["preview"] = preview.to_dict()
    payload["bindingStatus"] = "completed"
    payload = apply_reference_stage(payload, "bindings_generated")
    _save_job_payload(payload, root_dir=root_dir)
    return {"jobId": job_id, "preview": preview.to_dict(), "bindings": payload["bindings"]}


def export_reference_job(job_id: str, *, root_dir: Path | None = None) -> dict[str, Any]:
    payload = _load_job_payload(job_id, root_dir=root_dir)
    workspace_root = _workspace_root(root_dir)
    export_dir = workspace_root / "finish" / "reference" / "exports"
    export_dir.mkdir(parents=True, exist_ok=True)

    document = ReferenceDocument.from_dict(payload.get("document", {}))
    bindings = [
        __import__("reference_models").CitationBinding.from_dict(item)
        for item in payload.get("bindings", [])
        if isinstance(item, dict)
    ]
    all_candidates = [
        ReferenceCandidate.from_dict(item)
        for item in payload.get("englishCandidates", [])
        if isinstance(item, dict)
    ] + [
        ReferenceCandidate.from_dict(item)
        for item in payload.get("chineseCandidates", [])
        if isinstance(item, dict)
    ]

    result = export_reference_document(
        document,
        bindings,
        all_candidates,
        output_txt_path=export_dir / f"{job_id}.txt",
        output_docx_path=export_dir / f"{job_id}.docx",
    )
    payload["exportPaths"] = {
        "txt": result.output_path,
        "docx": result.output_docx_path,
    }
    payload["exportStatus"] = "completed"
    payload = apply_reference_stage(payload, "exported")
    _save_job_payload(payload, root_dir=root_dir)
    return {
        "jobId": job_id,
        "outputPath": result.output_path,
        "outputDocxPath": result.output_docx_path,
        "status": "exported",
    }


def get_reference_job_status(job_id: str, *, root_dir: Path | None = None) -> dict[str, Any]:
    return _load_job_payload(job_id, root_dir=root_dir)
