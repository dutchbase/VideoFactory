(function(){
const {scene:sceneObject,solid,drawing,duration:positiveDuration}=Blocks.room3d;
Blocks.promptLayers3d=function(H,root,options={}) {
  const s=sceneObject(H,root);s.el.classList.add("b-prompt-layers3d");const texts=options.layers||[['ROLE','You help me plan my week.'],['TASK','Sort my tasks for tomorrow.'],['EXAMPLE','Start with the most important task.'],['RULES','Give three concrete steps.']];
  s.camera.style.transform='translateZ(-260px) rotateX(-12deg) rotateY(-18deg)';
  const layers=texts.map(([label,text],i)=>{
    const layer=solid(H,s.camera,780,150,28);layer.el.style.transform=`translateY(${i*154}px) translateZ(${i*20}px)`;
    H.mk('span','b-layer-name b-reading',layer.front,label);H.mk('p','b-layer-body b-reading',layer.front,text);return layer.el;
  });
  function explode(at) {layers.forEach((layer,i)=>H.tl.fromTo(layer,{x:0,y:i*154,z:i*20},{x:(i-1.5)*20,y:i*180,z:(3-i)*110,duration:2,ease:'power2.inOut',immediateRender:false},at));}
  function assemble(at) {layers.forEach((layer,i)=>H.tl.to(layer,{x:0,y:i*154,z:0,duration:1.5,ease:'power3.inOut'},at));}
  return {...s,layers,explode,assemble};
};
})();
