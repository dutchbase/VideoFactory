"""Brand-first asset search and explicit, draft-only adaptation records."""
import hashlib
import json
from pathlib import Path
import re
from studio.paid_requests import atomic_json


def _asset_path(root, name, brand):
    lexical = Path(name)
    if lexical.is_absolute() or any(part.startswith('.') or part in ('_auth', '_studio') for part in lexical.parts):
        raise ValueError('Private files are not asset sources.')
    path = (root / lexical).resolve()
    if not path.is_relative_to(root) or not path.is_file(): raise ValueError('Invalid source asset.')
    parts = path.relative_to(root).parts
    allowed = parts[:1] == ('library',) or parts[:3] == ('brands', brand, 'library')
    if parts[:1] == ('videos',) and '04_scene' in parts:
        index = parts.index('04_scene')
        allowed = parts[index:index+2] == ('04_scene','assets')
        if allowed:
            try: allowed = json.loads((root.joinpath(*parts[:index]) / 'project.json').read_text()).get('brand') == brand
            except (OSError, ValueError): allowed = False
    if not allowed: raise ValueError('Use a brand/shared library or a matching video asset folder.')
    return path


def _immutable(path, content):
    if path.exists():
        if path.read_bytes() != content: raise ValueError('An immutable adaptation artifact changed.')
        return
    with path.open('xb') as stream: stream.write(content)


def find_assets(root, brand, query=''):
    if not re.fullmatch(r'[a-zA-Z0-9_-]+', brand): raise ValueError('Invalid brand.')
    root = Path(root)
    result = []
    for scope in (Path(root) / 'brands' / brand / 'library', Path(root) / 'library'):
        if not scope.is_dir(): continue
        for path in sorted(scope.rglob('*.json')):
            try: item = json.loads(path.read_text())
            except (OSError, ValueError): continue
            items = item if isinstance(item, list) else [item]
            for item in items:
                if isinstance(item, dict) and query.lower() in json.dumps(item).lower():
                    result.append(dict(item, record_path=str(path.relative_to(root))))
        for path in sorted(scope.rglob('material.md')):
            text = path.read_text()
            if query.lower() in text.lower():
                item = dict(re.findall(r'^([a-z_]+):\s*"?([^\n"]+)"?$', text, re.M))
                result.append(dict(item, record_path=str(path.relative_to(root))))
    return result


def plan_adaptation(root, source, source_brand, target_brand, *, rights, changes, token_restyle=False):
    root = Path(root).resolve()
    if not all(isinstance(b, str) and re.fullmatch(r'[a-zA-Z0-9_-]+', b) for b in (source_brand, target_brand)):
        raise ValueError('Invalid source or target brand.')
    path = _asset_path(root, source, source_brand)
    if not rights or not changes or not source_brand or not target_brand:
        raise ValueError('Source brand, target brand, rights and changes are required.')
    from libcore import ALLOWED
    if rights not in ALLOWED | {'own'}: raise ValueError('The source rights are not approved for reuse.')
    # Raster and captured UI cannot be safely changed through design tokens.
    suitable = path.suffix.lower() in ('.svg', '.html', '.css', '.json', '.py', '.js', '.tsx')
    if token_restyle and not suitable:
        raise ValueError('This asset needs recreation, not token restyling.')
    sha = hashlib.sha256(path.read_bytes()).hexdigest()
    record = dict(source=str(path.relative_to(root)), source_sha256=sha,
                  source_brand=source_brand, target_brand=target_brand, rights=rights,
                  changes=changes, method='token-restyle' if token_restyle else 'recreate',
                  status='draft', user_approved=False)
    ident = hashlib.sha256(json.dumps(record, sort_keys=True).encode()).hexdigest()[:20]
    atomic_json(root / 'brands' / target_brand / 'library/adaptations' / (ident + '.json'), record)
    return record


def adapt_asset(root, source, source_brand, target_brand, *, rights, changes,
                tokens=None, source_kind='unknown', replacement=None, validation=None):
    """Create a reusable draft with immutable source bytes and explicit evidence.

    Restyling only replaces declared ``{{TOKEN:name}}`` placeholders. Artwork
    with brand identity needs a recreated replacement and target-brand evidence.
    """
    root = Path(root).resolve()
    original = _asset_path(root, source, source_brand)
    if (not isinstance(validation, dict) or validation.get('target_brand') != target_brand or
            not validation.get('evidence') or validation.get('identity_removed') is not True or
            validation.get('claims_verified') is not True):
        raise ValueError('Target-brand evidence must verify removed source identity and all retained claims.')
    forbidden = source_kind in ('logo', 'character', 'screenshot', 'capture', 'screen', 'unknown')
    if tokens is not None:
        if forbidden or replacement is not None or original.suffix.lower() not in ('.svg', '.html', '.css', '.js'):
            raise ValueError('This asset requires recreation and target-brand evidence.')
        if not isinstance(tokens, dict) or not tokens or not all(
                isinstance(k, str) and re.fullmatch(r'[A-Za-z0-9_.-]+', k) and isinstance(v, str)
                and not any(c in v for c in ('<', '>', '{', '}', '\n', '\r')) for k,v in tokens.items()):
            raise ValueError('Use explicit token names and plain target values.')
        text = original.read_text()
        declared = set(re.findall(r'\{\{TOKEN:([A-Za-z0-9_.-]+)\}\}', text))
        if not declared or declared != set(tokens): raise ValueError('Every declared token needs an explicit target value.')
        for key, value in tokens.items(): text = text.replace('{{TOKEN:' + key + '}}', value)
        content = text.encode()
        suffix = original.suffix
        method = 'token-restyle'
    else:
        if not replacement or not isinstance(validation, dict) or validation.get('target_brand') != target_brand or not validation.get('evidence'):
            raise ValueError('Recreation needs replacement artwork and target-brand validation evidence.')
        recreated = _asset_path(root, replacement, target_brand)
        content = recreated.read_bytes()
        if not content or content == original.read_bytes(): raise ValueError('A recreated replacement must have new bytes.')
        suffix = recreated.suffix
        method = 'recreated'
    record = plan_adaptation(root, source, source_brand, target_brand, rights=rights,
                             changes=changes, token_restyle=tokens is not None)
    ident = hashlib.sha256(json.dumps(dict(record, result=hashlib.sha256(content).hexdigest()), sort_keys=True).encode()).hexdigest()[:20]
    directory = root / 'brands' / target_brand / 'library/adaptations' / ident
    directory.mkdir(parents=True, exist_ok=True)
    snapshot = directory / ('source' + original.suffix)
    _immutable(snapshot, original.read_bytes())
    artifact = directory / ('asset' + suffix)
    _immutable(artifact, content)
    record.update(method=method, id=ident, source_snapshot=str(snapshot.relative_to(root)),
                  artifact=str(artifact.relative_to(root)), artifact_sha256=hashlib.sha256(content).hexdigest(),
                  validation=validation, tokens=tokens, claims_verification=validation['evidence'])
    atomic_json(directory / 'adaptation.json', record)
    return record
