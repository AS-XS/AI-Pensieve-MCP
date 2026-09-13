"""In-memory accounting for one client task against an unchanged archive.

Feed structured results once, including failures. This helper does not read a
database, use gold labels, store text, or replace the model's substantive answer.
"""


def passages(value, inherited=None):
    """Extract bodies/snippets once from structured MCP results, not text mirrors."""
    if isinstance(value, list):
        for item in value:
            yield from passages(item, inherited)
    elif isinstance(value, dict):
        source = dict(inherited or {})
        context = value.get("conversation", {})
        if isinstance(context, dict):
            source.update({k: context[k] for k in ("provider", "account") if k in context})
            if "source_id" in context:
                source["conversation_id"] = context["source_id"]
        source.update(value.get("provenance") or {})
        source.update({k: value[k] for k in ("provider", "account", "conversation_id") if k in value})
        record = value.get("record_id", value.get("node_source_id", value.get("source_id")))
        for field in ("text", "snippet"):
            if isinstance(value.get(field), str):
                yield source, record, field, value[field], value.get("offset", 0)
        for key, item in value.items():
            if key not in ("conversation", "provenance"):
                yield from passages(item, source)


def source_key(source):
    return source['provider'], source['account']


def scope_key(arguments):
    return (tuple(sorted(set(arguments.get('providers') or []))),
            tuple(sorted(set(arguments.get('accounts') or []))),
            arguments.get('date_from'), arguments.get('date_to'))


def selected(sources, arguments):
    providers = arguments.get('providers') or ([arguments['provider']] if arguments.get('provider') else [])
    accounts = arguments.get('accounts') or ([arguments['account']] if arguments.get('account') else [])
    return {(p, a) for p, a in sources if (not providers or p in providers) and (not accounts or a in accounts)}


class CoverageLedger:
    """Client-owned task accounting; start fresh after any archive change.

    Feed only calls to the selected archive, including client validation failures.
    Inventory and traversal refer to imported data, not complete provider exports.
    """

    def __init__(self):
        self.attempts = self.failures = self.unfinished = self.characters = 0
        self.inventory_complete = False
        self.inventory_totals = None
        self.known, self.searched, self.returned, self.traversed = set(), set(), set(), set()
        self.searches_without_inventory = 0
        self.chains, self.completed_scopes = {}, set()
        self.complete = False

    def record(self, tool, arguments, result=None, failed=False, unfinished=False):
        self.attempts += 1
        if unfinished:
            self.unfinished += 1
            return
        if failed or result is None:
            self.failures += 1
            return
        if tool in ('list_sources', 'search_history') and isinstance(result, dict):
            result = result['result']  # MCP structured wrapper for list returns.
        if tool == 'archive_status':
            self.known.update(map(source_key, result['sources']))
            self.inventory_totals = dict(result['totals'])
            self.inventory_complete = True
        elif tool == 'list_sources':
            self.known.update(map(source_key, result))
            if not arguments.get('provider') and not arguments.get('account'):
                self.inventory_complete = True
        if tool == 'cross_reference':
            found = set(map(source_key, result['bundles']))
            self.known.update(found)
            self.searched.update(found)
        elif tool in ('search_history', 'search_conversations', 'get_conversation_matches'):
            self.searched.update(selected(self.known, arguments))
            if not self.inventory_complete:
                self.searches_without_inventory += 1
        for source, _, _, body, _ in passages(result):
            self.characters += len(body)
            if body and source.get('provider') is not None and source.get('account') is not None:
                key = source_key(source)
                self.known.add(key)
                self.returned.add(key)
                if tool in ('search_history', 'search_conversations', 'get_conversation_matches'):
                    self.searched.add(key)
        if tool not in ('survey_archive', 'sweep_archive'):
            return
        scope = scope_key(arguments)
        key = (tool, scope)
        cursor = arguments.get('cursor')
        contiguous = cursor is None or (key in self.chains and self.chains[key] == cursor)
        if tool == 'survey_archive':
            self.known.update(map(source_key, result['sources']))
        if not contiguous:
            return
        next_cursor = result['next_cursor']
        if next_cursor is None:
            self.chains.pop(key, None)
            self.completed_scopes.add(scope)
            if not any(scope):
                self.complete = True
        else:
            self.chains[key] = next_cursor
        # Date-limited traversal is not full history for a source.
        if scope[2] is None and scope[3] is None:
            if tool == 'survey_archive':
                self.traversed.update(source_key(s) for s in result['sources'] if s['status'] == 'complete')
            elif next_cursor is None:
                self.traversed.update(selected(self.known, arguments))

    def summary(self):
        def rows(sources):
            return [dict(provider=p, account=a) for p, a in sorted(sources)]
        return {
            'attempted_calls': self.attempts, 'failed_calls': self.failures,
            'unfinished_calls': self.unfinished,
            'successful_results': self.attempts - self.failures - self.unfinished,
            'returned_text_characters': self.characters,
            'inventory_complete': self.inventory_complete, 'inventory_totals': self.inventory_totals,
            'known_sources': rows(self.known), 'sources_searched': rows(self.searched),
            'sources_with_returned_text': rows(self.returned),
            'known_sources_without_returned_text': rows(self.known - self.returned),
            'sources_fully_traversed': rows(self.traversed),
            'complete_archive_traversal': self.complete,
            'completed_scopes': [dict(providers=list(p), accounts=list(a), date_from=d1, date_to=d2)
                                 for p, a, d1, d2 in sorted(self.completed_scopes, key=str)],
            'searches_without_complete_inventory': self.searches_without_inventory,
            'note': 'Returned text includes text/snippet fields, including title snippets and repeated reads. '
                    'Searched sources may have no matches. Complete traversal requires an observed cursor chain '
                    'from the start; it is not proof of complete provider exports. Restart accounting after archive changes.',
        }


def coverage_from_events(events, server):
    """Adapt a Codex JSON event stream without reading its prompt or gold corpus."""
    ledger = CoverageLedger()
    pending = {}
    completed = set()
    for event in events:
        item = event.get('item', {})
        if item.get('type') != 'mcp_tool_call' or item.get('server') != server:
            continue
        identity = item.get('id')
        if event.get('type') == 'item.started':
            pending[identity] = item
        elif event.get('type') == 'item.completed':
            if identity is not None and identity in completed:
                continue
            completed.add(identity)
            pending.pop(identity, None)
            ledger.record(item['tool'], item.get('arguments') or {},
                          (item.get('result') or {}).get('structured_content'),
                          failed=bool(item.get('error')) or item.get('status') == 'failed')
    for item in pending.values():
        ledger.record(item['tool'], item.get('arguments') or {}, unfinished=True)
    return ledger.summary()
