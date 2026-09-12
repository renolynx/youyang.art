#!/usr/bin/env python3
"""2026 content pass: two new works, refreshed About copy, new footer year.

Run once against _src/content/site.json. From here on site.json is edited by hand —
_src/bootstrap-from-adobe.py is kept only as a record of the original import.
"""
import json, pathlib

P = pathlib.Path('_src/content/site.json')
site = json.loads(P.read_text())
pages = site['pages']
by = {p['slug']: p for p in pages}

B = 'f-body" style="font-size:21px;font-weight:300'
D = 'f-display" style="font-size:21px;font-weight:400'
def body(*runs):
    """runs: plain string, or (text, href) to link it in the display face."""
    out = []
    for r in runs:
        if isinstance(r, tuple):
            out.append('<a href="%s"%s><span class="%s">%s</span></a>'
                       % (r[1], ' target="_blank" rel="noopener"' if r[1].startswith('http') else '', D, r[0]))
        else:
            out.append('<span class="%s">%s</span>' % (B, r))
    return {'html': ''.join(out), 'align': 'left', 'lh': 40.0}

def text(paras, **kw):
    b = {'type': 'text', 'maxw': 800, 'width': 85.0, 'paras': paras}
    b.update(kw); return b

# ── 1. two new project pages ──────────────────────────────────────────────
begin = {
 'slug': 'begin-with-pieces', 'type': 'project', 'title': 'Begin with Pieces',
 'masthead': 'Begin with Pieces', 'arrow': True, 'year': '2023',
 'ogImage': 'media/begin-with-pieces-still.webp',
 'description': "Animated short film adapted from Yuko Taniguchi's poem, made with AI in the loop for the Creativity Camp Study.",
 'blocks': [
   {'type': 'embed', 'maxw': 1920, 'width': 100.0, 'pt': 0.0, 'pb': 60.0, 'capAlign': 'left',
    'caption': "Animated short film 'Begin with Pieces', 3 min, 2023",
    'embed': 'https://player.vimeo.com/video/815918697'},
   text([body("Adapted from the poem of the same name by Yuko Taniguchi, the film flows through a synesthetic mental space — abstract painting and shimmering computer visuals held together by AI image generation, with a group of adolescents softly reciting the poem.")],
        pt=0.0),
   {'type': 'image', 'width': 90.0, 'pt': 40.0, 'pb': 30.0, 'capAlign': 'left',
    'src': 'media/begin-with-pieces-still.jpg',
    'caption': "Still from 'Begin with Pieces', 2023"},
   text([body("Yuko Taniguchi is also a collaborator on the Creativity Camp Study, an art–health–education research project run by educators, artists and scientists at the University of Minnesota. Its workshops use creativity and self-expression as tools for coping with depression, helping adolescents facing mental health challenges break out of negative thought patterns.")],
        pt=27.0),
   text([body("The film premiered in 2023 at the Weisman Art Museum, in 'The World Inside You' — an exhibition of work made by the young artists of the Creativity Camp.")],
        pt=27.0, pb=60.0),
 ],
 'related': ['inside-my-eyes', 'for-the-best', 'i-love-you-forever-now'],
}

mountain = {
 'slug': 'inheriting-a-mountain', 'type': 'project',
 'title': 'Inheriting a Mountain', 'masthead': 'Inheriting a Mountain',
 'arrow': True, 'year': '2024',
 'ogImage': 'media/inheriting-a-mountain.webp',
 'description': 'Ceramic installation made for the ice of Bdé Umáŋ, Minneapolis, 2024.',
 'blocks': [
   {'type': 'image', 'pt': 0.0, 'pb': 20.0, 'capAlign': 'left',
    'src': 'media/inheriting-a-mountain.jpg',
    'caption': "'Inheriting Mountain on Land of 10,000 Lakes', 2024, ceramic installation, photographed on the ice of Bdé Umáŋ, Minneapolis"},
   text([body("Minnesota is a place with no mountains.")], pt=56.0),
   text([body("In the 1890s a jade mountain carved for the Qianlong emperor was looted from the Old Summer Palace in Beijing. It passed through the hands of an American legation secretary, crossed the ocean, and was bought at auction by T. B. Walker — the lumber baron whose private collection became this state's first art museum. The jade mountain is still here, in the permanent collection of the Minneapolis Institute of Art, a few miles from where I have been living.")],
        pt=27.0),
   text([body("I made my own mountain out of clay, carried it onto the frozen lake the settlers renamed Lake Harriet, and sat down with it. The Dakota called this water Bdé Umáŋ. The piece was shown at the Minneapolis College of Art and Design as part of a Jerome Fellowship.")],
        pt=27.0, pb=60.0),
 ],
 'related': ['inside-my-eyes', 'begin-with-pieces', 'for-the-best'],
}

begin['cover'] = 'media/begin-with-pieces__crop.jpg'
mountain['cover'] = 'media/inheriting-a-mountain__crop.jpg'

for new in (begin, mountain):
    if new['slug'] in by:
        pages[[i for i, p in enumerate(pages) if p['slug'] == new['slug']][0]] = new
    else:
        pages.insert([i for i, p in enumerate(pages) if p['slug'] == 'inside-my-eyes'][0], new)
by = {p['slug']: p for p in pages}

# ── 2. galleries ──────────────────────────────────────────────────────────
def put(gallery, item, before=None):
    items = by[gallery]['items']
    items[:] = [i for i in items if i['href'] != item['href']]
    at = next((n for n, i in enumerate(items) if i['href'] == before), 0) if before else 0
    items.insert(at, item)

put('home', {'href': '/begin-with-pieces', 'cover': 'media/begin-with-pieces__crop.jpg',
             'title': 'Begin with Pieces', 'meta': '2023'})
put('home', {'href': '/inheriting-a-mountain', 'cover': 'media/inheriting-a-mountain__crop.jpg',
             'title': 'Inheriting a Mountain', 'meta': '2024'})
put('animation', {'href': '/begin-with-pieces', 'cover': 'media/begin-with-pieces__crop.jpg',
                  'title': 'Begin with Pieces', 'meta': '2023'}, before='/inside-my-eyes')

# ── 3. About copy ─────────────────────────────────────────────────────────
about = by['about']
blocks = about['blocks']

# intro, second paragraph: Feinaki is in its seventh year; he works across two countries
blocks[0]['cols'][1]['blocks'][0]['paras'][1] = body(
    "In 2019 he co-founded ",
    ("Feinaki Beijing Animation Week", "https://www.instagram.com/feinaki/"),
    ", an independent festival now in its seventh year. He teaches, curates and organises between China and the United States.")

# after the Inside My Eyes still-frame caption, the two works that followed
insert_at = next(i for i, b in enumerate(blocks)
                 if b['type'] == 'text' and 'Still frames' in b['paras'][0]['html']) + 1
if not any(b.get('_id') == 'since' for b in blocks):
    blocks[insert_at:insert_at] = [
      {'_id': 'since', 'type': 'columns', 'pt': 60.0, 'cols': [
        {'flex': 110.0, 'blocks': [
          {'type': 'image', 'width': 100.0, 'maxw': 900, 'capAlign': 'left',
           'src': 'media/begin-with-pieces-still.jpg', 'href': '/begin-with-pieces',
           'caption': "Still from '<span class=\"f-display\"><a href=\"/begin-with-pieces\">Begin with Pieces</a></span>', 2023"}]},
        {'flex': 90.0, 'blocks': [
          text([body("A second film followed the same year. ",
                     ("Begin with Pieces", "/begin-with-pieces"),
                     " (2023) takes another Yuko Taniguchi poem into a synesthetic mind-space, recited by the adolescents of the Creativity Camp Study and premiered at the Weisman Art Museum.")],
               maxw=560)]},
      ]},
      {'type': 'image', 'pt': 56.0, 'pb': 20.0, 'capAlign': 'left',
       'src': 'media/inheriting-a-mountain.jpg', 'href': '/inheriting-a-mountain',
       'caption': "'<span class=\"f-display\"><a href=\"/inheriting-a-mountain\">Inheriting Mountain on Land of 10,000 Lakes</a></span>', 2024, ceramic installation on the ice of Bdé Umáŋ, Minneapolis"},
      text([body("Away from the screen, I have been working in clay. ",
                 ("Inheriting a Mountain", "/inheriting-a-mountain"),
                 " (2024) answers a jade mountain looted from the Old Summer Palace in the 1890s and now sitting in a Minneapolis museum: I made my own, carried it onto a frozen lake, and sat down with it. The work was shown at the Minneapolis College of Art and Design as part of a Jerome Fellowship.")],
           pt=64.0),
      text([body("Between the films I organise. Feinaki keeps running in Beijing; in 2026 I spent half a year in Dali building a community operating system for a live-in creative space, and I run Wild Mountain Dojo, a workshop practice about making a life you would actually want to live. The animation and the organising are the same work to me — both are about getting a room full of people to imagine something together.")],
           pt=27.0, pb=20.0),
    ]

site['site']['footer'] = '©2026'
P.write_text(json.dumps(site, indent=1, ensure_ascii=False))
print('pages now:', len(pages))
print('about blocks:', len(about['blocks']))
