"""Hierarchical summarization with complete token-bounded input coverage."""
import uuid
from fastapi import HTTPException
from sqlmodel import Session, select
from backend.app.models.models import DocumentVersion, Job, Summary
from backend.app.services.job_service import PipelineError, job_service
from backend.app.services.summary_service import source_snapshot
from backend.processor.canonical import validate_spans

class SummaryWorker:
    def __init__(self, engine, ai): self.engine, self.ai = engine, ai

    def execute(self, claim: Job, check=lambda: None):
        model, model_version = claim.payload["model"], claim.payload["model_version"]
        capability = self.ai.capability(model)
        if capability["version"] != model_version: raise PipelineError("ERR_MODEL_VERSION_CHANGED")
        max_output = min(128, max(16, capability["max_input_tokens"] // 4))
        units = []
        with Session(self.engine) as session:
            if source_snapshot(session, claim.notebook_id) != claim.payload["snapshot"]: raise PipelineError("ERR_SOURCE_CHANGED")
            versions = []
            for source in claim.payload["snapshot"]:
                version = session.exec(select(DocumentVersion).where(DocumentVersion.document_id == uuid.UUID(source["document_id"]), DocumentVersion.version == source["version"])).first()
                if not version: raise PipelineError("ERR_SOURCE_NOT_READY")
                versions.append((source, version.canonical_text, version.sections))
        for source, text, sections in versions:
            section_index, previous_path = -1, None
            for section in sections:
                check()
                path = section.get("section_path") or "Nội dung"
                if section_index < 0 or path != previous_path: section_index += 1
                previous_path = path
                section_text = text[section["start"]:section["end"]]
                spans = self.ai.split(section_text, model)
                validate_spans(section_text, spans)
                for span in spans:
                    units.append({"document_id": source["document_id"], "version": source["version"],
                        "start_offset": section["start"] + span["start"], "end_offset": section["start"] + span["end"],
                        "section_path": path, "section_index": section_index, "text": section_text[span["start"]:span["end"]]})
        if not units: raise PipelineError("ERR_EMPTY_DOCUMENT")
        with Session(self.engine) as session:
            job_service.fenced(session, claim)
            summary = session.get(Summary, claim.summary_id)
            summary.parts, summary.processed_units, summary.total_units = [], 0, len(units)
            session.add(summary); session.commit()
        def summarize(text):
            check()
            response = self.ai.request("/summarize", {"text": text, "model_type": model, "expected_version": model_version, "max_output_tokens": max_output})
            if response.get("model_version") != model_version: raise PipelineError("ERR_MODEL_VERSION_CHANGED")
            result = response.get("summary", "").strip()
            if not result: raise PipelineError("ERR_EMPTY_SUMMARY")
            return result
        parts = []
        for unit in units:
            output = summarize(unit["text"])
            parts.append({key: value for key, value in unit.items() if key != "text"} | {"summary": output})
            with Session(self.engine) as session:
                job = job_service.fenced(session, claim)
                summary = session.get(Summary, claim.summary_id)
                summary.parts, summary.processed_units = list(parts), len(parts)
                job.progress = 0.8 * len(parts) / len(units)
                session.add(summary); session.add(job); session.commit()
        def reduce(texts):
            values = list(texts)
            for _ in range(12):
                check()
                if len(values) == 1: return values[0]
                combined = "\n\n".join(values)
                spans = self.ai.split(combined, model)
                validate_spans(combined, spans)
                next_values = [summarize(combined[span["start"]:span["end"]]) for span in spans]
                if len(next_values) >= len(values): raise PipelineError("ERR_SUMMARY_REDUCTION")
                values = next_values
            raise PipelineError("ERR_SUMMARY_REDUCTION")
        document_summaries = []
        for source in claim.payload["snapshot"]:
            document_parts = [p for p in parts if p["document_id"] == source["document_id"]]
            groups = {}
            for part in document_parts: groups.setdefault(part["section_index"], []).append(part["summary"])
            section_summaries = [reduce(values) for values in groups.values()]
            document_summaries.append(reduce(section_summaries))
        result = reduce(document_summaries)
        check()
        with Session(self.engine) as session:
            job = job_service.fenced(session, claim)
            if source_snapshot(session, claim.notebook_id) != claim.payload["snapshot"]: raise PipelineError("ERR_SOURCE_CHANGED")
            summary = session.get(Summary, claim.summary_id)
            summary.content, summary.status, summary.error_code = result, "succeeded", None
            session.add(summary); job_service.succeed(session, job); session.commit()
