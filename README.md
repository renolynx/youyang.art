# youyang.art

The personal site, rebuilt as plain static files so it no longer needs an Adobe
Creative Cloud subscription. Same design, same URLs, same content, plus the work
made since 2023.

## What's here

```
index.html, about/, home/, animation/, sketch-book/, <project>/   built pages
assets/css, assets/js, assets/fonts                               the design system
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

That rewrites every page. Nothing else to install — Python 3 is enough.

To preview before pushing:

```bash
python3 -m http.server 8900
```

and open http://localhost:8900

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

## Going live on youyang.art

1. Push to GitHub; Settings → Pages → deploy from `main` / root.
2. When ready to move the domain, set `"customDomain": true` in
   `_src/content/site.json`, rebuild, and push — that writes the `CNAME` file.
3. At the domain registrar, point `youyang.art` at GitHub Pages:
   `A` records to `185.199.108.153`, `185.199.109.153`, `185.199.110.153`,
   `185.199.111.153`, and `www` as a `CNAME` to `renolynx.github.io`.
4. Back in Settings → Pages, set the custom domain and tick "Enforce HTTPS".

Only after step 3 does the Adobe site stop being the one people see.

## Still to do

- The contact form has no backend. It opens the visitor's mail app with the
  message pre-filled. For a real form, sign up at formspree.io or web3forms.com
  and put the endpoint in `site.json` as `"formAction"`.
- The 42-second clip at the foot of `/maybe-you-shouldve-swallowed` is now served
  from this repo (`media/maybe-you-shouldve-swallowed-clip.mp4`, 720p, 13MB),
  rescued off Adobe's CDN. It is the one film on the site that isn't on Vimeo —
  upload it there if you'd rather not carry the file.
- The favicon only exists at 32×32 — Adobe never stored a bigger one. A larger
  source file would sharpen the phone home-screen icon.
