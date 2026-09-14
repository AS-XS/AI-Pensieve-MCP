# Security and privacy reports

This project is a local, single-user archive. The connected MCP client can read
the complete database it opens, and may forward retrieved text to its model
provider. Do not include conversation content, exports, database files, or
source paths in a public issue or pull request.

Report suspected privacy or security problems privately through
[GitHub Private Vulnerability Reporting](https://github.com/AS-XS/AI-Pensieve-MCP/security/advisories/new).
This channel is enabled for the public repository.

Include a short description, affected version/commit, reproduction using
synthetic data where possible, and the smallest relevant log or error. Do not
include real conversation exports or database files. Allow time for a fix before
public disclosure; do not post vulnerability details in a public issue.

This reporting channel is for voluntary bug reports; it adds no telemetry,
automatic archive upload, or runtime permission check.

The [privacy guide](docs/privacy/README.md) and
[implementation review](docs/privacy/REVIEW.md) describe the intended data
boundary and current limitations. This is not a security certification, a
multi-user isolation layer, or a guarantee that a connected model will resist
instructions embedded in archived text.
