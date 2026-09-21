#!/usr/bin/env python3
"""Check static output and both deployment bases without network or dependencies.

Run after build.py. The alternate deployment is rendered in memory; no generated
pages or configuration are changed. This does not test browser layout or input.
"""
import importlib.util
import json
import re
import sys
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urljoin, urlsplit
from xml.etree import ElementTree

ROOT = Path(__file__).resolve().parent.parent
CONTENT = json.loads((ROOT / '_src/content/site.json').read_text())
SETTINGS = CONTENT['site']
PAGES = CONTENT['pages']
ERRORS = []


class Document(HTMLParser):
    def __init__(self, text):
        super().__init__(convert_charrefs=True)
        self.elements = []
        self.ids = Counter()
        self.headings = []
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        self.elements.append((tag, attrs))
        if attrs.get('id'):
            self.ids[attrs['id']] += 1
        if re.fullmatch(r'h[1-6]', tag):
            self.headings.append(int(tag[1]))

    def select(self, tag=None, **attrs):
        return [a for t, a in self.elements
                if (tag is None or t == tag)
                and all(a.get(k) == v for k, v in attrs.items())]


def expected_pages():
    result = {}
    for page in PAGES:
        slug = page['slug']
        canonical = '' if '/' + slug == SETTINGS['home'] else slug + '/'
        result[slug + '/index.html'] = (page, 'en', canonical)
        if not canonical:
            result['index.html'] = (page, 'en', '')
        if page.get('zh'):
            path = 'zh/' + canonical
            result[path + 'index.html'] = (page, 'zh-Hans', path)
    return result


EXPECTED = expected_pages()


def error(label, message):
    ERRORS.append(label + ': ' + message)


def local_target(url, base, label):
    parsed = urlsplit(url)
    site = urlsplit(base)
    if parsed.scheme not in ('http', 'https') or parsed.netloc != site.netloc:
        return None
    prefix = site.path.rstrip('/') + '/'
    if not parsed.path.startswith(prefix):
        error(label, 'URL escapes deployment prefix: ' + url)
        return None
    path = unquote(parsed.path[len(prefix):])
    if path.endswith('/') or not path:
        path += 'index.html'
    elif (ROOT / path).is_dir():
        path += '/index.html'
    return path, unquote(parsed.fragment)


def verify_documents(texts, base, scenario):
    base = base.rstrip('/') + '/'
    docs = {path: Document(text) for path, text in texts.items()}
    references = 0
    for path, doc in docs.items():
        label = scenario + '/' + path
        page, language, canonical_path = EXPECTED[path]
        canonical = base + canonical_path
        if len(doc.select('h1')) != 1:
            error(label, 'expected exactly one h1')
        if len(doc.select('main')) != 1:
            error(label, 'expected exactly one main landmark')
        if len(doc.select('html')) != 1 or doc.select('html')[0].get('lang') != language:
            error(label, 'incorrect document language')
        for name, count in doc.ids.items():
            if count > 1:
                error(label, 'duplicate id ' + name)
        previous = 0
        for level in doc.headings:
            if level > previous + 1:
                error(label, 'skipped heading level')
            previous = level
        if [a.get('href') for a in doc.select('link', rel='canonical')] != [canonical]:
            error(label, 'incorrect canonical URL')
        if [a.get('content') for a in doc.select('meta', property='og:url')] != [canonical]:
            error(label, 'incorrect Open Graph URL')
        english_path = '' if page['slug'] == 'home' else page['slug'] + '/'
        expected_alternates = ({'en': base + english_path,
                                'zh-Hans': base + 'zh/' + english_path,
                                'x-default': base + english_path}
                               if page.get('zh') else {})
        alternates = doc.select('link', rel='alternate')
        if ({a.get('hreflang'): a.get('href') for a in alternates} != expected_alternates
                or len(alternates) != len(expected_alternates)):
            error(label, 'incorrect language alternates')
        switches = [a for a in doc.select('a')
                    if 'language-switch' in a.get('class', '').split()]
        switch_target = ((base + english_path) if language == 'zh-Hans'
                         else base + 'zh/' + (english_path if page.get('zh') else ''))
        if len(switches) != 1 or urljoin(base + path, switches[0].get('href', '')) != switch_target:
            error(label, 'incorrect language-switch destination')
        for tag, attrs in doc.elements:
            urls = [attrs[a] for a in ('href', 'src', 'poster', 'data-full') if attrs.get(a)]
            if tag == 'meta' and attrs.get('property') == 'og:image':
                urls.append(attrs.get('content', ''))
            for value in urls:
                target = local_target(urljoin(base + path, value), base, label)
                if target is None:
                    continue
                references += 1
                file, fragment = target
                if file not in docs and not (ROOT / file).is_file():
                    error(label, 'missing internal target: ' + value)
                if fragment and file in docs and fragment not in docs[file].ids:
                    error(label, 'missing fragment: ' + value)
        for alternate in alternates:
            file, _ = local_target(alternate['href'], base, label)
            other = docs.get(file)
            if other and ({a.get('hreflang'): a.get('href') for a in other.select('link', rel='alternate')}
                          != expected_alternates):
                error(label, 'nonreciprocal language alternates')
    print('%s: checked %d HTML pages and %d local URL references' % (scenario, len(docs), references))


def verify_assets():
    for css in sorted((ROOT / 'assets/css').glob('*.css')):
        text = css.read_text()
        for value in re.findall(r'url\(\s*[\'"]?([^\)\'"\s]+)', text):
            if urlsplit(value).scheme or value.startswith(('#', '//')):
                continue
            if not (css.parent / unquote(urlsplit(value).path)).is_file():
                error(str(css.relative_to(ROOT)), 'missing CSS asset: ' + value)


def main():
    configured_base = (SETTINGS['url'] if SETTINGS.get('customDomain')
                       else SETTINGS.get('previewUrl', SETTINGS['url'])).rstrip('/')
    outputs = {str(p.relative_to(ROOT)) for p in ROOT.rglob('index.html') if not any(part in ('.git', '.desk', '_src') for part in p.relative_to(ROOT).parts)}
    for extra in outputs - EXPECTED.keys():
        error('generated output', 'unexpected stale page: ' + extra)
    for missing in EXPECTED.keys() - outputs:
        error('generated output', 'missing page: ' + missing)
    texts = {p: (ROOT / p).read_text() for p in EXPECTED if (ROOT / p).is_file()}
    verify_documents(texts, configured_base, 'generated output')
    try:
        urls = [e.text for e in ElementTree.parse(ROOT / 'sitemap.xml').findall('.//{*}loc')]
    except (OSError, ElementTree.ParseError) as exc:
        urls = []
        error('sitemap.xml', 'missing or invalid output: ' + str(exc))
    expected_urls = {configured_base + '/' + info[2] for info in EXPECTED.values()}
    if set(urls) != expected_urls or len(urls) != len(set(urls)):
        error('sitemap.xml', 'canonical URL set or uniqueness is incorrect')
    robots = (ROOT / 'robots.txt').read_text() if (ROOT / 'robots.txt').is_file() else ''
    if 'Sitemap: ' + configured_base + '/sitemap.xml' not in robots:
        error('robots.txt', 'sitemap base is incorrect')
    if not (ROOT / '.nojekyll').exists():
        error('deployment', 'missing .nojekyll')
    verify_assets()

    # Exercise the real renderer under both bases, without writing generated files.
    sys.dont_write_bytecode = True
    spec = importlib.util.spec_from_file_location('site_builder', ROOT / '_src/build.py')
    builder = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(builder)
    for base in dict.fromkeys([SETTINGS.get('previewUrl', configured_base), SETTINGS['url']]):
        builder.SITE_URL = base.rstrip('/')
        rendered = {}
        for path, (page, language, _) in EXPECTED.items():
            builder.LANG = 'zh' if language == 'zh-Hans' else 'en'
            localized = {**page, **page['zh'], 'slug': page['slug']} if builder.LANG == 'zh' else page
            rendered[path] = builder.render(localized, len(Path(path).parts) - 1)
        verify_documents(rendered, base, 'in-memory ' + base)
    if ERRORS:
        print('\nFAILED: %d issue(s)' % len(ERRORS))
        for issue in ERRORS:
            print(' - ' + issue)
        return 1
    print('PASS: routes, assets, fragments, headings, IDs, metadata, languages and sitemap.')
    print('Browser layout and interactive behavior were not tested by this script.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
