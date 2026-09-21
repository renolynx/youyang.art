"""Real loopback HTTP regression tests; fresh local fixtures, no publish/live calls."""
import copy
import importlib.util
import io
import json
import os
from pathlib import Path
import shutil
import tempfile
import threading
import unittest
from http.client import HTTPConnection
from http.server import ThreadingHTTPServer
from unittest.mock import patch
from urllib.parse import urlsplit

ROOT=Path(__file__).resolve().parent.parent

class CmsHttpTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory(prefix='youyang-cms-http-')
        cls.root=Path(cls.temp.name)
        shutil.copytree(ROOT/'_src',cls.root/'_src',ignore=shutil.ignore_patterns('__pycache__', 'cv.html', 'cv-password.txt'))
        (cls.root/'assets/css').mkdir(parents=True)
        (cls.root/'assets/css/fixture.css').write_text('body{color:inherit}')
        (cls.root/'assets/private.json').write_text('{"private":true}')
        (cls.root/'media').mkdir()
        (cls.root/'media/fixture.webp').write_bytes(b'RIFFfixtureWEBP')
        (cls.root/'private.txt').write_text('fixture secret')
        (cls.root/'media/escape.css').symlink_to(cls.root/'private.txt')
        spec=importlib.util.spec_from_file_location('isolated_cms_edit',ROOT/'_src/edit.py')
        cls.edit=importlib.util.module_from_spec(spec)
        with patch.dict(os.environ,{'YOUYANG_ROOT':str(cls.root)}): spec.loader.exec_module(cls.edit)
        cls.cms=ThreadingHTTPServer(('127.0.0.1',0),cls.edit.H)
        cls.renderer=ThreadingHTTPServer(('127.0.0.1',0),cls.edit.PreviewH)
        cls.edit.PORT=cls.cms.server_port
        cls.origin='http://127.0.0.1:'+str(cls.cms.server_port)
        cls.preview_origin='http://127.0.0.1:'+str(cls.renderer.server_port)
        cls.edit.PREVIEW_ORIGIN=cls.preview_origin
        for server in (cls.cms,cls.renderer):
            threading.Thread(target=server.serve_forever,daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        for server in (cls.cms,cls.renderer): server.shutdown();server.server_close()
        cls.temp.cleanup()

    def request(self,path,method='GET',body=None,headers=None,preview=False):
        connection=HTTPConnection('127.0.0.1',(self.renderer if preview else self.cms).server_port,timeout=5)
        payload=body if isinstance(body,bytes) else json.dumps(body).encode() if body is not None else None
        supplied=dict(headers or {})
        if body is not None: supplied.setdefault('Content-Type','application/json')
        connection.request(method,path,body=payload,headers=supplied)
        response=connection.getresponse()
        result=response.status,dict(response.headers),response.read()
        connection.close()
        return result

    def authorized(self): return {'Origin':self.origin,'X-Desk-Token':self.edit.TOKEN,'Sec-Fetch-Site':'same-origin'}

    def test_01_token_and_api_are_not_readable_from_preview_or_foreign_origin(self):
        status,headers,body=self.request('/api/site')
        self.assertEqual(status,200)
        self.assertIn(self.edit.TOKEN,json.loads(body)['token'])
        self.assertIn('no-store',headers['Cache-Control'])
        for endpoint in ('/api/site','/api/history','/api/activity-config','/api/health'):
            for metadata in ({'Origin':self.preview_origin},{'Origin':'https://invalid.example'}, {'Sec-Fetch-Site':'same-site','Sec-Fetch-Mode':'no-cors'}):
                with self.subTest(endpoint=endpoint,metadata=metadata):
                    status,headers,body=self.request(endpoint,headers=metadata)
                    self.assertEqual(status,403)
                    self.assertNotIn(self.edit.TOKEN.encode(),body)
                    self.assertNotIn('Access-Control-Allow-Origin',headers)

    def test_02_write_requires_origin_and_process_token(self):
        before=self.edit.STORE.read()['revision']
        for headers in ({}, {'X-Desk-Token':'wrong'}, {'X-Desk-Token':self.edit.TOKEN,'Origin':self.preview_origin}, {'X-Desk-Token':self.edit.TOKEN,'Host':'outside.example'}):
            self.assertEqual(self.request('/api/site','POST',{},headers)[0],403)
        self.assertEqual(self.edit.STORE.read()['revision'],before)

    def test_03_renderer_runs_only_on_second_origin_and_does_not_save_input(self):
        current=self.edit.STORE.read();draft=copy.deepcopy(current['site'])
        page=next(page for page in draft['pages'] if page['type']=='project')
        page['blocks']=[{'type':'section','title':'Preview fixture','body':'<p>Unsaved sentinel</p><script>window.fixtureContentScript=true</script>'}]
        status,headers,body=self.request('/api/preview','POST',{'site':draft,'slug':page['slug'],'lang':'en'},self.authorized())
        self.assertEqual(status,200)
        result=json.loads(body)
        self.assertNotIn('html',result)
        url=urlsplit(result['url'])
        self.assertEqual(url.scheme+'://'+url.netloc,self.preview_origin)
        status,headers,rendered=self.request(url.path,preview=True)
        self.assertEqual(status,200)
        self.assertIn(b'Unsaved sentinel',rendered)
        self.assertIn(b'window.fixtureContentScript=true',rendered)
        self.assertIn(b'<base href="/site/',rendered)
        self.assertNotIn(self.edit.TOKEN.encode(),rendered)
        self.assertIn("connect-src 'self'",headers['Content-Security-Policy'])
        self.assertNotIn('Access-Control-Allow-Origin',headers)
        self.assertEqual(self.edit.STORE.read()['revision'],current['revision'])
        self.assertEqual(self.request(url.path)[0],404)
        self.assertEqual(self.request('/site/'+page['slug']+'/')[0],302)
        self.assertEqual(self.request('/site/'+page['slug']+'/')[1]['Location'],self.preview_origin+'/site/'+page['slug']+'/')

    def test_04_preview_has_no_cms_routes_and_no_file_server_fallback(self):
        for method in ('GET','HEAD'):
            for endpoint in ('/','/api/site','/api/history','/api/activity-config','/desk.js','/activity-admin.js','/_src/edit.py','/private.txt','/assets/private.json','/media/escape.css','/site/_src/edit.py','/media/%2e%2e/_src/edit.py','/assets/../private.txt'):
                with self.subTest(method=method,endpoint=endpoint): self.assertEqual(self.request(endpoint,method,preview=True)[0],404)
        self.assertEqual(self.request('/api/site','POST',{},self.authorized(),preview=True)[0],405)
        self.assertEqual(self.request('/api/site','OPTIONS',preview=True)[0],405)
        self.assertEqual(self.request('/site/',headers={'Host':'localhost:'+str(self.renderer.server_port)},preview=True)[0],403)
        self.assertEqual(self.request('/assets/css/fixture.css',preview=True)[0],200)
        self.assertEqual(self.request('/site/assets/css/fixture.css',preview=True)[0],200)
        self.assertEqual(self.request('/media/fixture.webp',preview=True)[0],200)

    def test_05_cms_head_does_not_inherit_arbitrary_files(self):
        for method in ('GET','HEAD'):
            for endpoint in ('/_src/edit.py','/private.txt','/assets/private.json','/media/escape.css','/assets/%2e%2e/_src/content/site.json'):
                self.assertEqual(self.request(endpoint,method)[0],404)

    def test_06_expired_preview_can_be_replaced_without_affecting_content(self):
        with patch.object(self.edit.time,'monotonic',return_value=10): url=self.edit.SNAPSHOTS.put('<p>old fixture</p>')
        with patch.object(self.edit.time,'monotonic',return_value=311):
            self.assertEqual(self.request(urlsplit(url).path,preview=True)[0],410)
            renewed=self.edit.SNAPSHOTS.put('<p>new fixture</p>')
            self.assertEqual(self.request(urlsplit(renewed).path,preview=True)[2],b'<p>new fixture</p>')

    def test_07_configuration_is_explicit_fixed_and_recoverable(self):
        with patch.dict(os.environ,{'YOUYANG_BROKER_URL':''}):
            self.assertEqual(json.loads(self.request('/api/activity-config')[2]),{'brokerUrl':'','cmsOrigin':self.origin})
        valid='https://fixture.example/cms/connect'
        with patch.dict(os.environ,{'YOUYANG_BROKER_URL':valid}): self.assertEqual(json.loads(self.request('/api/activity-config')[2])['brokerUrl'],valid)
        for value in ('http://external.example/cms/connect','https://owner:secret@fixture.example/cms/connect','https://fixture.example/api/proxy','https://fixture.example/cms/connect?owner=owner','https://fixture.example/cms/connect#token','javascript:alert(1)'):
            with patch.dict(os.environ,{'YOUYANG_BROKER_URL':value}): self.assertEqual(self.request('/api/activity-config')[0],400)
        with patch.dict(os.environ,{'YOUYANG_BROKER_URL':valid}): self.assertEqual(self.request('/api/activity-config')[0],200)

    def test_08_http_cas_conflict_preserves_first_writer_and_recovery(self):
        current=self.edit.STORE.read();one=copy.deepcopy(current['site']);two=copy.deepcopy(current['site'])
        one['pages'][0]['description']='Fixture first writer'
        two['pages'][0]['description']='Fixture retained second input'
        def save(data): return self.request('/api/site','POST',{'site':data,'revision':current['revision'],'sourceRevision':current['sourceRevision']},self.authorized())
        self.assertEqual(save(one)[0],200)
        self.assertEqual(save(two)[0],409)
        latest=self.edit.STORE.read()
        self.assertEqual(latest['site']['pages'][0]['description'],'Fixture first writer')
        status,_,body=self.request('/api/reload-source','POST',{'revision':latest['revision'],'site':two},self.authorized())
        self.assertEqual(status,200)
        snapshots=[json.loads(path.read_text()) for path in (self.edit.STORE.private/'history').glob('*.json')]
        self.assertTrue(any(item['site']['pages'][0]['description']=='Fixture retained second input' for item in snapshots))

    def test_09_media_upload_still_optimizes_and_previews_without_publishing(self):
        from PIL import Image
        image=io.BytesIO();Image.new('RGB',(12,9),(20,40,60)).save(image,format='PNG')
        boundary='cms-fixture-upload-boundary'
        multipart=(f'--{boundary}\r\nContent-Disposition: form-data; name="files"; filename="../../fixture-upload.png"\r\nContent-Type: image/png\r\n\r\n'.encode()+image.getvalue()+f'\r\n--{boundary}--\r\n'.encode())
        headers={**self.authorized(),'Content-Type':'multipart/form-data; boundary='+boundary}
        source_before=self.edit.STORE.source.read_bytes()
        status,_,body=self.request('/api/upload','POST',multipart,headers)
        self.assertEqual(status,200)
        uploaded=json.loads(body)['added'][0]
        self.assertEqual((uploaded['w'],uploaded['h']),(12,9))
        self.assertTrue(uploaded['src'].startswith('media/fixture-upload-'))
        self.assertTrue(uploaded['src'].endswith('.webp'))
        self.assertEqual(self.request('/'+uploaded['src'],preview=True)[0],200)
        self.assertEqual(self.edit.STORE.source.read_bytes(),source_before)
        self.assertFalse((self.root/'fixture-upload.png').exists())

    def test_10_cv_uses_exact_existing_frozen_html_without_private_inputs(self):
        current=self.edit.STORE.read()['site']
        cv=next(page for page in current['pages'] if page['type']=='cv')
        directory=self.root/cv['slug'];directory.mkdir()
        frozen=b'<!doctype html><html><head><title>Synthetic frozen CV</title></head><body><p id="fixture-frozen">Frozen fixture, no private CV</p><a href="../">Home</a></body></html>'
        target=directory/'index.html';target.write_bytes(frozen)
        try:
            self.assertFalse((self.root/'_src/content/cv.html').exists())
            self.assertFalse((self.root/'_src/cv-password.txt').exists())
            status,_,body=self.request('/api/preview','POST',{'site':current,'slug':cv['slug'],'lang':'en'},self.authorized())
            self.assertEqual(status,200)
            result=json.loads(body)
            self.assertEqual(result['mode'],'frozen')
            self.assertIn('冻结',result['message'])
            self.assertEqual(result['url'],self.preview_origin+'/site/'+cv['slug']+'/')
            status,_,rendered=self.request(urlsplit(result['url']).path,preview=True)
            self.assertEqual(status,200)
            self.assertEqual(rendered,frozen)
            self.assertEqual(target.read_bytes(),frozen)
            self.assertNotIn(b'Available on request',rendered)
        finally: target.unlink();directory.rmdir()

    def test_11_missing_frozen_cv_is_a_recoverable_error_on_both_routes(self):
        current=self.edit.STORE.read()['site']
        cv=next(page for page in current['pages'] if page['type']=='cv')
        requests=[self.request('/api/preview','POST',{'site':current,'slug':cv['slug'],'lang':'en'},self.authorized()),self.request('/site/'+cv['slug']+'/',preview=True)]
        for status,_,body in requests:
            self.assertEqual(status,503)
            result=json.loads(body)
            self.assertEqual(result['code'],'frozen_preview_unavailable')
            self.assertTrue(result['recoverable'])
            self.assertNotIn(b'Available on request',body)
        self.assertEqual(self.request('/api/health')[0],200)

    def test_12_frozen_cv_symlinks_are_rejected_without_reading_target(self):
        current=self.edit.STORE.read()['site']
        cv=next(page for page in current['pages'] if page['type']=='cv')
        directory=self.root/cv['slug']
        with tempfile.TemporaryDirectory(prefix='untrusted-frozen-fixture-') as outside:
            external=Path(outside)/'index.html';external.write_text('symlink target must not be returned')
            for parent_link in (False,True):
                if parent_link: directory.symlink_to(outside,target_is_directory=True)
                else:
                    directory.mkdir();(directory/'index.html').symlink_to(external)
                try:
                    status,_,body=self.request('/api/preview','POST',{'site':current,'slug':cv['slug'],'lang':'en'},self.authorized())
                    self.assertEqual(status,503)
                    self.assertNotIn(b'symlink target must not be returned',body)
                    self.assertEqual(self.request('/site/'+cv['slug']+'/',preview=True)[0],503)
                finally:
                    if parent_link: directory.unlink()
                    else: (directory/'index.html').unlink();directory.rmdir()

if __name__=='__main__': unittest.main()
