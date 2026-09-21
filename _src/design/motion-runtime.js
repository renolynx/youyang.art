/** Consumer metadata only. Shared motion implementation and rendered content stay authoritative. */
(()=>{
 const mounts=new WeakMap();
 const mount=node=>{let id=mounts.get(node);if(!id){id=crypto.randomUUID();mounts.set(node,id);}return id;};
 const stamp=()=>{
  for(const node of document.querySelectorAll('[data-motion-surface="website"][data-motion-entity],[data-motion-surface="cms-preview"][data-motion-entity]')){
   const physical=mount(node);node.dataset.motionMount=physical;node.dataset.motionId=node.dataset.motionEntity+'-'+physical;
  }
  const nav=document.querySelector('.site-nav[data-motion-surface="website"],.site-nav[data-motion-surface="cms-preview"]');
  if(!nav)return;
  const geometry=nav.dataset.motionSurface==='cms-preview'?'preview-navigation-geometry':'website-navigation-geometry';
  for(const rect of nav.querySelectorAll('.ys-motion-tabs-fluid rect')){
   const physical=mount(rect);rect.dataset.motionMount=physical;
   rect.dataset.motionId=geometry+'-'+physical;
   rect.dataset.motionEntity=geometry;
   rect.dataset.motionSurface=nav.dataset.motionSurface;rect.dataset.motionAction='navigation-geometry';
   rect.dataset.motionOwner=nav.dataset.motionEntity;
   rect.dataset.motionBusinessKey=nav.dataset.motionBusinessKey;
  }
 };
 let observer;
 const attach=()=>{stamp();if(observer)return;observer=new MutationObserver(stamp);observer.observe(document.documentElement,{childList:true,subtree:true});};
 window.YouyangMotionInventory={stamp};
 attach();
 addEventListener('pagehide',()=>{observer?.disconnect();observer=null;});
 addEventListener('pageshow',event=>{if(event.persisted)attach();});
})();
