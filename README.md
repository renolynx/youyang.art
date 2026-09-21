# youyang.art

Youyang Yu's personal site, built as plain static files with self-hosted images
and fonts. The 2026 update retains the handwritten identity and complete earlier
project archive, with a new homepage and bilingual pages for Work, Wilder Mountain
Dojo, Writing and About.

## Current release and sole working copy · 2026-09-21

The approved B2 website and content studio presentation is now maintained here, on `main`. All existing narrative content, media, private CV inputs and the September Chinese-title punctuation fix were retained.

- Public website: https://youyang.art
- Canonical editable repository: `/Users/a1-6/Documents/youyang.art`
- Content studio: http://127.0.0.1:8766/
- Read-only draft preview: http://127.0.0.1:8767/site/

Continue content and design work in this repository only. The B1/B2, design-capability and Auis work directories are historical material; do not use them as release sources. The content studio runs locally and is not published as a public admin service. Its activity connector is optional and requires a configured, compatible production broker; the historical demo is not a production backend.

The presentation snapshot and its future update boundary are described in `_src/design/README.md`. `python3 _src/build.py` and `_src/verify.py` work without any old process directory.

## Current structure

- `/` is the English homepage; `/home/` remains a compatible alias.
- `/zh/` is the Chinese homepage.
- `/work/`, `/wilder-mountain-dojo/`, `/writing/`, `/about/` have matching `/zh/` pages.
- Existing animation, sketchbook and project URLs remain available in English.
- `/about-archive/` preserves the earlier studio notes and production material.

Basecamp is described as planned for three Saturday afternoons in November 2026,
at three Twin Cities venues, two hours per workshop. Exact dates and venues are
not yet announced. Activity inquiries use email; there is no registration backend.

## What's here

```
index.html, about/, home/, animation/, sketch-book/, <project>/   built pages
assets/css, assets/js, assets/fonts                               site visual language
media/                                                            every image, as WebP
_src/content/site.json                                            ← all the content lives here
_src/build.py                                                     turns that JSON into the pages
_src/optimize.py                                                  shrinks new images into media/
_originals/                                                       full-size files pulled off Adobe (not in git)
```

## Changing something

Edit `_src/content/site.json`, then:

```bash
python3 _src/build.py
```

That rewrites every page, including Chinese pages. Nothing else to install —
Python 3 is enough. Shared English content lives on each page; `zh` overrides
its title, description, hero and blocks. Navigation uses `label` and `labelZh`.

The `hero`, `section`, `project_grid`, and `link_list` blocks power the new pages.
Existing image, text, video and gallery blocks remain supported.

To preview before pushing:

```bash
python3 _src/edit.py --no-open
```

and open http://127.0.0.1:8766/site/. The desk serves only public assets and preview routes; private CV inputs and draft history are not exposed as files.

Check generated navigation, assets and metadata with:

```bash
python3 _src/verify.py
```

The verifier checks static output. Before publishing, visually check the homepage,
Chinese pages and a legacy project at desktop and mobile widths, then test the
language switch, mobile menu and image lightbox.

## Adding an image

Drop the file into a folder, then:

```bash
python3 _src/optimize.py <that folder>
```

It writes a web-sized WebP into `media/` and records the dimensions in
`_src/media.json`. Reference it from `site.json` as `media/<name>.<original ext>`
— the builder maps it to the WebP.

## Fonts

Adobe Fonts stops working when the subscription does, so the five Adobe
typefaces were replaced with open-licence ones, self-hosted in `assets/fonts`:

| was (Adobe) | now (SIL Open Font License) | where |
|---|---|---|
| Halogen Black | Archivo, width 125 | the big three-line title |
| Sofia Pro Light | Hanken Grotesk | body copy |
| Upgrade Light | Archivo, width 88 | captions |
| Calder Script | Shadows Into Light | nav |
| Adobe Handwriting Ernie | Parisienne | the signature and the logo |

Every substitute was measured against the original: all set widths land within
3% of what Adobe was rendering, except the nav, which is 7% narrower.

## Content studio (September 2026)

```bash
python3 _src/edit.py
```

Open http://127.0.0.1:8766. The desk uses the adopted dark ceramic palette and shared controls, with the site's own content structure. The adopted snapshot does not claim current full-system certification.

1. Search the content library, then open a work or website page. Card and list
   views share the same records. New content can be a work, event, practice card
   or note; add its reference to a page's card group when it is ready to appear.
2. Edit title, cover and summary once. Home, Work and the old galleries read
   references to the same record. Intentional local differences and Chinese copy
   stay in `overrides` and `cardZh`. Existing URLs stay fixed.
3. Reuse an image from the library or upload new ones. Images get unique names;
   new derivatives fit their longest edge within 1800 px (1280 for animation).
4. Edits autosave to `.desk/draft.json`, **not** the public content file. The side
   preview uses the actual site renderer with the current input. “另窗预览” shows
   the saved draft. Save failures keep input; stale versions cannot overwrite
   another tab. History keeps recent drafts; “载入最新正本” archives the current
   input and loads canonical content after an external edit.
5. “检查与发布” builds an isolated copy, verifies links/assets/languages, and shows
   affected records. Confirming publishes verified output, commits only named
   content/build/media files and pushes to the existing GitHub Pages repository.
   Push and live deployment are distinct; `release.json` identifies the content
   revision. The desk checks the online marker while it remains open.

The public site uses https://youyang.art, deployed from `main` / root on GitHub
Pages. Domain setup is complete. Code/design changes are committed separately;
ordinary content publishing deliberately excludes unrelated source edits.

`_src/content_model.py` owns card resolution and validation. `desk_store.py`
owns draft revisions, history and verified releases. `_src/desk/` owns the editor.
The content document remains the canonical local source; generated HTML is not
edited by hand. Commit/push failures leave the draft available for retry.

For isolated tests, set `YOUYANG_ROOT=/path/to/copy EDIT_PORT=18767`. Do not test
publication against the production remote. Regression checks:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s _src -p 'test_*.py'
python3 _src/build.py
python3 _src/verify.py
```

This is a local, single-editor CMS. It does not yet implement multiuser accounts,
review assignments, scheduled publication or a contributor/series database.

## The CV page (`/cv/`)

`_src/content/cv.html` (the readable CV) and `_src/cv-password.txt` are **not**
in git. `build.py` encrypts the CV with the password (AES-256-CBC + HMAC,
PBKDF2 keys) and ships only the ciphertext; the browser decrypts it after the
password is entered, so the password never leaves the visitor's machine. Change
the password by editing the text file and rebuilding. Copies of both files live
in the vault under `项目/youyang.art/`.

## Still to do

- Contact is a plain mailto link. For a real form, sign up at formspree.io or
  web3forms.com and put the endpoint in `site.json` as `"formAction"`.
- The 42-second clip at the foot of `/maybe-you-shouldve-swallowed` is now served
  from this repo (`media/maybe-you-shouldve-swallowed-clip.mp4`, 720p, 13MB),
  rescued off Adobe's CDN. It is the one film on the site that isn't on Vimeo —
  upload it there if you'd rather not carry the file.
- The favicon only exists at 32×32 — Adobe never stored a bigger one. A larger
  source file would sharpen the phone home-screen icon.
