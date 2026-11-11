"""Preserve legacy citations before cascading chunk deletion."""
from sqlmodel import select
from backend.app.models.models import Citation, DocumentChunk, QAHistory, Summary


def preserve_document_history(session, document):
    rows = session.exec(select(Citation, DocumentChunk).join(DocumentChunk, Citation.chunk_id == DocumentChunk.docuchunk_id)
                        .where(DocumentChunk.document_id == document.document_id)).all()
    for citation, chunk in rows:
        history = session.get(QAHistory, citation.qa_id)
        if not history: continue
        snapshot = list(history.citation_snapshot)
        if any(item.get("document_id") == str(document.document_id) and item.get("start_offset") == citation.start_offset
               and item.get("end_offset") == citation.end_offset for item in snapshot): continue
        snapshot.append({"document_id": str(document.document_id), "source_title": document.file_name,
            "version": chunk.version, "snippet": chunk.content, "start_offset": citation.start_offset,
            "end_offset": citation.end_offset, "page_number": chunk.page_number, "page_end": chunk.page_end,
            "section_path": chunk.section_path})
        history.citation_snapshot = snapshot; session.add(history)
    for summary in session.exec(select(Summary).where(Summary.document_id == document.document_id)).all():
        if not summary.source_snapshot:
            summary.source_snapshot = [{"document_id": str(document.document_id), "source_title": document.file_name,
                                        "version": document.current_version}]
            session.add(summary)
