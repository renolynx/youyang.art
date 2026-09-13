"""Local drafts and verified releases. No writes to public content until a build passes."""
import contextlib
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import threading
import time
from content_model import validate

def encoded(value): return (json.dumps(value, ensure_ascii=False, indent=1)+'\n').encode()
def digest(data): return hashlib.sha256(data).hexdigest()
def atomic(path, data):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as f:
        f.write(data); name=f.name
    os.replace(name, path)

class Conflict(ValueError): pass

class Store:
    def __init__(self, root):
        self.root=Path(root); self.source=self.root/'_src/content/site.json'
        self.private=self.root/'.desk'; self.draft=self.private/'draft.json'
        self.lock=threading.RLock()
    def source_revision(self): return digest(self.source.read_bytes())
    def read(self):
        source_revision=self.source_revision()
        if self.draft.exists():
            record=json.loads(self.draft.read_text())
            return {**record, 'revision':digest(encoded(record['site'])), 'conflict':record['sourceRevision']!=source_revision}
        site=json.loads(self.source.read_text())
        return {'site':site,'revision':digest(encoded(site)),'sourceRevision':source_revision,'conflict':False}
    def save(self, site, revision, source_revision):
        with self.lock:
            current=self.read()
            if current['conflict'] or current['revision']!=revision or self.source_revision()!=source_revision:
                raise Conflict('内容已在别处更新。当前输入已保留，请先导出草稿，再重新载入核对。')
            validate(site)
            # Existing addresses and page identities stay stable; new records may be added.
            before={p.get('id',p['slug']):p['slug'] for p in json.loads(self.source.read_text())['pages']}
            after={p.get('id',p['slug']):p['slug'] for p in site['pages']}
            if any(after.get(k)!=v for k,v in before.items()): raise ValueError('已有页面不能通过内容台删除或改地址。')
            if digest(encoded(site))!=current['revision']:
                history=self.private/'history';history.mkdir(parents=True,exist_ok=True)
                atomic(history/(str(time.time_ns())+'.json'),encoded(current))
                for old in sorted(history.glob('*.json'))[:-30]: old.unlink()
            atomic(self.draft,encoded({'site':site,'sourceRevision':source_revision,'savedAt':time.time()}))
            return self.read()
    def reload_source(self, revision, unsaved):
        with self.lock:
            current=self.read()
            if current['revision']!=revision: raise Conflict('草稿又发生变化，请重新载入。')
            history=self.private/'history';history.mkdir(parents=True,exist_ok=True)
            atomic(history/(str(time.time_ns())+'.json'),encoded(current))
            if isinstance(unsaved,dict) and 'pages' in unsaved:
                atomic(history/(str(time.time_ns())+'.json'),encoded({'site':unsaved,'sourceRevision':current['sourceRevision']}))
            if self.draft.exists(): self.draft.unlink()
            return self.read()
    def history(self):
        return [{'id':p.stem,'savedAt':p.stat().st_mtime} for p in sorted((self.private/'history').glob('*.json'),reverse=True)]
    def command(self, args, cwd=None):
        p=subprocess.run(args,cwd=cwd or self.root,capture_output=True,text=True,timeout=120)
        if p.returncode: raise RuntimeError((p.stdout+p.stderr)[-3000:] or 'Command failed')
        return p.stdout.strip()
    @contextlib.contextmanager
    def prepared(self, revision):
        current=self.read()
        if current['conflict'] or current['revision']!=revision: raise Conflict('草稿已变化，请重新检查这次更新。')
        self.private.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(prefix='build-',dir=self.private) as name:
            stage=Path(name)
            shutil.copytree(self.root/'_src',stage/'_src',ignore=shutil.ignore_patterns('__pycache__'))
            for folder in ('assets','media'): (stage/folder).symlink_to(self.root/folder,target_is_directory=True)
            if (self.root/'favicon.ico').exists(): shutil.copy(self.root/'favicon.ico',stage/'favicon.ico')
            atomic(stage/'_src/content/site.json',encoded(current['site']))
            result=self.command([sys.executable,'_src/build.py'],stage)
            proof=self.command([sys.executable,'_src/verify.py'],stage)
            paths=[line.strip() for line in result.splitlines() if line.startswith('   ')]
            paths+=['robots.txt','sitemap.xml','.nojekyll','_src/content/site.json']
            if (stage/'CNAME').exists(): paths.append('CNAME')
            atomic(stage/'release.json',encoded({'revision':revision,'builtAt':time.time()}));paths.append('release.json')
            old={p['slug']:p for p in json.loads(self.source.read_text())['pages']}
            changed=[p['title'] for p in current['site']['pages'] if old.get(p['slug'])!=p]
            yield stage,paths,{'ok':True,'revision':revision,'changed':changed,'pages':len(paths)-6,'verification':proof.splitlines()[0]}
    def prepare(self, revision):
        with self.lock, self.prepared(revision) as (_,__,result): return result
    def release(self, revision, push=True):
        with self.lock, self.prepared(revision) as (stage,paths,result):
            # Preserve originals until every generated file is installed successfully.
            previous={p:(self.root/p).read_bytes() if (self.root/p).exists() else None for p in paths}
            try:
                for p in paths: atomic(self.root/p,(stage/p).read_bytes())
            except Exception:
                for p,data in previous.items():
                    if data is None: (self.root/p).unlink(missing_ok=True)
                    else: atomic(self.root/p,data)
                raise
            current=self.read();current['sourceRevision']=self.source_revision()
            atomic(self.draft,encoded({k:current[k] for k in ('site','sourceRevision','savedAt') if k in current}))
            if not push: return {**result,'state':'local'}
            # Exact content/build/media paths only. Never git add -A or include private inputs.
            manifest=json.loads((self.root/'_src/media.json').read_text())
            paths+=['_src/media.json']+[m['src'] for m in manifest.values() if (self.root/m['src']).is_file()]
            paths=sorted(set(paths))
            self.command(['git','add','--']+paths)
            diff=subprocess.run(['git','diff','--cached','--quiet','--']+paths,cwd=self.root)
            if diff.returncode:
                self.command(['git','-c','user.name=Dio','-c','user.email=dio@agent.local','commit','--only','-m','Update website content from content desk','--']+paths)
            commit=self.command(['git','rev-parse','HEAD'])
            atomic(self.private/'release.json',encoded({**result,'commit':commit,'state':'push-pending'}))
            self.command(['git','push'])
            result.update(commit=commit,state='pushed')
            atomic(self.private/'release.json',encoded(result))
            return result
