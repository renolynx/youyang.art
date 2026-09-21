'use strict';
function field(label,path,val,tall){return '<label class="f"'+nativeFieldAttrs(path,true)+'><span>'+esc(label)+'</span>'+(tall?'<textarea'+nativeFieldAttrs(path)+' class="'+(tall==='tall'?'tall':'')+'" data-path="'+esc(path)+'">'+esc(val)+'</textarea>':'<input'+nativeFieldAttrs(path)+' type="text" data-path="'+esc(path)+'" value="'+esc(val)+'">')+'</label>';}
function get(obj,path){return path.split('.').reduce((o,k)=>o==null?undefined:o[/^\d+$/.test(k)?+k:k],obj);}
function set(obj,path,v){const ks=path.split('.');let o=obj;for(let i=0;i<ks.length-1;i++){const k=/^\d+$/.test(ks[i])?+ks[i]:ks[i];if(o[k]==null)o[k]={};o=o[k];}o[ks[ks.length-1]]=v;}
function dropZone(action,multi,hint){return '<button type="button" class="small" data-media="'+esc(action)+'">从素材库选择</button>'+'<label class="drop" data-action="'+esc(action)+'">'+(multi?'拖入或选择照片':'拖入或选择一张照片')+'<input type="file" accept="image/*" '+(multi?'multiple':'')+'><small>'+(hint||'JPG / PNG / WebP · 自动压成 WebP，最长边 1800')+'</small></label>';}
function imgField(base,keySrc,keyCap,keyAlt,capLabel){const src=get(cur(),base+'.'+keySrc);let h='';if(src)h+='<div class="thumb wide"><img src="'+thumbUrl(src)+'" alt=""><button class="small danger" data-clear="'+esc(base+'.'+keySrc)+'">移除</button><div class="t">'+esc(src)+'</div></div>';h+=dropZone('set:'+base+'.'+keySrc,false);if(keyCap)h+=field(capLabel||'图片说明',base+'.'+keyCap,get(cur(),base+'.'+keyCap)||'',true);if(keyAlt)h+=field('替代文字（给读屏器与搜索引擎）',base+'.'+keyAlt,get(cur(),base+'.'+keyAlt)||'');return h;}
let CUR=null;function cur(){return CUR.page;}
function blockCard(b,i){const base='blocks.'+i;let h='<div data-block="'+i+'"><header><span class="kind">'+(KIND[b.type]||b.type)+(b.id?' <span class="tag">#'+esc(b.id)+'</span>':'')+'</span><button class="small" data-move="'+i+':-1">↑</button><button class="small" data-move="'+i+':1">↓</button><button class="small danger" data-del="'+i+'">删除</button></header>';
if(b.type==='section'){h+=field('小标（kicker）',base+'.kicker',b.kicker||'')+field('标题',base+'.title',b.title||'')+field('正文 HTML',base+'.body',b.body||'','tall');h+='<div class="two">'+(b.links||[]).map((l,j)=>field('链接文字 '+(j+1),base+'.links.'+j+'.label',l.label||'')+field('链接地址 '+(j+1),base+'.links.'+j+'.href',l.href||'')).join('')+'</div><div class="rowbtns"><button class="small" data-addlink="'+i+'">+ 链接</button></div>';h+='<p class="hint" style="margin:10px 0 0">这一段的照片（可选，放在正文旁边）</p>'+imgField(base,'image','imageCaption','imageAlt');}
else if(b.type==='text'){(b.paras||[]).forEach((q,j)=>{h+=field('段落 '+(j+1)+'（HTML）',base+'.paras.'+j+'.html',q.html||'','tall')});h+='<div class="rowbtns"><button class="small" data-addpara="'+i+'">+ 段落</button></div>';}
else if(b.type==='image'){h+=imgField(base,'src','caption','alt');h+=field('点击跳转到（可选，如 /for-the-best）',base+'.href',b.href||'');}
else if(b.type==='grid'){h+='<div class="thumbs">'+(b.items||[]).map((it,j)=>'<div class="thumb"><img src="'+thumbUrl(it.src)+'" alt=""><button class="small danger" data-rm="'+base+'.items.'+j+'">×</button><div class="t">'+esc(stem(it.src))+'</div></div>').join('')+'</div>'+dropZone('grid:'+base,true)+field('整组说明',base+'.caption',b.caption||'')+field('每行几张（留空 = 按比例自动排）',base+'.perRow',b.perRow||'');}
else if(b.type==='project_grid'){h+=field('小标（kicker）',base+'.kicker',b.kicker||'')+field('标题',base+'.title',b.title||'');(b.items||[]).forEach((it,j)=>{const ib=base+'.items.'+j;if(it.ref){h+=referenceRow(it,ib);return;}h+='<div class="item"><div>'+(it.cover?'<div class="thumb"><img src="'+thumbUrl(it.cover)+'" alt=""></div>':'<div class="thumb"><div class="t" style="height:100px">还没有封面</div></div>')+dropZone('set:'+ib+'.cover',false,'换封面')+'</div><div><div class="three">'+field('标题',ib+'.title',it.title||'')+field('年份',ib+'.meta',it.meta||'')+field('链接',ib+'.href',it.href||'')+'</div>'+field('一句话',ib+'.description',it.description||'',true)+'<div class="rowbtns"><button class="small danger" data-rm="'+ib+'">删掉这张卡</button></div></div></div>'});h+='<div class="rowbtns"><button class="small" data-additem="'+i+'">+ 卡片</button></div>';}
else if(b.type==='link_list'){h+=field('标题',base+'.title',b.title||'');(b.items||[]).forEach((it,j)=>{const ib=base+'.items.'+j;h+='<div class="item" style="grid-template-columns:1fr"><div><div class="three">'+field('标题',ib+'.title',it.title||'')+field('小字',ib+'.meta',it.meta||'')+field('链接',ib+'.href',it.href||'')+'</div>'+field('说明',ib+'.description',it.description||'',true)+'<div class="rowbtns"><button class="small danger" data-rm="'+ib+'">删掉</button></div></div></div>'});h+='<div class="rowbtns"><button class="small" data-additem="'+i+'">+ 条目</button></div>';}
else if(b.type==='embed'){h+=field('Vimeo/YouTube 播放器地址',base+'.embed',b.embed||'')+field('说明',base+'.caption',b.caption||'');}
else if(b.type==='video'){h+=field('视频文件（media/…mp4）',base+'.video',b.video||'')+field('说明',base+'.caption',b.caption||'');}
else if(b.type==='columns'){h+='<p class="hint">旧站的两栏版式，文字在这里改：</p>';(b.cols||[]).forEach((c,ci)=>(c.blocks||[]).forEach((x,xi)=>{if(x.type==='text')(x.paras||[]).forEach((q,qi)=>{h+=field('栏 '+(ci+1)+' 段落 '+(qi+1),base+'.cols.'+ci+'.blocks.'+xi+'.paras.'+qi+'.html',q.html||'','tall')});if(x.type==='image')h+='<div class="thumb"><img src="'+thumbUrl(x.src)+'" alt=""><div class="t">'+esc(stem(x.src))+'</div></div>'+field('说明',base+'.cols.'+ci+'.blocks.'+xi+'.caption',x.caption||'');}));if(b.caption!==undefined)h+=field('整块说明',base+'.caption',b.caption||'');}
else h+='<p class="hint">这种块没有可改的文字。</p>';
return '<details class="card block-editor"'+nativeDetailsAttrs(b,'block')+'><summary>'+esc((b.title||KIND[b.type]||b.type))+'<small>'+esc(b.kicker||'展开编辑内容与排列')+'</small></summary>'+h+'</div></details>';}
function bind(){const m=$('#main');m.querySelectorAll('[data-media]').forEach(b=>b.onclick=()=>openMedia(b.dataset.media));m.querySelectorAll('[data-ref-move]').forEach(b=>b.onclick=()=>{const [path,d]=b.dataset.refMove.split(':');const ks=path.split('.'),i=+ks.pop(),a=get(cur(),ks.join('.')),j=i+(+d);if(j<0||j>=a.length)return;[a[i],a[j]]=[a[j],a[i]];setDirty(true);renderPage(CUR)});
m.querySelectorAll('[data-path]').forEach(el=>el.oninput=()=>{let v=el.value;if(el.dataset.path.endsWith('.perRow'))v=v?+v:undefined;const old=get(cur(),el.dataset.path);if(el.dataset.path==='title'&&cur().masthead===old)cur().masthead=v;set(cur(),el.dataset.path,v);setDirty(true)});
m.querySelectorAll('[data-clear]').forEach(b=>b.onclick=()=>{set(cur(),b.dataset.clear,undefined);setDirty(true);renderPage(CUR)});
m.querySelectorAll('[data-rm]').forEach(b=>b.onclick=()=>{const path=b.dataset.rm,ks=path.split('.'),idx=+ks.pop();get(cur(),ks.join('.')).splice(idx,1);setDirty(true);renderPage(CUR)});
m.querySelectorAll('[data-del]').forEach(b=>b.onclick=()=>{if(!confirm('删除这一块？'))return;cur().blocks.splice(+b.dataset.del,1);setDirty(true);renderPage(CUR)});
m.querySelectorAll('[data-move]').forEach(b=>b.onclick=()=>{const [i,d]=b.dataset.move.split(':').map(Number),a=cur().blocks,j=i+d;if(j<0||j>=a.length)return;[a[i],a[j]]=[a[j],a[i]];setDirty(true);renderPage(CUR)});
m.querySelectorAll('[data-addlink]').forEach(b=>b.onclick=()=>{const bl=cur().blocks[+b.dataset.addlink];(bl.links=bl.links||[]).push({label:'',href:'/'});setDirty(true);renderPage(CUR)});
m.querySelectorAll('[data-addpara]').forEach(b=>b.onclick=()=>{const bl=cur().blocks[+b.dataset.addpara];(bl.paras=bl.paras||[]).push({html:'<span class="f-body" style="font-size:21px;font-weight:300"></span>',align:'left',lh:40});setDirty(true);renderPage(CUR)});
m.querySelectorAll('[data-additem]').forEach(b=>b.onclick=()=>{if(cur().blocks[+b.dataset.additem].type==='project_grid'){chooseReference(+b.dataset.additem);return;}const bl=cur().blocks[+b.dataset.additem];(bl.items=bl.items||[]).push(bl.type==='project_grid'?{href:'/',title:'',meta:'',description:''}:{href:'/',title:'',meta:'',description:''});setDirty(true);renderPage(CUR)});
m.querySelectorAll('[data-add]').forEach(b=>b.onclick=()=>{const t=b.dataset.add,bl=cur().blocks=cur().blocks||[];const T={section:{type:'section',title:'',body:'<p></p>'},'section-image':{type:'section',title:'',body:'<p></p>',image:'',imageCaption:''},project_grid:{type:'project_grid',title:'',items:[]},text:{type:'text',maxw:800,width:85,paras:[{html:'<span class="f-body" style="font-size:21px;font-weight:300"></span>',align:'left',lh:40}],pt:27},image:{type:'image',pt:40,pb:20,capAlign:'left',src:'',caption:''},grid:{type:'grid',pt:41,width:100,items:[]}};bl.push(JSON.parse(JSON.stringify(T[t])));setDirty(true);renderPage(CUR);window.scrollTo(0,document.body.scrollHeight)});
m.querySelectorAll('.drop').forEach(z=>{const inp=z.querySelector('input');z.ondragover=ev=>{ev.preventDefault();z.classList.add('over')};z.ondragleave=()=>z.classList.remove('over');z.ondrop=ev=>{ev.preventDefault();z.classList.remove('over');upload(z.dataset.action,ev.dataTransfer.files)};inp.onchange=()=>upload(z.dataset.action,inp.files)});}

let activityMount=null,activityLoading=null;
let DATA=null,MEDIA={},sel=null,dirty=false,REV='',SOURCE='',TOKEN='',PUBLISHED=null,filter='all',query='',saving=null,saveTimer,previewTimer,previewSeq=0,mediaAction=null,mediaOrigin=null;
const $=s=>document.querySelector(s),esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const KIND={text:'文字',section:'段落',project_grid:'作品卡片',link_list:'链接列表',image:'单张照片',grid:'照片组',embed:'视频嵌入',video:'视频',columns:'两栏',social_icons:'社交图标',spacer:'留白',button:'按钮'};
const TYPES={editorial:'网站页面',project:'作品与实践',gallery:'旧站画廊',page:'存档',cv:'简历'};
const stem=ref=>(ref||'').split('/').pop().replace(/\.[^.]+$/,'');
const thumbUrl=ref=>MEDIA[stem(ref)]?'/'+MEDIA[stem(ref)].src:'';
// Business identity belongs to the actual DATA object. Numeric paths only
// locate that object in the current document; they never become identity keys.
// WeakMaps stay private to this loaded draft and do not add fields to its JSON.
const nativeObjects=new WeakMap(),nativeMounts=new WeakMap();
function nativeObjectKey(object){
 if(!object||typeof object!=='object')throw Error('Native editor identity needs a data object');
 let key=nativeObjects.get(object);if(!key){key=crypto.randomUUID();nativeObjects.set(object,key);}return key;
}
function nativeMount(node){let key=nativeMounts.get(node);if(!key){key=crypto.randomUUID();nativeMounts.set(node,key);}return key;}
function nativeToken(value){let h=2166136261;for(const c of String(value))h=Math.imul(h^c.charCodeAt(0),16777619);return(h>>>0).toString(36);}
function nativeKey(object,action){return 'cms-object-'+nativeObjectKey(object)+'-'+nativeToken(action);}
function nativeFieldOwner(path){const keys=path.split('.'),property=keys.pop();return{object:keys.length?get(cur(),keys.join('.')):cur(),property};}
function nativeFieldAttrs(path,wrapper=false){const {object,property}=nativeFieldOwner(path);return ' data-native-key="'+nativeKey(object,(wrapper?'field-wrap:':'field:')+property)+'" data-native-business-key="'+nativeObjectKey(object)+'" data-native-action="field:'+esc(property)+'"';}
function nativeDetailsAttrs(object,action){return ' data-native-key="'+nativeKey(object,'details:'+action)+'" data-native-business-key="'+nativeObjectKey(object)+'" data-native-action="details:'+esc(action)+'"';}
const nativeControlSelector='[data-motion-id],button,input,select,textarea,summary,dialog,output,progress,meter,a[href],[tabindex],[aria-live],[contenteditable]:not([contenteditable=false]),[role=tab],[role=switch],[role=checkbox],[role=button],[role=dialog],[role=status],[role=alert],[role=log],[role=progressbar],[role=slider],[role=spinbutton],[role=textbox],[role=combobox],[role=listbox],[role=option],[role=radio],[role=menuitem],[role=menuitemcheckbox],[role=menuitemradio],[role=tabpanel],[role=tooltip]';
function nativeAction(node){
 if(node.dataset.nativeAction)return{business:node.dataset.nativeBusinessKey,action:node.dataset.nativeAction,key:node.dataset.nativeKey,entity:node.matches('textarea')?'cms-content-field-multiline':'cms-content-field-text'};
 if(node.matches('summary')){const d=node.parentElement;return{business:d.dataset.nativeBusinessKey,action:d.dataset.nativeAction,key:d.dataset.nativeKey+'-toggle',entity:'cms-content-section-toggle'};}
 if(node.matches('.library-card')){const object=DATA.pages.find(p=>'#'+p.slug===node.getAttribute('href'));const record='record-'+nativeToken(object.id||object.slug);return{business:record,action:'open-record',key:'cms-'+record+'-open',entity:'cms-content-record'};}
 let object,action,entity;
 if(node.dataset.path!==undefined){const field=nativeFieldOwner(node.dataset.path);object=field.object;action='field:'+field.property;entity=node.matches('textarea')?'cms-content-field-multiline':'cms-content-field-text';}
 else if(node.dataset.rm!==undefined){object=get(cur(),node.dataset.rm);action='remove-item';entity='cms-content-item-remove';}
 else if(node.dataset.refMove!==undefined){const [path,direction]=node.dataset.refMove.split(':');object=get(cur(),path);action=Number(direction)<0?'move-up':'move-down';entity='cms-content-item-'+action;}
 else if(node.dataset.del!==undefined){object=cur().blocks[Number(node.dataset.del)];action='remove-block';entity='cms-content-block-remove';}
 else if(node.dataset.move!==undefined){const [index,direction]=node.dataset.move.split(':');object=cur().blocks[Number(index)];action=Number(direction)<0?'move-up':'move-down';entity='cms-content-block-'+action;}
 else if(node.dataset.addlink!==undefined||node.dataset.addpara!==undefined||node.dataset.additem!==undefined){const name=['addlink','addpara','additem'].find(key=>node.dataset[key]!==undefined);object=cur().blocks[Number(node.dataset[name])];action=name;entity='cms-content-'+name;}
 else if(node.dataset.add!==undefined){object=cur();action='add-block:'+node.dataset.add;entity='cms-content-block-add';}
 else if(node.dataset.clear!==undefined||node.dataset.media!==undefined||node.matches('input[type=file]')&&node.closest('[data-action]')){
  const clear=node.dataset.clear,raw=clear||node.dataset.media||node.closest('[data-action]').dataset.action;
  const [kind,path]=clear?['set',raw]:raw.split(':');
  const target=kind==='grid'?{object:get(cur(),path),property:'items'}:nativeFieldOwner(path);
  object=target.object;action=(clear?'clear':node.matches('input')?'upload':'choose-media')+':'+target.property;
  entity=clear?'cms-content-image-clear':node.matches('input')?'cms-content-image-upload':'cms-content-image-choose';
 }
 if(object)return{business:nativeObjectKey(object),action,key:nativeKey(object,action),entity};
 if(node.dataset.mediaKey!==undefined)return{business:'media-'+nativeToken(node.dataset.mediaKey),action:'choose-media',key:'cms-media-item-'+nativeToken(node.dataset.mediaKey),entity:'cms-media-item'};
 if(node.dataset.historyId!==undefined)return{business:'history-'+nativeToken(node.dataset.historyId),action:'restore-history',key:'cms-history-item-'+nativeToken(node.dataset.historyId),entity:'cms-history-item'};
 if(node.matches('.reference-name a')){const row=node.closest('.reference-row');return{business:row.dataset.nativeBusinessKey,action:'open-reference',key:row.dataset.nativeKey+'-open',entity:'cms-content-reference-link'};}
 if(node.matches('a[href]')&&CUR){return{business:nativeObjectKey(CUR.page),action:'language:'+node.getAttribute('href').includes('@zh'),key:nativeKey(CUR.page,'language:'+node.getAttribute('href').includes('@zh')),entity:'cms-content-language-link'};}
 const semantic=node.id?('cms-'+node.id):node.dataset.motionId|| (node.dataset.export!==undefined?'cms-export-draft':null);
 if(semantic)return{business:'native-shell',action:semantic,key:semantic,entity:semantic};
 // No positional/name fallback: an unsupported dynamic control stays visible
// to the independent inventory as missing until its actual role is authored.
 return null;
}
function annotateNativeMotion(scope){
 const nodes=[...(scope.matches?.(nativeControlSelector)?[scope]:[]),...scope.querySelectorAll(nativeControlSelector)];
 for(const node of nodes){
  if(node.closest('#activity-admin-root,[data-activity-dialog]'))continue;
  const info=nativeAction(node);if(!info)continue;
  // Preserve only the surface of this control's actual connected native owner.
  const ownerSurface=node.closest('[data-motion-surface]')?.dataset.motionSurface;
  if(node.isConnected&&ownerSurface==='cms-content')node.dataset.motionOwnerSurface=ownerSurface;
  node.dataset.nativeKey=info.key;
  node.dataset.motionEntity=info.entity;node.dataset.motionAction=info.action;node.dataset.motionBusinessKey=info.business;
  if(!node.dataset.motionId||node.dataset.nativeBusinessKey||info.business!=='native-shell')node.dataset.motionId=info.key;
  node.dataset.motionMount=nativeMount(node);
 }
}
// Only the native navigation owns these shared engine output elements.
// Its two physical rects have actual Element UUIDs, never order-based identities.
function annotateNativeGeometry(){
 const nav=document.querySelector('.page-nav');if(!nav)return;
 const ownerSurface=nav.closest('[data-motion-surface]')?.dataset.motionSurface;
 nav.dataset.motionId='cms-navigation';nav.dataset.motionEntity='cms-navigation';nav.dataset.motionAction='navigate';nav.dataset.motionBusinessKey='native-navigation';nav.dataset.motionMount=nativeMount(nav);
 for(const shape of nav.querySelectorAll('.ys-motion-tabs-fluid rect')){
  // Retain the actual connected owner across this engine element's removal.
  if(ownerSurface==='cms-content')shape.dataset.motionOwnerSurface=ownerSurface;
  const mount=nativeMount(shape);shape.dataset.motionId='cms-navigation-geometry-'+mount;shape.dataset.motionEntity='cms-navigation-geometry';shape.dataset.motionOwner='cms-navigation';shape.dataset.motionAction='indicator-geometry';shape.dataset.motionBusinessKey='native-navigation';shape.dataset.motionMount=mount;
 }
}
// Reconcile keyed real editor nodes. Reordering a DATA record moves its existing
// field/file/summary nodes; it does not serialize browser-only editing state.
function renderNativeEditor(html,sameRecord){
 const main=$('#main'),template=document.createElement('template');template.innerHTML=html;
 annotateNativeMotion(template.content);
 if(!sameRecord){main.replaceChildren(template.content);annotateNativeMotion(main);return;}
 const oldByKey=new Map([...main.querySelectorAll('[data-native-key]')].map(node=>[node.dataset.nativeKey,node]));
 const active=main.contains(document.activeElement)?document.activeElement:null;
 const selection=active&&typeof active.selectionStart==='number'?{start:active.selectionStart,end:active.selectionEnd,direction:active.selectionDirection}:null;
 const scroll=active?{left:active.scrollLeft,top:active.scrollTop}:null;
 const claimed=new Set();
 function reconcile(parent,children){
  let cursor=parent.firstChild;
  for(const fresh of children){
   if(fresh.nodeType!==1){
    const node=cursor?.nodeType===fresh.nodeType?cursor:fresh;
    if(node!==fresh&&node.nodeValue!==fresh.nodeValue)node.nodeValue=fresh.nodeValue;
    if(node!==cursor)parent.insertBefore(node,cursor);cursor=node.nextSibling;continue;
   }
   const key=fresh.dataset.nativeKey;
   // Unnamed layout wrappers may be reused structurally; only explicitly keyed
   // DATA controls carry business identity. Never give an index to either one.
   const candidate=key?oldByKey.get(key):cursor?.nodeType===1&&!cursor.dataset.nativeKey?cursor:null;
   const reuse=candidate&&candidate.tagName===fresh.tagName&&!claimed.has(candidate);
   const node=reuse?candidate:fresh;
   if(reuse){
    claimed.add(node);
    // Keep the exact browser value/files and open state; DATA already receives
    // every input event. Native composition and selection stay on this node.
    for(const attr of [...node.attributes])if(!fresh.hasAttribute(attr.name)&&!['open','data-motion-mount','data-motion-id','style'].includes(attr.name))node.removeAttribute(attr.name);
    for(const attr of [...fresh.attributes])if(!['open','data-motion-mount','data-motion-id','value'].includes(attr.name))node.setAttribute(attr.name,attr.value);
    // DATA is the existing native input owner. A derived/programmatic change
    // (for example title -> masthead) must refresh an unedited retained field.
    // Keep the active editing/composition target and file input browser state.
    if(node!==active&&node.matches('input:not([type=file]),textarea')&&node.value!==fresh.value)node.value=fresh.value;
    if(!node.matches('input,textarea'))reconcile(node,[...fresh.childNodes]);
   }else if(node.nodeType===1)reconcile(node,[...node.childNodes]);
   if(node!==cursor){
    if(parent.moveBefore&&node.isConnected&&parent.isConnected)parent.moveBefore(node,cursor);
    else parent.insertBefore(node,cursor);
   }
   cursor=node.nextSibling;
  }
  while(cursor){const next=cursor.nextSibling;cursor.remove();cursor=next;}
 }
 reconcile(main,[...template.content.childNodes]);
 annotateNativeMotion(main);
 if(active?.isConnected){if(document.activeElement!==active)active.focus({preventScroll:true});if(selection)active.setSelectionRange(selection.start,selection.end,selection.direction);active.scrollLeft=scroll.left;active.scrollTop=scroll.top;}
}

function status(text,cls=''){ $('#status').textContent=text;$('#status').className=cls; }
async function api(path,body){const r=await fetch(path,body===undefined?{}:{method:'POST',headers:{'Content-Type':'application/json','X-Desk-Token':TOKEN},body:JSON.stringify(body)});const j=await r.json();if(!r.ok)throw Error(j.error||'请求失败');return j}
function setDirty(v){dirty=v;$('#dirty').textContent=v?'正在编辑 · 尚未保存':'草稿已保存在本机';if(v){clearTimeout(saveTimer);saveTimer=setTimeout(()=>saveDraft().catch(()=>{}),1200);queuePreview()}}
function pageFor(ref){return DATA.pages.find(p=>(p.id||p.slug)===ref)}
function resolved(it){if(!it.ref)return it;const p=pageFor(it.ref);return {href:'/'+p.slug,title:p.cardTitle||p.title,cover:p.cover,meta:p.cardMeta||p.year,description:p.summary,...(CUR?.lang==='zh'?p.cardZh:{}),...it.overrides}}
function uses(id){const found=[];for(const p of DATA.pages){const walk=v=>{if(v&&typeof v==='object'){if(v.ref===id&&!found.includes(p.title))found.push(p.title);Object.values(v).forEach(walk)}};walk(p)}return found}
function referenceRow(it,path){const c=resolved(it),p=pageFor(it.ref);return '<div class="reference-row" data-native-key="'+nativeKey(it,'reference-row')+'" data-native-business-key="'+nativeObjectKey(it)+'">'+(c.cover?'<img src="'+thumbUrl(c.cover)+'" alt="">':'')+'<div class="reference-name"><a href="#'+p.slug+'">'+esc(c.title)+'</a><p>引用原条目'+(it.overrides?' · 保留此处的呈现差异':'')+'</p></div><button data-ref-move="'+path+':-1" aria-label="上移 '+esc(c.title)+'">↑</button><button data-ref-move="'+path+':1" aria-label="下移 '+esc(c.title)+'">↓</button><button data-rm="'+path+'" aria-label="移除此处引用 '+esc(c.title)+'">移除</button></div>'}
function entries(){const out=[];for(const p of DATA.pages){out.push({key:p.slug,page:p,label:p.title,lang:'en'});if(p.zh)out.push({key:p.slug+'@zh',page:p.zh,label:(p.zh.title||p.title)+' · 中文',lang:'zh',parent:p})}return out}
function isChanged(p){const old=PUBLISHED?.pages.find(x=>x.slug===p.slug);return !old||JSON.stringify(old)!==JSON.stringify(p)}
// Keep each connected record card (and its shared material instance) alive.
// Filtering/searching changes visibility; only changed card content is rendered.
const libraryCards=new Map();
let libraryEmpty=null;
function libraryCardHTML(p){let ref=p.cover||p.hero?.image;const galleryFirst=p.items?.[0];if(!ref&&galleryFirst)ref=galleryFirst.ref?pageFor(galleryFirst.ref)?.cover:galleryFirst.cover;const fallback=(p.blocks||[]).find(b=>b.type==='project_grid')?.items?.[0];if(!ref&&fallback)ref=fallback.ref?pageFor(fallback.ref)?.cover:fallback.cover;return '<div class="cover">'+(ref?'<img src="'+thumbUrl(ref)+'" alt="" loading="lazy">':'<span class="no-cover">'+esc(p.hero?.title||p.title)+'</span>')+'</div><div class="content"><div class="meta"><span>'+esc(TYPES[p.type])+' '+esc(p.year||'')+'</span><span class="'+(isChanged(p)?'draft':'')+'">'+(isChanged(p)?'有草稿':'已发布')+'</span></div><h2>'+esc(p.title)+'</h2><p>'+esc(p.summary||p.hero?.intro||p.description||'')+'</p></div>';}
function renderLibrary(){
 const container=$('#library-cards'),rank=p=>p.type==='project'?0:p.type==='editorial'?1:2;
 const pages=[...DATA.pages].sort((a,b)=>rank(a)-rank(b)),keys=new Set(pages.map(p=>p.slug)),search=query.toLocaleLowerCase();
 for(const [key,card] of libraryCards)if(!keys.has(key)){card.node.remove();libraryCards.delete(key);}
 let cursor=container.firstElementChild,visibleCount=0;
 for(const p of pages){
  const html=libraryCardHTML(p);let card=libraryCards.get(p.slug);
  if(!card){const node=document.createElement('a');node.className='library-card';node.setAttribute('href','#'+p.slug);card={node,html:null};libraryCards.set(p.slug,card);}
  if(card.html!==html){card.node.innerHTML=html;card.html=html;}
  const visible=(filter==='all'||p.type===filter||p.contentKind===filter)&&JSON.stringify(p).toLocaleLowerCase().includes(search);
  if(card.node.hidden===visible)card.node.hidden=!visible;
  if(visible)visibleCount++;
  // Do not move an already correctly ordered node, even while it is hidden.
  if(card.node!==cursor)container.insertBefore(card.node,cursor);
  cursor=card.node.nextElementSibling;
 }
 if(!libraryEmpty){libraryEmpty=document.createElement('p');libraryEmpty.className='empty';libraryEmpty.textContent='没有找到内容。试试别的关键词。';container.append(libraryEmpty);}
 libraryEmpty.hidden=visibleCount>0;
 $('#library-count').textContent=visibleCount+' 条内容';
 annotateNativeMotion(container,'library');document.querySelectorAll('[data-kind]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.kind===filter)));document.querySelectorAll('[data-view]').forEach(b=>b.classList.toggle('active',b.dataset.view===filter));
}
function openView(kind){filter=kind;location.hash='library';select('library')}
// Returning from an activity portal waits for its real focus-scope teardown.
// History traversal may already have reset focus to body before hashchange.
let activityFocusReturn=false;
// Only activity-owned portals may defer the native workspace focus return.
const activityFocusPortalSelector='[data-activity-dialog],[data-activity-portal="select"][data-motion-surface="cms-workshops"]';
function restoreActivityContentFocus(){
 const workspace=$('#activity-workspace');
 if(!activityFocusReturn||sel==='activities'||!workspace.hidden||document.querySelector(activityFocusPortalSelector))return;
 const focused=document.activeElement;
 // Keep a user's focus on any visible native control selected during navigation.
 if(focused&&focused!==document.body&&focused!==document.documentElement&&!workspace.contains(focused)&&!focused.closest(activityFocusPortalSelector)){activityFocusReturn=false;return;}
 activityFocusReturn=false;
 (document.querySelector('.page-nav [data-view].active')||document.querySelector('[data-view="all"]'))?.focus();
}
window.addEventListener('youyang:activity-dialog-closed',restoreActivityContentFocus);
function select(key){
 const workspace=$('#activity-workspace'),wasActivities=!workspace.hidden,activities=key==='activities',focused=document.activeElement;
 if(activities)activityFocusReturn=false;
 else if(wasActivities)activityFocusReturn=!focused||focused===document.body||focused===document.documentElement||workspace.contains(focused)||!!focused.closest(activityFocusPortalSelector);
 sel=key;
 if(wasActivities&&!activities)window.dispatchEvent(new CustomEvent('youyang:activity-visibility',{detail:{visible:false}}));
 workspace.hidden=!activities;
 if(!wasActivities&&activities)window.dispatchEvent(new CustomEvent('youyang:activity-visibility',{detail:{visible:true}}));
 $('#activities').classList.toggle('active',activities);$('#activities').setAttribute('aria-current',activities?'page':'false');$('#save').hidden=activities;$('#publish').hidden=activities;$('.save-state').hidden=activities;
 if(activities){$('#library').hidden=true;$('#editor').hidden=true;$('#location').textContent='活动管理';++previewSeq;document.querySelectorAll('[data-view]').forEach(b=>b.classList.remove('active'));mountActivities();return;}
 const e=entries().find(x=>x.key===key);
 if(!e){$('#library').hidden=false;$('#editor').hidden=true;$('#location').textContent='内容库';CUR=null;renderLibrary();}
 else{$('#library').hidden=true;$('#editor').hidden=false;$('#location').textContent='编辑内容';renderPage(e);}
 restoreActivityContentFocus();
}
function renderPage(e){const sameRecord=CUR?.page===e.page;CUR=e;const p=e.page,parent=e.parent||p;$('#editing-title').textContent=e.label;
 const path='/site/'+(e.lang==='zh'?'zh/':'')+(parent.slug==='home'?'':parent.slug+'/');$('#preview-link').href=path;
 let h='<h2>'+esc(e.label)+'</h2><p class="hint">修改会自动存为本机草稿，检查与发布后才会上线。</p>';
 if(parent.zh){h+='<div class="rowbtns"><a href="#'+parent.slug+'">English</a><a href="#'+parent.slug+'@zh">中文</a></div>'}
 if(parent.type==='cv'){h+='<div class="card"><p>简历继续使用现有密码保护。正文与密码保存在本机私有文件中，内容台不显示它们。</p></div>';renderNativeEditor(h,sameRecord);queuePreview();return}
 if(p.type==='project'){const where=uses(p.id||p.slug);h+='<p class="reused">'+(where.length?'这条内容被 '+where.length+' 个页面引用：'+esc(where.join('、'))+'。共用字段在这里改一次。':'尚未放入首页或作品集；可以在网站页面的卡片组中引用它。')+'</p>'}
 h+='<section class="card"><header><span class="kind">'+(p.type==='project'?'共用作品资料':'页面信息')+'</span><span class="tag">/'+parent.slug+'/</span></header>'+field('标题','title',p.title||'');
 if(p.type==='project'){h+='<div class="two">'+field('年份','year',p.year||'')+field('卡片署名与年份','cardMeta',p.cardMeta||p.year||'')+'</div>'+field('卡片简介','summary',p.summary||'',true);if(p.cardTitle&&p.cardTitle!==p.title)h+=field('卡片短标题','cardTitle',p.cardTitle);h+='<p class="hint">作品封面</p>'+(p.cover?'<div class="thumb wide"><img src="'+thumbUrl(p.cover)+'" alt="作品封面"></div>':'')+dropZone('set:cover',false);}
 h+='</section>';
 if(p.hero)h+='<details class="card"'+nativeDetailsAttrs(p.hero,'hero')+'><summary>开篇与主图<small>'+esc(p.hero.title||'')+'</small></summary>'+field('小标','hero.eyebrow',p.hero.eyebrow||'')+field('开篇标题','hero.title',p.hero.title||'')+field('副题','hero.subtitle',p.hero.subtitle||'')+field('引言','hero.intro',p.hero.intro||'',true)+imgField('hero','image','imageCaption','imageAlt')+'</details>';
 if(p.cardZh)h+='<details class="card"'+nativeDetailsAttrs(p.cardZh,'chinese-card')+'><summary>中文卡片资料<small>中文页面引用同一作品的中文表达</small></summary>'+field('中文标题','cardZh.title',p.cardZh.title||'')+field('中文简介','cardZh.description',p.cardZh.description||'',true)+field('中文署名与年份','cardZh.meta',p.cardZh.meta||'')+'</details>';
 h+='<details class="card"'+nativeDetailsAttrs(p,'page-settings')+'><summary>页面摘要与标题设置</summary>'+field('搜索与分享描述','description',p.description||'',true)+(p.masthead!==undefined?field('作品页大标题','masthead',p.masthead):'')+'</details>';
 (p.blocks||[]).forEach((b,i)=>{h+=blockCard(b,i)});
 if(parent.type==='gallery')h+='<details class="card" open'+nativeDetailsAttrs(p,'gallery')+'><summary>画廊内容</summary>'+(p.items||[]).map((it,i)=>it.ref?referenceRow(it,'items.'+i):'<p>'+esc(it.title)+'</p>').join('')+'</details>';
 h+='<div class="add"><button data-add="section">＋ 文字段落</button><button data-add="image">＋ 照片</button><button data-add="grid">＋ 照片组</button><button data-add="project_grid">＋ 卡片组</button></div>';
 renderNativeEditor(h,sameRecord);bind();queuePreview();
}
function queuePreview(){if(!CUR)return;$('#preview-state').textContent='· 更新中';clearTimeout(previewTimer);previewTimer=setTimeout(updatePreview,350)}
async function updatePreview(){if(!CUR||sel==='activities')return;const n=++previewSeq,e=CUR;$('#preview-state').textContent='· 更新中';try{const j=await api('/api/preview',{site:DATA,slug:(e.parent||e.page).slug,lang:e.lang});if(n!==previewSeq||CUR!==e)return;const url=new URL(j.url),parent=e.parent||e.page,frozenPath='/site/'+(e.lang==='zh'?'zh/':'')+(parent.slug==='home'?'':parent.slug+'/');const validPath=j.mode==='frozen'?parent.type==='cv'&&url.pathname===frozenPath:/^\/draft\/[A-Za-z0-9_-]{32}$/.test(url.pathname);if(url.protocol!=='http:'||url.hostname!=='127.0.0.1'||url.origin===location.origin||url.search||url.hash||!validPath)throw Error('预览地址无效');$('#preview-frame').src=url.href;$('#preview-link').href=url.href;$('#preview-state').textContent=j.mode==='frozen'?'· 现有冻结版本':'· 当前输入'}catch(e){$('#preview-state').textContent='· 未更新';status('预览未更新：'+e.message,'bad')}}
async function saveDraft(){clearTimeout(saveTimer);if(saving){await saving;if(dirty)return saveDraft();return}if(!dirty)return;const snapshot=JSON.stringify(DATA),restoreSaveFocus=document.activeElement===$('#save');$('#save').disabled=true;$('#dirty').textContent='保存中…';saving=(async()=>{try{const j=await api('/api/site',{site:JSON.parse(snapshot),revision:REV,sourceRevision:SOURCE});REV=j.revision;SOURCE=j.sourceRevision;if(JSON.stringify(DATA)===snapshot){dirty=false;$('#dirty').textContent='草稿已保存在本机'}else{$('#dirty').textContent='正在编辑';}status('')}catch(e){dirty=true;$('#dirty').textContent='未保存 · 输入仍在';status('保存失败：'+e.message+' 可点击“导出草稿”保留当前输入。','bad');if(!$('#export-recovery')){const b=document.createElement('button');b.id='export-recovery';b.dataset.motionId='cms-export-recovery';b.textContent='导出草稿';b.onclick=exportDraft;$('#status').append(' ',b);annotateNativeMotion($('#status'))}throw e}finally{$('#save').disabled=false;if(restoreSaveFocus&&document.activeElement===document.body)$('#save').focus();saving=null}})();await saving}
function exportDraft(){const blob=new Blob([JSON.stringify(DATA,null,2)],{type:'application/json'}),url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download='youyang-local-draft.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000)}
function showDialog(title,html,actions=''){ $('#dlg-title').textContent=title;$('#dlg-body').innerHTML=html;$('#dlg-actions').innerHTML=actions;annotateNativeMotion($('#dlg'),'dialog');if(!$('#dlg').open)$('#dlg').showModal() }
function showLog(title,text){showDialog(title,'<pre class="log">'+esc(text)+'</pre>')}
function chooseReference(index){const pages=DATA.pages.filter(p=>p.type==='project'||p.type==='editorial');showDialog('选择要呈现的内容','<p class="hint">这里只保存引用。标题、封面和简介跟随原条目更新。</p><label class="f"><span>内容条目</span><select id="ref-choice">'+pages.map(p=>'<option value="'+esc(p.id||p.slug)+'">'+esc(p.title)+'</option>').join('')+'</select></label>','<button id="ref-add" class="primary">加入卡片组</button>');$('#ref-add').onclick=()=>{(cur().blocks[index].items||=[]).push({ref:$('#ref-choice').value});$('#dlg').close();setDirty(true);renderPage(CUR)}}
function openMedia(action=null){mediaAction=action;mediaOrigin=document.activeElement;$('#media-search').value='';$('#media-help').textContent=action?'选择已有照片直接复用，原图不会被替换。':'这里是站点已经使用的照片。编辑内容时可直接选用，无需再次上传。';renderMedia();$('#media-dialog').showModal()}
function renderMedia(){const q=$('#media-search').value.toLocaleLowerCase();$('#media-grid').innerHTML=Object.entries(MEDIA).filter(([key])=>key.toLocaleLowerCase().includes(q)).map(([key,m])=>'<button class="media-tile" data-media-key="'+esc(key)+'"><img src="/'+esc(m.src)+'" alt="" loading="lazy"><span>'+esc(key)+'<br>'+m.w+' × '+m.h+'</span></button>').join('')||'<p class="empty">没有匹配的照片。</p>';annotateNativeMotion($('#media-grid'),'media');$('#media-grid').querySelectorAll('[data-media-key]').forEach(b=>b.onclick=()=>{const key=b.dataset.mediaKey,m=MEDIA[key];if(!mediaAction){$('#media-help').textContent=key+' · '+m.w+' × '+m.h+' · 在编辑页点击“从素材库选择”即可复用。';return}applyMedia(mediaAction,[{ref:m.src,stem:key,...m}]);$('#media-dialog').close();[...document.querySelectorAll('[data-media]')].find(b=>b.dataset.media===mediaAction)?.focus()})}
function applyMedia(action,items){const [kind,path]=action.split(':');for(const a of items){MEDIA[a.stem]={src:a.src,w:a.w,h:a.h,anim:a.anim,bytes:a.bytes};if(kind==='set')set(cur(),path,a.ref);else if(kind==='grid'){const g=get(cur(),path);(g.items||=[]).push({src:a.ref,w:a.w,h:a.h})}}setDirty(true);renderPage(CUR)}
async function upload(action,files){if(!files.length)return;status('正在压缩并加入素材库…');const fd=new FormData();for(const f of files)fd.append('files',f);try{const r=await fetch('/api/upload',{method:'POST',headers:{'X-Desk-Token':TOKEN},body:fd}),j=await r.json();if(!r.ok)throw Error(j.error);for(const a of j.added)MEDIA[a.stem]=a;if(action)applyMedia(action,j.added);status('已加入 '+j.added.length+' 张照片。');renderMedia()}catch(e){status('上传未完成：'+e.message,'bad')}}
async function prepareRelease(){try{await saveDraft();$('#publish').disabled=true;status('正在检查页面、图片和链接…');const j=await api('/api/prepare',{revision:REV});status('检查通过，可以核对这次更新。');showDialog('发布前，看一眼。','<p>'+esc(j.verification)+'</p><p class="hint">将更新这些内容及其引用卡片。发布到现有的 youyang.art。</p><ul class="release-list">'+(j.changed.length?j.changed.map(t=>'<li>'+esc(t)+'</li>').join(''):'<li>内容没有新变化；仍可重建并重试上次推送。</li>')+'</ul>','<button data-export>导出草稿</button><button id="release-confirm" class="primary">发布这次更新 ↗</button>');$('[data-export]').onclick=exportDraft;$('#release-confirm').onclick=async()=>{const b=$('#release-confirm');b.disabled=true;b.textContent='正在发布…';try{const r=await api('/api/publish',{revision:j.revision});const current=await api('/api/site');REV=current.revision;SOURCE=current.sourceRevision;PUBLISHED=structuredClone(DATA);status('已推送 '+r.commit.slice(0,7)+'，正在等待线上更新。');showLog('已推送，等待上线','内容已提交到 GitHub。线上发布仍需构建，下面会核对线上版本。');checkLive(r.revision)}catch(e){showLog('发布未完成，草稿已保留',e.message);status('发布未完成。可以重试“检查与发布”；草稿仍保存在本机。','bad')}finally{b.disabled=false}}}catch(e){status('检查未通过：'+e.message,'bad')}finally{$('#publish').disabled=false}}
async function checkLive(revision,attempt=0){try{const j=await api('/api/live');if(j.state==='live'&&j.revision===revision){status('✓ 已上线 · youyang.art');return}}catch{}if(attempt<20){status('已推送，等待 GitHub Pages 上线…');setTimeout(()=>checkLive(revision,attempt+1),6000)}else status('已推送；尚未确认线上版本。请稍后打开网站核对。')}

function newContent(){showDialog('留下一件新发生的事。','<label class="f"><span>内容类型</span><select id="new-kind"><option value="work">作品</option><option value="event">共创活动</option><option value="card">练习卡片</option><option value="note">文字与札记</option></select></label><label class="f"><span>标题</span><input id="new-title" type="text" required></label><label class="f"><span>页面地址（英文、数字与短横线，创建后固定）</span><input id="new-slug" type="text" placeholder="a-shared-afternoon" pattern="[a-z0-9]+(-[a-z0-9]+)*" required></label><p class="hint">先创建本机草稿。到网站页面的卡片组里引用它，发布时一起上线。</p>','<button id="create-content" class="primary">创建草稿</button>');$('#create-content').onclick=()=>{const title=$('#new-title').value.trim(),slug=$('#new-slug').value.trim();if(!title||!/^([a-z0-9]+-)*[a-z0-9]+$/.test(slug)||DATA.pages.some(p=>p.slug===slug)){status('请填标题和一个未使用的英文地址。','bad');return}DATA.pages.push({id:slug,slug,type:'project',contentKind:$('#new-kind').value,title,masthead:title,year:'',summary:'',blocks:[{type:'section',title:'',body:'<p></p>'}]});$('#dlg').close();setDirty(true);location.hash=slug}}
async function historyDialog(){try{const items=await api('/api/history');showDialog('草稿历史','<p class="hint">保留最近 30 次保存。恢复仅替换本机草稿，发布仍需检查。</p>'+items.map(i=>'<p><button data-history-id="'+i.id+'">恢复 '+new Date(i.savedAt*1000).toLocaleString()+'</button></p>').join('')+(items.length?'':'<p>还没有更早的草稿。</p>'),'<button id="export-history">导出当前草稿</button>');$('#export-history').onclick=exportDraft;document.querySelectorAll('[data-history-id]').forEach(b=>b.onclick=async()=>{try{await saveDraft();const old=await api('/api/history/'+b.dataset.historyId);DATA=old.site;setDirty(true);await saveDraft();$('#dlg').close();select(sel);status('已恢复为本机草稿，尚未发布。')}catch(e){status(e.message,'bad')}})}catch(e){status(e.message,'bad')}}
async function mountActivities(){if(activityMount||activityLoading)return;const root=$('#activity-admin-root');root.setAttribute('aria-busy','true');activityLoading=(async()=>{try{const config=await api('/api/activity-config');const module=await import('/activity-admin.js');activityMount=module.mountActivityAdmin(root,{...config,onReturn:()=>{location.hash='library'}})}catch(error){root.replaceChildren();const message=document.createElement('p');message.setAttribute('role','alert');message.dataset.motionId='cms-activity-load-error';message.textContent='活动管理未能打开：'+error.message;const retry=document.createElement('button');retry.textContent='重新打开活动管理';retry.dataset.motionId='cms-activity-retry';retry.onclick=()=>mountActivities();root.append(message,retry)}finally{root.removeAttribute('aria-busy');activityLoading=null}})();await activityLoading}
window.addEventListener('pagehide',()=>{if(!$('#activity-workspace').hidden)window.dispatchEvent(new CustomEvent('youyang:activity-visibility',{detail:{visible:false}}));activityMount?.unmount();activityMount=null});
window.addEventListener('pageshow',event=>{if(event.persisted&&sel==='activities')mountActivities()});
$('#activities').onclick=()=>{location.hash='activities'};$('#preview-refresh').onclick=()=>updatePreview();
$('#save').onclick=()=>saveDraft().catch(()=>{});$('#publish').onclick=prepareRelease;$('#new').onclick=newContent;$('#history').onclick=historyDialog;$('#all-media').onclick=()=>openMedia();$('#media-search').oninput=renderMedia;$('#media-upload').onchange=e=>upload(mediaAction,e.target.files);$('#search').oninput=e=>{query=e.target.value;renderLibrary()};$('#back').onclick=()=>location.hash='library';
document.querySelectorAll('[data-view]').forEach(b=>b.onclick=()=>openView(b.dataset.view));document.querySelectorAll('[data-kind]').forEach(b=>b.onclick=()=>{filter=b.dataset.kind;renderLibrary()});document.querySelectorAll('[data-close]').forEach(b=>b.onclick=()=>$('#'+b.dataset.close).close());
$('#grid-view').onclick=()=>{$('#library-cards').classList.remove('list');$('#grid-view').setAttribute('aria-pressed','true');$('#list-view').setAttribute('aria-pressed','false')};$('#list-view').onclick=()=>{$('#library-cards').classList.add('list');$('#list-view').setAttribute('aria-pressed','true');$('#grid-view').setAttribute('aria-pressed','false')};
function previewWidth(narrow){$('#preview-frame').classList.toggle('narrow',narrow);$('#preview-narrow').setAttribute('aria-pressed',String(narrow));$('#preview-wide').setAttribute('aria-pressed',String(!narrow))}$('#preview-wide').onclick=()=>previewWidth(false);$('#preview-narrow').onclick=()=>previewWidth(true);
window.addEventListener('hashchange',()=>select(location.hash.slice(1)||'library'));window.addEventListener('beforeunload',e=>{if(dirty){e.preventDefault();e.returnValue=''}});document.addEventListener('keydown',e=>{if((e.metaKey||e.ctrlKey)&&e.key==='s'){e.preventDefault();saveDraft().catch(()=>{})}});
annotateNativeMotion(document);
annotateNativeGeometry();
const nativeGeometryObserver=new MutationObserver(()=>annotateNativeGeometry());
function observeNativeGeometry(){nativeGeometryObserver.observe(document.querySelector('.page-nav'),{childList:true,subtree:true});annotateNativeGeometry();}
observeNativeGeometry();window.addEventListener('pagehide',()=>nativeGeometryObserver.disconnect());window.addEventListener('pageshow',event=>{if(event.persisted)observeNativeGeometry()});
(async()=>{try{const j=await api('/api/site');DATA=j.site;MEDIA=j.media;TOKEN=j.token;REV=j.revision;SOURCE=j.sourceRevision;PUBLISHED=j.published||structuredClone(DATA);$('#dirty').textContent='草稿保存在本机';select(location.hash.slice(1)||'library');const release=await api('/api/release');if(release.state==='pushed')checkLive(release.revision);if(j.conflict)status('正本已在别处更新。请先导出草稿，再核对版本。','bad')}catch(e){status('内容读取失败：'+e.message,'bad')}})();

$('#reload-source').onclick=()=>{showDialog('载入最新正本？','<p>当前输入和已有草稿会保留在草稿历史中。载入后，可继续编辑最新版本。</p>','<button id="reload-confirm" class="primary">保留草稿历史并载入</button>');$('#reload-confirm').onclick=async()=>{try{clearTimeout(saveTimer);if(saving)await saving.catch(()=>{});const current=await api('/api/site');const j=await api('/api/reload-source',{revision:current.revision,site:DATA});DATA=j.site;REV=j.revision;SOURCE=j.sourceRevision;PUBLISHED=structuredClone(DATA);setDirty(false);$('#dlg').close();select(sel);status('已载入正本。之前的输入可在草稿历史中找回。')}catch(e){status(e.message,'bad')}}};
