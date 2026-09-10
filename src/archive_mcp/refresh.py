import json
from collections import Counter
from pathlib import Path

from .auto_import import import_all
from .db import archive_status, initialize
from .sync import default_roots, sync_local


def refresh_archive(connection, config):
    data = json.loads(Path(config).read_text(encoding="utf-8"))
    initialize(connection)
    counts = Counter(files=0)
    formats = Counter()
    warnings = Counter()
    batches = []

    for export in data.get("exports", []):
        result = import_all(
            connection, [Path(export["path"]).expanduser()],
            export.get("account", "default"),
        )
        batches.append(result.pop("batch_id"))
        formats.update(result.pop("formats"))
        warnings.update(result.pop("warnings"))
        counts.update(result)

    local = data.get("local")
    local_counts = sync_local(
        connection, *default_roots(), local.get("account", "default"),
        providers=local.get("providers"),
    ) if local is not None else {"files": 0}

    return {
        "exports": {
            "batches": batches,
            **dict(counts),
            "formats": dict(sorted(formats.items())),
            "warnings": dict(sorted(warnings.items())),
        },
        "local": local_counts,
        "archive": archive_status(connection)["totals"],
    }
