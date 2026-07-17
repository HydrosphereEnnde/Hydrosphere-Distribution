# Hydrosphere Distribution

Welcome to the official public distribution repository for **Hydrosphere**.

## Purpose

This repository is used exclusively for the distribution of official Hydrosphere release assets, including:
* Official installers for Windows
* Cryptographically signed update manifests
* Official release notes and changelogs
* Associated release metadata and assets

> [!NOTE]
> **Source Code Notice:** This repository does **not** contain the application's source code. The core codebase of Hydrosphere is maintained in a separate private repository.

## Important Usage Rules

* **No Direct Development:** This repository is not a development environment. Do not submit pull requests containing code changes or application logic.
* **No Secrets:** Do not publish or commit any secrets, private keys, certificates, environment files, or credentials here.
* **Licensing:** Use of official Hydrosphere binaries requires a valid Hydrosphere license.
* **Pre-release Status:** Stable releases are not currently published here. They will only be made available once the automated build, signing, and verification pipelines are fully prepared.

## Security & Authenticity Architecture

GitHub serves as a transport layer and storage medium for distribution assets; it is **not** the cryptographic authority.

Once the full flow defined in the main repository's private issue #208 (internal reference only) is implemented, the authenticity of all artifacts will rely on the following cryptographic trust model:
1. **Ed25519 Signed Manifest**: An update manifest (`hydrosphere-update-manifest-v1.json`) containing metadata and file hashes, signed using a secure Ed25519 key.
2. **SHA-256 Integrity Verification**: The SHA-256 checksum of every artifact must match the hash recorded in the signed manifest.
3. **Authenticode Signature**: The installer executable (`.exe`) must carry a valid Authenticode signature.
4. **Fail-Closed Validation**: The Hydrosphere application will implement strict, fail-closed cryptographic validation of all update manifests and downloaded binaries.

## Documentation Reference

For details on the planned layout and structure of releases, see [docs/release-layout.md](docs/release-layout.md).
