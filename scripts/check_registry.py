"""Validate public Registry metadata against its schema and published package."""
import json
from pathlib import Path
import tomllib
from urllib.request import urlopen

from jsonschema import Draft7Validator, FormatChecker


def fetch_json(url):
    with urlopen(url, timeout=30) as response:
        return json.load(response)


def main():
    root = Path(__file__).resolve().parents[1]
    server = json.loads((root / "server.json").read_text())
    schema = fetch_json(server["$schema"])
    Draft7Validator(schema, format_checker=FormatChecker()).validate(server)
    project = tomllib.loads((root / "pyproject.toml").read_text())["project"]
    package, = server["packages"]
    assert package["identifier"] == project["name"]
    assert server["version"] == package["version"] == project["version"]
    published = fetch_json(
        f'https://pypi.org/pypi/{package["identifier"]}/{package["version"]}/json'
    )
    marker = f'<!-- mcp-name: {server["name"]} -->'
    assert marker in published["info"]["description"], "Published ownership marker missing"
    assert published["urls"], "No published package files"
    print("Registry schema, package versions, and published PyPI ownership marker passed.")


if __name__ == "__main__":
    main()
