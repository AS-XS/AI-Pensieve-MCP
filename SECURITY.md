# Security and privacy reports

This project is a local, single-user archive. The connected MCP client can read
the complete database it opens, and may forward retrieved text to its model
provider. Do not include conversation content, exports, database files, or
source paths in a public issue or pull request.

Before publication, the owner must add a concrete private reporting address or
enable GitHub private vulnerability reporting. That contact route is not yet
configured in this local prototype.

Once that route exists, for a suspected privacy or security problem, contact the repository owner
privately with a short description, affected version/commit, reproduction using
synthetic data where possible, and the smallest relevant log or error. Allow
time for a fix before public disclosure. If you cannot contact the owner,
remove private data and open a minimal issue describing only the behavior.

The [privacy guide](docs/privacy/README.md) and
[implementation review](docs/privacy/REVIEW.md) describe the intended data
boundary and current limitations. This is not a security certification, a
multi-user isolation layer, or a guarantee that a connected model will resist
instructions embedded in archived text.
