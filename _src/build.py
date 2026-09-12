#!/usr/bin/env python3
"""Build youyang.art from _src/content/site.json into static pages at the repo root."""
import html, json, pathlib, re, shutil, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
SITE = json.loads((ROOT / '_src/content/site.json').read_text())
MEDIA = json.loads((ROOT / '_src/media.json').read_text())
S = SITE['site']
PAGES = SITE['pages']
BY_SLUG = {p['slug']: p for p in PAGES}
ROW_H = 240          # justified-grid row height
PLAIN = re.compile(r'<[^>]+>')

def esc(t): return html.escape(t or '', quote=True)

def asset(ref, prefix=''):
    """media/<stem>.<ext> from the content file -> the optimized webp + its size."""
    if not ref: return None
    stem = pathlib.Path(ref).stem
    m = MEDIA.get(stem)
    if not m:
        print('  ! missing media:', ref, file=sys.stderr)
        return None
    return {'src': prefix + m['src'], 'w': m['w'], 'h': m['h'], 'anim': m['anim']}

def rel(depth):
    return '../' * depth

def pad(b, geom=False):
    out = []
    if b.get('pt'): out.append('padding-top:%gpx' % b['pt'])
    if b.get('pb'): out.append('padding-bottom:%gpx' % b['pb'])
    if geom:
        if b.get('width'): out.append('width:%g%%' % b['width'])
        if b.get('maxw'): out.append('max-width:%dpx' % b['maxw'])
    return ' style="%s"' % ';'.join(out) if out else ''

def fix_links(s, depth):
    """Root-relative links in content -> relative, so the build also opens from file://."""
    return re.sub(r'href="/([a-z0-9-]*)"', lambda m: 'href="%s%s"' % (rel(depth), m.group(1) or ''), s or '')

def caption(b, depth, cls='caption'):
    c = b.get('caption')
    if not c: return ''
    extra = ' caption--%s' % b['capAlign'] if b.get('capAlign') in ('left', 'right') else ''
    return '<figcaption class="%s%s">%s</figcaption>' % (cls, extra, fix_links(c, depth))

def alt_from(b):
    c = PLAIN.sub('', b.get('caption') or '').strip()
    return c[:180]

def img_tag(a, alt, cls='', lazy=True, sizes=None, full=None):
    return ('<img src="%s" width="%d" height="%d" alt="%s"%s%s%s%s>'
            % (a['src'], a['w'], a['h'], esc(alt),
               ' class="%s"' % cls if cls else '',
               ' loading="lazy" decoding="async"' if lazy else '',
               ' sizes="%s"' % sizes if sizes else '',
               ' data-full="%s"' % full if full else ''))

def block(b, depth, inline=False):
    p = rel(depth)
    t = b['type']
    if t == 'text':
        body = ''.join(
            '<p%s>%s</p>' % (
                ''.join(x for x in [
                    ' style="' + ';'.join(
                        ([('line-height:%gpx' % q['lh'])] if q.get('lh') else []) +
                        ([('text-align:%s' % q['align'])] if q.get('align') and q['align'] != 'left' else [])
                    ) + '"' if (q.get('lh') or (q.get('align') and q['align'] != 'left')) else ''
                ]),
                fix_links(q['html'], depth))
            for q in b.get('paras', []))
        return '<div class="block block--text"%s>%s</div>' % (pad(b, True), body)

    if t == 'image':
        a = asset(b.get('src'), p)
        if not a: return ''
        tag = img_tag(a, alt_from(b), cls='zoomable' if not b.get('href') else '')
        if b.get('href'):
            tag = '<a href="%s%s">%s</a>' % (p, b['href'].lstrip('/'), tag)
        return '<figure class="block"%s>%s%s</figure>' % (pad(b, True), tag, caption(b, depth))

    if t == 'embed':
        ratio = b.get('ratio') or 56.25
        return ('<div class="block"%s><div class="embed" style="padding-bottom:%g%%">'
                '<iframe src="%s" title="%s" loading="lazy" frameborder="0" '
                'allow="autoplay; fullscreen; picture-in-picture" allowfullscreen></iframe></div>%s</div>'
                % (pad(b, True), ratio, esc(b['embed']), esc(alt_from(b) or 'Video'), caption(b, depth)))

    if t == 'video':
        return ('<div class="block"%s><div class="embed" style="padding-bottom:56.25%%">'
                '<iframe src="%s" title="Video" loading="lazy" frameborder="0" allowfullscreen></iframe>'
                '</div>%s</div>' % (pad(b, True), esc(b.get('embed') or b.get('video') or ''), caption(b, depth)))

    if t == 'grid':
        per = b.get('perRow')
        figs = []
        for it in b['items']:
            a = asset(it['src'], p)
            if not a: continue
            ar = it['w'] / max(it['h'], 1)
            style = ('width:calc(%.4f%% )' % (100 / per)) if per else \
                    ('flex:%.4f 1 %.0fpx' % (ar, ar * ROW_H))
            figs.append('<figure style="%s">%s</figure>'
                        % (style, img_tag(a, '', cls='zoomable')))
        cls = 'grid' + (' grid--flush' if b.get('perRow') else '')
        return '<div class="block"%s><div class="%s">%s</div>%s</div>' % (
            pad(b, True), cls, ''.join(figs), caption(b, depth))

    if t == 'columns':
        cols = []
        for c in b['cols']:
            inner = ''.join(block(x, depth, inline=True) for x in c['blocks'])
            cols.append('<div style="flex:%g 1 0">%s</div>' % (c['flex'], inner))
        return '<div class="block cols"%s>%s</div>' % (pad(b, True), ''.join(cols))

    if t == 'social_icons':
        return social_row(links=b.get('links'))
    if t == 'button':
        return ('<div class="block block--button"%s><a class="pill" href="%s">%s</a></div>'
                % (pad(b, True), esc(b.get('href') or '#contact'), esc(b.get('label') or '↓ here ↓')))
    if t == 'form':
        return contact_form(b)
    if t == 'spacer':
        return '<div class="block"%s></div>' % pad(b, True)
    return ''

ICON = {
 'twitter': '<svg viewBox="0 0 30 24" aria-hidden="true"><path d="M24.71 5.89C24 6.2 23.2 6.4 22.4 6.53c0.82-0.5 1.45-1.29 1.75-2.23c-0.77 0.46-1.62 0.8-2.53 1C20.92 4.5 19.9 4 18.7 4c-2.2 0-3.99 1.81-3.99 4.04c0 0.3 0 0.6 0.1 0.92C11.54 8.8 8.6 7.2 6.6 4.7C6.3 5.3 6.1 6 6.1 6.77c0 1.4 0.7 2.6 1.8 3.36c-0.65-0.02-1.27-0.2-1.81-0.51c0 0 0 0 0 0.1c0 2 1.4 3.6 3.2 3.96c-0.34 0.09-0.69 0.14-1.05 0.14c-0.26 0-0.51-0.03-0.75-0.07c0.51 1.6 2 2.8 3.7 2.8c-1.36 1.08-3.08 1.73-4.95 1.73c-0.32 0-0.64-0.02-0.95-0.06C7.05 19.3 9.1 20 11.4 20c7.33 0 11.34-6.15 11.34-11.49c0-0.18 0-0.35-0.01-0.52C23.5 7.4 24.2 6.7 24.7 5.89z"/></svg>',
 'instagram': '<svg viewBox="0 0 30 24" aria-hidden="true"><path d="M15,5.4c2.1,0,2.4,0,3.2,0c0.8,0,1.2,0.2,1.5,0.3c0.4,0.1,0.6,0.3,0.9,0.6c0.3,0.3,0.5,0.5,0.6,0.9c0.1,0.3,0.2,0.7,0.3,1.5c0,0.8,0,1.1,0,3.2s0,2.4,0,3.2c0,0.8-0.2,1.2-0.3,1.5c-0.1,0.4-0.3,0.6-0.6,0.9c-0.3,0.3-0.5,0.5-0.9,0.6c-0.3,0.1-0.7,0.2-1.5,0.3c-0.8,0-1.1,0-3.2,0s-2.4,0-3.2,0c-0.8,0-1.2-0.2-1.5-0.3c-0.4-0.1-0.6-0.3-0.9-0.6c-0.3-0.3-0.5-0.5-0.6-0.9c-0.1-0.3-0.2-0.7-0.3-1.5c0-0.8,0-1.1,0-3.2s0-2.4,0-3.2c0-0.8,0.2-1.2,0.3-1.5c0.1-0.4,0.3-0.6,0.6-0.9c0.3-0.3,0.5-0.5,0.9-0.6c0.3-0.1,0.7-0.2,1.5-0.3C12.6,5.4,12.9,5.4,15,5.4 M15,4c-2.2,0-2.4,0-3.3,0c-0.9,0-1.4,0.2-1.9,0.4C9.3,4.6,8.8,4.9,8.4,5.3C7.9,5.8,7.6,6.2,7.4,6.8C7.2,7.3,7.1,7.9,7,8.7C7,9.6,7,9.8,7,12s0,2.4,0,3.3c0,0.9,0.2,1.4,0.4,1.9c0.2,0.5,0.5,1,0.9,1.4c0.4,0.4,0.9,0.7,1.4,0.9c0.5,0.2,1.1,0.3,1.9,0.4c0.9,0,1.1,0,3.3,0s2.4,0,3.3,0c0.9,0,1.4-0.2,1.9-0.4c0.5-0.2,1-0.5,1.4-0.9c0.4-0.4,0.7-0.9,0.9-1.4c0.2-0.5,0.3-1.1,0.4-1.9c0-0.9,0-1.1,0-3.3s0-2.4,0-3.3c0-0.9-0.2-1.4-0.4-1.9c-0.2-0.5-0.5-1-0.9-1.4c-0.4-0.4-0.9-0.7-1.4-0.9c-0.5-0.2-1.1-0.3-1.9-0.4C17.4,4,17.2,4,15,4L15,4z M15,7.9c-2.3,0-4.1,1.8-4.1,4.1s1.8,4.1,4.1,4.1s4.1-1.8,4.1-4.1S17.3,7.9,15,7.9z M15,14.7c-1.5,0-2.7-1.2-2.7-2.7s1.2-2.7,2.7-2.7s2.7,1.2,2.7,2.7S16.5,14.7,15,14.7z M19.3,6.8c-0.5,0-1,0.4-1,1s0.4,1,1,1s1-0.4,1-1S19.8,6.8,19.3,6.8z"/></svg>',
 'email': '<svg viewBox="0 0 30 24" aria-hidden="true"><path d="M23 5H7c-1.1 0-2 .9-2 2v10c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V7c0-1.1-.9-2-2-2zm0 4.5l-8 4.5-8-4.5V7l8 4.5L23 7v2.5z"/></svg>',
 'vimeo': '<svg viewBox="0 0 30 24" aria-hidden="true"><path d="M25 8.2c-.1 2.4-1.8 5.8-5.1 10-3.4 4.4-6.3 6.6-8.6 6.6-1.5 0-2.7-1.3-3.7-4l-2-7.4c-.7-2.7-1.5-4-2.4-4-.2 0-.8.4-1.8 1.1L.4 9c1.3-1.1 2.5-2.2 3.7-3.3C5.8 4.2 7 3.4 7.8 3.4c1.9-.2 3.1 1.1 3.5 3.9.5 3 .8 4.9 1 5.6.5 2.4 1.1 3.5 1.8 3.5.5 0 1.3-.8 2.3-2.4 1-1.6 1.6-2.9 1.6-3.7.1-1.3-.4-2-1.6-2-.5 0-1.1.1-1.7.4C15.9 5.4 18.1 3.5 21 3.6c2.7.1 3.9 1.6 3.8 4.6z"/></svg>',
 'youtube': '<svg viewBox="0 0 30 24" aria-hidden="true"><path d="M26 8.2c-.3-1.1-1.1-1.9-2.2-2.2C21.9 5.5 15 5.5 15 5.5s-6.9 0-8.8.5C5.1 6.3 4.3 7.1 4 8.2c-.5 1.9-.5 5.8-.5 5.8s0 3.9.5 5.8c.3 1.1 1.1 1.9 2.2 2.2 1.9.5 8.8.5 8.8.5s6.9 0 8.8-.5c1.1-.3 1.9-1.1 2.2-2.2.5-1.9.5-5.8.5-5.8s0-3.9-.5-5.8zM12.8 17.6V10.4l5.7 3.6-5.7 3.6z"/></svg>',
}

def kind_of(url):
    for k in ICON:
        if k in (url or '') or (k == 'email' and (url or '').startswith('mailto')):
            return k
    if 'instagram' in (url or ''): return 'instagram'
    return 'email'

def social_row(cls='block', links=None):
    items = links or S['social']
    out = []
    for x in items:
        url = x.get('url', '')
        name = x.get('name') or kind_of(url)
        out.append('<a href="%s"%s aria-label="%s">%s</a>'
                   % (esc(url), '' if url.startswith('mailto') else ' target="_blank" rel="noopener"',
                      esc(name.title()), ICON.get(name, ICON['email'])))
    return '<div class="%s"><div class="social-row">%s</div></div>' % (cls, ''.join(out))

def contact_form(b=None):
    action = S.get('formAction') or ''
    attrs = (' action="%s" method="post"' % esc(action)) if action else \
            (' data-mailto="%s"' % esc(S['email']))
    return ('<div class="block block--form" id="contact"%s>'
            '<form class="contact-form"%s>' % (pad(b or {}, True), attrs) +
            '<label for="cf-name">Name *</label>'
            '<input id="cf-name" name="name" type="text" placeholder="Your Name..." required>'
            '<label for="cf-email">Email Address *</label>'
            '<input id="cf-email" name="email" type="email" placeholder="Your Email Address..." required>'
            '<label for="cf-msg">Message *</label>'
            '<textarea id="cf-msg" name="message" placeholder="Your Message..." required></textarea>'
            '<button type="submit">Submit</button>'
            '<p class="form-note">This opens your mail app with the message ready to send. '
            'Prefer to write directly? <a href="mailto:%s">%s</a></p>'
            '</form></div>' % (esc(S['email']), esc(S['email'])))

def cover(item, depth):
    a = asset(item.get('cover'), rel(depth))
    if not a: return ''
    href = rel(depth) + item['href'].lstrip('/')
    meta = ''
    if item.get('title') or item.get('meta'):
        meta = ('<span class="cover-meta">%s%s</span>'
                % ('<span class="t">%s</span>' % esc(item['title']) if item.get('title') else '',
                   '<span class="d">%s</span>' % esc(item['meta']) if item.get('meta') else ''))
    return ('<a class="cover" href="%s"><span class="cover-img">%s</span>%s</a>'
            % (href, img_tag(a, item.get('title') or '', sizes='(max-width:768px) 100vw, 50vw'), meta))

def head(page, depth):
    p = rel(depth)
    slug = page['slug']
    title = S['name'] if slug == 'about' else '%s - %s' % (S['name'], page.get('title') or slug)
    desc = page.get('description') or S['description']
    og = page.get('ogImage') or S.get('ogImage')
    canon = S['url'] + ('/' if slug == 'about' else '/%s' % slug)
    return f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<meta name="keywords" content="{esc(S['keywords'])}">
<link rel="canonical" href="{esc(canon)}">
<meta property="og:type" content="website">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:url" content="{esc(canon)}">
{f'<meta property="og:image" content="{S["url"]}/{og}">' if og else ''}
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" href="{p}favicon.ico" sizes="32x32">
<link rel="apple-touch-icon" href="{p}assets/apple-touch-icon.png">
<link rel="preload" as="font" type="font/woff2" href="{p}assets/fonts/hanken-latin.woff2" crossorigin>
<link rel="preload" as="font" type="font/woff2" href="{p}assets/fonts/archivo-latin.woff2" crossorigin>
<link rel="stylesheet" href="{p}assets/css/site.css">
</head>
<body>
<a class="skip-link" href="#main">Skip to content</a>
<span id="top"></span>
'''

def header(page, depth):
    p = rel(depth)
    links = ''.join(
        '<a href="%s%s"%s>%s</a>' % (p, n['href'].lstrip('/'),
            ' aria-current="page"' if n['href'].lstrip('/') == page['slug'] else '', esc(n['label']))
        for n in S['nav'])
    return f'''<header class="site-header">
<button class="nav-toggle" aria-expanded="false" aria-label="Menu" aria-controls="site-nav"><span></span><span></span><span></span></button>
<nav class="site-nav" id="site-nav" data-open="false">{links}</nav>
<div class="site-logo"><a href="{p}home">{esc(S['logo'])}</a></div>
</header>
{'' if page.get('masthead') else '<div class="header-placeholder"></div>'}
'''

def masthead(page):
    if not page.get('masthead'): return ''
    tag = ('<p class="tagline">%s</p>' % esc(page['tagline'])) if page.get('tagline') else ''
    arrow = ('<button class="masthead-arrow" aria-label="Scroll to content"></button>'
             if page.get('arrow') else '')
    return f'''<div class="masthead">
<div class="masthead-inner">
<h1>{esc(page['masthead'])}</h1>
{tag}{arrow}
</div>
</div>
<div class="masthead-placeholder"></div>
'''

def related(page, depth):
    slugs = page.get('related') or []
    items = []
    for s in slugs[:3]:
        pg = BY_SLUG.get(s)
        if not pg: continue
        cov = pg.get('cover') or next((i['cover'] for g in PAGES if g['type'] == 'gallery'
                                       for i in g['items'] if i['href'].lstrip('/') == s), None)
        items.append(cover({'href': '/' + s, 'cover': cov,
                            'title': pg.get('title'), 'meta': pg.get('year', '')}, depth))
    if not items: return ''
    return ('<section class="related shell"><h2 class="related-title">You may also like</h2>'
            '<div class="related-grid">%s</div>'
            '<p class="related-top"><a href="#top">↑ Back to Top</a></p></section>'
            % ''.join(items))

def tail(page, depth):
    p = rel(depth)
    foot = page.get('footer', S['footer'])
    return f'''<footer class="site-footer">{foot}</footer>
</div>
<button class="to-top" aria-label="Back to top"></button>
<div class="lightbox" role="dialog" aria-modal="true" aria-label="Enlarged image">
<button class="lightbox-close" aria-label="Close">&times;</button><img alt="">
</div>
<script src="{p}assets/js/site.js" defer></script>
</body>
</html>
'''

def render(page, depth):
    out = [head(page, depth), header(page, depth), masthead(page),
           '<div class="site-wrap"><main id="main" class="shell">']
    if page['type'] == 'gallery':
        out.append('<div class="covers">%s</div>'
                   % ''.join(cover(i, depth) for i in page['items']))
    else:
        out.append(''.join(block(b, depth) for b in page.get('blocks', [])))
    out.append('</main>')
    out.append(related(page, depth))
    out.append(tail(page, depth))
    return ''.join(out)

def main():
    written = []
    for page in PAGES:
        slug = page['slug']
        if slug == 'about':
            (ROOT / 'index.html').write_text(render(page, 0)); written.append('index.html')
        d = ROOT / slug
        d.mkdir(exist_ok=True)
        (d / 'index.html').write_text(render(page, 1)); written.append(slug + '/index.html')
    cname = ROOT / 'CNAME'
    if S.get('customDomain'):
        cname.write_text(S['url'].split('//')[1] + '\n')
    elif cname.exists():
        cname.unlink()
    (ROOT / '.nojekyll').write_text('')
    (ROOT / 'robots.txt').write_text('User-agent: *\nAllow: /\nSitemap: %s/sitemap.xml\n' % S['url'])
    urls = ''.join('<url><loc>%s%s</loc></url>' % (S['url'], '/' if p['slug'] == 'about' else '/' + p['slug'])
                   for p in PAGES)
    (ROOT / 'sitemap.xml').write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">%s</urlset>\n' % urls)
    print('built %d pages' % len(written))
    for w in written: print('  ', w)

if __name__ == '__main__':
    main()
