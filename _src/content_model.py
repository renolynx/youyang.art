"""One page per work; curated cards contain references and intentional overrides."""
import copy
import re
from urllib.parse import urlsplit

FIELDS = {'title': 'cardTitle', 'cover': 'cover', 'meta': 'cardMeta', 'description': 'summary'}

def card(item, pages, lang='en'):
    if 'ref' not in item:
        return item
    page = next((p for p in pages if p.get('id', p['slug']) == item['ref']), None)
    if page is None:
        raise ValueError('Unknown card reference: ' + str(item['ref']))
    localized = page.get('cardZh', {}) if lang == 'zh' else {}
    out = {'href': '/' + page['slug'], 'title': page.get('cardTitle', page['title']),
           'cover': page.get('cover', ''), 'meta': page.get('cardMeta', page.get('year', '')),
           'description': page.get('summary', '')}
    out.update(localized)
    out.update(item.get('overrides', {}))
    return out

def collections(doc):
    for page in doc['pages']:
        for lang, variant in [('en', page), ('zh', page.get('zh', {}))]:
            if page['type'] == 'gallery' and 'items' in variant:
                yield page, lang, variant['items']
            for b in variant.get('blocks', []):
                if b.get('type') == 'project_grid':
                    yield page, lang, b.get('items', [])

def migrate(doc):
    doc = copy.deepcopy(doc)
    by = {p['slug']: p for p in doc['pages']}
    for p in by.values(): p.setdefault('id', p['slug'])
    # Work is the primary editorial description. Older galleries keep intentional differences.
    ordered = sorted(list(collections(doc)), key=lambda x: (x[0]['slug'] != 'work', x[1] != 'en'))
    seen = set()
    for _, lang, items in ordered:
        for it in items:
            slug = urlsplit(it.get('href', '')).path.strip('/')
            if slug not in by or 'ref' in it: continue
            p = by[slug]
            for field, target in FIELDS.items():
                if field not in it or (slug, lang, field) in seen: continue
                seen.add((slug, lang, field))
                if lang == 'zh': p.setdefault('cardZh', {})[field] = it[field]
                else: p[target] = it[field]
    for p in by.values():
        if p.get('cardTitle') == p.get('title'): p.pop('cardTitle', None)
        if p.get('cardMeta') == p.get('year'): p.pop('cardMeta', None)
        defaults = card({'ref': p['id']}, doc['pages'])
        if p.get('cardZh'):
            p['cardZh'] = {k: v for k, v in p['cardZh'].items() if v != defaults.get(k)}
    for _, lang, items in collections(doc):
        for idx, it in enumerate(items):
            slug = urlsplit(it.get('href', '')).path.strip('/')
            if slug not in by or 'ref' in it: continue
            ref = {'ref': by[slug]['id']}
            resolved = card(ref, doc['pages'], lang)
            overrides = {k: v for k, v in it.items() if resolved.get(k) != v}
            # An omitted description in an archival card is intentional.
            for k in FIELDS:
                if k not in it and resolved.get(k): overrides[k] = ''
            if overrides: ref['overrides'] = overrides
            items[idx] = ref
    doc['schemaVersion'] = 2
    validate(doc)
    return doc

def validate(doc):
    if not isinstance(doc, dict) or not isinstance(doc.get('site'), dict) or not isinstance(doc.get('pages'), list):
        raise ValueError('Invalid site document')
    slugs, ids = set(), set()
    for p in doc['pages']:
        slug, ident = p.get('slug', ''), p.get('id', p.get('slug'))
        if not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', slug) or slug in slugs:
            raise ValueError('Invalid or duplicate page address: ' + slug)
        if ident in ids: raise ValueError('Duplicate content ID')
        if p.get('type') not in ('editorial', 'project', 'gallery', 'page', 'cv') or not p.get('title'):
            raise ValueError('Every page needs a title and supported type')
        slugs.add(slug); ids.add(ident)
    for _, lang, items in collections(doc):
        for it in items:
            resolved = card(it, doc['pages'], lang)
            if not resolved.get('href'): raise ValueError('Card needs a destination')
    return doc
