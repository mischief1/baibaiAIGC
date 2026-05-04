from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


def _copy_list(values: list[Any] | None) -> list[Any]:
    if not values:
        return []
    copied: list[Any] = []
    for value in values:
        if isinstance(value, dict):
            copied.append(dict(value))
        elif isinstance(value, list):
            copied.append(list(value))
        else:
            copied.append(value)
    return copied


def _copy_dict(values: dict[str, Any] | None) -> dict[str, Any]:
    if not values:
        return {}
    copied: dict[str, Any] = {}
    for key, value in values.items():
        if isinstance(value, dict):
            copied[key] = dict(value)
        elif isinstance(value, list):
            copied[key] = list(value)
        else:
            copied[key] = value
    return copied


@dataclass
class SentenceNode:
    sentence_id: str
    paragraph_id: str
    text: str
    order: int = 0
    section_title: str = ""
    has_citation: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "sentenceId": self.sentence_id,
            "paragraphId": self.paragraph_id,
            "text": self.text,
            "order": self.order,
            "sectionTitle": self.section_title,
            "hasCitation": self.has_citation,
            "metadata": _copy_dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "SentenceNode":
        return cls(
            sentence_id=str(payload.get("sentenceId", "")),
            paragraph_id=str(payload.get("paragraphId", "")),
            text=str(payload.get("text", "")),
            order=int(payload.get("order", 0) or 0),
            section_title=str(payload.get("sectionTitle", "") or ""),
            has_citation=bool(payload.get("hasCitation")),
            metadata=_copy_dict(payload.get("metadata")),
        )


@dataclass
class ParagraphNode:
    paragraph_id: str
    text: str
    order: int = 0
    section_title: str = ""
    sentences: list[SentenceNode] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "paragraphId": self.paragraph_id,
            "text": self.text,
            "order": self.order,
            "sectionTitle": self.section_title,
            "sentences": [sentence.to_dict() for sentence in self.sentences],
            "metadata": _copy_dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "ParagraphNode":
        sentence_payloads = payload.get("sentences") if isinstance(payload.get("sentences"), list) else []
        return cls(
            paragraph_id=str(payload.get("paragraphId", "")),
            text=str(payload.get("text", "")),
            order=int(payload.get("order", 0) or 0),
            section_title=str(payload.get("sectionTitle", "") or ""),
            sentences=[
                SentenceNode.from_dict(item)
                for item in sentence_payloads
                if isinstance(item, dict)
            ],
            metadata=_copy_dict(payload.get("metadata")),
        )


@dataclass
class ReferenceDocument:
    source_path: str
    file_type: str = ""
    title: str = ""
    paragraphs: list[ParagraphNode] = field(default_factory=list)
    sentence_count: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "sourcePath": self.source_path,
            "fileType": self.file_type,
            "title": self.title,
            "paragraphs": [paragraph.to_dict() for paragraph in self.paragraphs],
            "sentenceCount": self.sentence_count,
            "metadata": _copy_dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "ReferenceDocument":
        paragraph_payloads = payload.get("paragraphs") if isinstance(payload.get("paragraphs"), list) else []
        return cls(
            source_path=str(payload.get("sourcePath", "")),
            file_type=str(payload.get("fileType", "") or ""),
            title=str(payload.get("title", "") or ""),
            paragraphs=[
                ParagraphNode.from_dict(item)
                for item in paragraph_payloads
                if isinstance(item, dict)
            ],
            sentence_count=int(payload.get("sentenceCount", 0) or 0),
            metadata=_copy_dict(payload.get("metadata")),
        )


@dataclass
class SentenceCandidate:
    sentence_id: str
    text: str
    score: float = 0.0
    paragraph_id: str = ""
    section_title: str = ""
    matched_signals: list[str] = field(default_factory=list)
    keywords: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "sentenceId": self.sentence_id,
            "text": self.text,
            "score": self.score,
            "paragraphId": self.paragraph_id,
            "sectionTitle": self.section_title,
            "matchedSignals": _copy_list(self.matched_signals),
            "keywords": _copy_list(self.keywords),
            "metadata": _copy_dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "SentenceCandidate":
        return cls(
            sentence_id=str(payload.get("sentenceId", "")),
            text=str(payload.get("text", "")),
            score=float(payload.get("score", 0.0) or 0.0),
            paragraph_id=str(payload.get("paragraphId", "") or ""),
            section_title=str(payload.get("sectionTitle", "") or ""),
            matched_signals=[str(item) for item in payload.get("matchedSignals", []) if isinstance(item, str)],
            keywords=[str(item) for item in payload.get("keywords", []) if isinstance(item, str)],
            metadata=_copy_dict(payload.get("metadata")),
        )


@dataclass
class TopicCluster:
    topic_id: str
    label: str
    query: str = ""
    sentence_ids: list[str] = field(default_factory=list)
    keywords: list[str] = field(default_factory=list)
    summary: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "topicId": self.topic_id,
            "label": self.label,
            "query": self.query,
            "sentenceIds": _copy_list(self.sentence_ids),
            "keywords": _copy_list(self.keywords),
            "summary": self.summary,
            "metadata": _copy_dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "TopicCluster":
        return cls(
            topic_id=str(payload.get("topicId", "")),
            label=str(payload.get("label", "")),
            query=str(payload.get("query", "") or ""),
            sentence_ids=[str(item) for item in payload.get("sentenceIds", []) if isinstance(item, str)],
            keywords=[str(item) for item in payload.get("keywords", []) if isinstance(item, str)],
            summary=str(payload.get("summary", "") or ""),
            metadata=_copy_dict(payload.get("metadata")),
        )


@dataclass
class ReferenceCandidate:
    candidate_id: str
    title: str
    authors: list[str] = field(default_factory=list)
    year: str = ""
    source: str = ""
    language: str = ""
    doi: str = ""
    url: str = ""
    journal: str = ""
    abstract: str = ""
    query: str = ""
    relevance_score: float = 0.0
    matched_topic_ids: list[str] = field(default_factory=list)
    verified: bool = False
    user_confirmed: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "candidateId": self.candidate_id,
            "title": self.title,
            "authors": _copy_list(self.authors),
            "year": self.year,
            "source": self.source,
            "language": self.language,
            "doi": self.doi,
            "url": self.url,
            "journal": self.journal,
            "abstract": self.abstract,
            "query": self.query,
            "relevanceScore": self.relevance_score,
            "matchedTopicIds": _copy_list(self.matched_topic_ids),
            "verified": self.verified,
            "userConfirmed": self.user_confirmed,
            "metadata": _copy_dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "ReferenceCandidate":
        return cls(
            candidate_id=str(payload.get("candidateId", "")),
            title=str(payload.get("title", "")),
            authors=[str(item) for item in payload.get("authors", []) if isinstance(item, str)],
            year=str(payload.get("year", "") or ""),
            source=str(payload.get("source", "") or ""),
            language=str(payload.get("language", "") or ""),
            doi=str(payload.get("doi", "") or ""),
            url=str(payload.get("url", "") or ""),
            journal=str(payload.get("journal", "") or ""),
            abstract=str(payload.get("abstract", "") or ""),
            query=str(payload.get("query", "") or ""),
            relevance_score=float(payload.get("relevanceScore", 0.0) or 0.0),
            matched_topic_ids=[str(item) for item in payload.get("matchedTopicIds", []) if isinstance(item, str)],
            verified=bool(payload.get("verified")),
            user_confirmed=bool(payload.get("userConfirmed")),
            metadata=_copy_dict(payload.get("metadata")),
        )


@dataclass
class CitationBinding:
    binding_id: str
    sentence_id: str
    paragraph_id: str
    candidate_id: str
    citation_index: int = 0
    marker: str = ""
    confidence: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "bindingId": self.binding_id,
            "sentenceId": self.sentence_id,
            "paragraphId": self.paragraph_id,
            "candidateId": self.candidate_id,
            "citationIndex": self.citation_index,
            "marker": self.marker,
            "confidence": self.confidence,
            "metadata": _copy_dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "CitationBinding":
        return cls(
            binding_id=str(payload.get("bindingId", "")),
            sentence_id=str(payload.get("sentenceId", "")),
            paragraph_id=str(payload.get("paragraphId", "") or ""),
            candidate_id=str(payload.get("candidateId", "")),
            citation_index=int(payload.get("citationIndex", 0) or 0),
            marker=str(payload.get("marker", "") or ""),
            confidence=float(payload.get("confidence", 0.0) or 0.0),
            metadata=_copy_dict(payload.get("metadata")),
        )


@dataclass
class ReferencePreview:
    job_id: str
    annotated_text: str = ""
    references_text: str = ""
    bindings: list[CitationBinding] = field(default_factory=list)
    used_candidates: list[ReferenceCandidate] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "jobId": self.job_id,
            "annotatedText": self.annotated_text,
            "referencesText": self.references_text,
            "bindings": [binding.to_dict() for binding in self.bindings],
            "usedCandidates": [candidate.to_dict() for candidate in self.used_candidates],
            "metadata": _copy_dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "ReferencePreview":
        binding_payloads = payload.get("bindings") if isinstance(payload.get("bindings"), list) else []
        candidate_payloads = payload.get("usedCandidates") if isinstance(payload.get("usedCandidates"), list) else []
        return cls(
            job_id=str(payload.get("jobId", "")),
            annotated_text=str(payload.get("annotatedText", "") or ""),
            references_text=str(payload.get("referencesText", "") or ""),
            bindings=[
                CitationBinding.from_dict(item)
                for item in binding_payloads
                if isinstance(item, dict)
            ],
            used_candidates=[
                ReferenceCandidate.from_dict(item)
                for item in candidate_payloads
                if isinstance(item, dict)
            ],
            metadata=_copy_dict(payload.get("metadata")),
        )


@dataclass
class ReferenceApplyResult:
    job_id: str
    output_path: str = ""
    output_docx_path: str = ""
    reference_count: int = 0
    binding_count: int = 0
    status: str = "pending"
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "jobId": self.job_id,
            "outputPath": self.output_path,
            "outputDocxPath": self.output_docx_path,
            "referenceCount": self.reference_count,
            "bindingCount": self.binding_count,
            "status": self.status,
            "metadata": _copy_dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "ReferenceApplyResult":
        return cls(
            job_id=str(payload.get("jobId", "")),
            output_path=str(payload.get("outputPath", "") or ""),
            output_docx_path=str(payload.get("outputDocxPath", "") or ""),
            reference_count=int(payload.get("referenceCount", 0) or 0),
            binding_count=int(payload.get("bindingCount", 0) or 0),
            status=str(payload.get("status", "pending") or "pending"),
            metadata=_copy_dict(payload.get("metadata")),
        )


@dataclass
class ReferenceJob:
    job_id: str
    source_path: str
    status: str = "created"
    analysis_status: str = "pending"
    english_search_status: str = "pending"
    chinese_search_status: str = "pending"
    binding_status: str = "pending"
    export_status: str = "pending"
    document: dict[str, Any] = field(default_factory=dict)
    analysis_summary: dict[str, Any] = field(default_factory=dict)
    sentence_candidates: list[dict[str, Any]] = field(default_factory=list)
    topic_clusters: list[dict[str, Any]] = field(default_factory=list)
    english_candidates: list[ReferenceCandidate] = field(default_factory=list)
    chinese_candidates: list[ReferenceCandidate] = field(default_factory=list)
    bindings: list[CitationBinding] = field(default_factory=list)
    export_paths: dict[str, Any] = field(default_factory=dict)
    created_at: str = ""
    updated_at: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "jobId": self.job_id,
            "sourcePath": self.source_path,
            "status": self.status,
            "analysisStatus": self.analysis_status,
            "englishSearchStatus": self.english_search_status,
            "chineseSearchStatus": self.chinese_search_status,
            "bindingStatus": self.binding_status,
            "exportStatus": self.export_status,
            "document": _copy_dict(self.document),
            "analysisSummary": _copy_dict(self.analysis_summary),
            "sentenceCandidates": _copy_list(self.sentence_candidates),
            "topicClusters": _copy_list(self.topic_clusters),
            "englishCandidates": [candidate.to_dict() for candidate in self.english_candidates],
            "chineseCandidates": [candidate.to_dict() for candidate in self.chinese_candidates],
            "bindings": [binding.to_dict() for binding in self.bindings],
            "exportPaths": _copy_dict(self.export_paths),
            "createdAt": self.created_at,
            "updatedAt": self.updated_at,
            "metadata": _copy_dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "ReferenceJob":
        english_payloads = payload.get("englishCandidates") if isinstance(payload.get("englishCandidates"), list) else []
        chinese_payloads = payload.get("chineseCandidates") if isinstance(payload.get("chineseCandidates"), list) else []
        binding_payloads = payload.get("bindings") if isinstance(payload.get("bindings"), list) else []
        return cls(
            job_id=str(payload.get("jobId", "")),
            source_path=str(payload.get("sourcePath", "")),
            status=str(payload.get("status", "created") or "created"),
            analysis_status=str(payload.get("analysisStatus", "pending") or "pending"),
            english_search_status=str(payload.get("englishSearchStatus", "pending") or "pending"),
            chinese_search_status=str(payload.get("chineseSearchStatus", "pending") or "pending"),
            binding_status=str(payload.get("bindingStatus", "pending") or "pending"),
            export_status=str(payload.get("exportStatus", "pending") or "pending"),
            document=_copy_dict(payload.get("document")),
            analysis_summary=_copy_dict(payload.get("analysisSummary")),
            sentence_candidates=_copy_list(payload.get("sentenceCandidates")),
            topic_clusters=_copy_list(payload.get("topicClusters")),
            english_candidates=[
                ReferenceCandidate.from_dict(item)
                for item in english_payloads
                if isinstance(item, dict)
            ],
            chinese_candidates=[
                ReferenceCandidate.from_dict(item)
                for item in chinese_payloads
                if isinstance(item, dict)
            ],
            bindings=[
                CitationBinding.from_dict(item)
                for item in binding_payloads
                if isinstance(item, dict)
            ],
            export_paths=_copy_dict(payload.get("exportPaths")),
            created_at=str(payload.get("createdAt", "") or ""),
            updated_at=str(payload.get("updatedAt", "") or ""),
            metadata=_copy_dict(payload.get("metadata")),
        )
