#!/usr/bin/env python3
"""Build youyang.art from _src/content/site.json into static pages at the repo root."""
import base64, hashlib, html, json, os, pathlib, re, secrets, shutil, subprocess, sys
from urllib.parse import urlsplit

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from content_model import card as resolve_card, validate
from motion_inventory import annotate as annotate_motion

ROOT = pathlib.Path(__file__).resolve().parent.parent
SITE = json.loads((ROOT / '_src/content/site.json').read_text())
validate(SITE)
MEDIA = json.loads((ROOT / '_src/media.json').read_text())
S = SITE['site']
PAGES = SITE['pages']
BY_SLUG = {p['slug']: p for p in PAGES}
SITE_URL = (S['url'] if S.get('customDomain') else S.get('previewUrl', S['url'])).rstrip('/')
LANG = 'en'
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

def route(slug, lang='en'):
    slug = slug.strip('/')
    if slug in ('', 'home'):
        return 'zh/' if lang == 'zh' else ''
    prefix = 'zh/' if lang == 'zh' and BY_SLUG.get(slug, {}).get('zh') else ''
    return prefix + slug + '/'

def href(url, depth, lang=None):
    """Keep links inside the project on both a domain and GitHub Pages subpath."""
    if not url or url.startswith(('#', 'mailto:', 'tel:', 'http:', 'https:', '//')):
        return esc(url)
    bits = urlsplit(url)
    path = bits.path.strip('/')
    if path in BY_SLUG or path in ('', 'home'):
        path = route(path, lang or LANG)
    suffix = ('?' + bits.query if bits.query else '') + ('#' + bits.fragment if bits.fragment else '')
    return esc((rel(depth) + path or './') + suffix)

def pad(b, geom=False):
    out = []
    if b.get('pt'): out.append('padding-top:%gpx' % b['pt'])
    if b.get('pb'): out.append('padding-bottom:%gpx' % b['pb'])
    if geom:
        if b.get('width'): out.append('width:%g%%' % b['width'])
        if b.get('maxw'): out.append('max-width:%dpx' % b['maxw'])
    return ' style="%s"' % ';'.join(out) if out else ''

def fix_links(s, depth):
    """Content links follow the current language and output directory depth."""
    return re.sub(r'href="(/[^" ]*)"', lambda m: 'href="%s"' % href(html.unescape(m.group(1)), depth), s or '')

def caption(b, depth, cls='caption'):
    c = b.get('caption')
    if not c: return ''
    extra = ' caption--%s' % b['capAlign'] if b.get('capAlign') in ('left', 'right') else ''
    return '<figcaption class="%s%s">%s</figcaption>' % (cls, extra, fix_links(c, depth))

def alt_from(b):
    if b.get('alt'): return b['alt']
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
    if t in ('section', 'project_grid', 'link_list'):
        return editorial_block(b, depth)
    if t == 'text':
        body = ''.join(
            (fix_links(q['html'], depth) if q['html'].lstrip().startswith('<p') else '<p%s>%s</p>' % (
                ''.join(x for x in [
                    ' style="' + ';'.join(
                        ([('line-height:%gpx' % q['lh'])] if q.get('lh') else []) +
                        ([('text-align:%s' % q['align'])] if q.get('align') and q['align'] != 'left' else [])
                    ) + '"' if (q.get('lh') or (q.get('align') and q['align'] != 'left')) else ''
                ]),
                fix_links(q['html'], depth)))
            for q in b.get('paras', []))
        return '<div class="block block--text"%s>%s</div>' % (pad(b, True), body)

    if t == 'image':
        a = asset(b.get('src'), p)
        if not a: return ''
        tag = img_tag(a, alt_from(b), cls='zoomable' if not b.get('href') else '')
        if b.get('href'):
            tag = '<a href="%s">%s</a>' % (href(b['href'], depth), tag)
        return '<figure class="block"%s>%s%s</figure>' % (pad(b, True), tag, caption(b, depth))

    if t == 'embed':
        ratio = b.get('ratio') or 56.25
        return ('<div class="block"%s><div class="embed" style="padding-bottom:%g%%">'
                '<iframe src="%s" title="%s" loading="lazy" frameborder="0" '
                'allow="autoplay; fullscreen; picture-in-picture" allowfullscreen></iframe></div>%s</div>'
                % (pad(b, True), ratio, esc(b['embed']), esc(alt_from(b) or 'Video'), caption(b, depth)))

    if t == 'video':
        poster = asset(b.get('poster'), p)
        ratio = b.get('ratio') or 56.25
        return ('<div class="block"%s><div class="embed" style="padding-bottom:%g%%">'
                '<video controls preload="metadata" playsinline%s>'
                '<source src="%s%s" type="video/mp4">'
                '</video></div>%s</div>'
                % (pad(b, True), ratio,
                   ' poster="%s"' % poster['src'] if poster else '',
                   p, esc(b['video']), caption(b, depth)))

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
                % (pad(b, True), href(b.get('href') or '#contact', depth), esc(b.get('label') or '↓ here ↓')))
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
            '<button type="submit" class="sample-primary ys-button">Submit</button>'
            '<p class="form-note">This opens your mail app with the message ready to send. '
            'Prefer to write directly? <a href="mailto:%s">%s</a></p>'
            '</form></div>' % (esc(S['email']), esc(S['email'])))

def cover(item, depth):
    item = resolve_card(item, PAGES, LANG)
    a = asset(item.get('cover'), rel(depth))
    if not a: return ''
    target = href(item['href'], depth)
    meta = ''
    if item.get('title') or item.get('meta'):
        meta = ('<span class="cover-meta">%s%s</span>'
                % ('<span class="t">%s</span>' % esc(item['title']) if item.get('title') else '',
                   '<span class="d">%s</span>' % esc(item['meta']) if item.get('meta') else ''))
    return ('<a class="cover" href="%s"><span class="cover-img">%s</span>%s</a>'
            % (target, img_tag(a, item.get('title') or '', sizes='(max-width:768px) 100vw, 50vw'), meta))

def editorial_image(b, depth, eager=False):
    a = asset(b.get('image'), rel(depth))
    if not a: return ''
    caption_text = b.get('imageCaption', '')
    return '<figure class="editorial-image">%s%s</figure>' % (
        img_tag(a, b.get('imageAlt') or caption_text, lazy=not eager),
        '<figcaption>%s</figcaption>' % esc(caption_text) if caption_text else '')

def arrow(url):
    """↗ means 'leaves the site'; internal links get →."""
    return '↗' if (url or '').startswith(('http:', 'https:', '//')) else '→'

def external_attrs(url):
    return ' target="_blank" rel="noopener"' if (url or '').startswith(('http:', 'https:', '//')) else ''

def editorial_links(links, depth):
    return '<div class="editorial-links">%s</div>' % ''.join(
        '<a class="text-link" href="%s"%s>%s<span aria-hidden="true"> %s</span></a>' % (href(i['href'], depth), external_attrs(i['href']), esc(i['label']), arrow(i['href']))
        for i in links) if links else ''

def editorial_block(b, depth):
    section_id = ' id="%s"' % esc(b['id']) if b.get('id') else ''
    kicker = '<p class="eyebrow">%s</p>' % esc(b['kicker']) if b.get('kicker') else ''
    title = '<h2>%s</h2>' % esc(b['title']) if b.get('title') else ''
    if b['type'] == 'project_grid':
        cards = []
        for item in b.get('items', []):
            item = resolve_card(item, PAGES, LANG)
            a = asset(item.get('cover'), rel(depth)) if item.get('cover') else None
            cards.append('<article class="project-card%s"><a href="%s">'
                         '%s<div class="project-info">'
                         '<h3>%s</h3><p class="project-meta">%s</p>%s</div><span class="card-open" aria-hidden="true">→</span></a></article>' % (
                             '' if a else ' project-card--text', href(item['href'], depth),
                             '<div class="project-image">%s</div>' % img_tag(a, '') if a else '',
                             esc(item.get('title')), esc(item.get('meta')),
                             '<p class="project-description">%s</p>' % esc(item['description']) if item.get('description') else ''))
        return '<section class="editorial-section project-section"%s>%s%s<div class="project-grid">%s</div></section>' % (section_id, kicker, title, ''.join(cards))
    if b['type'] == 'link_list':
        entries = ''.join('<li><a href="%s"><span class="list-meta">%s</span><h3>%s</h3><p>%s</p><span class="list-arrow" aria-hidden="true">%s</span></a></li>' % (
            href(i['href'], depth), esc(i.get('meta')), esc(i.get('title')), esc(i.get('description')), arrow(i['href'])) for i in b.get('items', []))
        return '<section class="editorial-section"%s>%s%s<ul class="editorial-list">%s</ul></section>' % (section_id, kicker, title, entries)
    cls = 'editorial-section' + (' section-with-image' if b.get('image') else '')
    if b.get('id') == 'basecamp': cls += ' basecamp-section'
    return '<section class="%s"%s><div class="section-copy">%s%s<div class="prose">%s</div>%s</div>%s</section>' % (
        cls, section_id, kicker, title, fix_links(b.get('body', ''), depth),
        editorial_links(b.get('links'), depth), editorial_image(b, depth))

def editorial_hero(page, depth):
    h = page.get('hero', {})
    cls = 'editorial-hero web-hero' + (' hero-with-image' if h.get('image') else '')
    return '<div class="%s"><div class="hero-copy ds-title">%s<h1>%s</h1>%s%s%s</div>%s</div>' % (
        cls, '<p class="eyebrow">%s</p>' % esc(h['eyebrow']) if h.get('eyebrow') else '',
        re.sub(r'([\u3400-\u9fff]+[，。、；：！？）」』》]*)', r'<span class="nowrap">\1</span>', esc(h.get('title') or page.get('title'))),
        '<p class="hero-subtitle">%s</p>' % esc(h['subtitle']) if h.get('subtitle') else '',
        '<p class="hero-intro">%s</p>' % esc(h['intro']) if h.get('intro') else '',
        editorial_links(h.get('links'), depth), editorial_image(h, depth, eager=True))

CV_SOURCE = ROOT / '_src/content/cv.html'
CV_PASSWORD = ROOT / '_src/cv-password.txt'
PBKDF2_ITER = 250000

def encrypt_cv(password, plaintext):
    """AES-256-CBC + HMAC-SHA256, keys from PBKDF2-SHA256 — decryptable with WebCrypto, no Python deps."""
    salt = secrets.token_bytes(16)
    keys = hashlib.pbkdf2_hmac('sha256', password.encode(), salt, PBKDF2_ITER, 80)
    key, iv, mac_key = keys[:32], keys[32:48], keys[48:]
    ct = subprocess.run(['openssl', 'enc', '-aes-256-cbc', '-K', key.hex(), '-iv', iv.hex()],
                        input=plaintext.encode(), capture_output=True, check=True).stdout
    import hmac
    tag = hmac.new(mac_key, ct, 'sha256').digest()
    b64 = lambda b: base64.b64encode(b).decode()
    return {'salt': b64(salt), 'iv': b64(iv), 'ct': b64(ct), 'tag': b64(tag), 'iter': PBKDF2_ITER}

def cv_page(page, depth):
    zh = LANG == 'zh'
    if not (CV_SOURCE.exists() and CV_PASSWORD.exists()):
        print('  ! cv: need _src/content/cv.html and _src/cv-password.txt (both untracked)', file=sys.stderr)
        return '<div class="editorial-hero"><div class="hero-copy"><p class="eyebrow">CV</p><h1 class="ds-title">Curriculum vitae</h1><p class="hero-intro">Available on request — <a href="mailto:%s">%s</a>.</p></div></div>' % (esc(S['email']), esc(S['email']))
    blob = encrypt_cv(CV_PASSWORD.read_text().strip(), CV_SOURCE.read_text())
    return (f'''<div class="editorial-hero web-hero cv-lock" id="cv-lock"><div class="hero-copy"><p class="eyebrow">CV · 2026</p>
<h1 class="ds-title">Curriculum vitae</h1>
<p class="hero-intro">This page is shared on request. Enter the password, or <a href="mailto:{esc(S['email'])}?subject=CV">write to me</a> for one.</p>
<form class="cv-form" id="cv-form" autocomplete="off"><label for="cv-pass" class="visually-hidden">Password</label>
<input id="cv-pass" type="password" placeholder="Password" required autocomplete="current-password">
<button type="submit" class="cv-button sample-primary ys-button">Open CV</button><p class="cv-error" id="cv-error" role="alert" hidden>That password didn’t work.</p></form>
</div></div>
<article class="cv" id="cv-content" hidden></article>
<script type="application/json" id="cv-blob">{json.dumps(blob)}</script>
<script src="{rel(depth)}assets/js/cv.js" defer></script>''')

def design_profile():
    file = ROOT / '_src/design/website-profile.json'
    if not file.is_file():
        raise RuntimeError('Shared website design missing; run node _src/sync_design.mjs with YESHAN_DESIGN_ROOT.')
    return json.loads(file.read_text())

def design_inline():
    return (ROOT / '_src/design/website-inline.css').read_text()

def head(page, depth):
    p = rel(depth)
    slug = page['slug']
    title = S['name'] + (' · 俞悠洋' if slug == 'home' else ' — ' + (page.get('title') or slug))
    desc = page.get('description') or S['description']
    og = page.get('ogImage') or S.get('ogImage')
    canon = SITE_URL + '/' + route(slug, LANG)
    alternates = ''
    if BY_SLUG[slug].get('zh'):
        alternates = ''.join('<link rel="alternate" hreflang="%s" href="%s/%s">\n' % (code, SITE_URL, route(slug, lng)) for code, lng in [('en','en'),('zh-Hans','zh'),('x-default','en')])
    return f'''<!doctype html>
<html lang="{'zh-Hans' if LANG == 'zh' else 'en'}" data-theme="{design_profile()['theme']}" data-button-style="{design_profile()['recipe']['appearance']['buttonStyle']}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<meta name="keywords" content="{esc(S['keywords'])}">
<link rel="canonical" href="{esc(canon)}">
{'<meta name="robots" content="noindex, nofollow">' if page.get('noindex') else ''}
{alternates}
<meta property="og:type" content="website">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:url" content="{esc(canon)}">
{f'<meta property="og:image" content="{SITE_URL}/{og}">' if og else ''}
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" href="{p}favicon.ico" sizes="32x32">
<link rel="apple-touch-icon" href="{p}assets/apple-touch-icon.png">
<link rel="preload" as="font" type="font/woff2" href="{p}assets/fonts/hanken-latin.woff2" crossorigin>
<link rel="preload" as="font" type="font/woff2" href="{p}assets/fonts/archivo-latin.woff2" crossorigin>
<link rel="stylesheet" href="{p}assets/css/site.css">
<link rel="stylesheet" href="{p}assets/css/design.css">
<link rel="stylesheet" href="{p}assets/css/website.css">
<style id="youyang-recipe-projection">{design_inline()}</style>
</head>
<body class="{'editorial-page' if page['type'] in ('editorial', 'cv') else 'archive-page'} page-{esc(slug)}">
<a class="skip-link" href="#main">{'跳到正文' if LANG == 'zh' else 'Skip to content'}</a>
<span id="top"></span>
'''

def header(page, depth):
    p = rel(depth)
    current = page['slug']
    if current not in ('home', 'work', 'wilder-mountain-dojo', 'writing', 'about'):
        current = 'writing' if page.get('type') == 'essay' else ('about' if current in ('about-archive', 'cv') else 'work')
    links = ''.join(
        '<a href="%s"%s>%s</a>' % (href(n['href'], depth),
            ' aria-current="page"' if n['href'].strip('/') == current else '', esc(n.get('labelZh', n['label']) if LANG == 'zh' else n['label']))
        for n in S['nav'])
    localized = bool(BY_SLUG[page['slug']].get('zh'))
    language_target = page['slug'] if localized else 'home'
    language = '<a class="language-switch" href="%s" lang="%s" aria-label="%s">%s</a>' % (
        href('/' + language_target, depth, 'en' if LANG == 'zh' else 'zh'),
        'en' if LANG == 'zh' else 'zh-Hans', 'Read in English' if LANG == 'zh' else ('阅读中文版' if localized else '前往中文首页'), 'EN' if LANG == 'zh' else '中文')
    return f'''<header class="site-header ds-masthead">
<button class="nav-toggle" aria-expanded="false" aria-label="{'菜单' if LANG == 'zh' else 'Menu'}" aria-controls="site-nav"><svg class="menu-open" viewBox="0 0 24 24" aria-hidden="true"><path d="M4 6h16M4 12h16M4 18h16"/></svg><svg class="menu-close" viewBox="0 0 24 24" aria-hidden="true"><path d="m6 6 12 12M6 18 18 6"/></svg></button>
<nav class="site-nav" id="site-nav" data-open="false">{links}<div class="nav-extras">{language.replace('class="language-switch"', 'class="nav-language"')}<a class="header-contact" href="mailto:{esc(S['email'])}">{'联系' if LANG == 'zh' else 'Contact'}</a></div></nav>
<div class="header-tools">{language}<a class="header-contact" href="mailto:{esc(S['email'])}">{'联系' if LANG == 'zh' else 'Contact'}</a></div>
<div class="site-logo"><a href="{href('/', depth)}" aria-label="{'俞悠洋，首页' if LANG == 'zh' else 'Youyang Yu, home'}">{esc(S['logo'])}</a></div>
</header>
{'' if page.get('masthead') and page['type'] != 'editorial' else '<div class="header-placeholder"></div>'}
'''

def masthead(page):
    if not page.get('masthead'): return ''
    tag = ('<p class="tagline">%s</p>' % esc(page['tagline'])) if page.get('tagline') else ''
    arrow = ('<button class="masthead-arrow" aria-label="Scroll to content"></button>'
             if page.get('arrow') else '')
    return f'''<div class="masthead web-hero">
<div class="masthead-inner">
<h1 class="ds-title">{esc(page['masthead'])}</h1>
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
                                       for raw in g['items'] for i in [resolve_card(raw, PAGES, LANG)] if i['href'].lstrip('/') == s), None)
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
    return f'''<footer class="site-footer ds-footer">{foot}</footer>
</div>
<button class="to-top" aria-label="{'返回顶部' if LANG == 'zh' else 'Back to top'}"></button>
<div class="lightbox" role="dialog" aria-modal="true" aria-label="{'放大图片' if LANG == 'zh' else 'Enlarged image'}">
<button class="lightbox-close" aria-label="{'关闭' if LANG == 'zh' else 'Close'}">&times;</button><img alt="">
</div>
<script src="{p}assets/js/design.js" defer></script>
<script src="{p}assets/js/site.js" defer></script>
</body>
</html>
'''

def work_tools(page):
    zh = LANG == 'zh'
    groups = [(str(i), b.get('title', '')) for i, b in enumerate(page.get('blocks', []))]
    return ('<div class="work-tools" hidden><div class="work-filters" role="group" aria-label="%s">'
            '<button type="button" data-filter="all" aria-pressed="true">%s</button>%s</div>'
            '<label class="work-search"><span>%s</span><input type="search" id="work-search" placeholder="%s"></label>'
            '<p id="work-count" role="status" aria-live="polite"></p></div>'
            '<p id="work-empty" hidden>%s</p>') % (
                '按类别浏览' if zh else 'Browse by practice', '全部' if zh else 'All work',
                ''.join('<button type="button" data-filter="%s" aria-pressed="false">%s</button>' % (key, esc(title)) for key, title in groups),
                '搜索作品' if zh else 'Find something', '标题、年份或关键词' if zh else 'Title, year or a word…',
                '没有找到，试试其他词或类别。' if zh else 'No matches. Try another word or category.')

def render(page, depth, motion_preview=False):
    out = [head(page, depth), '<div class="site-wrap ds-document sample-web" data-link-feedback>', header(page, depth), '' if page['type'] == 'editorial' else masthead(page),
           '<main id="main" class="shell">']
    if page['type'] == 'editorial':
        out.append(editorial_hero(page, depth))
        if page['slug'] == 'work': out.append(work_tools(page))
    elif page['type'] == 'cv':
        out.append(cv_page(page, depth))
    elif not page.get('masthead'):
        out.append('<div class="web-hero"><h1 class="archive-title ds-title">%s</h1></div>' % esc(page.get('title') or page['slug']))
    if page['type'] == 'gallery':
        out.append('<div class="covers">%s</div>'
                   % ''.join(cover(i, depth) for i in page['items']))
    else:
        out.append(''.join(block(b, depth) for b in page.get('blocks', [])))
    out.append('</main>')
    out.append(related(page, depth))
    out.append(tail(page, depth))
    route_key = ('index.html' if depth == 0 else (page['slug']+'/' if LANG=='en' else route(page['slug'], LANG)) + 'index.html')
    return annotate_motion(''.join(out), route_key, preview=motion_preview)

def main():
    global LANG
    written = []
    website_css = (ROOT / "_src/design/website.css").read_bytes()
    target_css = ROOT / "assets/css/website.css"
    if not target_css.exists() or target_css.read_bytes() != website_css:
        target_css.write_bytes(website_css)
    # A source snapshot omits private CV inputs by design. Preserve the existing
    # encrypted output exactly instead of silently publishing a degraded fallback.
    preserve_cv = not (CV_SOURCE.exists() and CV_PASSWORD.exists())
    frozen_cv = {}
    if preserve_cv:
        for page in PAGES:
            if page.get('type') != 'cv': continue
            destinations = [page['slug'] + '/index.html']
            if page.get('zh'): destinations.append(route(page['slug'], 'zh') + 'index.html')
            for name in destinations:
                frozen = ROOT / name
                if not frozen.is_file():
                    raise RuntimeError('Frozen CV output missing: ' + name + '; retain the existing public artifact. Private credentials are not requested.')
                frozen_cv[name] = frozen.read_bytes()
    for page in PAGES:
        slug = page['slug']
        LANG = 'en'
        if '/' + slug == S.get('home', '/home'):
            (ROOT / 'index.html').write_text(render(page, 0)); written.append('index.html')
        d = ROOT / slug
        d.mkdir(exist_ok=True)
        destination = slug + '/index.html'
        if destination not in frozen_cv:
            (d / 'index.html').write_text(render(page, 1))
        written.append(destination)
        if page.get('zh'):
            LANG = 'zh'
            localized = {**page, **page['zh'], 'slug': slug}
            d = ROOT / route(slug, 'zh')
            d.mkdir(parents=True, exist_ok=True)
            depth = len(d.relative_to(ROOT).parts)
            destination = str(d.relative_to(ROOT)) + '/index.html'
            if destination not in frozen_cv:
                (d / 'index.html').write_text(render(localized, depth))
            written.append(destination)
    for name, original in frozen_cv.items():
        if (ROOT / name).read_bytes() != original:
            raise RuntimeError('Frozen CV output changed: ' + name)
    LANG = 'en'
    cname = ROOT / 'CNAME'
    if S.get('customDomain'):
        cname.write_text(S['url'].split('//')[1] + '\n')
    elif cname.exists():
        cname.unlink()
    (ROOT / '.nojekyll').write_text('')
    (ROOT / 'robots.txt').write_text('User-agent: *\nAllow: /\nSitemap: %s/sitemap.xml\n' % SITE_URL)
    urls = ''.join('<url><loc>%s/%s</loc></url>' % (SITE_URL, route(p['slug'], lang))
                   for p in PAGES for lang in (['en', 'zh'] if p.get('zh') else ['en']))
    (ROOT / 'sitemap.xml').write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">%s</urlset>\n' % urls)
    print('built %d pages' % len(written))
    for w in written: print('  ', w)

if __name__ == '__main__':
    main()
