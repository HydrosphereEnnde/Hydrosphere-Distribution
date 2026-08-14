"""Pruebas focalizadas del generador del bloque de descarga del README."""
from __future__ import annotations

import importlib.util
import json
import shutil
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "update_readme_release.py"
FIXTURES = Path(__file__).resolve().parent / "fixtures"


def load_module():
    spec = importlib.util.spec_from_file_location("update_readme_release", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


mod = load_module()

README_TEMPLATE = """# Hydrosphere

> Cita comercial.

<!-- RELEASE:START -->
contenido previo
<!-- RELEASE:END -->

## Instalación

Texto estático que no debe cambiar.

## Documentación técnica

Reglas de distribución.
"""


def sample_release() -> dict:
    return json.loads((FIXTURES / "release_v0.0.4.json").read_text(encoding="utf-8"))


def sample_manifest() -> dict:
    return json.loads((FIXTURES / "manifest_v0.0.4.json").read_text(encoding="utf-8"))


class ExtractReleaseInfoTests(unittest.TestCase):
    def test_valid_stable_release_uses_published_asset(self) -> None:
        info = mod.extract_release_info(sample_release())
        self.assertEqual(info["version"], "0.0.4")
        self.assertEqual(info["tag_name"], "v0.0.4")
        self.assertEqual(info["published_es"], "14 de agosto de 2026")
        self.assertEqual(info["size_label"], "201 MB")
        self.assertEqual(
            info["sha256"],
            "2c7b0761161e7e37a7591d99e5e4d5d88ed9de8a383f905a453bdb291d1d5489",
        )
        self.assertTrue(info["download_url"].endswith("Hydrosphere-0.0.4-win-x86_64-per-user.exe"))
        self.assertNotIn("hydrosphere-update-manifest-v1.json", info["download_url"])
        self.assertNotIn("/archive/", info["download_url"])
        self.assertNotIn(".tar.gz", info["download_url"])
        self.assertNotIn(".zip", info["download_url"])

    def test_manifest_hash_matches_github_digest(self) -> None:
        info = mod.extract_release_info(sample_release(), manifest=sample_manifest())
        self.assertEqual(
            info["sha256"],
            "2c7b0761161e7e37a7591d99e5e4d5d88ed9de8a383f905a453bdb291d1d5489",
        )

    def test_hash_from_manifest_when_digest_missing(self) -> None:
        release = sample_release()
        for asset in release["assets"]:
            asset.pop("digest", None)
        info = mod.extract_release_info(release, manifest=sample_manifest())
        self.assertEqual(
            info["sha256"],
            "2c7b0761161e7e37a7591d99e5e4d5d88ed9de8a383f905a453bdb291d1d5489",
        )

    def test_hash_mismatch_between_digest_and_manifest_fails(self) -> None:
        manifest = sample_manifest()
        manifest["payload"]["artifacts"][0]["sha256"] = "0" * 64
        with self.assertRaises(mod.ReadmeReleaseError) as ctx:
            mod.extract_release_info(sample_release(), manifest=manifest)
        self.assertEqual(ctx.exception.code, "hash_mismatch")

    def test_missing_hash_fails(self) -> None:
        release = sample_release()
        for asset in release["assets"]:
            asset.pop("digest", None)
        with self.assertRaises(mod.ReadmeReleaseError) as ctx:
            mod.extract_release_info(release)
        self.assertEqual(ctx.exception.code, "hash_missing")

    def test_prerelease_is_skipped(self) -> None:
        release = sample_release()
        release["prerelease"] = True
        with self.assertRaises(mod.SkipRelease) as ctx:
            mod.extract_release_info(release)
        self.assertEqual(ctx.exception.code, "prerelease")

    def test_draft_is_skipped(self) -> None:
        release = sample_release()
        release["draft"] = True
        with self.assertRaises(mod.SkipRelease) as ctx:
            mod.extract_release_info(release)
        self.assertEqual(ctx.exception.code, "draft")

    def test_missing_installer_fails(self) -> None:
        release = sample_release()
        release["assets"] = [release["assets"][1]]
        with self.assertRaises(mod.ReadmeReleaseError) as ctx:
            mod.extract_release_info(release)
        self.assertEqual(ctx.exception.code, "installer_missing")

    def test_json_and_source_archives_are_not_selected(self) -> None:
        release = sample_release()
        release["assets"] = [
            {
                "name": "hydrosphere-update-manifest-v1.json",
                "size": 1217,
                "browser_download_url": "https://github.com/HydrosphereEnnde/Hydrosphere-Distribution/releases/download/v0.0.4/hydrosphere-update-manifest-v1.json",
                "digest": "sha256:" + "a" * 64,
            },
            {
                "name": "source.zip",
                "size": 10,
                "browser_download_url": "https://github.com/HydrosphereEnnde/Hydrosphere-Distribution/archive/refs/tags/v0.0.4.zip",
                "digest": "sha256:" + "b" * 64,
            },
        ]
        with self.assertRaises(mod.ReadmeReleaseError) as ctx:
            mod.extract_release_info(release)
        self.assertEqual(ctx.exception.code, "installer_missing")

    def test_ambiguous_installers_fail(self) -> None:
        release = sample_release()
        clone = deepcopy(release["assets"][0])
        clone["name"] = "Hydrosphere-0.0.5-win-x86_64-per-user.exe"
        clone["browser_download_url"] = (
            "https://github.com/HydrosphereEnnde/Hydrosphere-Distribution/releases/download/v0.0.4/"
            "Hydrosphere-0.0.5-win-x86_64-per-user.exe"
        )
        release["assets"].append(clone)
        with self.assertRaises(mod.ReadmeReleaseError) as ctx:
            mod.extract_release_info(release)
        self.assertEqual(ctx.exception.code, "installer_ambiguous")

    def test_release_notes_are_not_used(self) -> None:
        release = sample_release()
        release["body"] = "[pwned](https://evil.example) <script>alert(1)</script>"
        release["name"] = "Ignorar este título malicioso"
        info = mod.extract_release_info(release)
        rendered = mod.render_release_block(info)
        self.assertNotIn("pwned", rendered)
        self.assertNotIn("evil.example", rendered)
        self.assertNotIn("<script>", rendered)
        self.assertNotIn("Ignorar este título", rendered)

    def test_foreign_download_url_is_rejected(self) -> None:
        release = sample_release()
        release["assets"][0]["browser_download_url"] = "https://evil.example/installer.exe"
        with self.assertRaises(mod.ReadmeReleaseError) as ctx:
            mod.extract_release_info(release)
        self.assertEqual(ctx.exception.code, "unsafe_url")


class ReplaceBlockTests(unittest.TestCase):
    def test_preserves_text_outside_markers(self) -> None:
        info = mod.extract_release_info(sample_release())
        updated = mod.replace_release_block(README_TEMPLATE, mod.render_release_block(info))
        self.assertTrue(updated.startswith("# Hydrosphere\n"))
        self.assertIn("> Cita comercial.", updated)
        self.assertIn("## Instalación\n\nTexto estático que no debe cambiar.", updated)
        self.assertIn("## Documentación técnica\n\nReglas de distribución.", updated)
        self.assertIn("contenido previo", README_TEMPLATE)
        self.assertNotIn("contenido previo", updated)

    def test_replacement_is_idempotent(self) -> None:
        updated, meta = mod.update_readme_text(README_TEMPLATE, sample_release())
        again, meta2 = mod.update_readme_text(updated, sample_release())
        self.assertTrue(meta["changed"])
        self.assertFalse(meta2["changed"])
        self.assertEqual(updated, again)

    def test_missing_markers_fail_without_rewriting(self) -> None:
        with self.assertRaises(mod.ReadmeReleaseError) as ctx:
            mod.replace_release_block("# sin marcadores\n", "nuevo")
        self.assertEqual(ctx.exception.code, "markers_invalid")

    def test_generated_block_links_exe_not_json(self) -> None:
        info = mod.extract_release_info(sample_release())
        block = mod.render_release_block(info)
        self.assertIn("Hydrosphere-0.0.4-win-x86_64-per-user.exe", block)
        self.assertNotIn("hydrosphere-update-manifest-v1.json", block)
        self.assertIn("SHA-256: `2c7b0761161e7e37a7591d99e5e4d5d88ed9de8a383f905a453bdb291d1d5489`", block)
        self.assertIn("14 de agosto de 2026", block)
        self.assertIn("201 MB", block)


class CliTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="readme-release-"))
        self.addCleanup(lambda: shutil.rmtree(self.tmp, ignore_errors=True))
        self.readme = self.tmp / "README.md"
        self.readme.write_text(README_TEMPLATE, encoding="utf-8")
        self.release_json = self.tmp / "release.json"
        self.release_json.write_text(
            (FIXTURES / "release_v0.0.4.json").read_text(encoding="utf-8"),
            encoding="utf-8",
        )
        self.meta = self.tmp / "meta.json"

    def test_cli_updates_readme_and_is_idempotent(self) -> None:
        code = mod.main(
            [
                "--readme",
                str(self.readme),
                "--release-json",
                str(self.release_json),
                "--meta-out",
                str(self.meta),
            ]
        )
        self.assertEqual(code, 0)
        meta = json.loads(self.meta.read_text(encoding="utf-8"))
        self.assertTrue(meta["changed"])
        text = self.readme.read_text(encoding="utf-8")
        self.assertIn("Hydrosphere-0.0.4-win-x86_64-per-user.exe", text)
        self.assertTrue(text.startswith("# Hydrosphere\n"))
        self.assertIn("Texto estático que no debe cambiar.", text)

        code2 = mod.main(
            [
                "--readme",
                str(self.readme),
                "--release-json",
                str(self.release_json),
                "--meta-out",
                str(self.meta),
            ]
        )
        self.assertEqual(code2, 0)
        meta2 = json.loads(self.meta.read_text(encoding="utf-8"))
        self.assertFalse(meta2["changed"])

    def test_cli_skips_prerelease_without_touching_readme(self) -> None:
        release = sample_release()
        release["prerelease"] = True
        self.release_json.write_text(json.dumps(release), encoding="utf-8")
        before = self.readme.read_text(encoding="utf-8")
        code = mod.main(
            [
                "--readme",
                str(self.readme),
                "--release-json",
                str(self.release_json),
                "--meta-out",
                str(self.meta),
            ]
        )
        self.assertEqual(code, 2)
        self.assertEqual(self.readme.read_text(encoding="utf-8"), before)
        meta = json.loads(self.meta.read_text(encoding="utf-8"))
        self.assertTrue(meta["skipped"])

    def test_cli_ambiguous_asset_does_not_modify_readme(self) -> None:
        release = sample_release()
        extra = deepcopy(release["assets"][0])
        extra["name"] = "Hydrosphere-9.9.9-win-x86_64-per-user.exe"
        extra["browser_download_url"] = (
            "https://github.com/HydrosphereEnnde/Hydrosphere-Distribution/releases/download/v0.0.4/"
            "Hydrosphere-9.9.9-win-x86_64-per-user.exe"
        )
        release["assets"].append(extra)
        self.release_json.write_text(json.dumps(release), encoding="utf-8")
        before = self.readme.read_text(encoding="utf-8")
        code = mod.main(["--readme", str(self.readme), "--release-json", str(self.release_json)])
        self.assertEqual(code, 1)
        self.assertEqual(self.readme.read_text(encoding="utf-8"), before)


class ReleaseSelectorTests(unittest.TestCase):
    def test_release_event_uses_numeric_id(self) -> None:
        selector = mod.resolve_release_selector("release", release_id="514537781")
        self.assertEqual(selector, {"mode": "id", "value": "514537781"})

    def test_repository_dispatch_uses_safe_tag(self) -> None:
        selector = mod.resolve_release_selector(
            "repository_dispatch",
            dispatch_tag="v0.0.4",
        )
        self.assertEqual(selector, {"mode": "tag", "value": "v0.0.4"})

    def test_repository_dispatch_rejects_malicious_tag(self) -> None:
        with self.assertRaises(mod.ReadmeReleaseError) as ctx:
            mod.resolve_release_selector(
                "repository_dispatch",
                dispatch_tag="v0.0.4\n; curl https://evil.example",
            )
        self.assertEqual(ctx.exception.code, "unsafe_tag")

    def test_workflow_dispatch_without_tag_uses_latest_stable(self) -> None:
        selector = mod.resolve_release_selector("workflow_dispatch")
        self.assertEqual(selector, {"mode": "latest_stable", "value": ""})

    def test_unsupported_event_fails(self) -> None:
        with self.assertRaises(mod.ReadmeReleaseError) as ctx:
            mod.resolve_release_selector("push")
        self.assertEqual(ctx.exception.code, "unsupported_event")


class WorkflowContractTests(unittest.TestCase):
    def test_workflow_checks_out_main_and_accepts_canonical_dispatch(self) -> None:
        text = (ROOT / ".github/workflows/update-readme-release.yml").read_text(encoding="utf-8")
        self.assertIn("ref: main", text)
        self.assertIn("repository_dispatch:", text)
        self.assertIn("stable-release-published", text)
        self.assertIn("types: [published]", text)
        self.assertIn("contents: write", text)
        self.assertNotIn("pull_request:", text)
        self.assertIn('git push origin HEAD:main', text)


if __name__ == "__main__":
    unittest.main()
