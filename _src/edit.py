#!/usr/bin/env python3
"""Local content editor for youyang.art — photos in, words edited, site rebuilt, pushed.

    python3 _src/edit.py            # opens http://127.0.0.1:8766

A static site has no server to receive uploads, so this runs on your Mac:
drop photos → they are optimised into media/ and written into _src/content/site.json →
"保存并重建" runs build.py + verify.py → "发布" commits and pushes to GitHub Pages.
Only Python 3 + Pillow are needed (the same as build.py / optimize.py).
"""
import cgi, json, os, pathlib, subprocess, sys, time, webbrowser, mimetypes, re
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / '_src'))
import optimize  # noqa: E402

SITE = ROOT / '_src/content/site.json'
UPLOADS = ROOT / '_originals-new/uploads'
DS = pathlib.Path('/Users/a1-6/Documents/2026 野山道场/项目/野山道场/设计系统')
PORT = int(os.environ.get("EDIT_PORT", 8766))

def run(cmd):
    r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    return r.returncode, (r.stdout + r.stderr).strip()

def safe_name(name):
    stem = re.sub(r'[^A-Za-z0-9一-鿿._-]+', '-', pathlib.Path(name).stem).strip('-') or 'photo'
    return stem + pathlib.Path(name).suffix.lower()

class H(SimpleHTTPRequestHandler):
    def log_message(self, *a): pass

    def send_json(self, obj, code=200):
        body = json.dumps(obj, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers(); self.wfile.write(body)

    def send_file(self, path, ctype=None):
        path = pathlib.Path(path)
        if not path.is_file():
            self.send_error(404); return
        data = path.read_bytes()
        self.send_response(200)
        self.send_header('Content-Type', ctype or mimetypes.guess_type(str(path))[0] or 'application/octet-stream')
        self.send_header('Content-Length', str(len(data)))
        self.send_header('Cache-Control', 'no-store')
        self.end_headers(); self.wfile.write(data)

    def do_GET(self):
        p = self.path.split('?')[0]
        if p == '/':
            self.send_response(200); self.send_header('Content-Type', 'text/html; charset=utf-8'); self.end_headers()
            self.wfile.write(UI.encode()); return
        if p == '/api/site':
            self.send_json({'site': json.loads(SITE.read_text()), 'media': optimize.load_manifest()}); return
        if p == '/api/health':
            self.send_json({'service': 'youyang-desk', 'root': str(ROOT)}); return
        if p == '/ds/theme.css':
            f = DS / 'theme.css'
            if f.exists():
                css = f.read_text().replace("url('assets/Mluvka.woff2')", "url('/ds/Mluvka.woff2')")
                self.send_response(200); self.send_header('Content-Type', 'text/css'); self.end_headers(); self.wfile.write(css.encode())
            else:
                self.send_response(200); self.send_header('Content-Type', 'text/css'); self.end_headers(); self.wfile.write(b'/* design system not found on this machine */')
            return
        if p == '/ds/Mluvka.woff2':
            self.send_file(DS / 'assets/Mluvka.woff2', 'font/woff2'); return
        # everything else: the built site, for thumbnails and preview
        rel = p.lstrip('/')
        target = ROOT / rel
        if target.is_dir(): target = target / 'index.html'
        self.send_file(target)

    def do_POST(self):
        p = self.path.split('?')[0]
        if p == '/api/site':
            n = int(self.headers.get('Content-Length', 0))
            data = json.loads(self.rfile.read(n))
            SITE.write_text(json.dumps(data, ensure_ascii=False, indent=1))
            c1, o1 = run([sys.executable, '_src/build.py'])
            c2, o2 = run([sys.executable, '_src/verify.py'])
            self.send_json({'ok': c1 == 0 and c2 == 0, 'build': o1.splitlines()[0] if o1 else '', 'verify': o2.splitlines()[-2:] if o2 else []})
            return
        if p == '/api/upload':
            form = cgi.FieldStorage(fp=self.rfile, headers=self.headers,
                                    environ={'REQUEST_METHOD': 'POST', 'CONTENT_TYPE': self.headers['Content-Type']})
            slug = safe_name(form.getfirst('slug', 'misc')).rsplit('.', 1)[0]
            folder = UPLOADS / slug; folder.mkdir(parents=True, exist_ok=True)
            items = form['files'] if isinstance(form['files'], list) else [form['files']]
            manifest = optimize.load_manifest(); added = []
            for it in items:
                if not it.filename: continue
                name = safe_name(it.filename)
                dst = folder / name
                i = 1
                while dst.exists() and dst.stem in manifest:
                    dst = folder / ('%s-%d%s' % (pathlib.Path(name).stem, i, pathlib.Path(name).suffix)); i += 1
                dst.write_bytes(it.file.read())
                stem, e = optimize.optimize_one(dst, manifest)
                added.append({'ref': 'media/' + dst.name, 'stem': stem, **e})
            optimize.save_manifest(manifest)
            self.send_json({'added': added}); return
        if p == '/api/publish':
            n = int(self.headers.get('Content-Length', 0))
            msg = (json.loads(self.rfile.read(n) or b'{}').get('message') or 'Content update').strip()
            steps = []
            for cmd in (['git', 'add', '-A', '--', '.', ':!_src/content/cv.html', ':!_src/cv-password.txt'],
                        ['git', 'commit', '-m', msg],
                        ['git', 'push']):
                c, o = run(cmd); steps.append({'cmd': ' '.join(cmd[:2]), 'code': c, 'out': o[-800:]})
                if c != 0 and cmd[1] != 'commit': break
            self.send_json({'steps': steps}); return
        self.send_error(404)

UI = r'''<!doctype html><html lang="zh-Hans"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>youyang.art · 内容台</title>
<link rel="stylesheet" href="/ds/theme.css">
<style>
:root{
  --bg:var(--ds-primitive-color-neutral-950,#111);--panel:var(--ds-primitive-color-neutral-850,#212121);--raised:var(--ds-primitive-color-neutral-800,#2a2a2a);
  --line:var(--ds-primitive-color-neutral-700,#4a4a4a);--text:var(--ds-primitive-color-neutral-50,#f5f5f5);--muted:var(--ds-primitive-color-neutral-400,#a3a3a3);
  --accent:var(--ds-primitive-color-sage-200,#d2dcc7);--accent-ink:var(--ds-primitive-color-sage-800,#32442a);--accent-hi:var(--ds-primitive-color-sage-100,#e5ecdf);
  --ok:var(--ds-primitive-color-green-200,#b9e2c1);--bad:var(--ds-primitive-color-red-200,#ffc5bd);
  --r-card:14px;--r-btn:8px;--r-input:8px;--font:Mluvka,"PingFang SC","Hiragino Sans GB",system-ui,sans-serif;
}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--text);font:400 14px/1.6 var(--font);}
a{color:var(--accent)}
.top{position:sticky;top:0;z-index:5;display:flex;align-items:center;gap:12px;padding:12px 20px;background:var(--panel);border-bottom:1px solid var(--line)}
.top h1{font:500 16px/1.4 var(--font);margin:0 auto 0 0}
.top .status{color:var(--muted);font-size:13px;max-width:44vw;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
button{font:500 14px/1.4 var(--font);padding:8px 14px;border-radius:var(--r-btn);border:1px solid var(--line);background:var(--raised);color:var(--text);cursor:pointer}
button:hover{border-color:var(--accent)}
button.primary{background:var(--accent);color:var(--accent-ink);border-color:var(--accent)}
button.primary:hover{background:var(--accent-hi)}
button.small{padding:4px 10px;font-size:12px}
button.danger:hover{border-color:var(--bad);color:var(--bad)}
button[disabled]{opacity:.5;cursor:progress}
.wrap{display:grid;grid-template-columns:260px 1fr;min-height:calc(100vh - 57px)}
.side{border-right:1px solid var(--line);padding:16px 12px;background:var(--panel)}
.side h2{font:500 12px/1.4 var(--font);letter-spacing:.08em;text-transform:uppercase;color:var(--muted);margin:14px 8px 6px}
.side a.page{display:flex;justify-content:space-between;gap:8px;padding:7px 10px;border-radius:var(--r-btn);color:var(--text);text-decoration:none;font-size:13px}
.side a.page:hover{background:var(--raised)}
.side a.page.on{background:var(--accent);color:var(--accent-ink)}
.side a.page small{color:inherit;opacity:.6}
.main{padding:24px 28px 80px;max-width:1040px}
.main h2{font:500 22px/1.3 var(--font);margin:0 0 4px}
.main .hint{color:var(--muted);margin:0 0 20px;font-size:13px}
.card{background:var(--panel);border:1px solid var(--line);border-radius:var(--r-card);padding:16px 18px;margin:0 0 14px}
.card header{display:flex;align-items:center;gap:10px;margin-bottom:10px}
.card header .kind{font-size:12px;letter-spacing:.06em;text-transform:uppercase;color:var(--muted);flex:1}
label.f{display:block;margin:8px 0}
label.f span{display:block;font-size:12px;color:var(--muted);margin-bottom:3px}
input[type=text],textarea{width:100%;font:400 14px/1.5 var(--font);padding:8px 10px;border-radius:var(--r-input);border:1px solid var(--line);background:var(--bg);color:var(--text)}
textarea{min-height:76px;resize:vertical}
textarea.tall{min-height:140px}
input:focus,textarea:focus{outline:2px solid var(--ds-primitive-color-focus-300,#cabaff);outline-offset:1px;border-color:transparent}
.two{display:grid;grid-template-columns:1fr 1fr;gap:0 14px}
.three{display:grid;grid-template-columns:2fr 1fr 2fr;gap:0 14px}
.drop{display:flex;flex-direction:column;align-items:center;justify-content:center;min-height:96px;padding:14px;border:1px dashed var(--muted);border-radius:var(--r-card);color:var(--text);cursor:pointer;text-align:center;margin:10px 0}
.drop small{color:var(--muted)}
.drop.over{border-color:var(--accent);background:rgba(210,220,199,.08)}
.drop input{display:none}
.thumbs{display:flex;flex-wrap:wrap;gap:10px;margin:8px 0}
.thumb{width:150px;background:var(--raised);border-radius:var(--r-btn);overflow:hidden;position:relative}
.thumb img{display:block;width:100%;height:100px;object-fit:cover}
.thumb .t{padding:6px 8px;font-size:11px;color:var(--muted);word-break:break-all}
.thumb button{position:absolute;top:6px;right:6px}
.thumb.wide{width:100%;max-width:420px}
.thumb.wide img{height:180px}
.item{border-top:1px solid var(--line);padding:10px 0 4px;display:grid;grid-template-columns:150px 1fr;gap:14px}
.item .thumb{width:150px}
.rowbtns{display:flex;gap:8px;flex-wrap:wrap;margin-top:8px}
.add{display:flex;gap:10px;flex-wrap:wrap;margin:18px 0}
.log{white-space:pre-wrap;font:12px/1.5 Menlo,monospace;background:var(--bg);border:1px solid var(--line);border-radius:var(--r-btn);padding:10px 12px;color:var(--muted);max-height:220px;overflow:auto}
.ok{color:var(--ok)} .bad{color:var(--bad)}
.tag{display:inline-block;font-size:11px;padding:1px 8px;border-radius:999px;background:var(--raised);color:var(--muted);margin-left:6px}
dialog{background:var(--panel);color:var(--text);border:1px solid var(--line);border-radius:var(--r-card);padding:20px 22px;max-width:560px;width:92vw}
dialog::backdrop{background:rgba(0,0,0,.6)}
</style></head><body>
<div class="top"><h1>youyang.art · 内容台 <span class="tag" id="dirty">已保存</span></h1>
<span class="status" id="status">读取中…</span>
<a id="preview" href="/" target="_blank"><button>预览</button></a>
<button id="save" class="primary">保存并重建</button>
<button id="publish">发布到 GitHub</button></div>
<div class="wrap"><nav class="side" id="side"></nav><main class="main" id="main"></main></div>
<dialog id="dlg"><h3 id="dlg-title" style="margin:0 0 8px;font-weight:500"></h3><div class="log" id="dlg-log"></div><div class="rowbtns" style="justify-content:flex-end"><button id="dlg-close">关闭</button></div></dialog>
<script>
'use strict';
let DATA=null, MEDIA={}, sel=null, dirty=false;
const $=s=>document.querySelector(s), esc=s=>String(s??'').replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const stem=ref=>(ref||'').split('/').pop().replace(/\.[^.]+$/,'');
const thumbUrl=ref=>{const m=MEDIA[stem(ref)];return m?'/'+m.src:''};
const KIND={text:'文字',section:'段落',project_grid:'作品卡片',link_list:'链接列表',image:'单张照片',grid:'照片组',embed:'视频嵌入',video:'视频',columns:'两栏（旧站版式）',social_icons:'社交图标',spacer:'留白',button:'按钮'};
function setDirty(v){dirty=v;$('#dirty').textContent=v?'有未保存的改动':'已保存';}
function status(s,cls){const el=$('#status');el.textContent=s;el.className='status '+(cls||'');}
async function load(){const r=await fetch('/api/site');const j=await r.json();DATA=j.site;MEDIA=j.media;renderSide();const first=location.hash.slice(1)||'home';select(first);status('已读取 '+DATA.pages.length+' 页');}
function entries(){const out=[];for(const p of DATA.pages){out.push({key:p.slug,page:p,label:p.title||p.slug,lang:'en'});if(p.zh)out.push({key:p.slug+'@zh',page:p.zh,label:(p.zh.title||p.title)+'（中文）',lang:'zh',parent:p});}return out;}
function renderSide(){const groups={editorial:'主页面',project:'作品与项目',gallery:'旧站画廊',page:'存档',cv:'简历'};const side=$('#side');side.innerHTML='';const by={};for(const e of entries()){const t=e.parent?e.parent.type:e.page.type;(by[t]=by[t]||[]).push(e);}
for(const t of Object.keys(groups)){if(!by[t])continue;side.insertAdjacentHTML('beforeend','<h2>'+groups[t]+'</h2>');for(const e of by[t]){const n=countImgs(e.page);side.insertAdjacentHTML('beforeend','<a class="page'+(sel===e.key?' on':'')+'" href="#'+e.key+'" data-key="'+e.key+'">'+esc(e.label)+'<small>'+(n?n+' 图':'无图')+'</small></a>');}}
side.querySelectorAll('a.page').forEach(a=>a.onclick=ev=>{ev.preventDefault();select(a.dataset.key)});}
function countImgs(p){let n=0;const walk=b=>{if(!b)return;if(b.image||b.src||b.cover)n++;(b.items||[]).forEach(walk);(b.blocks||[]).forEach(walk);(b.cols||[]).forEach(c=>(c.blocks||[]).forEach(walk));};if(p.hero)walk(p.hero);(p.blocks||[]).forEach(walk);(p.items||[]).forEach(walk);return n;}
function select(key){sel=key;location.hash=key;renderSide();const e=entries().find(x=>x.key===key);if(!e){$('#main').innerHTML='<p>没有这一页</p>';return;}renderPage(e);}
function field(label,path,val,tall){return '<label class="f"><span>'+esc(label)+'</span>'+(tall?'<textarea class="'+(tall==='tall'?'tall':'')+'" data-path="'+esc(path)+'">'+esc(val)+'</textarea>':'<input type="text" data-path="'+esc(path)+'" value="'+esc(val)+'">')+'</label>';}
function get(obj,path){return path.split('.').reduce((o,k)=>o==null?undefined:o[/^\d+$/.test(k)?+k:k],obj);}
function set(obj,path,v){const ks=path.split('.');let o=obj;for(let i=0;i<ks.length-1;i++){const k=/^\d+$/.test(ks[i])?+ks[i]:ks[i];if(o[k]==null)o[k]={};o=o[k];}o[ks[ks.length-1]]=v;}
function dropZone(action,multi,hint){return '<label class="drop" data-action="'+esc(action)+'">'+(multi?'拖入或选择照片':'拖入或选择一张照片')+'<input type="file" accept="image/*" '+(multi?'multiple':'')+'><small>'+(hint||'JPG / PNG / WebP · 自动压成 WebP，最长边 1800')+'</small></label>';}
function imgField(base,keySrc,keyCap,keyAlt,capLabel){const src=get(cur(),base+'.'+keySrc);let h='';if(src)h+='<div class="thumb wide"><img src="'+thumbUrl(src)+'" alt=""><button class="small danger" data-clear="'+esc(base+'.'+keySrc)+'">移除</button><div class="t">'+esc(src)+'</div></div>';h+=dropZone('set:'+base+'.'+keySrc,false);if(keyCap)h+=field(capLabel||'图片说明',base+'.'+keyCap,get(cur(),base+'.'+keyCap)||'',true);if(keyAlt)h+=field('替代文字（给读屏器与搜索引擎）',base+'.'+keyAlt,get(cur(),base+'.'+keyAlt)||'');return h;}
let CUR=null;function cur(){return CUR.page;}
function renderPage(e){CUR=e;const p=e.page;let h='<h2>'+esc(e.label)+' <span class="tag">'+(e.parent?e.parent.type:p.type)+' · /'+(e.lang==='zh'?'zh/':'')+(e.parent?e.parent.slug:p.slug)+'/</span></h2>';
h+='<p class="hint">改完点右上「保存并重建」；照片放进去就直接生效。文字框里可以写 HTML（&lt;p&gt;、&lt;a&gt;、&lt;strong&gt;）。</p>';
if(p.type==='cv'){h+='<div class="card"><header><span class="kind">简历</span></header><p>简历正文在 <code>_src/content/cv.html</code>（不进 git），密码在 <code>_src/cv-password.txt</code>。改完保存并重建即可重新加密。</p></div>';$('#main').innerHTML=h;return;}
h+='<div class="card"><header><span class="kind">页面信息</span></header>'+field('标题','title',p.title||'')+field('描述（搜索与分享时显示）','description',p.description||'',true)+(p.masthead!==undefined?field('大标题（masthead）','masthead',p.masthead||''):'')+'</div>';
if(p.hero){h+='<div class="card"><header><span class="kind">开篇（hero）</span></header>'+field('小标','hero.eyebrow',p.hero.eyebrow||'')+field('标题','hero.title',p.hero.title||'')+field('副题','hero.subtitle',p.hero.subtitle||'')+field('引言','hero.intro',p.hero.intro||'',true)+imgField('hero','image','imageCaption','imageAlt')+'</div>';}
(p.blocks||[]).forEach((b,i)=>{h+=blockCard(b,i)});
if(p.items&&p.type==='gallery'){h+='<div class="card"><header><span class="kind">封面列表</span></header>';p.items.forEach((it,j)=>{h+='<div class="item"><div class="thumb"><img src="'+thumbUrl(it.cover)+'" alt=""><div class="t">'+esc(it.title||'')+'</div></div><div>'+field('标题','items.'+j+'.title',it.title||'')+field('年份/说明','items.'+j+'.meta',it.meta||'')+dropZone('set:items.'+j+'.cover',false,'换封面')+'</div></div>'});h+='</div>';}
h+='<div class="add">'+(e.parent&&e.parent.type==='editorial'||p.type==='editorial'?'<button data-add="section">+ 加一段（标题 + 正文）</button><button data-add="section-image">+ 加一段带照片</button><button data-add="project_grid">+ 加一组卡片</button>':'<button data-add="text">+ 加一段文字</button><button data-add="image">+ 加一张照片</button><button data-add="grid">+ 加一组照片</button>')+'</div>';
$('#main').innerHTML=h;bind();}
function blockCard(b,i){const base='blocks.'+i;let h='<div class="card" data-block="'+i+'"><header><span class="kind">'+(KIND[b.type]||b.type)+(b.id?' <span class="tag">#'+esc(b.id)+'</span>':'')+'</span><button class="small" data-move="'+i+':-1">↑</button><button class="small" data-move="'+i+':1">↓</button><button class="small danger" data-del="'+i+'">删除</button></header>';
if(b.type==='section'){h+=field('小标（kicker）',base+'.kicker',b.kicker||'')+field('标题',base+'.title',b.title||'')+field('正文 HTML',base+'.body',b.body||'','tall');h+='<div class="two">'+(b.links||[]).map((l,j)=>field('链接文字 '+(j+1),base+'.links.'+j+'.label',l.label||'')+field('链接地址 '+(j+1),base+'.links.'+j+'.href',l.href||'')).join('')+'</div><div class="rowbtns"><button class="small" data-addlink="'+i+'">+ 链接</button></div>';h+='<p class="hint" style="margin:10px 0 0">这一段的照片（可选，放在正文旁边）</p>'+imgField(base,'image','imageCaption','imageAlt');}
else if(b.type==='text'){(b.paras||[]).forEach((q,j)=>{h+=field('段落 '+(j+1)+'（HTML）',base+'.paras.'+j+'.html',q.html||'','tall')});h+='<div class="rowbtns"><button class="small" data-addpara="'+i+'">+ 段落</button></div>';}
else if(b.type==='image'){h+=imgField(base,'src','caption','alt');h+=field('点击跳转到（可选，如 /for-the-best）',base+'.href',b.href||'');}
else if(b.type==='grid'){h+='<div class="thumbs">'+(b.items||[]).map((it,j)=>'<div class="thumb"><img src="'+thumbUrl(it.src)+'" alt=""><button class="small danger" data-rm="'+base+'.items.'+j+'">×</button><div class="t">'+esc(stem(it.src))+'</div></div>').join('')+'</div>'+dropZone('grid:'+base,true)+field('整组说明',base+'.caption',b.caption||'')+field('每行几张（留空 = 按比例自动排）',base+'.perRow',b.perRow||'');}
else if(b.type==='project_grid'){h+=field('小标（kicker）',base+'.kicker',b.kicker||'')+field('标题',base+'.title',b.title||'');(b.items||[]).forEach((it,j)=>{const ib=base+'.items.'+j;h+='<div class="item"><div>'+(it.cover?'<div class="thumb"><img src="'+thumbUrl(it.cover)+'" alt=""></div>':'<div class="thumb"><div class="t" style="height:100px">还没有封面</div></div>')+dropZone('set:'+ib+'.cover',false,'换封面')+'</div><div><div class="three">'+field('标题',ib+'.title',it.title||'')+field('年份',ib+'.meta',it.meta||'')+field('链接',ib+'.href',it.href||'')+'</div>'+field('一句话',ib+'.description',it.description||'',true)+'<div class="rowbtns"><button class="small danger" data-rm="'+ib+'">删掉这张卡</button></div></div></div>'});h+='<div class="rowbtns"><button class="small" data-additem="'+i+'">+ 卡片</button></div>';}
else if(b.type==='link_list'){h+=field('标题',base+'.title',b.title||'');(b.items||[]).forEach((it,j)=>{const ib=base+'.items.'+j;h+='<div class="item" style="grid-template-columns:1fr"><div><div class="three">'+field('标题',ib+'.title',it.title||'')+field('小字',ib+'.meta',it.meta||'')+field('链接',ib+'.href',it.href||'')+'</div>'+field('说明',ib+'.description',it.description||'',true)+'<div class="rowbtns"><button class="small danger" data-rm="'+ib+'">删掉</button></div></div></div>'});h+='<div class="rowbtns"><button class="small" data-additem="'+i+'">+ 条目</button></div>';}
else if(b.type==='embed'){h+=field('Vimeo/YouTube 播放器地址',base+'.embed',b.embed||'')+field('说明',base+'.caption',b.caption||'');}
else if(b.type==='video'){h+=field('视频文件（media/…mp4）',base+'.video',b.video||'')+field('说明',base+'.caption',b.caption||'');}
else if(b.type==='columns'){h+='<p class="hint">旧站的两栏版式，文字在这里改：</p>';(b.cols||[]).forEach((c,ci)=>(c.blocks||[]).forEach((x,xi)=>{if(x.type==='text')(x.paras||[]).forEach((q,qi)=>{h+=field('栏 '+(ci+1)+' 段落 '+(qi+1),base+'.cols.'+ci+'.blocks.'+xi+'.paras.'+qi+'.html',q.html||'','tall')});if(x.type==='image')h+='<div class="thumb"><img src="'+thumbUrl(x.src)+'" alt=""><div class="t">'+esc(stem(x.src))+'</div></div>'+field('说明',base+'.cols.'+ci+'.blocks.'+xi+'.caption',x.caption||'');}));if(b.caption!==undefined)h+=field('整块说明',base+'.caption',b.caption||'');}
else h+='<p class="hint">这种块没有可改的文字。</p>';
return h+'</div>';}
function bind(){const m=$('#main');
m.querySelectorAll('[data-path]').forEach(el=>el.oninput=()=>{let v=el.value;if(el.dataset.path.endsWith('.perRow'))v=v?+v:undefined;set(cur(),el.dataset.path,v);setDirty(true)});
m.querySelectorAll('[data-clear]').forEach(b=>b.onclick=()=>{set(cur(),b.dataset.clear,undefined);setDirty(true);renderPage(CUR)});
m.querySelectorAll('[data-rm]').forEach(b=>b.onclick=()=>{const path=b.dataset.rm,ks=path.split('.'),idx=+ks.pop();get(cur(),ks.join('.')).splice(idx,1);setDirty(true);renderPage(CUR)});
m.querySelectorAll('[data-del]').forEach(b=>b.onclick=()=>{if(!confirm('删除这一块？'))return;cur().blocks.splice(+b.dataset.del,1);setDirty(true);renderPage(CUR)});
m.querySelectorAll('[data-move]').forEach(b=>b.onclick=()=>{const [i,d]=b.dataset.move.split(':').map(Number),a=cur().blocks,j=i+d;if(j<0||j>=a.length)return;[a[i],a[j]]=[a[j],a[i]];setDirty(true);renderPage(CUR)});
m.querySelectorAll('[data-addlink]').forEach(b=>b.onclick=()=>{const bl=cur().blocks[+b.dataset.addlink];(bl.links=bl.links||[]).push({label:'',href:'/'});setDirty(true);renderPage(CUR)});
m.querySelectorAll('[data-addpara]').forEach(b=>b.onclick=()=>{const bl=cur().blocks[+b.dataset.addpara];(bl.paras=bl.paras||[]).push({html:'<span class="f-body" style="font-size:21px;font-weight:300"></span>',align:'left',lh:40});setDirty(true);renderPage(CUR)});
m.querySelectorAll('[data-additem]').forEach(b=>b.onclick=()=>{const bl=cur().blocks[+b.dataset.additem];(bl.items=bl.items||[]).push(bl.type==='project_grid'?{href:'/',title:'',meta:'',description:''}:{href:'/',title:'',meta:'',description:''});setDirty(true);renderPage(CUR)});
m.querySelectorAll('[data-add]').forEach(b=>b.onclick=()=>{const t=b.dataset.add,bl=cur().blocks=cur().blocks||[];const T={section:{type:'section',title:'',body:'<p></p>'},'section-image':{type:'section',title:'',body:'<p></p>',image:'',imageCaption:''},project_grid:{type:'project_grid',title:'',items:[]},text:{type:'text',maxw:800,width:85,paras:[{html:'<span class="f-body" style="font-size:21px;font-weight:300"></span>',align:'left',lh:40}],pt:27},image:{type:'image',pt:40,pb:20,capAlign:'left',src:'',caption:''},grid:{type:'grid',pt:41,width:100,items:[]}};bl.push(JSON.parse(JSON.stringify(T[t])));setDirty(true);renderPage(CUR);window.scrollTo(0,document.body.scrollHeight)});
m.querySelectorAll('.drop').forEach(z=>{const inp=z.querySelector('input');z.ondragover=ev=>{ev.preventDefault();z.classList.add('over')};z.ondragleave=()=>z.classList.remove('over');z.ondrop=ev=>{ev.preventDefault();z.classList.remove('over');upload(z.dataset.action,ev.dataTransfer.files)};inp.onchange=()=>upload(z.dataset.action,inp.files)});}
async function upload(action,files){if(!files.length)return;status('上传并压缩 '+files.length+' 张…');const fd=new FormData();fd.append('slug',(CUR.parent?CUR.parent.slug:cur().slug)||'misc');for(const f of files)fd.append('files',f);const r=await fetch('/api/upload',{method:'POST',body:fd});const j=await r.json();const [kind,path]=action.split(':');for(const a of j.added){MEDIA[a.stem]={src:a.src,w:a.w,h:a.h,anim:a.anim};if(kind==='set'){set(cur(),path,a.ref);if(path.endsWith('.src')||path.endsWith('.image')){/* nothing else */}}else if(kind==='grid'){const g=get(cur(),path);(g.items=g.items||[]).push({src:a.ref,w:a.w,h:a.h});}}
setDirty(true);renderPage(CUR);status('已加入 '+j.added.length+' 张（记得保存并重建）','ok');}
$('#save').onclick=async()=>{const b=$('#save');b.disabled=true;status('保存、重建、校验中…');const r=await fetch('/api/site',{method:'POST',body:JSON.stringify(DATA)});const j=await r.json();b.disabled=false;setDirty(false);MEDIA=(await (await fetch('/api/site')).json()).media;status((j.ok?'✓ ':'✗ ')+j.build+' · '+(j.verify||[]).join(' '),j.ok?'ok':'bad');if(!j.ok)showLog('重建或校验有问题',JSON.stringify(j,null,1));};
$('#publish').onclick=async()=>{if(dirty){alert('先保存并重建，再发布。');return;}const msg=prompt('提交说明（会出现在 GitHub 记录里）','Update photos and text');if(msg===null)return;const b=$('#publish');b.disabled=true;status('提交并推送…');const r=await fetch('/api/publish',{method:'POST',body:JSON.stringify({message:msg})});const j=await r.json();b.disabled=false;const bad=j.steps.some(s=>s.code!==0&&s.cmd!=='git commit');status(bad?'✗ 发布失败，看日志':'✓ 已推送，GitHub Pages 一两分钟后更新',bad?'bad':'ok');showLog('发布',j.steps.map(s=>'$ '+s.cmd+' → '+s.code+'\n'+s.out).join('\n\n'));};
function showLog(t,txt){$('#dlg-title').textContent=t;$('#dlg-log').textContent=txt;$('#dlg').showModal();}
$('#dlg-close').onclick=()=>$('#dlg').close();
window.addEventListener('beforeunload',ev=>{if(dirty){ev.preventDefault();ev.returnValue=''}});
document.addEventListener('keydown',ev=>{if((ev.metaKey||ev.ctrlKey)&&ev.key==='s'){ev.preventDefault();$('#save').click()}});
load();
</script></body></html>'''

if __name__ == '__main__':
    srv = ThreadingHTTPServer(('127.0.0.1', PORT), H)
    url = 'http://127.0.0.1:%d/' % PORT
    print('youyang.art 内容台 →', url, '(Ctrl-C 退出)')
    if '--no-open' not in sys.argv:
        webbrowser.open(url)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
