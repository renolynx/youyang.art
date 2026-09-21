"""Consumer-owned semantic inventory. HTML bytes are only extended at parsed tags.

Identity uses public route/media/action keys and semantic regions, never text,
names or sibling positions. Equal semantics deliberately share an entity; each
physical DOM mount is assigned independently by the consumer runtime.
"""
from html.parser import HTMLParser
from urllib.parse import urljoin, urlsplit
import hashlib
import json
import pathlib

SOURCE_FILES=['_src/motion_inventory.py','_src/design/motion-runtime.js','_src/build.py','_src/content_model.py','_src/sync_design.mjs','_src/prepare_design.mjs','_src/design/website.css','_src/design/website-profile.json','_src/design/website-inline.css','assets/css/site.css','assets/css/website.css','assets/css/design.css','assets/css/fonts.css','assets/js/site.js','assets/js/design.js','_src/content/site.json','_src/media.json']
CAPABILITIES={
 'navigation':(['current','target','interrupted','unmounted','restored'],['pointer','Enter','ArrowRight','ArrowLeft','pagehide','pageshow'], 'system/motion-tabs.js','control'),
 'mobile-navigation':(['closed','open','interrupted','resized','reduced'],['click','Escape','viewport-change','reduced-change'],'assets/js/site.js + assets/css/site.css','layout'),
 'mobile-icon':(['closed','open'],['owner:click','owner:Escape'],'_src/design/website.css + assets/js/site.js',None),
 'lightbox-image':(['empty','selected-image','cleared'],['zoom-click','Enter','Escape'],'assets/js/site.js',None),
 'link':(['idle','hover','focus','pressed','destination'],['pointerenter','pointerleave','focus','Enter','click'],'system/link-feedback.css + assets/css/site.css','control'),
 'card':(['visible','hover','focus-within','hidden','restored'],['pointerenter','pointerleave','focus','search','filter'],'assets/css/site.css + assets/js/site.js','control'),
 'image-effect':(['idle','hover','reversed','hidden'],['owner:pointerenter','owner:pointerleave','filter'],'assets/css/site.css','control'),
 'cover-pseudo':(['idle','hover','reversed','hidden'],['owner:pointerenter','owner:pointerleave'],'assets/css/site.css','control'),
 'field':(['empty','editing','invalid','retained'],['input','focus','blur','submit'],'assets/js/site.js + assets/css/site.css',None),
 'filter':(['selected','unselected','empty-results','restored'],['click','keyboard','popstate'],'assets/js/site.js + assets/css/site.css','control'),
 'status':(['idle','updated','hidden'],['search','filter','response'],'assets/js/site.js',None),
 'scroll':(['top','scrolling','target','interrupted'],['click','Enter','wheel','reduced-change'],'assets/js/site.js','native-scroll'),
 'lightbox':(['closed','open','focus-trapped','closed-restored'],['zoom-click','Enter','Space','Escape','Tab','backdrop-click'],'assets/js/site.js',None),
 'zoom':(['idle','focus','open','restored'],['click','Enter','Space','Escape'],'assets/js/site.js',None),
 'media':(['idle','playing','paused'],['native-media-control'],'_src/build.py + browser-media',None),
 'submit':(['idle','invalid','handoff-pending'],['submit'],'assets/js/site.js',None),
}
def digest(value): return hashlib.sha256(value.encode()).hexdigest()[:20]
def public_key(value, route):
    target=urlsplit(urljoin('https://consumer.invalid/'+route, value or ''))
    return (target.netloc if target.netloc!='consumer.invalid' else '')+target.path+('?' + target.query if target.query else '')+('#'+target.fragment if target.fragment else '')
class Node:
    def __init__(self,tag,attrs,raw,start,parent):
        self.tag=tag;self.attrs=dict(attrs);self.raw=raw;self.start=start;self.parent=parent;self.children=[]
        if parent:parent.children.append(self)
    @property
    def classes(self):return set(self.attrs.get('class','').split())
    def ancestors(self):
        node=self.parent
        while node:
            yield node;node=node.parent
    def descendants(self):
        for child in self.children:
            yield child;yield from child.descendants()
class Markup(HTMLParser):
    def __init__(self,text):
        super().__init__(convert_charrefs=False);self.text=text;self.nodes=[];self.stack=[];self.offsets=[0]
        for line in text.splitlines(True):self.offsets.append(self.offsets[-1]+len(line))
        self.feed(text)
    def handle_starttag(self,tag,attrs):
        line,col=self.getpos();node=Node(tag,attrs,self.get_starttag_text(),self.offsets[line-1]+col,self.stack[-1] if self.stack else None);self.nodes.append(node)
        if tag not in {'area','base','br','col','embed','hr','img','input','link','meta','param','source','track','wbr'}:self.stack.append(node)
    def handle_startendtag(self,tag,attrs):
        self.handle_starttag(tag,attrs)
        if self.stack and self.stack[-1].tag==tag:self.stack.pop()
    def handle_endtag(self,tag):
        for i in range(len(self.stack)-1,-1,-1):
            if self.stack[i].tag==tag:del self.stack[i:];break

def family(node):
    a=node.attrs;c=node.classes
    if 'site-nav' in c:return 'navigation'
    if 'nav-toggle' in c:return 'mobile-navigation'
    if node.tag=='svg' and any('nav-toggle' in p.classes for p in node.ancestors()):return 'mobile-icon'
    if node.tag=='img' and any('lightbox' in p.classes for p in node.ancestors()):return 'lightbox-image'
    if 'project-card' in c or 'cover' in c and node.tag=='a':return 'card'
    if 'cover-img' in c:return 'cover-pseudo'
    if 'cover-meta' in c or node.tag=='img' and any('project-image' in p.classes for p in node.ancestors()):return 'image-effect'
    if node.tag=='svg' and any('social-row' in p.classes for p in node.ancestors()):return 'image-effect'
    if 'masthead-arrow' in c or 'to-top' in c:return 'scroll'
    if 'lightbox' in c or 'lightbox-close' in c:return 'lightbox'
    if 'zoomable' in c:return 'zoom'
    if 'data-filter' in a:return 'filter'
    if a.get('id') in {'work-count','work-empty'} or 'aria-live' in a:return 'status'
    if node.tag in {'input','select','textarea'}:return 'field'
    if node.tag in {'video','audio','iframe'}:return 'media'
    if node.tag=='button' and a.get('type')=='submit':return 'submit'
    if node.tag=='a' and 'href' in a or node.tag=='button' or 'tabindex' in a:return 'link'
    return None

def identity(node, route):
    chain=list(reversed(list(node.ancestors())))+[node];scope=[]
    for p in chain:
        if p.attrs.get('id'):scope.append('id:'+p.attrs['id'])
        elif p.tag in {'header','footer','nav'}:scope.append(p.tag)
        elif p.classes & {'hero-copy','related','social-row','project-section','editorial-section','covers','contact-form'}:scope.append('region:'+','.join(sorted(p.classes & {'hero-copy','related','social-row','project-section','editorial-section','covers','contact-form'})))
    a=node.attrs
    action=a.get('id') or a.get('name') or ('filter:'+a['data-filter'] if 'data-filter' in a else None)
    reference=a.get('href') or a.get('src')
    if not reference:
        linked=next((x for x in node.descendants() if 'href' in x.attrs),None)
        reference=linked.attrs['href'] if linked else None
    if not reference:
        linked=next((x for x in node.ancestors() if 'href' in x.attrs),None)
        reference=linked.attrs['href'] if linked else None
    semantic=action or (public_key(reference,route) if reference else ','.join(sorted(node.classes)) or node.tag)
    return '/'.join(scope)+'|'+semantic+'|'+node.tag

def annotate(text, route, preview=False):
    """Return the same authored bytes with only consumer data-motion attrs added."""
    doc=Markup(text);patches=[]
    for node in doc.nodes:
        kind=family(node)
        if not kind:continue
        key=identity(node,route);entity='preview-'+kind if preview else 'website-'+kind+'-'+digest(key)
        # Physical IDs may repeat before runtime only for equal logical entities;
        # runtime supplies per-element mount identities without row-position keys.
        attrs={'data-motion-id':entity,'data-motion-entity':entity,'data-motion-action':kind,'data-motion-business-key':digest(key),'data-motion-surface':'cms-preview' if preview else 'website','data-motion-entry':'cms-preview' if preview else 'website-'+route.replace('/index.html','').replace('index.html','root').replace('/','-')}
        if kind in {'image-effect','cover-pseudo','mobile-icon','lightbox-image'}:
            owner=next((p for p in node.ancestors() if family(p) in {'card','link','zoom','navigation','mobile-navigation','lightbox'}),None)
            if owner:attrs['data-motion-owner']='preview-'+family(owner) if preview else 'website-'+family(owner)+'-'+digest(identity(owner,route))
        extra=''.join(' '+k+'="'+v+'"' for k,v in attrs.items())
        end=node.start+len(node.raw)-(2 if node.raw.endswith('/>') else 1)
        patches.append((end,extra))
    for offset,extra in reversed(patches):text=text[:offset]+extra+text[offset:]
    return text

def inventory(text,route):
    doc=Markup(text);rows={}
    for node in doc.nodes:
        kind=family(node)
        if not kind:continue
        entity=node.attrs.get('data-motion-entity') or 'website-'+kind+'-'+digest(identity(node,route))
        states,triggers,source,duration=CAPABILITIES[kind]
        states=list(states)
        if kind in {'card','image-effect','cover-pseudo'} and route not in {'work/index.html','zh/work/index.html'}:states=[state for state in states if state not in {'hidden','restored'}]
        if kind=='field' and 'required' not in node.attrs and node.attrs.get('type') not in {'email','url','number'}:states=[state for state in states if state!='invalid']
        selector='[data-motion-entity="'+entity+'"]'
        row={'id':entity,'selector':selector,'capability':kind,'states':states,'triggers':triggers,'adoption':'_src/build.py + _src/motion_inventory.py','implementation':source,'source':source,'durationClass':duration,'scenarios':['normal','reduced','reverse','interrupt','cleanup'],'status':'pending-observation','lifecycle':{'normal':'Actual browser state and effect trajectory required','reduced':'Actual reduced branch required','cleanup':'pagehide/controller destroy; exact document/frame/mount recorded'},'expectedInstances':0}
        if kind=='navigation':row['transition']='navigation'
        if node.attrs.get('data-motion-owner'):row['owner']=node.attrs['data-motion-owner']
        if entity not in rows:rows[entity]=row
        rows[entity]['expectedInstances']+=1
        if kind=='cover-pseudo':
            pseudo={**row,'entity':entity,'id':entity+'-after','selector':selector+'::after','capability':'cover-pseudo-effect','owner':node.attrs.get('data-motion-owner',entity),'expectedInstances':rows[entity]['expectedInstances']}
            rows[pseudo['id']]=pseudo
        if kind=='scroll':
            pseudo={**row,'entity':entity,'id':entity+'-before','selector':selector+'::before','capability':'scroll-icon','states':['visible','hidden'],'triggers':['owner:scroll','owner:viewport-change'],'durationClass':None,'owner':entity,'expectedInstances':rows[entity]['expectedInstances']}
            rows[pseudo['id']]=pseudo
    geometry={'id':'website-navigation-geometry','transition':'navigation','selector':'.site-nav .ys-motion-tabs-fluid rect','capability':'navigation-geometry','states':CAPABILITIES['navigation'][0],'triggers':CAPABILITIES['navigation'][1],'adoption':'assets/js/design.js','implementation':'system/motion-tabs.js','durationClass':'control','expectedInstances':2,'runtime':True,'identity':'Actual Element WeakMap UUID; stable owner/action/business key; no DOM row index','status':'pending-observation'}
    return list(rows.values())+[geometry]

def build_catalog(root):
    import importlib.util
    spec=importlib.util.spec_from_file_location('inventory_build',root/'_src/build.py');build=importlib.util.module_from_spec(spec);spec.loader.exec_module(build)
    entries=[]
    for page in build.PAGES:
        if page['type']=='cv':continue
        variants=[(page['slug']+'/index.html','en',page,1)]
        if '/'+page['slug']==build.S['home']:variants.append(('index.html','en',page,0))
        if page.get('zh'):
            route=build.route(page['slug'],'zh')+'index.html';variants.append((route,'zh',{**page,**page['zh']},len(pathlib.Path(route).parts)-1))
        for route,lang,current,depth in variants:
            build.LANG=lang;text=build.render(current,depth)
            entries.append({'id':'website-'+route.replace('/index.html','').replace('index.html','root').replace('/','-'),'kind':'website','surface':'website','route':'/'+route.replace('index.html',''),'artifact':route,'artifactSha256':hashlib.sha256(text.encode()).hexdigest(),'sourceFiles':SOURCE_FILES,'inventory':inventory(text,route)})
    # The actual preview renderer may serve arbitrary draft content/URLs. These
    # families are finite declarations, never a fixture URL allowlist.
    preview=[]
    for kind,(states,triggers,source,duration) in CAPABILITIES.items():
        preview.append({'id':'preview-'+kind,'selector':'[data-motion-action="'+kind+'"]','entity':'preview-'+kind,'states':states,'triggers':triggers,'capability':kind,'source':source,'durationClass':duration,'adoption':'_src/edit.py:preview -> _src/build.py:render(motion_preview=True)','runtime':True,'status':'pending-observation'})
    preview.append({'id':'preview-navigation-geometry','selector':'.site-nav .ys-motion-tabs-fluid rect','entity':'preview-navigation-geometry','states':CAPABILITIES['navigation'][0],'triggers':CAPABILITIES['navigation'][1],'capability':'navigation-geometry','expectedInstances':2,'runtime':True,'status':'pending-observation'})
    for kind,pseudo in [('cover-pseudo','after'),('scroll','before')]:
        states,triggers,source,duration=CAPABILITIES[kind]
        if kind=='scroll':states,triggers,duration=['visible','hidden'],['owner:scroll','owner:viewport-change'],None
        preview.append({'id':'preview-'+kind+'-'+pseudo,'entity':'preview-'+kind,'selector':'[data-motion-entity="preview-'+kind+'"]::'+pseudo,'states':states,'triggers':triggers,'capability':kind+'-effect','source':source,'durationClass':duration,'runtime':True,'status':'pending-observation'})
    entries.append({'id':'cms-preview','surface':'cms-preview','kind':'iframe','routePrefixes':['/draft/','/site/'],'urlPattern':'isolated preview /draft/<opaque-token>/ and /site/<route>/','sourceFiles':SOURCE_FILES+['_src/edit.py'],'inventory':preview})
    native=root/'_src/design/native-motion-inventory.json'
    if native.is_file():entries.extend(json.loads(native.read_text())['entrypoints'])
    return {'schemaVersion':2,'scope':'consumer declarations; actual observation/exercise and shared C1 certification remain separate','entrypoints':entries}
if __name__=='__main__':
    root=pathlib.Path(__file__).resolve().parent.parent
    target=root/'_src/design/consumer-motion-inventory.json'
    target.write_text(json.dumps(build_catalog(root),ensure_ascii=False,indent=2)+'\n')
    print(target)
