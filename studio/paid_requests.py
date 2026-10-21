"""Durable reservations. Uncertain requests retain their full maximum cost."""
from contextlib import contextmanager
from decimal import Decimal, InvalidOperation
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import tempfile


class BudgetError(ValueError):
    pass


def atomic_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(dir=path.parent, prefix='.' + path.name)
    try:
        with os.fdopen(fd, 'w') as stream:
            json.dump(value, stream, ensure_ascii=False, indent=2)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(name, path)
    finally:
        if os.path.exists(name): os.unlink(name)


def money(value):
    try: result = Decimal(str(value))
    except (InvalidOperation, TypeError): raise BudgetError('A known finite cost is required.') from None
    if not result.is_finite() or result < 0:
        raise BudgetError('A known finite cost is required.')
    return result


def _key(value):
    if not isinstance(value, str) or not re.fullmatch(r'[a-zA-Z0-9_-]{1,100}', value):
        raise BudgetError('Invalid run or request ID.')
    return value


def _run_scope(root, run_id):
    from studio.project_paths import resolve_project, project_id
    run = json.loads((Path(root) / '.studio/runs' / (_key(run_id) + '.json')).read_text())
    if isinstance(run.get('scope'), str):
        return run['scope']
    video_id = run.get('video_id')
    if not isinstance(video_id, str) or project_id(root, resolve_project(root, video_id)) != video_id:
        raise BudgetError('The paid run needs its exact canonical project identity.')
    return 'video:' + video_id


def quote_digest(quote):
    """Fingerprint the exact attempt, upper cost, and provider evidence."""
    fields = {key: quote[key] for key in ('request_id', 'logical_request_id', 'max_cost', 'evidence')}
    return hashlib.sha256(json.dumps(fields, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def _quote_paths(root, run_id):
    base = Path(root) / '.studio/paid' / _key(run_id)
    return base.with_suffix('.quotes.json'), base.with_suffix('.approvals.json')


def inspect_quote(root, run_id, request_id):
    quote_path, _ = _quote_paths(root, run_id)
    quotes = json.loads(quote_path.read_text()) if quote_path.exists() else {}
    quote = quotes.get(_key(request_id))
    if quote is None:
        quote = next((item for item in quotes.values() if isinstance(item, dict) and item.get('request_id') == request_id), None)
    if not isinstance(quote, dict): raise BudgetError('The exact paid request has no verified quote.')
    return dict(quote, fingerprint=quote_digest(quote))


def approve_quote(root, run_id, request_id, expected_quote, reviewer='human'):
    """Record a human decision for one quoted purchase attempt in this session."""
    from studio.permissions import current_session, require_permission
    if os.environ.get('VF_PERMISSION_WORKER') == '1':
        raise BudgetError('A worker cannot approve a purchase.')
    scope = _run_scope(root, run_id)
    permission = require_permission(root, scope)
    if not isinstance(reviewer, str) or not reviewer.strip(): raise BudgetError('A human reviewer is required.')
    _, path = _quote_paths(root, run_id)
    with _ledger(root, run_id):
        quote = inspect_quote(root, run_id, request_id)
        if expected_quote != quote['fingerprint']:
            raise BudgetError('The quote changed. Review the current cost and approve it again.')
        approvals = json.loads(path.read_text()) if path.exists() else {}
        approval = dict(request_id=quote['request_id'], quote_fingerprint=expected_quote,
                        session_id=current_session(root), grant_id=permission['grant_id'], reviewer=reviewer)
        approvals[quote['request_id']] = approval
        atomic_json(path, approvals)
        _mirror_paid(root, run_id, 'approvals.json', approvals)
    return approval


def _require_quote_approval(root, run_id, request_id, maximum):
    from studio.permissions import current_session, require_permission
    permission = require_permission(root, _run_scope(root, run_id))
    quote = inspect_quote(root, run_id, request_id)
    if money(quote['max_cost']) != maximum or quote['request_id'] != request_id:
        raise BudgetError('Purchase differs from the approved quoted attempt.')
    _, path = _quote_paths(root, run_id)
    approvals = json.loads(path.read_text()) if path.exists() else {}
    approval = approvals.get(request_id)
    if (not isinstance(approval, dict) or approval.get('quote_fingerprint') != quote['fingerprint']
            or approval.get('session_id') != current_session(root)
            or approval.get('grant_id') != permission['grant_id']):
        raise BudgetError('This exact paid request needs human approval of its known maximum cost in this session.')
    return quote


def _mirror_paid(root, run_id, name, value):
    """Keep export evidence beside the project; the root ledger stays authoritative."""
    run_id = _key(run_id)
    root = Path(root).resolve()
    run = json.loads((root / '.studio/runs' / (run_id + '.json')).read_text())
    # Older standalone ledgers did not identify a project. Never guess their target.
    if not run.get('video_id'): return
    from studio.project_paths import resolve_project, project_id
    project = resolve_project(root, run['video_id']).resolve()
    if project_id(root, project) != run['video_id']:
        raise BudgetError('The paid run needs its exact canonical project identity.')
    directory = project / 'runs' / run_id / 'paid'
    if not directory.resolve().is_relative_to(project):
        raise BudgetError('The paid evidence folder is outside its project.')
    if Path(name).name != name or not name.endswith('.json'):
        raise BudgetError('Invalid paid evidence filename.')
    atomic_json(directory / name, value)


@contextmanager
def _ledger(root, run_id):
    run_id = _key(run_id)
    directory = Path(root) / '.studio' / 'paid'
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / (run_id + '.json')
    with (directory / (run_id + '.lock')).open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        data = json.loads(path.read_text()) if path.exists() else {'requests': {}}
        yield data
        atomic_json(path, data)
        _mirror_paid(root, run_id, 'ledger.json', data)


def reserve(root, run_id, request_id, max_cost, *, provider='', purpose=''):
    request_id = _key(request_id)
    maximum = money(max_cost)
    run = json.loads((Path(root) / '.studio/runs' / (_key(run_id) + '.json')).read_text())
    limit = money(run['settings']['max_paid_spend'])
    with _ledger(root, run_id) as ledger:
        _require_quote_approval(root, run_id, request_id, maximum)
        requests = ledger['requests']
        if request_id in requests:
            raise BudgetError('This request already exists. Reconcile it before a retry.')
        if any(r['state'] in ('reserved', 'uncertain') for r in requests.values()):
            raise BudgetError('Reconcile the outstanding paid request before another request.')
        committed = sum((money(r['actual_cost'] if r['state'] == 'settled' else r['max_cost']) for r in requests.values()), Decimal(0))
        if committed + maximum > limit:
            raise BudgetError('The paid request exceeds the saved budget.')
        record = dict(id=request_id, max_cost=str(maximum), state='reserved', provider=provider, purpose=purpose)
        requests[request_id] = record
    return record


def settle(root, run_id, request_id, actual_cost, provider_request_id='', *, estimated_upper_bound=False):
    actual = money(actual_cost)
    with _ledger(root, run_id) as ledger:
        record = ledger['requests'][_key(request_id)]
        if actual > money(record['max_cost']):
            raise BudgetError('Provider cost exceeds the reservation; keep it unresolved.')
        if record['state'] == 'settled':
            if money(record['actual_cost']) != actual:
                raise BudgetError('A settled request cannot change cost.')
            return record
        record.update(state='settled', actual_cost=str(actual), provider_request_id=provider_request_id,
                      estimated_upper_bound=estimated_upper_bound)
    return record


def reconcile(root, run_id, request_id, actual_cost, provider_request_id='', *, evidence=''):
    from studio.permissions import require_permission
    require_permission(root, _run_scope(root, run_id))
    actual = money(actual_cost)
    with _ledger(root, run_id) as ledger:
        record = ledger['requests'][_key(request_id)]
        if actual > money(record['max_cost']): raise BudgetError('Cost exceeds the reserved maximum.')
        if record['state'] == 'settled' and not record.get('estimated_upper_bound') and money(record['actual_cost']) != actual:
            raise BudgetError('A final provider charge cannot be changed.')
        record.update(state='settled', actual_cost=str(actual), provider_request_id=provider_request_id,
                      estimated_upper_bound=False, reconciliation_evidence=evidence)
    return record


def record_quote(root, run_id, request_id, max_cost, evidence, *, retry=False):
    run_id, request_id = _key(run_id), _key(request_id)
    maximum = money(max_cost)
    if not evidence: raise BudgetError('A provider quote needs evidence.')
    run = json.loads((Path(root) / '.studio/runs' / (run_id + '.json')).read_text())
    if maximum > money(run['settings']['max_paid_spend']): raise BudgetError('Quote exceeds the saved budget.')
    path = Path(root) / '.studio/paid' / (run_id + '.quotes.json')
    with _ledger(root, run_id) as ledger:
        quotes = json.loads(path.read_text()) if path.exists() else {}
        attempted = request_id
        if retry:
            prior = [r for key,r in ledger['requests'].items() if key == request_id or key.startswith(request_id + '-retry-')]
            if not prior or any(r['state'] != 'settled' for r in prior):
                raise BudgetError('Reconcile every prior attempt before an explicit retry.')
            attempted = request_id + '-retry-' + str(len(prior))
            _key(attempted)
        elif request_id in ledger['requests']:
            raise BudgetError('This request was attempted. Reconcile it, then quote an explicit retry.')
        quote = dict(request_id=attempted, logical_request_id=request_id, max_cost=str(maximum), evidence=evidence)
        quotes[request_id] = quote
        atomic_json(path, quotes)
        _, approval_path = _quote_paths(root, run_id)
        if approval_path.exists():
            approvals = json.loads(approval_path.read_text())
            approvals.pop(attempted, None)
            atomic_json(approval_path, approvals)
        _mirror_paid(root, run_id, 'quotes.json', dict(run.get('settings', {}).get('paid_quotes', {}), **quotes))
    return quote


def managed_stage_validated(root, project, stage):
    """Validation for a managed run; deliberately writes no approval decision."""
    if os.environ.get('VF_PAID_GUARD') != '1': return False
    try:
        run_id = _key(os.environ.get('VF_RUN_ID'))
        run = json.loads((Path(root) / '.studio/runs' / (run_id + '.json')).read_text())
        from studio.project_paths import resolve_project
        if resolve_project(root, run['video_id']).resolve() != Path(project).resolve(): return False
        state = run['stages'][stage]
        if run['status'] != 'running' or state['status'] != 'validated': return False
        import hashlib
        return bool(state['artifacts']) and all(
            hashlib.sha256((Path(project) / name).read_bytes()).hexdigest() == digest
            for name, digest in state['artifacts'].items())
    except (OSError, ValueError, KeyError, TypeError): return False


def guarded_call(root, run_id, request_id, max_cost, call, *, provider='', purpose=''):
    reserve(root, run_id, request_id, max_cost, provider=provider, purpose=purpose)
    try:
        result = call()
    except BaseException:
        with _ledger(root, run_id) as ledger:
            ledger['requests'][request_id]['state'] = 'uncertain'
        raise
    # Charge the whole approved upper bound when no receipt is available.
    settle(root, run_id, request_id, max_cost, estimated_upper_bound=True)
    return result


def managed_quote(root, request_id, *, purpose='', metadata=None, run_id=None):
    """Return a saved, evidenced upper-bound quote for one exact request."""
    if run_id is None:
        if os.environ.get('VF_PAID_GUARD') != '1': return None
        if Path(os.environ.get('VF_RUN_ROOT', '')).resolve() != Path(root).resolve():
            raise BudgetError('Paid request root differs from its saved run.')
        run_id = os.environ.get('VF_RUN_ID')
    run_id = _key(run_id)
    run = json.loads((Path(root) / '.studio/runs' / (run_id + '.json')).read_text())
    request_id = _key(request_id)
    quote_path = Path(root) / '.studio/paid' / (run_id + '.quotes.json')
    quotes = json.loads(quote_path.read_text()) if quote_path.exists() else {}
    quote = quotes.get(request_id) or run.get('settings', {}).get('paid_quotes', {}).get(request_id)
    if not isinstance(quote, dict) or not quote.get('evidence'):
        pending = dict(run_id=run_id, request_id=request_id, purpose=purpose, metadata=metadata or {}, state='needs-quote')
        atomic_json(Path(root) / '.studio/paid' / (run_id + '-' + request_id + '.pending.json'),
                    pending)
        _mirror_paid(root, run_id, request_id + '.pending.json', pending)
        raise BudgetError(f'Paid {purpose or "request"} needs a verified maximum-cost quote: run {run_id}, request {request_id}. Details: {metadata or {}}')
    money(quote.get('max_cost'))
    _require_quote_approval(root, run_id, quote.get('request_id', request_id), money(quote['max_cost']))
    _mirror_paid(root, run_id, 'quotes.json', dict(run.get('settings', {}).get('paid_quotes', {}), **quotes))
    return run_id, dict(quote, request_id=quote.get('request_id', request_id))
