#!/usr/bin/env python3
"""Import Crystal monster files without overwriting existing Canary definitions.

Existing Canary monster names are authoritative. Crystal files are copied only when
no matching Game.createMonsterType(name) exists. This prevents the duplicate
registration errors caused by replacing/refreshed definitions during migration.
"""
from __future__ import annotations
import json, re
from pathlib import Path

SOURCE = Path('.crystalserver/data-global/monster')
DEST = Path('data-otservbr-global/monster')
OUT = Path('data-otservbr-global')
NAME_RE = re.compile(r'Game\\.createMonsterType\\(\\s*["\\\'](.+?)["\\\']\\s*\\)')


def norm(s: str) -> str:
    return re.sub(r'\\s+', ' ', s.strip().lower())


def name_of(path: Path):
    m = NAME_RE.search(path.read_text(encoding='utf-8'))
    return m.group(1) if m else None


def main():
    if not SOURCE.exists():
        raise SystemExit(f'Missing Crystal monster source: {SOURCE}')
    existing = {}
    for p in DEST.rglob('*.lua'):
        n = name_of(p)
        if n:
            existing[norm(n)] = p
    imported, skipped = [], []
    for src in sorted(SOURCE.rglob('*.lua')):
        n = name_of(src)
        if not n:
            continue
        key = norm(n)
        rel = src.relative_to(SOURCE)
        target = DEST / rel
        if key in existing:
            skipped.append({'name': n, 'source': str(src), 'existing': str(existing[key])})
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(src.read_text(encoding='utf-8'), encoding='utf-8')
        existing[key] = target
        imported.append({'name': n, 'source': str(src), 'canary_path': str(target)})
    (OUT/'monster_id_map.json').write_text(json.dumps({'policy':'preserve-existing-canary-monsters','imported':imported,'skipped_existing':skipped},ensure_ascii=False,indent=2)+'\\n',encoding='utf-8')
    report=['# Crystal -> Canary monster migration','','Existing Canary monster definitions are authoritative. Crystal definitions with an already registered name are skipped to prevent duplicate `Game.createMonsterType` registration.','','- Imported: '+str(len(imported)),'- Skipped because already registered: '+str(len(skipped)),'']
    (OUT/'CRYSTAL_CANARY_MONSTER_MIGRATION.md').write_text('\\n'.join(report),encoding='utf-8')
    print(json.dumps({'imported':len(imported),'skipped_existing':len(skipped)}))

if __name__ == '__main__': main()
