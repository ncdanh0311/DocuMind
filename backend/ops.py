"""Explicit operator commands. No command runs as part of API startup.

Use environment variables for credentials, never command-line connection strings.
Stop API/worker writes before migration, reconciliation, backup or restore.
"""
import argparse
from datetime import datetime, timezone, timedelta
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import urllib.request
import uuid

from sqlalchemy import MetaData, Table, inspect, select as sa_select, text
from sqlalchemy.engine import make_url
from sqlmodel import Session, select, create_engine
from backend.app.core.config import settings
from backend.app.models.models import Document, UploadReservation, StorageCleanupTask, SQLModel
from backend.app.services.storage import get_storage, source_path, validate_key
from backend.app.services.storage_quota import cleanup_pending, queue_cleanup


def checksum(stream):
    digest, size = hashlib.sha256(), 0
    while data := stream.read(1024 * 1024):
        digest.update(data); size += len(data)
    return digest.hexdigest(), size


def direct_url(): return settings.DATABASE_DIRECT_URL or settings.DATABASE_URL


def db_engine(url=None):
    url = url or direct_url()
    if "-pooler." in (make_url(url).host or ""):
        raise ValueError("Use DATABASE_DIRECT_URL for operator commands")
    return create_engine(url, hide_parameters=True, pool_pre_ping=True)


def preflight(engine):
    from alembic.config import Config
    from alembic.script import ScriptDirectory
    from alembic.runtime.migration import MigrationContext
    with engine.connect() as connection:
        tables = inspect(connection).get_table_names()
        revisions = list(MigrationContext.configure(connection).get_current_heads())
        vector = bool(connection.execute(text("SELECT 1 FROM pg_extension WHERE extname='vector'")).scalar())
    expected = ScriptDirectory.from_config(Config("alembic.ini")).get_current_head()
    result = {"database": {"revisions": revisions, "expected_revision": expected,
                           "vector": vector, "schema_current": revisions == [expected], "table_count": len(tables)}}
    project, branch, api_key = (os.environ.get(k) for k in ("NEON_PROJECT_ID", "NEON_BRANCH_ID", "NEON_API_KEY"))
    result["neon_control_plane"] = "not_configured"
    if all((project, branch, api_key)):
        if not all(part.replace("-", "").isalnum() for part in (project, branch)):
            raise ValueError("Invalid Neon project/branch identifier")
        request = urllib.request.Request(f"https://console.neon.tech/api/v2/projects/{project}/branches/{branch}/storage",
                                         headers={"Authorization": "Bearer " + api_key})
        with urllib.request.urlopen(request, timeout=15) as response: state = json.load(response)
        result["neon_control_plane"] = {"storage_enabled": bool(state.get("enabled")), "region": state.get("region")}
    if settings.STORAGE_BACKEND == "neon_s3":
        storage = get_storage()
        storage.client.head_bucket(Bucket=storage.bucket)
        acl = storage.client.get_bucket_acl(Bucket=storage.bucket)
        public_groups = ("AllUsers", "AuthenticatedUsers")
        if any(any(group in grant.get("Grantee", {}).get("URI", "") for group in public_groups)
               for grant in acl.get("Grants", [])):
            raise ValueError("Bucket must be private")
        result["storage"] = "reachable_private"
    else: result["storage"] = "local_development"
    return result


def reconcile(engine, apply=False, move=False):
    report = {"checked": 0, "updated": 0, "missing": [], "checksum_mismatch": []}
    with Session(engine) as session:
        for document in session.exec(select(Document)).all():
            report["checked"] += 1
            key = document.storage_key or f"{document.notebook_id}/{document.document_id}{Path(document.file_name).suffix.lower()}"
            storage = get_storage(document.storage_backend)
            if not storage.exists(key):
                report["missing"].append(str(document.document_id))
                if apply:
                    document.file_size_bytes = 0
                    document.text_error_code = "ERR_SOURCE_MISSING"
                    session.add(document)
                continue
            body = storage.open(key)
            try: digest, size = checksum(body)
            finally: body.close()
            if document.checksum and document.checksum != digest:
                report["checksum_mismatch"].append(str(document.document_id)); continue
            if move and document.storage_backend == "local":
                target = get_storage("neon_s3")
                if apply:
                    target.put_file(key, source_path(key))
                    body = target.open(key)
                    try: actual, actual_size = checksum(body)
                    finally: body.close()
                    if (actual, actual_size) != (digest, size): raise ValueError("ERR_STORAGE_VERIFY")
                    document.storage_backend = "neon_s3"
            if apply:
                document.storage_key, document.checksum, document.file_size_bytes = key, digest, size
                session.add(document); report["updated"] += 1
        if apply: session.commit()
    return report


def sweep(engine, apply=False):
    # Stale reservations remain charged until an operator confirms the uploader is stopped.
    with Session(engine) as session:
        stale = session.exec(select(UploadReservation).where(
            UploadReservation.created_at < datetime.now(timezone.utc) - timedelta(hours=1))).all()
        if apply:
            for row in stale:
                queue_cleanup(session, row.storage_backend, row.storage_key); session.delete(row)
            session.commit()
            return {"released_reservations": len(stale), **cleanup_pending(session)}
        return {"stale_reservations": len(stale), "pending_deletions": len(session.exec(select(StorageCleanupTask)).all())}


def pg_command(program, url, *args):
    parsed = make_url(url)
    env = os.environ.copy()
    env.update(PGHOST=parsed.host or "localhost", PGPORT=str(parsed.port or 5432),
               PGUSER=parsed.username or "postgres", PGPASSWORD=parsed.password or "", PGDATABASE=parsed.database or "")
    if parsed.query.get("sslmode"): env["PGSSLMODE"] = parsed.query["sslmode"]
    result = subprocess.run([program, *args], env=env, capture_output=True, timeout=600)
    if result.returncode: raise RuntimeError(program + " failed; check server/client version and credentials (details withheld)")


def backup(engine, output: Path):
    output = output.resolve()
    workspace = Path(__file__).resolve().parents[1]
    if output.is_relative_to(workspace): raise ValueError("Backup output must be outside the repository")
    if output.exists(): raise ValueError("Backup output must not exist")
    output.mkdir(parents=True)
    try:
        pg_command("pg_dump", direct_url(), "--format=custom", "--no-owner", "--no-privileges", "--file", str(output / "database.dump"))
        (output / "objects").mkdir()
        manifest = {"format": 1, "created_at": datetime.now(timezone.utc).isoformat(), "objects": [], "row_counts": {}}
        with engine.connect() as connection:
            manifest["revision"] = connection.execute(text("SELECT version_num FROM alembic_version")).scalar_one()
            from sqlalchemy import func
            for table in SQLModel.metadata.sorted_tables:
                manifest["row_counts"][table.name] = connection.execute(sa_select(func.count()).select_from(table)).scalar_one()
        with Session(engine) as session:
            if session.exec(select(UploadReservation)).first(): raise ValueError("Reconcile reservations before backup")
            for document in session.exec(select(Document)).all():
                if not document.storage_key: raise ValueError("Reconcile source keys before backup")
                name = hashlib.sha256(document.storage_key.encode()).hexdigest() + ".bin"
                body = get_storage(document.storage_backend).open(document.storage_key)
                try:
                    with (output / "objects" / name).open("wb") as target: shutil.copyfileobj(body, target)
                finally: body.close()
                with (output / "objects" / name).open("rb") as stream: digest, size = checksum(stream)
                if document.checksum and digest != document.checksum: raise ValueError("ERR_SOURCE_CHANGED")
                manifest["objects"].append({"document_id": str(document.document_id), "key": document.storage_key,
                                             "file": name, "sha256": digest, "size": size})
        with (output / "database.dump").open("rb") as stream: manifest["database_sha256"] = checksum(stream)[0]
        (output / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
        return {"objects": len(manifest["objects"]), "revision": manifest["revision"]}
    except Exception:
        # Keep incomplete files for diagnosis; absence of a manifest means this is not a usable backup.
        raise


def verify_backup(directory: Path):
    manifest = json.loads((directory / "manifest.json").read_text(encoding="utf-8"))
    if manifest.get("format") != 1: raise ValueError("Unsupported backup format")
    with (directory / "database.dump").open("rb") as stream:
        if checksum(stream)[0] != manifest["database_sha256"]: raise ValueError("Database checksum mismatch")
    seen = set()
    for entry in manifest["objects"]:
        validate_key(entry["key"])
        if entry["key"] in seen: raise ValueError("Duplicate storage key")
        seen.add(entry["key"])
        if Path(entry["file"]).name != entry["file"] or "\\" in entry["file"]: raise ValueError("Invalid backup filename")
        with (directory / "objects" / entry["file"]).open("rb") as stream:
            if checksum(stream) != (entry["sha256"], entry["size"]): raise ValueError("Object checksum mismatch")
    return manifest


def restore(engine, directory: Path):
    manifest = verify_backup(directory)
    with engine.connect() as connection:
        if inspect(connection).get_table_names(): raise ValueError("Restore requires an empty target database")
    storage = get_storage()
    if storage.list_keys(): raise ValueError("Restore requires an empty target bucket/directory")
    uploaded = []
    try:
        for entry in manifest["objects"]:
            storage.put_file(entry["key"], directory / "objects" / entry["file"]); uploaded.append(entry["key"])
        pg_command("pg_restore", direct_url(), "--dbname", make_url(direct_url()).database,
                   "--no-owner", "--no-privileges", "--single-transaction", str(directory / "database.dump"))
    except Exception:
        for key in uploaded: storage.delete(key)
        raise
    with Session(engine) as session:
        from sqlalchemy import func
        for name, expected in manifest.get("row_counts", {}).items():
            table = SQLModel.metadata.tables.get(name)
            if table is None or session.exec(select(func.count()).select_from(table)).one() != expected:
                raise ValueError("Restored row count mismatch")
        for entry in manifest["objects"]:
            document = session.get(Document, uuid.UUID(entry["document_id"]))
            if not document or document.storage_key != entry["key"]: raise ValueError("Restored metadata mismatch")
            document.storage_backend, document.file_size_bytes = settings.STORAGE_BACKEND, entry["size"]
            session.add(document)
        session.commit()
    return {"restored_objects": len(uploaded), "revision": manifest["revision"]}


def import_legacy(source, target, apply=False):
    """Copy to an already migrated EMPTY database, never mutate the legacy database."""
    report = {}
    with source.connect() as origin, target.begin() as destination:
        existing = set(inspect(origin).get_table_names())
        if "documents" in existing and "current_version" in {c["name"] for c in inspect(origin).get_columns("documents")}:
            raise ValueError("Source already uses versioned schema; use backup/restore instead")
        from backend.app.models import models as model_module
        model_classes = {value.__table__.name: value for value in vars(model_module).values()
                         if isinstance(value, type) and issubclass(value, SQLModel) and hasattr(value, "__table__")}
        for table in SQLModel.metadata.sorted_tables:
            if table.name == "storage_ledger": continue
            if destination.execute(sa_select(table).limit(1)).first(): raise ValueError("Legacy import requires empty target tables")
        document_notebooks = {}
        for table in SQLModel.metadata.sorted_tables:
            if table.name not in existing or table.name in ("auth_sessions", "password_reset_challenges", "auth_rate_limits", "jobs", "upload_reservations", "storage_cleanup_tasks", "storage_ledger"):
                continue
            legacy = Table(table.name, MetaData(), autoload_with=origin)
            count = 0
            for raw in origin.execute(sa_select(legacy)).mappings():
                values = {key: value for key, value in raw.items() if key in table.c}
                for key, value in list(values.items()):
                    if isinstance(value, datetime) and value.tzinfo is None: values[key] = value.replace(tzinfo=timezone.utc)
                if table.name == "documents":
                    document_notebooks[values["document_id"]] = values["notebook_id"]
                    values.update(current_version=0, requested_version=0, text_status="not_started",
                                  status="uploaded", error_code="ERR_REPROCESS_REQUIRED", storage_backend="local", file_size_bytes=None)
                    values.setdefault("storage_key", f"{values['notebook_id']}/{values['document_id']}{Path(values['file_name']).suffix.lower()}")
                if table.name == "document_chunks":
                    values["version"] = 0
                    if isinstance(values.get("embedding"), str): values["embedding"] = json.loads(values["embedding"])
                if table.name == "summaries":
                    values.setdefault("notebook_id", document_notebooks.get(values.get("document_id")))
                    values.update(model_version=values.get("model_version", "legacy"), pipeline_version="legacy",
                                  cache_key="legacy:" + str(values["summary_id"]),
                                  status="succeeded" if values.get("content") else "failed")
                record = model_classes[table.name](**values)
                values = {column.name: getattr(record, column.name) for column in table.columns}
                for column in table.columns:
                    if isinstance(column.type, __import__('sqlalchemy').Uuid) and isinstance(values[column.name], str):
                        values[column.name] = uuid.UUID(values[column.name])
                if apply: destination.execute(table.insert().values(**values))
                count += 1
            report[table.name] = count
        if apply:
            from sqlalchemy import func
            for name, expected in report.items():
                actual = destination.execute(sa_select(func.count()).select_from(SQLModel.metadata.tables[name])).scalar_one()
                if actual != expected: raise ValueError("Legacy row count mismatch")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["preflight", "reconcile", "migrate-files", "cleanup", "backup", "restore", "verify-backup", "import-legacy"])
    parser.add_argument("--apply", action="store_true", help="Required for data-changing operator commands")
    parser.add_argument("--writes-stopped", action="store_true", help="Confirm API and worker have been stopped")
    parser.add_argument("--directory", type=Path)
    args = parser.parse_args()
    try:
        if args.command == "verify-backup":
            if not args.directory: raise ValueError("--directory is required")
            manifest = verify_backup(args.directory)
            print(json.dumps({"verified_objects": len(manifest["objects"])})); return
        engine = db_engine()
        try:
            if args.command == "preflight": result = preflight(engine)
            else:
                if args.apply and not args.writes_stopped: raise ValueError("--writes-stopped is required")
                if args.command in ("backup", "restore"):
                    if not args.directory or not args.writes_stopped: raise ValueError("--directory and --writes-stopped are required")
                    if args.command == "restore" and not args.apply: raise ValueError("Restore requires --apply")
                    result = backup(engine, args.directory) if args.command == "backup" else restore(engine, args.directory)
                elif args.command == "cleanup": result = sweep(engine, args.apply)
                elif args.command == "import-legacy":
                    legacy = os.environ.get("LEGACY_DATABASE_URL")
                    if not legacy or make_url(legacy) == make_url(direct_url()): raise ValueError("A separate LEGACY_DATABASE_URL is required")
                    source = db_engine(legacy)
                    try: result = import_legacy(source, engine, args.apply)
                    finally: source.dispose()
                else: result = reconcile(engine, args.apply, args.command == "migrate-files")
            print(json.dumps(result, ensure_ascii=False, indent=2))
        finally: engine.dispose()
    except Exception as exc:
        # Provider and subprocess exceptions can contain credentials. Never print their text.
        if isinstance(exc, ValueError): print("Operation refused: " + str(exc))
        else: print("Operation failed (" + type(exc).__name__ + "). Check configuration; sensitive details withheld.")
        raise SystemExit(1) from None


if __name__ == "__main__": main()
