from __future__ import annotations

from pathlib import Path

from docx_pipeline import write_docx_paragraphs
from reference_binding import build_ordered_reference_list
from reference_models import CitationBinding, ReferenceApplyResult, ReferenceCandidate, ReferenceDocument, ReferencePreview


def _format_reference_line(index: int, candidate: ReferenceCandidate) -> str:
    authors = ", ".join(candidate.authors) if candidate.authors else "Unknown"
    year = candidate.year or "n.d."
    source = candidate.source or candidate.journal or "Unknown source"
    return f"[{index}] {authors} ({year}). {candidate.title}. {source}."


def _annotate_document(document: ReferenceDocument, bindings: list[CitationBinding]) -> list[str]:
    binding_map: dict[str, list[CitationBinding]] = {}
    for binding in bindings:
        binding_map.setdefault(binding.sentence_id, []).append(binding)

    paragraphs: list[str] = []
    for paragraph in document.paragraphs:
        text = paragraph.text
        for sentence in paragraph.sentences:
            sentence_bindings = sorted(binding_map.get(sentence.sentence_id, []), key=lambda item: item.citation_index)
            if not sentence_bindings:
                continue
            marker_text = "".join(binding.marker for binding in sentence_bindings)
            text = text.replace(sentence.text, f"{sentence.text}{marker_text}", 1)
        paragraphs.append(text)
    return paragraphs


def build_reference_preview(
    document: ReferenceDocument,
    bindings: list[CitationBinding],
    candidates: list[ReferenceCandidate],
) -> ReferencePreview:
    ordered_candidates = build_ordered_reference_list(bindings, candidates)
    annotated_paragraphs = _annotate_document(document, bindings)
    reference_lines = ["参考文献"] + [
        _format_reference_line(index, candidate)
        for index, candidate in enumerate(ordered_candidates, start=1)
    ]

    return ReferencePreview(
        job_id=document.source_path,
        annotated_text="\n\n".join(annotated_paragraphs),
        references_text="\n".join(reference_lines),
        bindings=bindings,
        used_candidates=ordered_candidates,
    )


def export_reference_document(
    document: ReferenceDocument,
    bindings: list[CitationBinding],
    candidates: list[ReferenceCandidate],
    *,
    output_txt_path: str | Path,
    output_docx_path: str | Path,
) -> ReferenceApplyResult:
    preview = build_reference_preview(document, bindings, candidates)
    txt_path = Path(output_txt_path)
    docx_path = Path(output_docx_path)
    txt_path.parent.mkdir(parents=True, exist_ok=True)
    docx_path.parent.mkdir(parents=True, exist_ok=True)

    full_text = f"{preview.annotated_text}\n\n{preview.references_text}".strip()
    txt_path.write_text(full_text, encoding="utf-8")

    paragraphs = preview.annotated_text.split("\n\n") if preview.annotated_text else []
    paragraphs.extend(preview.references_text.split("\n"))
    write_docx_paragraphs(paragraphs, docx_path)

    return ReferenceApplyResult(
        job_id=document.source_path,
        output_path=str(txt_path),
        output_docx_path=str(docx_path),
        reference_count=len(preview.used_candidates),
        binding_count=len(bindings),
        status="completed",
    )
