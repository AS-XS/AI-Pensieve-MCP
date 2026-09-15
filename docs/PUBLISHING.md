# Publishing the Python packages

Two distributions share version 0.1.0:

- `ai-pensieve-mcp` is built from the repository root and provides the read-only
  STDIO command plus `pensieve-archive`. Its GUI dependency remains optional.
- `ai-pensieve` is built from `packaging/desktop`, depends on the matching core
  with its GUI extra, and provides `ai-pensieve` and `pensieve` launchers.

Keep both versions and the desktop's exact core dependency aligned. The desktop
license/notice copies must match the root files. The core's PyPI description is
`docs/PYPI_README.md`, including its MCP Registry ownership marker.
The root README is the short user quickstart. Generated artwork prompts,
archives and local planning files are excluded from package distributions.

## One-time PyPI setup

Sign in to your own PyPI account and open
[Publishing](https://pypi.org/manage/account/publishing/). Add a pending GitHub
publisher for each package, using the fields below. For a new pair of projects,
bootstrap them sequentially: PyPI rejects two pending publishers with the same
workflow configuration. Add the core publisher and run the workflow first;
the core upload succeeds and the unconfigured desktop upload fails. Then add
the desktop publisher and rerun the failed publishing job, reusing the tested
artifacts. Once both projects exist, the same workflow publishes both normally.

| Field | Value |
| --- | --- |
| PyPI project name | `ai-pensieve-mcp`, then `ai-pensieve` |
| Owner | `AS-XS` |
| Repository name | `AI-Pensieve-MCP` |
| Workflow name | `publish.yml` |
| Environment name | `pypi` |

Configure the GitHub environment `pypi` to allow protected branches only.
The publishing workflow accepts a manual dispatch on `main`; it is not run by
PRs or every push. The main ruleset requires the existing four CI checks,
which now include distribution builds and installed-command/MCP smoke tests.

## Release

1. Merge the reviewed version changes through a passing PR.
2. Run **Publish PyPI packages** on `main` in GitHub Actions.
3. The build job reruns synthetic tests, builds wheels from source distributions,
   validates metadata, and verifies installed commands and a synthetic STDIO
   session. It uploads the tested artifacts to the publishing job.
4. The publishing job uses PyPI Trusted Publishing (OIDC), uploading the core
   before the desktop launcher. No stored PyPI API token is needed. Existing
   files are skipped to permit retrying a partially completed two-package upload;
   publish changed contents under a new version.
5. Test the registry artifacts with `uvx ai-pensieve` and
   `pipx install ai-pensieve`, using an explicit temporary `--database` for GUI
   checks. Test `uvx ai-pensieve-mcp` against a synthetic initialized archive.
6. Update the installation guide's publication status only after the registry
   commands have been verified. Record the release version and tested platform.

## MCP Registry

`server.json` describes the core server as `io.github.AS-XS/ai-pensieve-mcp`.
It points to the published PyPI core and requests one required positional input:
the absolute path to an existing imported archive. Clients use `uvx` to launch
the package over STDIO. The desktop launcher is a separate application and is
not an MCP server entry.

After publishing a new PyPI version, keep the package and server versions in
`server.json` aligned with `pyproject.toml`. Run **Publish MCP Registry metadata**
on `main` in GitHub Actions. This manual workflow checks the official schema,
versions and the ownership marker in the published PyPI description, then uses
GitHub OIDC and the pinned official publisher to register the metadata. It needs
no stored Registry token. The validation script requires Python 3.11+ and
`jsonschema==4.26.0`; these are release tools, not runtime requirements.

Check the [Registry API entry](https://registry.modelcontextprotocol.io/v0.1/servers/io.github.AS-XS%2Fai-pensieve-mcp/versions/latest)
after the workflow succeeds. Registration shares public package metadata;
archive paths are supplied locally by each user and archive contents are not
uploaded. Listing does not imply a security audit or guarantee inclusion in
every downstream marketplace.

Sources: [PyPI pending publishers](https://docs.pypi.org/trusted-publishers/creating-a-project-through-oidc/),
[PyPI publishing action](https://github.com/pypa/gh-action-pypi-publish),
[MCP Registry PyPI verification](https://github.com/modelcontextprotocol/registry/blob/main/docs/modelcontextprotocol-io/package-types.mdx).
