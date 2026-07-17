# Security Policy

## Responsible Disclosure

We take the security of Hydrosphere seriously. If you believe you have found a security vulnerability, please do **NOT** open a public issue. Doing so exposes the vulnerability to the public before a fix can be prepared.

Security reporting contact: pending publication before the first production release.

## Repository Hygiene and Safety Rules

To maintain the cryptographic integrity and safety of the Hydrosphere distribution pipeline, please adhere strictly to the following guidelines:

1. **No Public Vulnerabilities**: Do not disclose vulnerabilities in public issues, PRs, or discussions. Use the pending security reporting channel once published.
2. **No Secrets or Credentials**: Never commit secrets, passwords, API tokens, configuration files, or other credentials to this repository.
3. **No Private Keys or Certificates**: Do not upload or commit code signing private keys, certificates, or local test keys.
4. **No Suspicious Binaries**: Do not attach or commit unverified, untrusted, or unsigned binary files.
5. **No Implicit Trust**: Never trust a binary or asset solely because it is hosted on GitHub. Always verify using the official cryptographic verification flow (Ed25519 signature manifest and Authenticode signatures) once implemented.
