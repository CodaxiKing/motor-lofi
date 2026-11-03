"""Biblioteca de imagens externas para o modo DESENHO (sem dependências extras)."""
from __future__ import annotations
import argparse
import hashlib
import json
import shutil
import sqlite3
from pathlib import Path
from datetime import datetime, timezone

TYPES = {'character', 'environment', 'prop', 'expression', 'pose', 'animation', 'full_scene'}
MODES = {'FULL_SCENE', 'LAYERED_SCENE', 'HYBRID_SCENE'}
EXTS = {'.png', '.jpg', '.jpeg', '.webp'}

class VisualAssetLibrary:
    def __init__(self, root):
        self.root = Path(root).resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        self.store = self.root / 'files'
        self.store.mkdir(exist_ok=True)
        self.db = sqlite3.connect(self.root / 'assets.sqlite3')
        self.db.row_factory = sqlite3.Row
        self.db.execute('''CREATE TABLE IF NOT EXISTS assets (
            id TEXT PRIMARY KEY, kind TEXT NOT NULL, name TEXT NOT NULL,
            file TEXT NOT NULL, sha256 TEXT NOT NULL, tags TEXT NOT NULL,
            style TEXT NOT NULL, subject TEXT NOT NULL, view TEXT NOT NULL,
            pose TEXT NOT NULL, emotion TEXT NOT NULL, lighting TEXT NOT NULL,
            metadata TEXT NOT NULL, created_at TEXT NOT NULL)''')
        self.db.execute('CREATE INDEX IF NOT EXISTS idx_asset_kind ON assets(kind)')
        self.db.execute('CREATE INDEX IF NOT EXISTS idx_asset_hash ON assets(sha256)')
        self.db.commit()

    def close(self):
        self.db.close()

    def import_asset(self, path, *, kind, name, tags=(), style='', subject='', view='',
                     pose='', emotion='', lighting='', metadata=None):
        source = Path(path).resolve()
        if kind not in TYPES:
            raise ValueError('Tipo inválido: ' + kind)
        if not source.is_file() or source.suffix.lower() not in EXTS:
            raise ValueError('Arquivo inexistente ou formato não suportado')
        digest = hashlib.sha256(source.read_bytes()).hexdigest()
        existing = self.db.execute('SELECT * FROM assets WHERE sha256=?', (digest,)).fetchone()
        if existing:
            return dict(existing), False
        asset_id = digest[:16]
        target = self.store / (asset_id + source.suffix.lower())
        shutil.copy2(source, target)
        item = (asset_id, kind, name, str(target.relative_to(self.root)), digest,
                json.dumps(sorted(set(tags)), ensure_ascii=False), style, subject, view,
                pose, emotion, lighting, json.dumps(metadata or {}, ensure_ascii=False),
                datetime.now(timezone.utc).isoformat())
        self.db.execute('INSERT INTO assets VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)', item)
        self.db.commit()
        return self.get(asset_id), True

    def get(self, asset_id):
        row = self.db.execute('SELECT * FROM assets WHERE id=?', (asset_id,)).fetchone()
        return self._decode(row) if row else None

    @staticmethod
    def _decode(row):
        if row is None:
            return None
        d = dict(row)
        d['tags'] = json.loads(d['tags'])
        d['metadata'] = json.loads(d['metadata'])
        return d

    def search(self, *, kind=None, style=None, subject=None, view=None, pose=None,
               emotion=None, lighting=None, tags=()):
        clauses, params = [], []
        for key, value in [('kind', kind), ('style', style), ('subject', subject),
                           ('view', view), ('pose', pose), ('emotion', emotion), ('lighting', lighting)]:
            if value:
                clauses.append(key + '=?')
                params.append(value)
        sql = 'SELECT * FROM assets' + (' WHERE ' + ' AND '.join(clauses) if clauses else '')
        sql += ' ORDER BY created_at DESC'
        rows = [self._decode(row) for row in self.db.execute(sql, params)]
        required = set(tags)
        return [row for row in rows if required.issubset(row['tags'])]

    def plan(self, requests):
        """Requisitos por plano: matches estritos; nunca reutiliza pose/vista incompatível."""
        results = []
        for request in requests:
            criteria = {key: request.get(key) for key in
                        ('kind', 'style', 'subject', 'view', 'pose', 'emotion', 'lighting')}
            criteria['tags'] = request.get('tags', [])
            matches = self.search(**criteria)
            results.append({'request': request, 'status': 'reusable' if matches else 'missing',
                            'asset_id': matches[0]['id'] if matches else None,
                            'prompt': None if matches else self.prompt(request)})
        return results

    @staticmethod
    def prompt(request):
        details = ['Crie um asset ilustrado 2D para animação.',
                   'Tipo: ' + str(request.get('kind', 'full_scene')),
                   'Descrição: ' + str(request.get('description', ''))]
        for key, label in [('style', 'Estilo'), ('subject', 'Personagem/local'),
                           ('view', 'Ângulo'), ('pose', 'Pose'),
                           ('emotion', 'Expressão'), ('lighting', 'Iluminação')]:
            if request.get(key):
                details.append(label + ': ' + str(request[key]))
        details.append('Preserve rigorosamente a referência visual anexada, quando houver.')
        details.append('Sem texto, sem marca-dágua. Não inclua elementos extras.')
        if request.get('transparent'):
            details.append('Personagem/objeto isolado em PNG com transparência real.')
        return '\n'.join(details)


def main(argv=None):
    parser = argparse.ArgumentParser(description='Biblioteca de assets para DESENHO')
    parser.add_argument('--library', default='asset-library')
    sub = parser.add_subparsers(dest='command', required=True)
    add = sub.add_parser('import')
    add.add_argument('path')
    add.add_argument('--kind', required=True, choices=sorted(TYPES))
    add.add_argument('--name', required=True)
    for key in ('style', 'subject', 'view', 'pose', 'emotion', 'lighting'):
        add.add_argument('--' + key, default='')
    add.add_argument('--tags', default='')
    search = sub.add_parser('search')
    for key in ('kind', 'style', 'subject', 'view', 'pose', 'emotion', 'lighting'):
        search.add_argument('--' + key)
    search.add_argument('--tags', default='')
    plan = sub.add_parser('plan')
    plan.add_argument('requests_json')
    args = parser.parse_args(argv)
    lib = VisualAssetLibrary(args.library)
    try:
        if args.command == 'import':
            fields = {key: getattr(args, key) for key in ('style', 'subject', 'view', 'pose', 'emotion', 'lighting')}
            result, created = lib.import_asset(args.path, kind=args.kind, name=args.name,
                                                tags=args.tags.split(',') if args.tags else [], **fields)
            output = {'created': created, 'asset': result}
        elif args.command == 'search':
            fields = {key: getattr(args, key) for key in ('kind', 'style', 'subject', 'view', 'pose', 'emotion', 'lighting')}
            output = lib.search(tags=args.tags.split(',') if args.tags else [], **fields)
        else:
            requests = json.loads(Path(args.requests_json).read_text(encoding='utf-8'))
            if not isinstance(requests, list):
                raise ValueError('O JSON deve conter uma lista de solicitações')
            output = lib.plan(requests)
        print(json.dumps(output, indent=2, ensure_ascii=False))
    finally:
        lib.close()

if __name__ == '__main__':
    main()
