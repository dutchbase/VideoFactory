(function(){
window.Blocks=window.Blocks||{};
const NS='http://www.w3.org/2000/svg';
function drawing(parent,paths) {
  const svg=document.createElementNS(NS,'svg'); svg.setAttribute('viewBox','0 0 240 220');
  svg.setAttribute('aria-hidden','true'); parent.append(svg);
  paths.forEach(([d,accent])=>{const p=document.createElementNS(NS,'path');p.setAttribute('d',d);if(accent)p.setAttribute('class','b-accent-plate');svg.append(p);});
}
function sceneObject(H,root) {
  const el=H.mk('section','b-space3d',root),camera=H.mk('div','b-camera3d',el);
  const shadow=document.createElementNS(NS,'svg');shadow.setAttribute('class','b-shadow3d');shadow.setAttribute('viewBox','0 0 760 120');
  const face=document.createElementNS(NS,'path');face.setAttribute('d','M0 40L620 0L760 70L140 120Z');shadow.append(face);el.prepend(shadow);
  return {el,camera,shadow};
}
function solid(H,parent,width,height,depth) {
  if(![width,height,depth].every(v=>Number.isFinite(v)&&v>0))throw new RangeError('solid dimensions must be positive and finite');
  const el=H.mk('div','b-solid',parent);Object.assign(el.style,{width:width+'px',height:height+'px'});
  const faces={};
  for(const name of ['front','back','right','left','top','bottom']) {
    const face=H.mk('div','b-face3d b-'+name+(name==='front'?'':' b-side3d'),el);faces[name]=face;
    const horizontal=name==='left'||name==='right',vertical=name==='top'||name==='bottom';
    const w=horizontal?depth:width,h=vertical?depth:height;
    Object.assign(face.style,{width:w+'px',height:h+'px',left:(width-w)/2+'px',top:(height-h)/2+'px'});
    const transform={front:`translateZ(${depth/2}px)`,back:`rotateY(180deg) translateZ(${depth/2}px)`,right:`rotateY(90deg) translateZ(${width/2}px)`,left:`rotateY(-90deg) translateZ(${width/2}px)`,top:`rotateX(90deg) translateZ(${height/2}px)`,bottom:`rotateX(-90deg) translateZ(${height/2}px)`};
    face.style.transform=transform[name];
    face.style.borderWidth=Math.floor(Math.min(name==='front'?6:4,w/2,h/2))+'px';
  }
  return {el,...faces};
}
function positiveDuration(duration) {if(!Number.isFinite(duration)||duration<=0)throw new RangeError('duration must be positive and finite');}

Blocks.room3d={scene:sceneObject,solid,drawing,duration:positiveDuration};
})();
