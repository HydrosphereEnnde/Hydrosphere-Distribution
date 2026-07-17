# Release Asset Layout & Distribution Schema

> [!WARNING]
> Status: provisional bootstrap documentation. No production release contract is active yet.

## Purpose

This document outlines the planned structure, naming conventions, and validation constraints for Hydrosphere release assets. The final implementation details are subject to validation under issue #208 of the main repository.

## Planned Assets

For each official release, the following assets are expected to be compiled and made available:

* **Installer Executable:** `Hydrosphere-<version>-win-x86_64-per-user.exe`
  * Windows 64-bit per-user installer.
  * Must be signed with the official Hydrosphere Authenticode certificate.
* **Update Manifest:** `hydrosphere-update-manifest-v1.json`
  * Cryptographically signed envelope detailing release metadata and asset integrity hashes.

## Manifest Structure (Provisional)

The update manifest is designed as a self-contained envelope:

```json
{
  "payload": {
    "version": "1.0.0",
    "release_date": "2026-07-17T19:21:26Z",
    "assets": {
      "windows-x86_64": {
        "filename": "Hydrosphere-1.0.0-win-x86_64-per-user.exe",
        "sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
      }
    }
  },
  "algorithm": "ed25519",
  "key_id": "update-prod-2026-01",
  "signature": "..."
}
```

> [!NOTE]
> This structure is provisional and pending final validation in the main private issue #208.

## Distribution Rules

To guarantee supply chain security and prevent malicious interception or leakage:

1. **Versioning:** Never publish assets without explicit version tags in their filenames.
2. **Secrets:** Never publish private keys, build-time configurations, or secrets within the manifest or any associated assets.
3. **Signatures Required:** Never upload unsigned installer binaries.
4. **Signed Manifests:** Never publish an update manifest without a valid Ed25519 signature.
5. **Key Separation:** Do not reuse software license verification keys for signing release manifests.
6. **No Sole Reliance on TLS:** Do not rely purely on HTTPS transport security; the client application must cryptographically verify the manifest signature locally.
7. **No Arbitrary Authorities:** Do not use arbitrary URLs or third-party storage sites as update authorities.
8. **Automated Releases Only:** Never create or upload release assets manually. All official releases must be built and published solely via the authorized automated CI/CD pipeline.
9. **No Raw GitHub Artifacts:** Do not use raw GitHub Actions artifacts as the distribution channel for end-users. All assets must pass through the official release and signing pipeline before publication.

## Release Channels

* **`stable`**: Standard production-ready releases.
* **`beta`**: Pre-release builds for public beta testing and feedback.
* **`internal`**: Internal-only releases (maintained outside the public distribution repository in V1).
