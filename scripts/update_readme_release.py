#!/usr/bin/env python3
"""Actualiza el bloque delimitado de descarga del README a partir de una release publicada.

No infiere versión, hash ni URL: lee el JSON de la release (API autenticada o
payload del evento) y, opcionalmente, el manifiesto firmado ya publicado.
No descarga el instalador. No inserta notas de la release en el README.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

MARKER_START = "<!-- RELEASE:START -->"
MARKER_END = "<!-- RELEASE:END -->"
INSTALLER_RE = re.compile(
    r"^Hydrosphere-([0-9A-Za-z][0-9A-Za-z._]*)-win-x86_64-per-user\.exe$"
)
MANIFEST_ASSET_NAME = "hydrosphere-update-manifest-v1.json"
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
VERSION_RE = re.compile(r"^[0-9A-Za-z][0-9A-Za-z._]*$")
TAG_RE = re.compile(r"^v?[0-9A-Za-z][0-9A-Za-z._-]*$")
GITHUB_HOST = "github.com"
DOWNLOAD_REPO = "HydrosphereEnnde/Hydrosphere-Distribution"
RELEASES_INDEX_URL = f"https://github.com/{DOWNLOAD_REPO}/releases"
BADGE_IMAGE_URL = (
    "https://img.shields.io/badge/Descargar-Hydrosphere%20para%20Windows-0B5CAB"
    "?style=for-the-badge&logo=windows&logoColor=white"
)
MONTHS_ES = (
    "",
    "enero",
    "febrero",
    "marzo",
    "abril",
    "mayo",
    "junio",
    "julio",
    "agosto",
    "septiembre",
    "octubre",
    "noviembre",
    "diciembre",
)


class ReadmeReleaseError(Exception):
    """Error que debe abortar la actualización del README."""

    def __init__(self, message: str, *, code: str = "readme_release_error") -> None:
        super().__init__(message)
        self.code = code


class SkipRelease(Exception):
    """Release que no debe modificar el README (draft o prerelease)."""

    def __init__(self, message: str, *, code: str = "skipped") -> None:
        super().__init__(message)
        self.code = code


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ReadmeReleaseError(f"Archivo JSON no encontrado: {path}", code="json_missing") from exc
    except json.JSONDecodeError as exc:
        raise ReadmeReleaseError(f"JSON inválido: {path}", code="json_invalid") from exc


def _as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return False


def is_draft(release: dict[str, Any]) -> bool:
    return _as_bool(release.get("draft")) or _as_bool(release.get("isDraft"))


def is_prerelease(release: dict[str, Any]) -> bool:
    return _as_bool(release.get("prerelease")) or _as_bool(release.get("isPrerelease"))


def require_str(value: Any, *, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ReadmeReleaseError(f"Campo {field!r} ausente o vacío.", code="missing_field")
    return value.strip()


def assert_safe_github_url(url: str, *, expected_path_prefix: str, field: str) -> str:
    if any(ch.isspace() or ch in "()[]<>\"'" for ch in url):
        raise ReadmeReleaseError(
            f"URL {field} contiene caracteres no permitidos.",
            code="unsafe_url",
        )
    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.netloc.lower() != GITHUB_HOST:
        raise ReadmeReleaseError(f"URL {field} no es https://github.com/...", code="unsafe_url")
    expected = f"/{DOWNLOAD_REPO}/{expected_path_prefix.lstrip('/')}"
    if parsed.path != expected and not parsed.path.startswith(expected.rstrip("/") + "/"):
        if parsed.path != expected.rstrip("/"):
            raise ReadmeReleaseError(
                f"URL {field} no pertenece a {DOWNLOAD_REPO}/{expected_path_prefix}.",
                code="unsafe_url",
            )
    if parsed.query or parsed.fragment or parsed.username or parsed.password:
        raise ReadmeReleaseError(f"URL {field} incluye query, fragment o credenciales.", code="unsafe_url")
    return url


def parse_github_digest(raw: Any) -> str | None:
    if raw is None:
        return None
    if not isinstance(raw, str) or not raw.strip():
        return None
    text = raw.strip().lower()
    if text.startswith("sha256:"):
        text = text.split(":", 1)[1]
    if not SHA256_RE.fullmatch(text):
        raise ReadmeReleaseError(f"Digest SHA-256 inválido: {raw!r}", code="invalid_digest")
    return text


def sha256_from_manifest(manifest: dict[str, Any], installer_name: str) -> str:
    payload = manifest.get("payload")
    if not isinstance(payload, dict):
        raise ReadmeReleaseError("Manifiesto sin payload objeto.", code="invalid_manifest")
    artifacts = payload.get("artifacts")
    if not isinstance(artifacts, list):
        raise ReadmeReleaseError("Manifiesto sin lista de artifacts.", code="invalid_manifest")
    matches: list[str] = []
    for item in artifacts:
        if not isinstance(item, dict):
            continue
        if item.get("filename") != installer_name:
            continue
        digest = parse_github_digest(item.get("sha256"))
        if not digest:
            raise ReadmeReleaseError(
                "El manifiesto no incluye SHA-256 del instalador.",
                code="manifest_hash_missing",
            )
        matches.append(digest)
    if not matches:
        raise ReadmeReleaseError(
            f"El manifiesto no referencia el instalador {installer_name!r}.",
            code="manifest_installer_missing",
        )
    if len(matches) > 1:
        unique = set(matches)
        if len(unique) > 1:
            raise ReadmeReleaseError(
                "El manifiesto declara varios SHA-256 para el mismo instalador.",
                code="manifest_hash_ambiguous",
            )
    return matches[0]


def select_installer_asset(assets: Any) -> dict[str, Any]:
    if not isinstance(assets, list):
        raise ReadmeReleaseError("La release no incluye una lista de assets.", code="assets_missing")
    matches: list[dict[str, Any]] = []
    for asset in assets:
        if not isinstance(asset, dict):
            continue
        name = asset.get("name")
        if isinstance(name, str) and INSTALLER_RE.fullmatch(name):
            matches.append(asset)
    if not matches:
        raise ReadmeReleaseError(
            "No hay un instalador Windows x86_64 per-user "
            "(Hydrosphere-*-win-x86_64-per-user.exe) en la release.",
            code="installer_missing",
        )
    if len(matches) > 1:
        names = ", ".join(str(a.get("name")) for a in matches)
        raise ReadmeReleaseError(
            f"Hay más de un instalador candidato; no se modifica el README: {names}",
            code="installer_ambiguous",
        )
    return matches[0]


def parse_published_at(value: str) -> datetime:
    text = value.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        dt = datetime.fromisoformat(text)
    except ValueError as exc:
        raise ReadmeReleaseError(
            f"published_at inválido: {value!r}",
            code="invalid_published_at",
        ) from exc
    if dt.tzinfo is None:
        raise ReadmeReleaseError(
            "published_at no incluye zona horaria.",
            code="invalid_published_at",
        )
    return dt.astimezone(timezone.utc)


def format_date_es(dt: datetime) -> str:
    return f"{dt.day} de {MONTHS_ES[dt.month]} de {dt.year}"


def format_size_mb(size_bytes: int) -> str:
    if size_bytes <= 0:
        raise ReadmeReleaseError("El tamaño del instalador debe ser positivo.", code="invalid_size")
    mb = size_bytes / (1024 * 1024)
    rounded = max(1, int(round(mb)))
    return f"{rounded} MB"


def asset_download_url(asset: dict[str, Any]) -> str:
    url = asset.get("browser_download_url") or asset.get("downloadUrl")
    if not isinstance(url, str) or not url.strip():
        raise ReadmeReleaseError("El asset no incluye browser_download_url.", code="missing_download_url")
    return url.strip()


def release_html_url(release: dict[str, Any]) -> str:
    url = release.get("html_url") or release.get("url")
    if not isinstance(url, str) or not url.strip():
        raise ReadmeReleaseError("La release no incluye html_url.", code="missing_release_url")
    text = url.strip()
    # gh --json usa "url" como HTML; la API REST usa html_url y "url" como API.
    if text.startswith("https://api.github.com/"):
        raise ReadmeReleaseError(
            "html_url apunta a la API, no a la página de la release.",
            code="missing_release_url",
        )
    return text


def extract_release_info(
    release: dict[str, Any],
    *,
    manifest: dict[str, Any] | None = None,
) -> dict[str, str]:
    if not isinstance(release, dict):
        raise ReadmeReleaseError("La release debe ser un objeto JSON.", code="invalid_release")
    if is_draft(release):
        raise SkipRelease("Release draft: no se actualiza el README.", code="draft")
    if is_prerelease(release):
        raise SkipRelease("Release prerelease: no se actualiza el README.", code="prerelease")

    tag_name = require_str(release.get("tag_name") or release.get("tagName"), field="tag_name")
    if not TAG_RE.fullmatch(tag_name):
        raise ReadmeReleaseError(f"tag_name no seguro: {tag_name!r}", code="unsafe_tag")

    published_raw = require_str(
        release.get("published_at") or release.get("publishedAt"),
        field="published_at",
    )
    published = parse_published_at(published_raw)
    installer = select_installer_asset(release.get("assets"))
    installer_name = require_str(installer.get("name"), field="asset.name")
    match = INSTALLER_RE.fullmatch(installer_name)
    if not match:
        raise ReadmeReleaseError("Nombre de instalador inesperado.", code="installer_missing")
    version = match.group(1)
    if not VERSION_RE.fullmatch(version):
        raise ReadmeReleaseError(f"Versión extraída no segura: {version!r}", code="unsafe_version")

    size = installer.get("size")
    if not isinstance(size, int) or isinstance(size, bool):
        raise ReadmeReleaseError("El asset no incluye un tamaño entero.", code="invalid_size")

    download_url = assert_safe_github_url(
        asset_download_url(installer),
        expected_path_prefix=f"releases/download/{tag_name}/{installer_name}",
        field="browser_download_url",
    )
    notes_url = assert_safe_github_url(
        release_html_url(release),
        expected_path_prefix=f"releases/tag/{tag_name}",
        field="html_url",
    )

    expected_download_path = f"/HydrosphereEnnde/Hydrosphere-Distribution/releases/download/{tag_name}/{installer_name}"
    if urlparse(download_url).path != expected_download_path:
        raise ReadmeReleaseError(
            "La URL de descarga no coincide con tag y nombre de asset publicados.",
            code="unsafe_url",
        )

    digest = parse_github_digest(installer.get("digest"))
    manifest_digest = None
    if manifest is not None:
        manifest_digest = sha256_from_manifest(manifest, installer_name)
    if digest and manifest_digest and digest != manifest_digest:
        raise ReadmeReleaseError(
            "El SHA-256 del digest de GitHub no coincide con el del manifiesto.",
            code="hash_mismatch",
        )
    sha256 = digest or manifest_digest
    if not sha256:
        raise ReadmeReleaseError(
            "SHA-256 no disponible: el asset no trae digest y no se aportó manifiesto.",
            code="hash_missing",
        )

    return {
        "tag_name": tag_name,
        "version": version,
        "published_es": format_date_es(published),
        "size_label": format_size_mb(size),
        "sha256": sha256,
        "download_url": download_url,
        "release_url": notes_url,
        "installer_name": installer_name,
    }


def render_release_block(info: dict[str, str]) -> str:
    # Solo interpola campos ya validados (versión, URLs GitHub, hash hex, fecha propia).
    version = info["version"]
    download_url = info["download_url"]
    return "\n".join(
        [
            f"[![Descargar Hydrosphere para Windows]({BADGE_IMAGE_URL})]({download_url})",
            "",
            "## Descarga la última versión",
            "",
            "| Versión | Publicada | Instalador | Tamaño |",
            "| --- | --- | --- | --- |",
            f"| {version} | {info['published_es']} | Windows 64 bits | {info['size_label']} |",
            "",
            f"[Descargar Hydrosphere {version} para Windows]({download_url})",
            "",
            f"SHA-256: `{info['sha256']}`",
            "",
            f"[Ver notas de la versión]({info['release_url']}) · [Ver todas las versiones]({RELEASES_INDEX_URL})",
        ]
    )


def replace_release_block(readme: str, inner: str) -> str:
    start_count = readme.count(MARKER_START)
    end_count = readme.count(MARKER_END)
    if start_count != 1 or end_count != 1:
        raise ReadmeReleaseError(
            "El README debe contener exactamente un par de marcadores "
            f"{MARKER_START} / {MARKER_END}.",
            code="markers_invalid",
        )
    start = readme.find(MARKER_START)
    end = readme.find(MARKER_END)
    if start > end:
        raise ReadmeReleaseError("Marcadores de release en orden inverso.", code="markers_invalid")
    before = readme[: start + len(MARKER_START)]
    after = readme[end:]
    inner_clean = inner.strip("\n")
    return f"{before}\n{inner_clean}\n{after}"


def update_readme_text(
    readme: str,
    release: dict[str, Any],
    *,
    manifest: dict[str, Any] | None = None,
) -> tuple[str, dict[str, Any]]:
    info = extract_release_info(release, manifest=manifest)
    updated = replace_release_block(readme, render_release_block(info))
    changed = updated != readme
    meta = {
        "changed": changed,
        "skipped": False,
        "tag_name": info["tag_name"],
        "version": info["version"],
        "sha256": info["sha256"],
        "download_url": info["download_url"],
        "installer_name": info["installer_name"],
    }
    return updated, meta


def update_readme_file(
    readme_path: Path,
    release: dict[str, Any],
    *,
    manifest: dict[str, Any] | None = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    original = readme_path.read_text(encoding="utf-8")
    updated, meta = update_readme_text(original, release, manifest=manifest)
    if meta["changed"] and not dry_run:
        readme_path.write_text(updated, encoding="utf-8", newline="\n")
    meta["dry_run"] = dry_run
    return meta


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Actualiza el bloque de descarga del README desde una release publicada.",
    )
    parser.add_argument("--readme", type=Path, required=True, help="Ruta al README.md")
    parser.add_argument("--release-json", type=Path, required=True, help="JSON de la release (API GitHub)")
    parser.add_argument(
        "--manifest-json",
        type=Path,
        default=None,
        help="Manifiesto publicado (opcional; fuente de hash si falta digest)",
    )
    parser.add_argument("--meta-out", type=Path, default=None, help="Escribe metadatos JSON del resultado")
    parser.add_argument("--dry-run", action="store_true", help="No escribe el README")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        release = load_json(args.release_json)
        if not isinstance(release, dict):
            raise ReadmeReleaseError("El JSON de release debe ser un objeto.", code="invalid_release")
        manifest = None
        if args.manifest_json is not None:
            loaded = load_json(args.manifest_json)
            if not isinstance(loaded, dict):
                raise ReadmeReleaseError("El JSON de manifiesto debe ser un objeto.", code="invalid_manifest")
            manifest = loaded
        meta = update_readme_file(
            args.readme,
            release,
            manifest=manifest,
            dry_run=args.dry_run,
        )
    except SkipRelease as exc:
        meta = {"changed": False, "skipped": True, "code": exc.code, "message": str(exc)}
        if args.meta_out is not None:
            args.meta_out.write_text(json.dumps(meta, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"SKIP [{exc.code}]: {exc}", file=sys.stderr)
        return 2
    except ReadmeReleaseError as exc:
        print(f"ERROR [{exc.code}]: {exc}", file=sys.stderr)
        return 1

    if args.meta_out is not None:
        args.meta_out.write_text(json.dumps(meta, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    if meta["changed"]:
        print(f"README actualizado a {meta['tag_name']}")
    else:
        print(f"README ya estaba actualizado para {meta['tag_name']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
