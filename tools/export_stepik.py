#!/usr/bin/env python3
"""Read-only, standard-library export of an owned Stepik course.

Credentials are read from STEPIK_ACCESS_TOKEN, or from STEPIK_CLIENT_ID and
STEPIK_CLIENT_SECRET. Missing client credentials are requested without echo.
No credentials or token responses are written to the export. Only the OAuth
token request uses POST; all course and asset requests use GET.

Exit codes: 0 = requested mode completed, 1 = fatal setup/authentication error,
2 = partial export, 130 = interrupted. --skip-assets intentionally leaves the
overall archive partial, but returns 0 when all course content was exported.
--public explicitly requests an unauthenticated, partial snapshot; it never
prompts for credentials or silently substitutes public steps for author sources.
"""

from __future__ import annotations

import argparse
import base64
from collections import Counter
from datetime import datetime, timezone
import getpass
import hashlib
from html import unescape
from html.parser import HTMLParser
import json
import mimetypes
import os
from pathlib import Path
import re
import socket
import sys
import time
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urljoin, urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener
import warnings


BASE_URL = "https://stepik.org"
API_URL = BASE_URL + "/api/"
TOKEN_URL = BASE_URL + "/oauth2/token/"
USER_AGENT = "StepikOwnedCourseExporter/1.0"
BATCH_SIZE = 30
TIMEOUT = 60
ATTEMPTS = 3
ASSET_LIMIT = 95 * 1024 * 1024
CHUNK_SIZE = 1024 * 1024
RETRY_CODES = {408, 429, 500, 502, 503, 504}
RESOURCE_KEYS = {
    "courses": "courses",
    "sections": "sections",
    "units": "units",
    "lessons": "lessons",
    "steps": "steps",
    "step-sources": "step-sources",
}
FILE_EXTENSIONS = {
    "7z", "aac", "aiff", "ass", "avi", "avif", "bin", "bmp", "bz2",
    "c", "cc", "cpp", "cs", "css", "csv", "doc", "docx", "epub", "flac",
    "gif", "gz", "h", "heic", "ico", "ipynb", "java", "jpeg", "jpg",
    "js", "json", "m4a", "m4v", "md", "mkv", "mov", "mp3", "mp4",
    "mpeg", "mpg", "odp", "ods", "odt", "ogg", "ogv", "opus", "pdf",
    "png", "ppt", "pptx", "py", "r", "rar", "rtf", "srt", "svg",
    "tar", "tex", "tgz", "tif", "tiff", "tsv", "ttf", "txt", "vtt",
    "wav", "webm", "webp", "woff", "woff2", "xls", "xlsx", "xml",
    "xz", "yaml", "yml", "zip",
}
MEDIA_KEYS = {
    "image", "image_url", "thumbnail", "thumbnail_url", "thumbnails",
    "cover", "cover_url", "poster", "poster_url", "audio", "audio_url",
    "video", "video_url", "attachment", "attachments", "file", "files",
    "file_url", "download_url", "subtitle", "subtitles", "subtitle_files",
    "tests_archive", "test_archive", "archive", "document",
}
EXTERNAL_VIDEO_HOSTS = (
    "youtube.com", "youtube-nocookie.com", "youtu.be", "vimeo.com",
)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def atomic_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    with temporary.open("w", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    temporary.replace(path)


def read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as stream:
        return json.load(stream)


def unique_ids(values: Any) -> list[int]:
    if not isinstance(values, (list, tuple)):
        return []
    result: list[int] = []
    seen: set[int] = set()
    for value in values:
        if isinstance(value, dict):
            value = value.get("id")
        if isinstance(value, bool):
            continue
        try:
            number = int(value)
        except (TypeError, ValueError, OverflowError):
            continue
        if number > 0 and number not in seen:
            seen.add(number)
            result.append(number)
    return result


def object_id(value: Any) -> int | None:
    ids = unique_ids([value])
    return ids[0] if ids else None


class ExportError(Exception):
    """An intentionally sanitized error, safe to put in a manifest."""

    def __init__(self, message: str, status: int | None = None):
        super().__init__(message)
        self.status = status


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ExportError("Unexpected redirect from authenticated endpoint.", code)


class HTTPSAssetRedirect(HTTPRedirectHandler):
    """Never follow a downgrade or carry authorization to another host."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        try:
            destination = urlsplit(newurl)
            original = urlsplit(req.full_url)
        except ValueError:
            raise ExportError("Invalid asset redirect URL.") from None
        if destination.scheme != "https" or not destination.hostname:
            raise ExportError("Asset redirect did not use HTTPS.")
        if destination.username or destination.password:
            raise ExportError("Asset redirect contained URL credentials.")
        redirected = super().redirect_request(req, fp, code, msg, headers, newurl)
        if redirected is not None:
            if destination.hostname != original.hostname or destination.hostname != "stepik.org":
                redirected.remove_header("Authorization")
                redirected.remove_header("Proxy-authorization")
        return redirected


def retry_pause(attempt: int, headers: Any = None) -> None:
    delay = min(2 ** attempt, 4)
    if headers is not None:
        try:
            delay = max(delay, min(float(headers.get("Retry-After", "0")), 8))
        except (TypeError, ValueError):
            pass
    time.sleep(delay)


def request_json(opener, request: Request) -> dict[str, Any]:
    for attempt in range(ATTEMPTS):
        try:
            with opener.open(request, timeout=TIMEOUT) as response:
                data = response.read()
            try:
                result = json.loads(data)
            except (ValueError, UnicodeError):
                raise ExportError("Endpoint returned invalid JSON.") from None
            if not isinstance(result, dict):
                raise ExportError("Endpoint returned an unexpected JSON structure.")
            return result
        except HTTPError as error:
            status = error.code
            headers = error.headers
            error.close()
            if status in RETRY_CODES and attempt + 1 < ATTEMPTS:
                retry_pause(attempt, headers)
                continue
            suffix = " (access denied)" if status in (401, 403) else ""
            raise ExportError(f"HTTP {status}{suffix}.", status) from None
        except (URLError, TimeoutError, socket.timeout, ConnectionError, OSError):
            if attempt + 1 < ATTEMPTS:
                retry_pause(attempt)
                continue
            raise ExportError("Network request failed after bounded retries.") from None
    raise ExportError("Network request did not complete.")


def hidden_input(environment_name: str, prompt: str) -> str:
    value = os.environ.get(environment_name)
    if value:
        return value
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", getpass.GetPassWarning)
            value = getpass.getpass(prompt)
    except (getpass.GetPassWarning, EOFError):
        raise ExportError(
            "Secure credential input is unavailable. Set STEPIK_ACCESS_TOKEN or "
            "STEPIK_CLIENT_ID and STEPIK_CLIENT_SECRET in the process environment."
        ) from None
    if not value:
        raise ExportError("A required credential was empty.")
    return value


def obtain_token() -> str:
    existing = os.environ.get("STEPIK_ACCESS_TOKEN")
    if existing:
        return existing
    client_id = hidden_input("STEPIK_CLIENT_ID", "Stepik Client ID (hidden): ")
    client_secret = hidden_input("STEPIK_CLIENT_SECRET", "Stepik Client Secret (hidden): ")
    encoded = base64.b64encode((client_id + ":" + client_secret).encode("utf-8")).decode("ascii")
    request = Request(
        TOKEN_URL,
        data=urlencode({"grant_type": "client_credentials"}).encode("ascii"),
        headers={
            "Authorization": "Basic " + encoded,
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json",
            "User-Agent": USER_AGENT,
        },
        method="POST",
    )
    response = request_json(build_opener(NoRedirect()), request)
    token = response.get("access_token")
    if not isinstance(token, str) or not token:
        raise ExportError("OAuth response did not contain an access token.")
    return token


class StepikClient:
    def __init__(self, output: Path, token: str, fresh: bool, errors: list[dict[str, Any]]):
        self.output = output
        self.token = token
        self.fresh = fresh
        self.errors = errors
        self.opener = build_opener(NoRedirect())
        self.cache_hits: Counter[str] = Counter()
        self.network_objects: Counter[str] = Counter()
        self.blocked_status: int | None = None

    def fetch(self, resource: str, identifiers: list[int]) -> dict[int, dict[str, Any]]:
        identifiers = unique_ids(identifiers)
        found: dict[int, dict[str, Any]] = {}
        pending: list[int] = []
        for identifier in identifiers:
            path = self.output / "raw" / resource / f"{identifier}.json"
            if not self.fresh and path.is_file():
                try:
                    cached = read_json(path)
                    if isinstance(cached, dict) and object_id(cached.get("id")) == identifier:
                        found[identifier] = cached
                        self.cache_hits[resource] += 1
                        continue
                except (OSError, ValueError, UnicodeError):
                    pass
            pending.append(identifier)
        if pending and self.blocked_status is not None:
            self.errors.append({
                "stage": "api", "resource": resource, "ids": pending,
                "message": "Requests stopped after a previous access denial.",
                "http_status": self.blocked_status,
            })
            pending = []
        for offset in range(0, len(pending), BATCH_SIZE):
            batch = pending[offset:offset + BATCH_SIZE]
            if resource == "courses" and len(batch) == 1:
                url = API_URL + f"courses/{batch[0]}"
            else:
                url = API_URL + resource + "?" + urlencode({"ids[]": batch}, doseq=True)
            headers = {
                "Accept": "application/json",
                "User-Agent": USER_AGENT,
            }
            if self.token:
                headers["Authorization"] = "Bearer " + self.token
            request = Request(url, headers=headers, method="GET")
            try:
                response = request_json(self.opener, request)
                objects = response.get(RESOURCE_KEYS[resource])
                if resource == "step-sources" and objects is None:
                    objects = response.get("step_sources")
                if not isinstance(objects, list):
                    raise ExportError("API response omitted the expected resource array.")
                allowed = set(batch)
                for item in objects:
                    if not isinstance(item, dict):
                        continue
                    identifier = object_id(item.get("id"))
                    if identifier not in allowed:
                        continue
                    atomic_json(self.output / "raw" / resource / f"{identifier}.json", item)
                    found[identifier] = item
                    self.network_objects[resource] += 1
                missing = [identifier for identifier in batch if identifier not in found]
                if missing:
                    self.errors.append({
                        "stage": "api", "resource": resource, "ids": missing,
                        "message": "Requested IDs were absent from the API response.",
                    })
            except ExportError as error:
                self.errors.append({
                    "stage": "api", "resource": resource, "ids": batch,
                    "message": str(error), "http_status": error.status,
                })
                if error.status in (401, 403):
                    self.blocked_status = error.status
                    remaining = pending[offset + BATCH_SIZE:]
                    if remaining:
                        self.errors.append({
                            "stage": "api", "resource": resource, "ids": remaining,
                            "message": "Further batches stopped after access was denied.",
                            "http_status": error.status,
                        })
                    break
        print(f"{resource}: {len(found)}/{len(identifiers)} objects", flush=True)
        return {identifier: found[identifier] for identifier in identifiers if identifier in found}


def extension_from_url(url: str) -> str:
    try:
        suffix = Path(urlsplit(url).path).suffix.lower().lstrip(".")
    except (ValueError, OSError):
        return ""
    return suffix if re.fullmatch(r"[a-z0-9]{1,10}", suffix) else ""


def file_link(url: str) -> bool:
    try:
        path = urlsplit(url).path.lower()
    except ValueError:
        return False
    return extension_from_url(url) in FILE_EXTENSIONS or "/media/attachments/" in path


def looks_like_reference(value: str) -> bool:
    value = value.strip()
    if not value or any(character in value for character in ("\n", "\r", "<", ">")):
        return False
    return value.startswith(("https://", "http://", "//", "/media/", "/static/", "data:")) or file_link(value)


class MediaHTMLParser(HTMLParser):
    def __init__(self, collector: "AssetCollector", origin: dict[str, Any]):
        super().__init__(convert_charrefs=True)
        self.collector = collector
        self.origin = origin

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = {key.lower(): value for key, value in attrs if value is not None}
        tag = tag.lower()
        if tag in {"img", "source", "video", "audio", "iframe", "track", "embed"}:
            value = attributes.get("src")
            if value:
                kind = "image" if tag == "img" else tag
                self.collector.add(value, kind, self.origin, iframe=(tag == "iframe"))
        if tag == "video" and attributes.get("poster"):
            self.collector.add(attributes["poster"], "thumbnail", self.origin)
        if tag in {"img", "source"} and attributes.get("srcset"):
            srcset = attributes["srcset"]
            if not srcset.startswith("data:"):
                for candidate in srcset.split(","):
                    parts = candidate.strip().split()
                    if parts:
                        self.collector.add(parts[0], "image", self.origin)
        if tag in {"a", "link"} and attributes.get("href") and file_link(attributes["href"]):
            self.collector.add(attributes["href"], "file", self.origin)
        if tag == "object" and attributes.get("data") and file_link(attributes["data"]):
            self.collector.add(attributes["data"], "file", self.origin)

    handle_startendtag = handle_starttag


class AssetCollector:
    def __init__(self):
        self.records: dict[str, dict[str, Any]] = {}

    def add(self, reference: str, kind: str, origin: dict[str, Any], *,
            iframe: bool = False, selected: bool = True) -> None:
        if not isinstance(reference, str):
            return
        reference = unescape(reference).strip()
        if not reference or reference.startswith("#"):
            return
        try:
            url = urljoin(BASE_URL + "/", reference)
            parsed = urlsplit(url)
        except ValueError:
            url = reference
            parsed = None
        record = self.records.setdefault(url, {
            "url": url,
            "url_sha256": hashlib.sha256(url.encode("utf-8")).hexdigest(),
            "original_urls": [], "kinds": [], "origins": [],
            "selected": False, "status": "pending",
            "local_path": None, "sha256": None, "size": None, "mime": None,
        })
        if reference not in record["original_urls"]:
            record["original_urls"].append(reference)
        if kind not in record["kinds"]:
            record["kinds"].append(kind)
        if origin not in record["origins"]:
            record["origins"].append(dict(origin))
        if selected:
            record["selected"] = True
        if parsed is None:
            record.update(status="external", reason="invalid_url")
        elif parsed.scheme == "data":
            record.update(status="inline", reason="bytes_embedded_in_raw_content")
        elif parsed.scheme != "https":
            record.update(status="external", reason="https_required")
        elif parsed.username or parsed.password:
            record.update(status="external", reason="url_credentials_not_used")
        elif not parsed.hostname:
            record.update(status="external", reason="missing_hostname")
        elif any(parsed.hostname == host or parsed.hostname.endswith("." + host)
                 for host in EXTERNAL_VIDEO_HOSTS):
            record.update(status="external", reason="external_video_player")
        elif iframe and not file_link(url):
            record.update(status="external", reason="embedded_web_page")
        elif extension_from_url(url) in {"m3u8", "mpd"}:
            record.update(status="external", reason="streaming_playlist")

    def collect_video_variants(self, value: Any, origin: dict[str, Any]) -> None:
        variants: list[tuple[str, str]] = []
        if isinstance(value, list):
            for item in value:
                if isinstance(item, dict):
                    url = item.get("url") or item.get("src")
                    if isinstance(url, str):
                        variants.append((str(item.get("quality", "")), url))
                elif isinstance(item, str):
                    variants.append(("", item))
        elif isinstance(value, dict):
            for quality, item in value.items():
                url = item.get("url") if isinstance(item, dict) else item
                if isinstance(url, str):
                    variants.append((str(quality), url))
        if not variants:
            return

        def rank(variant: tuple[str, str]) -> tuple[int, int]:
            quality, url = variant
            digits = re.findall(r"\d+", quality)
            level = max((int(number) for number in digits), default={
                "high": 1080, "medium": 720, "low": 360,
            }.get(quality.lower(), 0))
            return level, int(extension_from_url(url) in {"mp4", "webm", "mov"})

        chosen = max(range(len(variants)), key=lambda index: rank(variants[index]))
        for index, (quality, url) in enumerate(variants):
            variant_origin = dict(origin, quality=quality)
            self.add(url, "video", variant_origin, selected=(index == chosen))

    def walk(self, value: Any, origin: dict[str, Any], path: str = "", context: str = "") -> None:
        if isinstance(value, dict):
            for key, child in value.items():
                key = str(key)
                field = f"{path}.{key}" if path else key
                child_origin = dict(origin, field=field)
                child_context = key if key in MEDIA_KEYS else context
                if key == "urls" and context == "video":
                    self.collect_video_variants(child, child_origin)
                    continue
                if isinstance(child, str):
                    if "<" in child and ">" in child:
                        try:
                            parser = MediaHTMLParser(self, child_origin)
                            parser.feed(child)
                            parser.close()
                        except (ValueError, AssertionError):
                            pass
                    direct = key in MEDIA_KEYS
                    nested = key in {"url", "src", "href", "download"} and bool(context)
                    if (direct or nested) and looks_like_reference(child):
                        self.add(child, child_context or "file", child_origin)
                else:
                    self.walk(child, origin, field, child_context)
        elif isinstance(value, list):
            for index, child in enumerate(value):
                field = f"{path}[{index}]"
                if isinstance(child, str):
                    if context and looks_like_reference(child):
                        self.add(child, context, dict(origin, field=field))
                    elif "<" in child and ">" in child:
                        try:
                            parser = MediaHTMLParser(self, dict(origin, field=field))
                            parser.feed(child)
                            parser.close()
                        except (ValueError, AssertionError):
                            pass
                else:
                    self.walk(child, origin, field, context)


def file_digest(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(CHUNK_SIZE), b""):
            digest.update(chunk)
    return digest.hexdigest()


def asset_extension(url: str, mime: str) -> str:
    extension = extension_from_url(url)
    if extension:
        return extension
    guessed = mimetypes.guess_extension(mime) or ".bin"
    extension = guessed.lstrip(".").lower()
    return extension if re.fullmatch(r"[a-z0-9]{1,10}", extension) else "bin"


class AssetDownloader:
    def __init__(self, output: Path, token: str, fresh: bool):
        self.output = output
        self.token = token
        self.fresh = fresh
        self.opener = build_opener(HTTPSAssetRedirect())
        self.cached: dict[str, dict[str, Any]] = {}
        manifest = output / "assets" / "manifest.json"
        if not fresh and manifest.is_file():
            try:
                previous = read_json(manifest)
                self.cached = {item["url"]: item for item in previous.get("assets", [])
                               if isinstance(item, dict) and isinstance(item.get("url"), str)}
            except (OSError, ValueError, UnicodeError, TypeError, KeyError, AttributeError):
                pass

    def reuse_cached(self, record: dict[str, Any]) -> bool:
        previous = self.cached.get(record["url"], {})
        relative = previous.get("local_path")
        if previous.get("status") != "downloaded" or not isinstance(relative, str):
            return False
        expected_pattern = r"assets/" + re.escape(record["url_sha256"]) + r"\.[a-z0-9]{1,10}"
        if not re.fullmatch(expected_pattern, relative):
            return False
        path = self.output / relative
        try:
            if path.is_file() and path.stat().st_size == previous.get("size"):
                digest = file_digest(path)
                if digest == previous.get("sha256") and path.stat().st_size <= ASSET_LIMIT:
                    for key in ("local_path", "sha256", "size", "mime", "final_url"):
                        if key in previous:
                            record[key] = previous[key]
                    record.update(status="downloaded", cache_hit=True)
                    return True
        except OSError:
            pass
        return False

    def download(self, record: dict[str, Any]) -> None:
        if not record["selected"]:
            if record["status"] == "pending":
                record.update(status="variant_omitted", reason="highest_quality_variant_selected")
            return
        if record["status"] != "pending":
            return
        if self.reuse_cached(record):
            return
        url = record["url"]
        headers = {"User-Agent": USER_AGENT, "Accept-Encoding": "identity"}
        if self.token and urlsplit(url).hostname == "stepik.org":
            headers["Authorization"] = "Bearer " + self.token
        request = Request(url, headers=headers, method="GET")
        temporary = self.output / "assets" / (record["url_sha256"] + ".part")
        temporary.parent.mkdir(parents=True, exist_ok=True)
        for attempt in range(ATTEMPTS):
            try:
                with self.opener.open(request, timeout=TIMEOUT) as response:
                    mime = response.headers.get_content_type()
                    record["mime"] = mime
                    record["final_url"] = response.geturl()
                    content_length = response.headers.get("Content-Length")
                    try:
                        declared_size = int(content_length) if content_length is not None else None
                    except (TypeError, ValueError):
                        declared_size = None
                    if declared_size is not None and declared_size > ASSET_LIMIT:
                        record.update(status="oversized", size=declared_size,
                                      reason="exceeds_95_MiB_repository_file_limit")
                        return
                    if mime in {"text/html", "application/xhtml+xml"}:
                        record.update(status="external", reason="server_returned_web_page")
                        return
                    digest = hashlib.sha256()
                    total = 0
                    with temporary.open("wb") as stream:
                        while True:
                            chunk = response.read(CHUNK_SIZE)
                            if not chunk:
                                break
                            total += len(chunk)
                            if total > ASSET_LIMIT:
                                record.update(status="oversized", size=declared_size,
                                              observed_size_at_least=total,
                                              reason="exceeds_95_MiB_repository_file_limit")
                                return
                            digest.update(chunk)
                            stream.write(chunk)
                    if declared_size is not None and total != declared_size:
                        raise ExportError("Asset response was truncated.")
                    extension = asset_extension(url, mime)
                    relative = "assets/" + record["url_sha256"] + "." + extension
                    temporary.replace(self.output / relative)
                    record.update(status="downloaded", local_path=relative,
                                  sha256=digest.hexdigest(), size=total, cache_hit=False)
                    return
            except HTTPError as error:
                status = error.code
                response_headers = error.headers
                error.close()
                if status in RETRY_CODES and attempt + 1 < ATTEMPTS:
                    retry_pause(attempt, response_headers)
                    continue
                record.update(status="failed", reason=f"HTTP {status}", http_status=status)
                return
            except ExportError as error:
                if "truncated" in str(error) and attempt + 1 < ATTEMPTS:
                    retry_pause(attempt)
                    continue
                record.update(status="failed", reason=str(error))
                return
            except (URLError, TimeoutError, socket.timeout, ConnectionError, OSError):
                if attempt + 1 < ATTEMPTS:
                    retry_pause(attempt)
                    continue
                record.update(status="failed", reason="Network or local file operation failed.")
                return
            finally:
                try:
                    if temporary.exists():
                        temporary.unlink()
                except OSError:
                    pass


class CourseExporter:
    def __init__(self, course_id: int, output: Path, fresh: bool, skip_assets: bool, public: bool = False):
        self.course_id = course_id
        self.output = output
        self.fresh = fresh
        self.skip_assets = skip_assets
        self.public = public
        self.started = utc_now()
        self.errors: list[dict[str, Any]] = []
        self.expected: dict[str, list[int]] = {key: [] for key in RESOURCE_KEYS}
        self.expected["courses"] = [course_id]
        self.objects: dict[str, dict[int, dict[str, Any]]] = {key: {} for key in RESOURCE_KEYS}
        self.bindings: list[dict[str, Any]] = []
        self.asset_records: list[dict[str, Any]] = []
        self.asset_status = "not_started"
        self.client: StepikClient | None = None
        self.interrupted = False
        self.fatal = False

    def reference_ids(self, resource: str, field: str) -> list[int]:
        values: list[int] = []
        for identifier, obj in self.objects[resource].items():
            raw = obj.get(field)
            if not isinstance(raw, list):
                self.errors.append({
                    "stage": "hierarchy", "resource": resource, "ids": [identifier],
                    "message": f"Expected list field '{field}' is missing or invalid.",
                })
                continue
            ids = unique_ids(raw)
            if len(ids) != len(raw):
                self.errors.append({
                    "stage": "hierarchy", "resource": resource, "ids": [identifier],
                    "message": f"Field '{field}' contains invalid or duplicate identifiers.",
                })
            values.extend(ids)
        return unique_ids(values)

    def fetch_content(self) -> None:
        assert self.client is not None
        self.objects["courses"] = self.client.fetch("courses", self.expected["courses"])
        self.expected["sections"] = self.reference_ids("courses", "sections")
        self.objects["sections"] = self.client.fetch("sections", self.expected["sections"])
        self.expected["units"] = self.reference_ids("sections", "units")
        self.objects["units"] = self.client.fetch("units", self.expected["units"])
        lessons: list[int] = []
        for identifier, unit in self.objects["units"].items():
            lesson = object_id(unit.get("lesson"))
            if lesson is None:
                self.errors.append({
                    "stage": "hierarchy", "resource": "units", "ids": [identifier],
                    "message": "Unit has no valid lesson identifier.",
                })
            else:
                lessons.append(lesson)
        self.expected["lessons"] = unique_ids(lessons)
        self.objects["lessons"] = self.client.fetch("lessons", self.expected["lessons"])
        self.expected["steps"] = self.reference_ids("lessons", "steps")
        self.expected["step-sources"] = list(self.expected["steps"])
        self.objects["steps"] = self.client.fetch("steps", self.expected["steps"])
        self.objects["step-sources"] = self.client.fetch("step-sources", self.expected["step-sources"])

    def write_snapshot(self) -> None:
        data = {
            "course": self.objects["courses"].get(self.course_id, {}),
            "sections": list(self.objects["sections"].values()),
            "units": list(self.objects["units"].values()),
            "lessons": list(self.objects["lessons"].values()),
            "steps": list(self.objects["steps"].values()),
            "step_sources": list(self.objects["step-sources"].values()),
        }
        atomic_json(self.output / "course.json", data)

    def write_steps(self) -> None:
        section_for_unit: dict[int, list[int]] = {}
        for section_id, section in self.objects["sections"].items():
            for unit_id in unique_ids(section.get("units", [])):
                section_for_unit.setdefault(unit_id, []).append(section_id)
        units_for_lesson: dict[int, list[int]] = {}
        for unit_id, unit in self.objects["units"].items():
            lesson_id = object_id(unit.get("lesson"))
            if lesson_id is not None:
                units_for_lesson.setdefault(lesson_id, []).append(unit_id)
        for lesson_id, lesson in self.objects["lessons"].items():
            for ordinal, step_id in enumerate(unique_ids(lesson.get("steps", [])), 1):
                source = self.objects["step-sources"].get(step_id)
                step = self.objects["steps"].get(step_id, {})
                unit_ids = units_for_lesson.get(lesson_id, [])
                section_ids = unique_ids([
                    section_id for unit_id in unit_ids
                    for section_id in section_for_unit.get(unit_id, [])
                ])
                position = object_id(step.get("position")) or object_id((source or {}).get("position")) or ordinal
                binding = {
                    "course_id": self.course_id, "section_ids": section_ids,
                    "unit_ids": unit_ids, "lesson_id": lesson_id, "step_id": step_id,
                    "position": position, "lesson_order": ordinal,
                    "step_url": f"{BASE_URL}/lesson/{lesson_id}/step/{position}",
                    "raw_step": f"raw/steps/{step_id}.json" if step else None,
                    "raw_step_source": f"raw/step-sources/{step_id}.json" if source else None,
                    "path": None, "status": "missing_author_source",
                }
                source_block = source.get("block") if source is not None else None
                valid_source_block = (
                    isinstance(source_block, dict)
                    and isinstance(source_block.get("name"), str)
                    and bool(source_block["name"].strip())
                )
                if valid_source_block:
                    block = source["block"]
                    name = re.sub(r"[^A-Za-z0-9_-]", "_", str(block.get("name") or "unknown"))[:64]
                    relative = f"steps/{lesson_id}/{position:02d}_{step_id}_{name}.step"
                    atomic_json(self.output / relative, {
                        "block": block, "id": str(step_id), "time": self.started,
                    })
                    binding.update(path=relative, status="exported", type=block.get("name"))
                elif source is not None:
                    binding["status"] = "invalid_author_source"
                    self.errors.append({
                        "stage": "step_files", "resource": "step-sources", "ids": [step_id],
                        "message": "Author source has no complete block object; public step was not substituted.",
                    })
                self.bindings.append(binding)
        print(f"step files: {sum(item['status'] == 'exported' for item in self.bindings)}/{len(self.bindings)}", flush=True)

    def collect_assets(self, token: str) -> None:
        collector = AssetCollector()
        for resource, objects in self.objects.items():
            for identifier, obj in objects.items():
                collector.walk(obj, {
                    "resource": resource, "id": identifier,
                    "raw_path": f"raw/{resource}/{identifier}.json",
                })
        self.asset_records = list(collector.records.values())
        downloader = AssetDownloader(self.output, token, self.fresh)
        print(f"assets: {len(self.asset_records)} references discovered", flush=True)
        for index, record in enumerate(self.asset_records, 1):
            if self.skip_assets:
                if record["status"] == "pending":
                    if record["selected"]:
                        record.update(status="skipped", reason="skip_assets_requested")
                    else:
                        record.update(status="variant_omitted", reason="highest_quality_variant_selected")
            else:
                downloader.download(record)
            if index % 10 == 0 or index == len(self.asset_records):
                self.write_assets_manifest()
                print(f"assets: {index}/{len(self.asset_records)} processed", flush=True)
        statuses = Counter(item["status"] for item in self.asset_records)
        self.asset_status = "skipped" if self.skip_assets else (
            "partial" if any(statuses[status] for status in ("failed", "oversized", "pending")) else "complete"
        )
        self.write_assets_manifest()

    def write_assets_manifest(self) -> None:
        atomic_json(self.output / "assets" / "manifest.json", {
            "schema_version": 1, "course_id": self.course_id,
            "generated_at": utc_now(), "status": self.asset_status,
            "maximum_file_size": ASSET_LIMIT,
            "selection": "Highest-quality video variant; all original variants remain in raw JSON.",
            "summary": dict(Counter(item["status"] for item in self.asset_records)),
            "assets": self.asset_records,
        })

    def finish(self) -> int:
        self.write_snapshot()
        if self.asset_status == "not_started" or any(item["status"] == "pending" for item in self.asset_records):
            self.asset_status = "partial"
            self.write_assets_manifest()
        missing = {
            resource: [identifier for identifier in expected if identifier not in self.objects[resource]]
            for resource, expected in self.expected.items()
        }
        content_ok = not self.errors and not any(missing.values()) and all(
            item["status"] == "exported" for item in self.bindings
        )
        status = "complete" if content_ok and self.asset_status == "complete" and not self.public else "partial"
        author_unavailable = bool(missing["step-sources"]) or any(
            item["status"] == "invalid_author_source" for item in self.bindings
        ) or (
            not self.objects["step-sources"] and (not content_ok or self.public)
        )
        course_object = self.objects["courses"].get(self.course_id, {})
        observed_expected_counts = {
            resource.replace("-", "_"): len(ids) for resource, ids in self.expected.items()
        }
        expected_counts = dict(observed_expected_counts)
        unknown_expected_counts = set()
        dependencies = {
            "courses": ("sections", "units", "lessons", "steps", "step_sources"),
            "sections": ("units", "lessons", "steps", "step_sources"),
            "units": ("lessons", "steps", "step_sources"),
            "lessons": ("steps", "step_sources"),
        }
        for parent, children in dependencies.items():
            if missing[parent]:
                unknown_expected_counts.update(children)
        for resource in unknown_expected_counts:
            expected_counts[resource] = None
        manifest = {
            "schema_version": 1, "course_id": self.course_id, "status": status,
            "mode": "public" if self.public else "author",
            "content_status": "complete" if content_ok else "partial",
            "author_sources_unavailable": author_unavailable,
            "author_sources_status": "unavailable" if author_unavailable and not self.objects["step-sources"] else (
                "partial" if author_unavailable else "complete"
            ),
            "assets_status": self.asset_status,
            "started_at": self.started, "finished_at": utc_now(),
            "source": {
                "course_url": f"{BASE_URL}/course/{self.course_id}",
                "api_base": API_URL, "course_api_url": API_URL + f"courses/{self.course_id}",
                "hierarchy": ["course.sections", "sections.units", "units.lesson", "lessons.steps"],
                "author_sources": "step-sources", "public_step_fallback": False,
            },
            "options": {"fresh": self.fresh, "skip_assets": self.skip_assets,
                        "public": self.public, "batch_size": BATCH_SIZE},
            "counts": {resource.replace("-", "_"): len(objects) for resource, objects in self.objects.items()},
            "expected_counts": expected_counts,
            "observed_expected_counts": observed_expected_counts,
            "unknown_expected_counts": sorted(unknown_expected_counts),
            "declared_counts": {
                "sections": len(course_object["sections"]) if isinstance(course_object.get("sections"), list) else None,
                "lessons": course_object.get("lessons_count"),
                "steps": course_object.get("steps_count"),
            },
            "missing_ids": missing,
            "errors": self.errors,
            "cache_hits": dict(self.client.cache_hits) if self.client else {},
            "network_objects": dict(self.client.network_objects) if self.client else {},
            "step_files": {
                "expected": len(self.bindings),
                "written": sum(item["status"] == "exported" for item in self.bindings),
                "bindings": self.bindings,
            },
            "assets_manifest": "assets/manifest.json",
            "asset_counts": dict(Counter(item["status"] for item in self.asset_records)),
            "notes": [
                "The archive preserves raw API fields without rewriting original content or media URLs.",
                "No users, submissions, statistics, comments, or learner progress endpoints are requested.",
                "External players and embedded web pages are recorded as external references.",
                "Files larger than 95 MiB are recorded with their URLs and are not saved as Git blobs.",
                "Cached objects are reused unless --fresh is supplied; only objects named in this snapshot are current.",
                "Null expected_counts means that a missing parent prevented discovery of the total; observed_expected_counts is only the known lower bound.",
            ],
        }
        atomic_json(self.output / "manifest.json", manifest)
        print(f"Export status: {status}; content: {manifest['content_status']}; assets: {self.asset_status}", flush=True)
        if author_unavailable:
            print("Author step sources are missing. This is a PARTIAL export; public steps were not substituted.", file=sys.stderr)
        if self.interrupted:
            return 130
        if self.fatal:
            return 1
        if content_ok and not self.public and (self.asset_status == "complete" or self.skip_assets):
            return 0
        return 2

    def run(self) -> int:
        self.output.mkdir(parents=True, exist_ok=True)
        stage = "authentication"
        try:
            token = "" if self.public else obtain_token()
            self.client = StepikClient(self.output, token, self.fresh, self.errors)
            stage = "content"
            self.fetch_content()
            self.write_snapshot()
            stage = "step_files"
            self.write_steps()
            stage = "assets"
            self.collect_assets(token)
        except KeyboardInterrupt:
            self.interrupted = True
            self.errors.append({"stage": stage, "message": "Export interrupted; completed files are preserved."})
        except ExportError as error:
            self.errors.append({"stage": stage, "message": str(error), "http_status": error.status})
            self.fatal = stage == "authentication"
        except Exception as error:
            # Do not interpolate arbitrary exception messages: an HTTP/library
            # exception may carry request headers or a credential-bearing URL.
            self.errors.append({
                "stage": stage,
                "message": f"Unexpected {type(error).__name__}; completed files are preserved.",
            })
            self.fatal = True
        return self.finish()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--course", type=int, default=86957, help="Owned course ID (default: 86957).")
    parser.add_argument("--output", type=Path, default=None,
                        help="Output directory (default: courses/<course ID>).")
    parser.add_argument("--skip-assets", action="store_true",
                        help="Discover media references but do not download media bytes.")
    parser.add_argument("--fresh", action="store_true",
                        help="Refetch API objects and media instead of reusing verified local cache.")
    parser.add_argument("--public", action="store_true",
                        help="Explicit unauthenticated partial snapshot; do not request credentials.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    arguments = parser.parse_args(argv)
    if arguments.course <= 0:
        parser.error("--course must be a positive integer")
    output = arguments.output or Path("courses") / str(arguments.course)
    exporter = CourseExporter(arguments.course, output, arguments.fresh, arguments.skip_assets, arguments.public)
    try:
        return exporter.run()
    except KeyboardInterrupt:
        print("Export interrupted.", file=sys.stderr)
        return 130
    except Exception as error:
        print(f"Export could not save its final files ({type(error).__name__}).", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
