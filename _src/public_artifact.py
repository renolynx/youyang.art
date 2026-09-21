#!/usr/bin/env python3
"""Assemble a new, explicit public tree from already rendered website output.

This command never builds, publishes, pushes, follows symlinks, or copies a repo.
Run build.py/verify.py in a complete isolated tree first. Missing public media or
frozen CV output is an error; no placeholder or private CV source is generated.
"""
import argparse
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path, PurePosixPath
import re
import shutil
import tempfile
from urllib.parse import unquote, urljoin, urlsplit


class ArtifactError(ValueError):
    pass


class References(HTMLParser):
    def __init__(self, text):
        super().__init__(convert_charrefs=True)
        self.urls = []
        self.css = []
        self.in_style = False
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        for key in ('src', 'href', 'poster', 'data-full'):
            if values.get(key):
                self.urls.append(values[key])
        if values.get('srcset'):
            self.urls.extend(item.strip().split()[0] for item in values['srcset'].split(',') if item.strip())
        if values.get('style'):
            self.css.append(values['style'])
        if tag == 'meta' and values.get('property') == 'og:image':
            self.urls.append(values.get('content', ''))
        self.in_style = tag == 'style' or self.in_style

    def handle_endtag(self, tag):
        if tag == 'style':
            self.in_style = False

    def handle_data(self, data):
        if self.in_style:
            self.css.append(data)


def css_references(text):
    values = re.findall(r'url\(\s*[\'"]?([^\)\'"\s]+)', text)
    values += re.findall(r'@import\s+[\'"]([^\'"]+)', text)
    return values


def page_paths(document):
    paths = set()
    for page in document['pages']:
        slug = page['slug']
        if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]*', slug):
            raise ArtifactError('Unsafe public page slug: ' + str(slug))
        paths.add(slug + '/index.html')
        home = '/' + slug == document['site'].get('home', '/home')
        if home:
            paths.add('index.html')
        if page.get('zh'):
            paths.add('zh/' + ('' if home else slug + '/') + 'index.html')
    return paths


def regular_file(root, relative):
    candidate = root / relative
    current = root
    for bit in PurePosixPath(relative).parts:
        current /= bit
        if current.is_symlink():
            raise ArtifactError('Public artifacts cannot contain symlinks: ' + relative)
    if not candidate.is_file() or not candidate.resolve().is_relative_to(root):
        raise ArtifactError('Missing public file: ' + relative)
    return candidate


def collect(root):
    document = json.loads(regular_file(root, '_src/content/site.json').read_text())
    media = json.loads(regular_file(root, '_src/media.json').read_text())
    pages = page_paths(document)
    media_paths = {item['src'] for item in media.values()}
    def videos(value):
        if isinstance(value, dict):
            for key, item in value.items():
                if key == 'video' and isinstance(item, str) and item.startswith('media/'):
                    yield item
                yield from videos(item)
        elif isinstance(value, list):
            for item in value:
                yield from videos(item)
    video_paths = set(videos(document))
    # These are already declared public URLs, including historical media no
    # longer linked from a visible page and dependencies hidden in frozen CV.
    # Preserve the explicit registry, never the whole media directory.
    for paths, extensions in ((media_paths, {'.png', '.jpg', '.jpeg', '.webp', '.gif', '.avif'}),
                              (video_paths, {'.mp4', '.webm', '.ogg'})):
        for relative in paths:
            if (not isinstance(relative, str) or not relative.startswith('media/')
                    or '\\' in relative or any(ord(char) < 32 for char in relative)
                    or str(PurePosixPath(relative)) != relative
                    or any(part.startswith('.') for part in PurePosixPath(relative).parts)
                    or PurePosixPath(relative).suffix.lower() not in extensions):
                raise ArtifactError('Unsafe registered public media: ' + str(relative))
    settings = document['site']
    bases = [settings[key].rstrip('/') + '/' for key in ('url', 'previewUrl') if settings.get(key)]
    configured = (settings['url'] if settings.get('customDomain') else settings.get('previewUrl', settings['url'])).rstrip('/') + '/'
    allowed = set(pages) | {'robots.txt', 'sitemap.xml', '.nojekyll', 'favicon.ico'}
    if settings.get('customDomain'):
        allowed.add('CNAME')
    # Only named release metadata fields are public; do not copy local release state.
    pending = list(pages | media_paths | video_paths | {'robots.txt', 'sitemap.xml', '.nojekyll'})
    if settings.get('customDomain'):
        pending.append('CNAME')
    if (root / 'favicon.ico').exists():
        pending.append('favicon.ico')
    chosen = {}

    def resolve_reference(value, parent):
        if not value or value.startswith(('#', 'data:', 'blob:', 'mailto:', 'tel:', 'javascript:')):
            return None
        url = urlsplit(urljoin(configured + parent, value))
        matching = sorted((base for base in bases if urlsplit(base).netloc == url.netloc), key=len, reverse=True)
        if not matching:
            return None
        base = next((b for b in matching if url.path.startswith(urlsplit(b).path)), None)
        if base is None:
            raise ArtifactError('Local reference escapes website deployment prefix: ' + value)
        decoded = unquote(url.path[len(urlsplit(base).path):])
        path = PurePosixPath(decoded)
        if decoded.startswith('/') or any(bit in ('.', '..') or bit.startswith('.') for bit in path.parts):
            raise ArtifactError('Unsafe public reference: ' + value)
        relative = str(path)
        if decoded.endswith('/') or not decoded:
            relative = (decoded if decoded else '') + 'index.html'
        elif relative + '/index.html' in pages:
            relative += '/index.html'
        extension = PurePosixPath(relative).suffix.lower()
        static_asset = (
            (relative.startswith('assets/css/') and extension == '.css')
            or (relative.startswith('assets/js/') and extension == '.js')
            or (relative.startswith('assets/fonts/') and extension in ('.woff', '.woff2', '.ttf', '.otf'))
            or (relative.startswith('assets/') and extension in ('.png', '.jpg', '.jpeg', '.webp', '.gif', '.svg', '.ico'))
            or (relative in media_paths and relative.startswith('media/') and extension in ('.png', '.jpg', '.jpeg', '.webp', '.gif', '.avif'))
            or (relative in video_paths and relative.startswith('media/') and extension in ('.mp4', '.webm', '.ogg'))
        )
        if relative not in allowed and not static_asset:
            raise ArtifactError('Reference outside public allowlist: ' + relative + ' from ' + parent)
        return relative

    while pending:
        relative = pending.pop()
        if relative in chosen:
            continue
        file = regular_file(root, relative)
        data = file.read_bytes()
        chosen[relative] = data
        refs = []
        if relative.endswith('.html'):
            parsed = References(data.decode('utf-8'))
            refs = parsed.urls + [v for css in parsed.css for v in css_references(css)]
        elif relative.endswith('.css'):
            refs = css_references(data.decode('utf-8'))
        for value in refs:
            dependency = resolve_reference(value, relative)
            if dependency:
                pending.append(dependency)
    release = root / 'release.json'
    if release.exists():
        obj = json.loads(regular_file(root, 'release.json').read_text())
        public = {key: obj[key] for key in ('revision', 'builtAt') if key in obj}
        chosen['release.json'] = (json.dumps(public, ensure_ascii=False) + '\n').encode()
    return chosen


def assemble(source, destination):
    source = Path(source).resolve()
    destination = Path(destination).absolute()
    if destination.exists():
        raise ArtifactError('Output must be a new directory: ' + str(destination))
    if destination.resolve().is_relative_to(source) or source.is_relative_to(destination.resolve()):
        raise ArtifactError('Output must be outside the source tree')
    chosen = collect(source)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='public-artifact-', dir=destination.parent) as temp:
        stage = Path(temp) / 'public'
        stage.mkdir()
        for relative, data in sorted(chosen.items()):
            target = stage / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
        manifest = {'scope': 'public-artifact-only; no hosting configuration changed', 'files': [
            {'path': key, 'bytes': len(value), 'sha256': hashlib.sha256(value).hexdigest()}
            for key, value in sorted(chosen.items())
        ]}
        (stage / 'public-manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
        shutil.move(str(stage), str(destination))
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, default=Path(__file__).resolve().parent.parent)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    try:
        manifest = assemble(args.source, args.out)
    except (ArtifactError, KeyError, json.JSONDecodeError) as error:
        parser.exit(1, str(error) + '\n')
    print(json.dumps({'output': str(args.out), 'files': len(manifest['files']), 'published': False}))


if __name__ == '__main__':
    main()
