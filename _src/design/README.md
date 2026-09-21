# Adopted website and content desk presentation

The 2026-09-21 release adopts the B2 presentation approved in the live preview.
The canonical content remains `_src/content/site.json`; private CV inputs, media and desk drafts are unchanged.

`assets/css/design.css`, `assets/js/design.js` and `_src/desk/design/` are the adopted, self-contained shared-design runtime snapshot. They do not read the archived worktrees. The website-specific CSS source is `_src/design/website.css`; `build.py` synchronizes it into `assets/css/website.css`. The saved website profile and inline projection preserve the approved recipe.

Future edits happen in this repository only. A future shared-system update must explicitly replace and verify the snapshot; do not run historical candidate generators or restore old content. The historical B2 origin is retained in Git and the project archive, not as a parallel editable product.
