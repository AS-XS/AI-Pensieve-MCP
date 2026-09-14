"""Expected import summaries for unchanged synthetic adapter fixtures."""


def expected_result(processed, state='new'):
    changes = {}
    for kind in ('conversations', 'nodes', 'memories'):
        changes[kind] = dict(new=0, updated=0, unchanged=0, protected=0, removed=0)
        changes[kind][state] = processed.get(kind, 0)
    return {**processed, 'changes': changes}
