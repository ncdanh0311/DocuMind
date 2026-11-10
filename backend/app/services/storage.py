"""Private local/Neon object storage. Credentials stay on the backend."""
from contextlib import contextmanager
from pathlib import Path, PurePosixPath
import shutil
import tempfile
from backend.app.core.config import settings


def validate_key(key: str) -> str:
    if not key or "\\" in key or any(ord(c) < 32 for c in key):
        raise ValueError("ERR_INVALID_STORAGE_KEY")
    if PurePosixPath(key).is_absolute() or any(p in (".", "..", "") for p in key.split("/")):
        raise ValueError("ERR_INVALID_STORAGE_KEY")
    return key


def storage_root() -> Path:
    root = Path(settings.UPLOAD_DIR).resolve()
    root.mkdir(parents=True, exist_ok=True)
    return root


def source_path(key: str) -> Path:
    root = storage_root()
    path = (root / validate_key(key)).resolve()
    if not path.is_relative_to(root): raise ValueError("ERR_INVALID_STORAGE_KEY")
    return path


class LocalStorage:
    def put_file(self, key, path):
        target = source_path(key)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, target)

    def open(self, key): return source_path(key).open("rb")
    def delete(self, key): source_path(key).unlink(missing_ok=True)
    def exists(self, key): return source_path(key).is_file()

    def list_keys(self):
        root = storage_root()
        return [p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file()]


class NeonStorage:
    def __init__(self):
        from urllib.parse import urlparse
        if not all((settings.AWS_ENDPOINT_URL_S3, settings.AWS_ACCESS_KEY_ID,
                    settings.AWS_SECRET_ACCESS_KEY, settings.AWS_REGION)):
            raise ValueError("ERR_STORAGE_NOT_CONFIGURED")
        endpoint = urlparse(settings.AWS_ENDPOINT_URL_S3)
        if endpoint.scheme != "https" or not endpoint.hostname or endpoint.username or endpoint.password:
            raise ValueError("ERR_STORAGE_ENDPOINT")
        import boto3
        from botocore.config import Config
        self.client = boto3.client("s3", endpoint_url=settings.AWS_ENDPOINT_URL_S3,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID, aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_REGION,
            config=Config(signature_version="s3v4", s3={"addressing_style": "path"},
                          request_checksum_calculation="when_required", response_checksum_validation="when_required",
                          connect_timeout=5, read_timeout=30, retries={"max_attempts": 2}))
        self.bucket = settings.STORAGE_BUCKET

    def put_file(self, key, path):
        with Path(path).open("rb") as stream:
            self.client.put_object(Bucket=self.bucket, Key=validate_key(key), Body=stream,
                                   ContentLength=Path(path).stat().st_size, ContentType="application/octet-stream")

    def open(self, key):
        return self.client.get_object(Bucket=self.bucket, Key=validate_key(key))["Body"]

    def delete(self, key):
        self.client.delete_object(Bucket=self.bucket, Key=validate_key(key))

    def exists(self, key):
        from botocore.exceptions import ClientError
        try:
            self.client.head_object(Bucket=self.bucket, Key=validate_key(key))
            return True
        except ClientError as exc:
            if str(exc.response.get("Error", {}).get("Code")) in ("404", "NoSuchKey", "NotFound"):
                return False
            raise

    def list_keys(self):
        keys, token = [], None
        while True:
            args = {"Bucket": self.bucket}
            if token: args["ContinuationToken"] = token
            page = self.client.list_objects_v2(**args)
            keys.extend(item["Key"] for item in page.get("Contents", []))
            if not page.get("IsTruncated"): return keys
            token = page["NextContinuationToken"]


def get_storage(backend: str | None = None):
    backend = backend or settings.STORAGE_BACKEND
    if backend == "local": return LocalStorage()
    if backend == "neon_s3": return NeonStorage()
    raise ValueError("ERR_STORAGE_BACKEND")


@contextmanager
def materialize(key: str, backend: str, suffix: str = ""):
    if backend == "local":
        yield source_path(key)
        return
    with tempfile.TemporaryDirectory(prefix="documind-source-") as directory:
        path = Path(directory) / ("source" + suffix)
        body = get_storage(backend).open(key)
        try:
            with path.open("wb") as target:
                size = 0
                while block := body.read(1024 * 1024):
                    size += len(block)
                    if size > settings.MAX_UPLOAD_BYTES: raise ValueError("ERR_FILE_TOO_LARGE")
                    target.write(block)
        finally:
            body.close()
        yield path
