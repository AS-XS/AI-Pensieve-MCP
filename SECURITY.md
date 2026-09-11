# Security and privacy reports

This project is a local, single-user archive. The connected MCP client can read
the complete database it opens, and may forward retrieved text to its model
provider. Do not include conversation content, exports, database files, or
source paths in a public issue or pull request.

As of 2026-09-10, this repository is private. GitHub's private vulnerability
reporting feature is [available for public repositories](https://docs.github.com/en/code-security/how-tos/report-and-fix-vulnerabilities/configure-vulnerability-reporting/configure-for-a-repository).
It is not active here. At public launch, the owner should enable it in repository
Settings > Advanced Security and verify that Security > Advisories offers
**Report a vulnerability**. Until then, no dedicated external reporting route
is configured.

Once enabled, use **Report a vulnerability** for suspected privacy or security
problems. Include a short description, affected version/commit, reproduction using
synthetic data where possible, and the smallest relevant log or error. Allow
time for a fix before public disclosure. If you cannot contact the owner,
remove private data and open a minimal issue describing only the behavior.
This reporting channel is for voluntary bug reports; it adds no telemetry,
automatic archive upload, or runtime permission check.

The [privacy guide](docs/privacy/README.md) and
[implementation review](docs/privacy/REVIEW.md) describe the intended data
boundary and current limitations. This is not a security certification, a
multi-user isolation layer, or a guarantee that a connected model will resist
instructions embedded in archived text.
