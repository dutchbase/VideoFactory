"""Tool-neutral, recoverable lessons. Brand rules need approval from a person."""
import hashlib
import json
from pathlib import Path
import re
from studio.paid_requests import atomic_json


def load_lessons(root, brand, stage):
    if not isinstance(brand, str) or not re.fullmatch(r'[a-zA-Z0-9_-]+', brand): raise ValueError('Invalid brand.')
    records = []
    for directory in (Path(root) / 'learning', Path(root) / 'brands' / brand / 'learning'):
        if not directory.exists(): continue
        for path in sorted(directory.glob('*.json')):
            try: item = json.loads(path.read_text())
            except (ValueError, OSError): continue
            if item.get('status') != 'verified': continue
            if item.get('brand') not in (None, brand): continue
            if item.get('kind') == 'brand-rule' and item.get('user_approved') is not True: continue
            if stage not in item.get('stages', [stage]): continue
            if not item.get('evidence') or not item.get('lesson'): continue
            records.append(item)
    return records


def record_learning(project, run_id, stage, findings=None):
    if not all(isinstance(x, str) and re.fullmatch(r'[a-zA-Z0-9_-]+', x) for x in (run_id, stage)):
        raise ValueError('Invalid learning record ID.')
    findings = findings or []
    value = dict(run_id=run_id, stage=stage, status='findings' if findings else 'none', findings=findings)
    atomic_json(Path(project) / 'learning' / (run_id + '-' + stage + '.json'), value)
    return value


def save_lesson(root, lesson, *, brand=None):
    if brand is not None and not re.fullmatch(r'[a-zA-Z0-9_-]+', brand): raise ValueError('Invalid brand.')
    if not isinstance(lesson, dict) or not lesson.get('lesson'):
        raise ValueError('A lesson is required.')
    if lesson.get('status') == 'verified' and not lesson.get('evidence'):
        raise ValueError('Verified lessons require evidence.')
    if lesson.get('kind') == 'brand-rule':
        # Agents may propose rules. Only a separate action by a person can adopt them.
        lesson = dict(lesson, status='proposed', user_approved=False)
    directory = Path(root) / 'brands' / brand / 'learning' if brand else Path(root) / 'learning'
    ident = hashlib.sha256(json.dumps(lesson, sort_keys=True).encode()).hexdigest()[:20]
    atomic_json(directory / (ident + '.json'), lesson)
    return ident
