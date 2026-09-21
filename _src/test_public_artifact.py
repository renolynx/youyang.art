"""Public output boundary tests using synthetic files, never existing user media."""
import functools
import hashlib
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import tempfile
import threading
import unittest
from urllib.error import HTTPError
from urllib.request import urlopen

from public_artifact import ArtifactError, assemble


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *_args):
        pass


class PublicArtifactTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name) / 'source'
        self.root.mkdir()
        self.out = Path(self.temp.name) / 'public'
        self.put('_src/content/site.json', json.dumps({
            'site': {'url': 'https://example.test', 'previewUrl': 'https://example.test/project', 'home': '/home'},
            'pages': [{'slug': 'home', 'zh': {'title': '首页'}, 'blocks': [{'video': 'media/clip.mp4'}]}, {'slug': 'cv'}],
        }))
        self.put('_src/media.json', json.dumps({'fixture': {'src': 'media/fixture.webp'}}))
        for page, prefix in [('index.html', ''), ('home/index.html', '../'), ('zh/index.html', '../'), ('cv/index.html', '../')]:
            self.put(page, '<!doctype html><html><head><link rel="stylesheet" href="' + prefix + 'assets/css/site.css"></head>'
                     '<body><img src="' + prefix + 'media/fixture.webp"><a href="' + prefix + 'cv/">CV</a></body></html>')
        self.put('assets/css/site.css', '@font-face{src:url(../fonts/source.woff2)}')
        self.put('assets/fonts/source.woff2', b'synthetic font boundary fixture')
        self.put('media/fixture.webp', b'synthetic media boundary fixture')
        self.put('media/clip.mp4', b'synthetic video boundary fixture')
        self.put('robots.txt', 'User-agent: *')
        self.put('sitemap.xml', '<urlset/>')
        self.put('.nojekyll', '')
        self.put('_src/desk/index.html', 'PRIVATE CMS')
        self.put('_src/cv-password.txt', 'SYNTHETIC TEST VALUE')
        self.put('.desk/draft.json', 'PRIVATE DRAFT')
        self.put('activity-admin.js', 'PRIVATE ADMIN BUNDLE')
        self.put('assets/js/not-referenced.js', 'UNREFERENCED')
        self.put('release.json', json.dumps({'revision': 'fixture-revision', 'builtAt': 1, 'root': '/private', 'token': 'fixture'}))

    def tearDown(self):
        self.temp.cleanup()

    def put(self, path, data):
        target = self.root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data if isinstance(data, bytes) else data.encode())

    def test_http_serves_only_allowlisted_public_bytes(self):
        manifest = assemble(self.root, self.out)
        for item in manifest['files']:
            value = (self.out / item['path']).read_bytes()
            self.assertEqual(hashlib.sha256(value).hexdigest(), item['sha256'])
            self.assertEqual(len(value), item['bytes'])
        self.assertEqual(json.loads((self.out / 'release.json').read_text()), {'revision': 'fixture-revision', 'builtAt': 1})
        handler = functools.partial(QuietHandler, directory=self.out)
        server = ThreadingHTTPServer(('127.0.0.1', 0), handler)
        worker = threading.Thread(target=server.serve_forever, daemon=True)
        worker.start()
        try:
            origin = 'http://127.0.0.1:' + str(server.server_port)
            with urlopen(origin + '/cv/') as response:
                self.assertEqual(response.read(), (self.root / 'cv/index.html').read_bytes())
            for path in ('/_src/desk/index.html', '/_src/content/site.json', '/_src/cv-password.txt', '/.desk/draft.json',
                         '/activity-admin.js', '/assets/js/not-referenced.js', '/api/site', '/api/cms/state'):
                with self.subTest(path=path), self.assertRaises(HTTPError) as error:
                    urlopen(origin + path)
                self.assertEqual(error.exception.code, 404)
        finally:
            server.shutdown()
            server.server_close()
            worker.join()

    def test_missing_frozen_cv_never_becomes_placeholder(self):
        (self.root / 'cv/index.html').unlink()
        with self.assertRaisesRegex(ArtifactError, 'Missing public file'):
            assemble(self.root, self.out)
        self.assertFalse(self.out.exists())

    def test_existing_content_video_is_kept_byte_for_byte(self):
        self.put('index.html', '<video><source src="media/clip.mp4" type="video/mp4"></video>')
        assemble(self.root, self.out)
        self.assertEqual((self.out / 'media/clip.mp4').read_bytes(), (self.root / 'media/clip.mp4').read_bytes())

    def test_registered_historical_media_survive_without_current_html_reference(self):
        self.put('_src/media.json', json.dumps({'fixture': {'src': 'media/fixture.webp'},
                                              'legacy': {'src': 'media/legacy-public.webp'}}))
        self.put('media/legacy-public.webp', b'synthetic historical public bytes')
        assemble(self.root, self.out)
        self.assertEqual((self.out / 'media/legacy-public.webp').read_bytes(), b'synthetic historical public bytes')
        self.assertEqual((self.out / 'media/clip.mp4').read_bytes(), (self.root / 'media/clip.mp4').read_bytes())
        self.assertFalse((self.out / '_src/media.json').exists())

    def test_registered_media_cannot_authorize_private_or_traversal_paths(self):
        for reference in ('media/../_src/cv-password.txt', '../source/media/fixture.webp',
                          '/media/fixture.webp', 'media/.private.webp', 'media/fake.js',
                          'media//fixture.webp', 'media/../_src/.hidden.webp'):
            with self.subTest(reference=reference):
                self.put('_src/media.json', json.dumps({'bad': {'src': reference}}))
                with self.assertRaises(ArtifactError):
                    assemble(self.root, self.out)
                self.assertFalse(self.out.exists())

    def test_missing_media_is_error_and_output_not_partially_written(self):
        (self.root / 'media/fixture.webp').unlink()
        with self.assertRaisesRegex(ArtifactError, 'Missing public file'):
            assemble(self.root, self.out)
        self.assertFalse(self.out.exists())

    def test_private_reference_is_rejected(self):
        for reference in ('_src/content/site.json', 'activity-admin.js', '.desk/draft.json', 'api/site', 'media/unlisted.webp',
                          'https://example.test/_src/desk/index.html'):
            with self.subTest(reference=reference):
                self.put('index.html', '<a href="' + reference + '">bad</a>')
                with self.assertRaises(ArtifactError):
                    assemble(self.root, self.out)
                self.assertFalse(self.out.exists())

    def test_asset_symlink_cannot_escape_whitelist(self):
        asset = self.root / 'assets/fonts/source.woff2'
        asset.unlink()
        asset.symlink_to(self.root / '_src/cv-password.txt')
        with self.assertRaisesRegex(ArtifactError, 'symlinks'):
            assemble(self.root, self.out)

    def test_output_must_be_new_and_outside_source(self):
        with self.assertRaises(ArtifactError):
            assemble(self.root, self.root / 'out')
        self.out.mkdir()
        self.put('unrelated.txt', 'untouched')
        with self.assertRaises(ArtifactError):
            assemble(self.root, self.out)


if __name__ == '__main__':
    unittest.main()
