(function(){
const {scene:sceneObject,solid,drawing,duration:positiveDuration}=Blocks.room3d;
Blocks.cube3d=function(H,root) {
  const s=sceneObject(H,root);s.el.classList.add("b-cube3d");const cube=solid(H,s.camera,740,740,740);
  s.camera.style.transform='translateZ(-260px) rotateX(-14deg) rotateY(-22deg)';
  const turn=(at,duration)=>{positiveDuration(duration);H.tl.fromTo(cube.el,{rotationY:0},{rotationY:-90,duration,ease:'power2.inOut',immediateRender:false},at);};
  return {...s,object:cube.el,front:cube.front,next:cube.right,turn};
};
})();
