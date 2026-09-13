#!/usr/bin/env python3
"""Local content library, draft editor and verified publisher. Python 3 + Pillow."""
import cgi
import importlib.util
import json
import mimetypes
import os
from pathlib import Path
import re
import secrets
import sys
import threading
import time
from urllib.parse import unquote, urlsplit
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
import webbrowser
import urllib.request

ROOT=Path(os.environ.get('YOUYANG_ROOT',Path(__file__).resolve().parent.parent)).resolve()
sys.path.insert(0,str(Path(__file__).resolve().parent))
import optimize
from content_model import validate
from desk_store import Store, Conflict
optimize.ROOT=ROOT;optimize.OUT=ROOT/'media';optimize.MANIFEST=ROOT/'_src/media.json'
STORE=Store(ROOT)
PORT=int(os.environ.get('EDIT_PORT',8766))
TOKEN=secrets.token_urlsafe(32)
UI=Path(__file__).resolve().parent/'desk'

def preview(data,slug,lang):
    validate(data)
    spec=importlib.util.spec_from_file_location('preview_'+secrets.token_hex(8),ROOT/'_src/build.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    module.SITE=data;module.S=data['site'];module.PAGES=data['pages'];module.BY_SLUG={p['slug']:p for p in data['pages']};module.LANG=lang
    page=module.BY_SLUG.get(slug)
    if not page: raise ValueError('找不到这一页')
    if lang=='zh': page={**page,**page.get('zh',{})}
    route=module.route(slug,lang);depth=len(route.strip('/').split('/')) if route else 0
    return module.render(page,depth).replace('<head>','<head><base href="/site/'+route+'">',1)

class H(SimpleHTTPRequestHandler):
    def log_message(self,*args): pass
    def send_bytes(self,data,ctype,code=200):
        self.send_response(code);self.send_header('Content-Type',ctype);self.send_header('Content-Length',str(len(data)));self.send_header('Cache-Control','no-store');self.send_header('X-Content-Type-Options','nosniff');self.end_headers();self.wfile.write(data)
    def send_json(self,obj,code=200): self.send_bytes(json.dumps(obj,ensure_ascii=False).encode(),'application/json; charset=utf-8',code)
    def file(self,path):
        if not path.is_file(): self.send_error(404);return
        self.send_bytes(path.read_bytes(),mimetypes.guess_type(str(path))[0] or 'application/octet-stream')
    def do_GET(self):
        if self.headers.get('Host') not in (f'127.0.0.1:{PORT}',f'localhost:{PORT}'): return self.send_error(403)
        p=unquote(urlsplit(self.path).path)
        try:
            if p=='/': return self.file(UI/'index.html')
            if p in ('/favicon.ico','/site/favicon.ico'): return self.file(ROOT/'favicon.ico')
            if p in ('/desk.css','/desk.js'): return self.file(UI/p[1:])
            if p=='/api/health': return self.send_json({'service':'youyang-desk','version':2,'root':str(ROOT)})
            if p=='/api/site': return self.send_json({**STORE.read(),'media':optimize.load_manifest(),'token':TOKEN,'published':json.loads(STORE.source.read_text())})
            if p=='/api/history': return self.send_json(STORE.history())
            if re.fullmatch(r'/api/history/[0-9]+',p): return self.file(STORE.private/'history'/(p.rsplit('/',1)[1]+'.json'))
            if p=='/api/live':
                f=STORE.private/'release.json'
                release=json.loads(f.read_text()) if f.exists() else {'state':'none'}
                if release.get('revision'):
                    try:
                        url=json.loads(STORE.source.read_text())['site']['url'].rstrip('/')+'/release.json?t='+str(time.time())
                        with urllib.request.urlopen(url,timeout=8) as response: live=json.load(response)
                        if live.get('revision')==release['revision']:
                            release['state']='live'
                            from desk_store import atomic, encoded
                            atomic(f,encoded(release))
                    except Exception: pass
                return self.send_json(release)
            if p=='/api/release':
                f=STORE.private/'release.json';return self.send_json(json.loads(f.read_text()) if f.exists() else {'state':'none'})
            if p.startswith('/site/'):
                local=p[len('/site/'):]
                if not local.startswith(('assets/','media/')):
                    bits=local.strip('/').split('/');lang='zh' if bits[0]=='zh' else 'en';slug=(bits[1] if len(bits)>1 else 'home') if lang=='zh' else (bits[0] or 'home')
                    return self.send_bytes(preview(STORE.read()['site'],slug,lang).encode(),'text/html; charset=utf-8')
                p='/'+local
            if p.startswith(('/media/','/assets/')):
                f=(ROOT/p.lstrip('/')).resolve()
                if not any(f.is_relative_to((ROOT/folder).resolve()) for folder in ('media','assets')): return self.send_error(403)
                return self.file(f)
            self.send_error(404)
        except (ValueError,KeyError) as e: self.send_json({'error':str(e)},400)
    def do_POST(self):
        if self.headers.get('Host') not in (f'127.0.0.1:{PORT}',f'localhost:{PORT}'): return self.send_error(403)
        try:
            origin=self.headers.get('Origin')
            if origin and origin!=f'http://{self.headers.get("Host")}': return self.send_json({'error':'Invalid origin'},403)
            if not secrets.compare_digest(self.headers.get('X-Desk-Token',''),TOKEN): return self.send_json({'error':'请重新打开内容台'},403)
            size=int(self.headers.get('Content-Length',0))
            if size>32*1024*1024: return self.send_json({'error':'单次上传请小于 32 MB'},413)
            if self.path=='/api/upload': return self.upload()
            data=json.loads(self.rfile.read(size) or b'{}')
            if self.path=='/api/site': return self.send_json(STORE.save(data['site'],data['revision'],data['sourceRevision']))
            if self.path=='/api/reload-source': return self.send_json(STORE.reload_source(data['revision'],data.get('site')))
            if self.path=='/api/preview': return self.send_json({'html':preview(data['site'],data['slug'],data.get('lang','en'))})
            if self.path=='/api/prepare': return self.send_json(STORE.prepare(data['revision']))
            if self.path=='/api/publish': return self.send_json(STORE.release(data['revision']))
            self.send_error(404)
        except Conflict as e: self.send_json({'error':str(e)},409)
        except (ValueError,KeyError,TypeError) as e: self.send_json({'error':str(e)},400)
        except Exception as e: self.send_json({'error':str(e)},500)
    def upload(self):
        form=cgi.FieldStorage(fp=self.rfile,headers=self.headers,environ={'REQUEST_METHOD':'POST','CONTENT_TYPE':self.headers['Content-Type']})
        items=form['files'] if isinstance(form['files'],list) else [form['files']]
        with STORE.lock:
            manifest=optimize.load_manifest();added=[]
            folder=ROOT/'_originals-new/uploads';folder.mkdir(parents=True,exist_ok=True)
            for it in items:
                if not it.filename: continue
                suffix=Path(it.filename).suffix.lower()
                if suffix not in optimize.EXT: raise ValueError('请选择 JPG、PNG、GIF 或 WebP 图片')
                stem=re.sub(r'[^A-Za-z0-9一-鿿_-]+','-',Path(it.filename).stem).strip('-') or 'photo'
                name=stem+'-'+secrets.token_hex(4)+suffix
                dst=folder/name;dst.write_bytes(it.file.read())
                key,entry=optimize.optimize_one(dst,manifest)
                added.append({'ref':'media/'+name,'stem':key,**entry})
            optimize.save_manifest(manifest)
        self.send_json({'added':added})

if __name__=='__main__':
    srv=ThreadingHTTPServer(('127.0.0.1',PORT),H)
    print(f'youyang.art 内容台 → http://127.0.0.1:{PORT}/',flush=True)
    if '--no-open' not in sys.argv: webbrowser.open(f'http://127.0.0.1:{PORT}/')
    try: srv.serve_forever()
    except KeyboardInterrupt: pass
