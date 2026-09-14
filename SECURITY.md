# Security and privacy reports

This project is a local, single-user archive. The connected MCP client can read
the complete database it opens, and may forward retrieved text to its model
provider. Do not include conversation content, exports, database files, or
source paths in a public issue or pull request.

The repository is public. As of 2026-09-14, GitHub private vulnerability
reporting is not yet enabled, and no dedicated private reporting address is
published.

Until a private channel is available, open a minimal issue asking the maintainer
for a private reporting route. Do not include vulnerability details, exploit
steps, private data, or logs in that public issue.

Once enabled, use [Report a vulnerability](https://github.com/AS-XS/AI-Pensieve-MCP/security/advisories/new)
for suspected privacy or security problems. Include a short description, affected
version/commit, reproduction using synthetic data where possible, and the smallest
relevant log or error. Allow time for a fix before public disclosure.

The maintainer can enable private reporting in repository Settings > Advanced
Security, then verify that Security > Advisories offers **Report a vulnerability**.
See [GitHub's configuration guide](https://docs.github.com/en/code-security/how-tos/report-and-fix-vulnerabilities/configure-vulnerability-reporting/configure-for-a-repository).

This reporting channel is for voluntary bug reports; it adds no telemetry,
automatic archive upload, or runtime permission check.

The [privacy guide](docs/privacy/README.md) and
[implementation review](docs/privacy/REVIEW.md) describe the intended data
boundary and current limitations. This is not a security certification, a
multi-user isolation layer, or a guarantee that a connected model will resist
instructions embedded in archived text.
