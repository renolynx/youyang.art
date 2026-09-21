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
PREVIEW_PORT=int(os.environ.get('EDIT_PREVIEW_PORT',8767))
PREVIEW_ORIGIN=f'http://127.0.0.1:{PREVIEW_PORT}'
TOKEN=secrets.token_urlsafe(32)
UI=Path(__file__).resolve().parent/'desk'
ASSET_EXTENSIONS={'.css','.js','.mjs','.png','.jpg','.jpeg','.webp','.gif','.svg','.ico','.woff','.woff2','.ttf','.otf','.mp4','.webm','.mp3','.ogg','.wav'}

def broker_url(value):
    """Only a configured, fixed login bridge; never a request-controlled proxy."""
    if not value: return ''
    parsed=urlsplit(value)
    local=parsed.hostname in ('127.0.0.1','localhost','[::1]','::1')
    if (parsed.scheme!='https' and not (parsed.scheme=='http' and local)) or not parsed.hostname or parsed.username or parsed.password or parsed.query or parsed.fragment or parsed.path!='/cms/connect':
        raise ValueError('YOUYANG_BROKER_URL 必须是受信任站点的 /cms/connect 完整地址')
    # Accessing .port also rejects malformed port declarations.
    parsed.port
    return value

class PreviewSnapshots:
    """Short-lived rendered documents, never tokens or writable content records."""
    def __init__(self): self.lock=threading.Lock();self.items={}
    def put(self,html):
        content=html if isinstance(html,bytes) else html.encode()
        if len(content)>2*1024*1024: raise ValueError('预览页面太大，请缩短单页内容')
        with self.lock:
            self._expire()
            while self.items and (len(self.items)>=24 or sum(len(item[1]) for item in self.items.values())+len(content)>8*1024*1024): self.items.pop(next(iter(self.items)))
            key=secrets.token_urlsafe(24);self.items[key]=(time.monotonic()+300,content)
            return PREVIEW_ORIGIN+'/draft/'+key
    def _expire(self):
        now=time.monotonic()
        for key in list(self.items):
            if self.items[key][0]<=now: del self.items[key]
    def get(self,key):
        with self.lock:
            self._expire()
            item=self.items.get(key)
            return item[1] if item else None

SNAPSHOTS=PreviewSnapshots()

class PreviewUnavailable(ValueError):
    """A missing or unsafe frozen page is recoverable, never replacement content."""

def frozen_preview(route):
    relative=Path(route)/'index.html'
    if relative.is_absolute() or any(part in ('.','..') for part in relative.parts):
        raise PreviewUnavailable('冻结简历的页面地址无效。请恢复原有冻结页面后刷新预览。')
    candidate=ROOT
    for part in relative.parts:
        candidate=candidate/part
        if candidate.is_symlink():
            raise PreviewUnavailable('冻结简历不能来自符号链接。请恢复原有冻结页面后刷新预览。')
    if not candidate.resolve().is_relative_to(ROOT) or not candidate.is_file():
        raise PreviewUnavailable('此环境缺少已冻结的简历页面。请恢复原有冻结页面后刷新预览；不会生成替代正文。')
    return candidate.read_bytes()

def public_asset(path):
    """Only renderer asset subtrees; no directory listing, HTML, maps or source."""
    if not path.startswith(('/media/','/assets/')): return None
    parts=Path(path.lstrip('/')).parts
    if any(part.startswith('.') for part in parts): return None
    candidate=(ROOT/path.lstrip('/')).resolve()
    allowed=(ROOT/parts[0]).resolve()
    if not candidate.is_relative_to(allowed) or candidate.suffix.lower() not in ASSET_EXTENSIONS: return None
    return candidate

def preview(data,slug,lang):
    validate(data)
    spec=importlib.util.spec_from_file_location('preview_'+secrets.token_hex(8),ROOT/'_src/build.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    module.SITE=data;module.S=data['site'];module.PAGES=data['pages'];module.BY_SLUG={p['slug']:p for p in data['pages']};module.LANG=lang
    page=module.BY_SLUG.get(slug)
    if not page: raise ValueError('找不到这一页')
    if lang=='zh': page={**page,**page.get('zh',{})}
    route=module.route(slug,lang);depth=len(route.strip('/').split('/')) if route else 0
    if page.get('type')=='cv' and not (module.CV_SOURCE.is_file() and module.CV_PASSWORD.is_file()):
        return {'content':frozen_preview(route),'frozen':True,'route':route}
    html=module.render(page,depth,motion_preview=True).replace('<head>','<head><base href="/site/'+route+'">',1)
    return {'content':html.encode(),'frozen':False,'route':route}

class Responses(SimpleHTTPRequestHandler):
    def log_message(self,*args): pass
    def send_bytes(self,data,ctype,code=200):
        self.send_response(code);self.send_header('Content-Type',ctype);self.send_header('Content-Length',str(len(data)));self.send_header('Cache-Control','private, no-store');self.send_header('X-Content-Type-Options','nosniff');self.send_header('Referrer-Policy','no-referrer');self.extra_headers();self.end_headers()
        if self.command!='HEAD': self.wfile.write(data)
    def extra_headers(self): pass
    def send_json(self,obj,code=200): self.send_bytes(json.dumps(obj,ensure_ascii=False).encode(),'application/json; charset=utf-8',code)
    def file(self,path):
        if not path.is_file(): self.send_error(404);return
        self.send_bytes(path.read_bytes(),mimetypes.guess_type(str(path))[0] or 'application/octet-stream')
    # SimpleHTTPRequestHandler's inherited HEAD would serve the working directory.
    def do_HEAD(self): self.do_GET()

class PreviewH(Responses):
    def extra_headers(self):
        self.send_header('Content-Security-Policy',"frame-ancestors http://127.0.0.1:%s http://localhost:%s; object-src 'none'; form-action 'none'; connect-src 'self'; base-uri 'self'"%(PORT,PORT))
        self.send_header('Cross-Origin-Resource-Policy','same-origin')
    def do_GET(self):
        if self.headers.get('Host')!=f'127.0.0.1:{self.server.server_port}': return self.send_error(403)
        p=unquote(urlsplit(self.path).path)
        try:
            if re.fullmatch(r'/draft/[A-Za-z0-9_-]{32}',p):
                content=SNAPSHOTS.get(p.rsplit('/',1)[1])
                if content is None: return self.send_bytes('预览已过期。请回内容台点击“刷新预览”。'.encode(),'text/plain; charset=utf-8',410)
                return self.send_bytes(content,'text/html; charset=utf-8')
            if p in ('/favicon.ico','/site/favicon.ico'): return self.file(ROOT/'favicon.ico')
            if p.startswith('/site/'):
                local=p[len('/site/'):]
                if local.startswith(('assets/','media/')): p='/'+local
                else:
                    # Exact known renderer routes only, including bilingual home.
                    routes={'':('home','en'),'zh/':('home','zh')}
                    for page in STORE.read()['site']['pages']:
                        slug=page['slug']
                        if slug!='home': routes[slug+'/']=(slug,'en')
                        if page.get('zh') and slug!='home': routes['zh/'+slug+'/']=(slug,'zh')
                    route=local if not local or local.endswith('/') else local+'/'
                    if route not in routes: return self.send_error(404)
                    slug,lang=routes[route]
                    document=preview(STORE.read()['site'],slug,lang)
                    return self.send_bytes(document['content'],'text/html; charset=utf-8')
            asset=public_asset(p)
            if asset: return self.file(asset)
            return self.send_error(404)
        except PreviewUnavailable as e: return self.send_json({'error':str(e),'code':'frozen_preview_unavailable','recoverable':True},503)
        except (ValueError,KeyError,TypeError) as e: return self.send_json({'error':str(e)},400)
    def do_POST(self): return self.send_json({'error':'预览入口不可写入'},405)
    def do_OPTIONS(self): return self.send_error(405)

class H(Responses):
    def extra_headers(self):
        self.send_header('Content-Security-Policy',"frame-ancestors 'none'; object-src 'none'; base-uri 'self'")
        self.send_header('Cross-Origin-Resource-Policy','same-origin')
    def trusted_request(self):
        host=self.headers.get('Host')
        if host not in (f'127.0.0.1:{self.server.server_port}',f'localhost:{self.server.server_port}'): return False
        origin=self.headers.get('Origin')
        if origin and origin!=f'http://{host}': return False
        # A preview or other site must not read token/history, even via no-cors.
        if self.headers.get('Sec-Fetch-Site') not in (None,'same-origin','none'): return False
        return True
    def do_GET(self):
        if self.headers.get('Host') not in (f'127.0.0.1:{self.server.server_port}',f'localhost:{self.server.server_port}'): return self.send_error(403)
        p=unquote(urlsplit(self.path).path)
        try:
            if p.startswith('/api/') and not self.trusted_request(): return self.send_json({'error':'Invalid origin'},403)
            if p=='/': return self.file(UI/'index.html')
            if p=='/favicon.ico': return self.file(ROOT/'favicon.ico')
            if p in ('/desk.css','/desk.js','/activity-admin.js','/activity-admin.css'): return self.file(UI/p[1:])
            if p.startswith('/design/'):
                asset=(UI/p.lstrip('/')).resolve()
                if not asset.is_relative_to((UI/'design').resolve()) or asset.suffix not in ('.css','.js','.woff2'): return self.send_error(404)
                return self.file(asset)
            if p=='/api/health': return self.send_json({'service':'youyang-desk','version':3})
            if p=='/api/activity-config':
                return self.send_json({'brokerUrl':broker_url(os.environ.get('YOUYANG_BROKER_URL','')),'cmsOrigin':f'http://{self.headers.get("Host")}'})
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
                self.send_response(302);self.send_header('Location',PREVIEW_ORIGIN+self.path);self.send_header('Cache-Control','no-store');self.end_headers();return
            asset=public_asset(p)
            if asset: return self.file(asset)
            self.send_error(404)
        except (ValueError,KeyError) as e: self.send_json({'error':str(e)},400)
    def do_POST(self):
        if not self.trusted_request(): return self.send_json({'error':'Invalid origin'},403)
        try:
            if not secrets.compare_digest(self.headers.get('X-Desk-Token',''),TOKEN): return self.send_json({'error':'请重新打开内容台'},403)
            size=int(self.headers.get('Content-Length',0))
            if size<0: return self.send_json({'error':'Invalid request size'},400)
            if size>32*1024*1024: return self.send_json({'error':'单次上传请小于 32 MB'},413)
            if self.path=='/api/upload': return self.upload()
            data=json.loads(self.rfile.read(size) or b'{}')
            if self.path=='/api/site': return self.send_json(STORE.save(data['site'],data['revision'],data['sourceRevision']))
            if self.path=='/api/reload-source': return self.send_json(STORE.reload_source(data['revision'],data.get('site')))
            if self.path=='/api/preview':
                document=preview(data['site'],data['slug'],data.get('lang','en'))
                if document['frozen']:
                    return self.send_json({'url':PREVIEW_ORIGIN+'/site/'+document['route'],'mode':'frozen','message':'正在预览现有冻结简历；本次没有重新生成简历正文。'})
                return self.send_json({'url':SNAPSHOTS.put(document['content']),'mode':'draft','expiresIn':300})
            if self.path=='/api/prepare': return self.send_json(STORE.prepare(data['revision']))
            if self.path=='/api/publish': return self.send_json(STORE.release(data['revision']))
            self.send_error(404)
        except PreviewUnavailable as e: self.send_json({'error':str(e),'code':'frozen_preview_unavailable','recoverable':True},503)
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
    PORT=srv.server_port
    preview_srv=ThreadingHTTPServer(('127.0.0.1',PREVIEW_PORT),PreviewH)
    PREVIEW_ORIGIN=f'http://127.0.0.1:{preview_srv.server_port}'
    threading.Thread(target=preview_srv.serve_forever,daemon=True).start()
    print(f'youyang.art 内容台 → http://127.0.0.1:{PORT}/',flush=True)
    if '--no-open' not in sys.argv: webbrowser.open(f'http://127.0.0.1:{PORT}/')
    try: srv.serve_forever()
    except KeyboardInterrupt: pass
    finally: preview_srv.shutdown();preview_srv.server_close();srv.server_close()
