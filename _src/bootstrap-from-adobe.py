#!/usr/bin/env python3
"""One-off: turn the scraped Portfolio structure into the editable site content file."""
import json, html, re, pathlib, collections

P = json.load(open('_src/parsed.json'))
FONT = {'bbkk': 'body', 'rfyp': 'display', 'ckdr': 'caption', 'tvbs': 'nav',
        'xzbg': 'script', 'qxnj': 'nav', 'ftnk': 'body', 'vcsm': 'body'}
BODY_DEFAULT = ('body', 21.0, 300)

def run_html(r):
    if r.get('br'): return '<br>'
    t = html.escape(r.get('t', '')).replace('​', '')
    if not t: return ''
    css, cls = [], []
    fam = FONT.get(r.get('ff'))
    if fam: cls.append('f-' + fam)
    if r.get('fs'): css.append('font-size:%gpx' % r['fs'])
    if r.get('fw'): css.append('font-weight:%d' % r['fw'])
    if r.get('color') and r['color'].lower() not in ('#4e4e4e', 'rgb(78,78,78)'):
        css.append('color:%s' % r['color'])
    if r.get('italic'): css.append('font-style:italic')
    if r.get('underline'): cls.append('u')
    inner = t
    if cls or css:
        inner = '<span%s%s>%s</span>' % (
            ' class="%s"' % ' '.join(cls) if cls else '',
            ' style="%s"' % ';'.join(css) if css else '', inner)
    if r.get('href'):
        href = r['href']
        ext = href.startswith('http') or href.startswith('mailto')
        inner = '<a href="%s"%s>%s</a>' % (html.escape(href),
                 ' target="_blank" rel="noopener"' if ext else '', inner)
    return inner

def paras(mod):
    out = []
    for p in mod.get('paras', []):
        s = p.get('style') or {}
        body = ''.join(run_html(r) for r in p['runs'])
        if not body.strip(): continue
        out.append({k: v for k, v in
                    {'html': body, 'align': s.get('align'), 'lh': s.get('lh')}.items() if v})
    return out

def caption(mod):
    c = mod.get('caption')
    if not c: return None
    c = re.sub(r'</?p>', '', c)
    c = re.sub(r'<span style="font-family:(\w+)[^"]*">',
               lambda m: '<span class="f-%s">' % FONT.get(m.group(1), 'caption'), c)
    c = re.sub(r'\sdata-selected-page-id="[^"]*"', '', c)
    c = re.sub(r'\starget="_self"', '', c)
    return re.sub(r'\s+', ' ', c).strip()

# Per-module max-width read off the live Adobe site (it applied these from JS, not CSS).
# Keys are block paths: top level "0", "1"…; nested "0c1/0" = block 0, column 1, child 0.
MAXW = {
 'about': {'0c1/0': 500, '1': 800, '3c0/0': 800, '3c1/0': 600, '4': 800, '5c0/0': 800,
           '6': 800, '8': 800, '9c1/0': 800, '11': 800, '13': 800, '15': 800, '16': 800},
 'inside-my-eyes': {'0': 1920, '1': 800, '3': 800, '5': 800, '7': 800},
}
DEFAULT_MAXW = {'text': 800, 'form': 800}

def block(m, slug='', path=''):
    t = m['type']
    b = {'type': {'media_collection': 'grid', 'tree': 'columns'}.get(t, t)}
    mw = MAXW.get(slug, {}).get(path, DEFAULT_MAXW.get(t))
    if mw: b['maxw'] = mw
    for k in ('pt', 'pb', 'width', 'align', 'capAlign'):
        if m.get(k) is not None: b[k] = m[k]
    cap = caption(m)
    if cap: b['caption'] = cap
    if t == 'text': b['paras'] = paras(m)
    elif t == 'image':
        b['src'] = m.get('src')
        if m.get('href'): b['href'] = m['href']
    elif t == 'embed': b['embed'] = m.get('embed')
    elif t == 'video': b['video'] = m.get('video')
    elif t == 'media_collection':
        b['items'] = [{'src': i['src'], 'w': i['w'], 'h': i['h']} for i in m['items']]
        if m.get('perRow'): b['perRow'] = m['perRow']
    elif t == 'tree':
        b['cols'] = [{'flex': c['flex'],
                      'blocks': [block(x, slug, '%sc%d/%d' % (path, ci, xi))
                                 for xi, x in enumerate(c['modules'])]}
                     for ci, c in enumerate(m['cols'])]
    elif t == 'social_icons':
        b['links'] = m.get('links', [])
    elif t == 'button':
        b['label'] = m.get('label', '')
        if m.get('href'): b['href'] = m['href']
        if m.get('btnAlign'): b['btnAlign'] = m['btnAlign']
    elif t == 'form':
        b['labels'] = m.get('labels', [])
        b['submit'] = m.get('submit', 'Submit')
    return b

TAGLINE = 'Teaching Artist\nAnimation Filmmaker\nCurator↓'

TITLES = {'2010': '2010', '2013': '2013', '2014': '2014 turkey', '2014-1': '2014',
          '2015': '2015', 'feinaki-2020': 'Feinaki 2020'}

pages = []
for slug in ['about', 'home', 'animation', 'sketch-book', 'inside-my-eyes', 'for-the-best',
             'i-love-you-forever-now', 'cwtch', 'maybe-you-shouldve-swallowed', 'a-man-in-love',
             'feinaki-2020', '2015', '2014-1', '2014', '2013', '2010']:
    src = P[slug]
    kind = 'gallery' if src['covers'] and not src['modules'] else \
           ('page' if slug == 'about' else 'project')
    mast = src['masthead'] or ''
    page = {'slug': slug, 'type': kind,
            'title': TITLES.get(slug, src['title'].replace('Youyang Yu - ', '').replace('Youyang Yu', '')),
            'masthead': re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', '', mast)).strip() or None}
    if kind == 'gallery':
        page['items'] = [{'href': c['href'], 'cover': c['cover'], 'title': c['title'],
                          'meta': c['meta']} for c in src['covers']]
        page['tagline'] = TAGLINE
    else:
        page['blocks'] = [block(m, slug, str(i)) for i, m in enumerate(src['modules'])]
        # the original ended with a "©2023" text block; the site footer carries the year now
        if page['blocks'] and page['blocks'][-1]['type'] == 'text':
            flat = re.sub(r'<[^>]+>', '', ''.join(q['html'] for q in page['blocks'][-1].get('paras', [])))
            if re.fullmatch(r'\s*©\s*\d{4}\s*', flat): page['blocks'].pop()
        if kind == 'page':
            page['tagline'] = TAGLINE
        if kind == 'project' and page['masthead']:
            page['arrow'] = True
        rel = [c['href'].lstrip('/') for c in src['covers']]
        if rel: page['related'] = rel
    pages.append(page)

site = {
  'site': {
    'name': 'Youyang Yu',
    'logo': 'yyy',
    'description': 'Animation Filmmaker/Teacher/Curator',
    'keywords': 'Personal Website,Portfolio,Animation,AI Artist,Animation Festival',
    'url': 'https://youyang.art',
    'email': 'qingdaoyyy@gmail.com',
    'nav': [{'label': 'ANIMATION', 'href': '/animation'},
            {'label': 'SKETCH BOOK', 'href': '/sketch-book'},
            {'label': 'ABOUT', 'href': '/about'}],
    'social': [{'name': 'twitter', 'url': 'https://twitter.com/FeralCliff'},
               {'name': 'instagram', 'url': 'https://www.instagram.com/renolynx/'},
               {'name': 'email', 'url': 'mailto:qingdaoyyy@gmail.com'}],
    'footer': '©2026',
    'ogImage': 'assets/og.jpg',
    'home': '/about',
  },
  'pages': pages,
}
pathlib.Path('_src/content').mkdir(parents=True, exist_ok=True)
pathlib.Path('_src/content/site.json').write_text(
    json.dumps(site, indent=1, ensure_ascii=False))
print('pages:', len(pages))
for p in pages:
    print(' ', p['slug'].ljust(30), p['type'].ljust(8),
          len(p.get('blocks', [])) or len(p.get('items', [])), 'blocks/items')
