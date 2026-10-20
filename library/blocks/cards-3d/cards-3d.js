(function(){
const {scene:sceneObject,solid,drawing,duration:positiveDuration}=Blocks.room3d;
Blocks.cards3d=function(H,root,options={}) {
  const s=sceneObject(H,root);s.el.classList.add("b-cards3d");const texts=options.cards||['MAIL','PLANNING','IDEAS'];
  s.camera.style.transform='translateZ(-160px) rotateX(-18deg) rotateY(-12deg)';
  const cards=texts.map((text,i)=>{
    const card=solid(H,s.camera,740,350,36);card.el.style.transform=`translateY(${i*28}px) translateZ(${-i*50}px) rotateZ(${i*3}deg)`;
    H.mk('h2','b-head3d b-reading',card.front,text);
    const icon=H.mk('div','b-card-icon',card.front);
    const drawings=[[['M25 50H215V175H25Z',true],['M25 50L120 125L215 50']], [['M40 40H200V195H40Z',true],['M40 85H200 M75 20V60 M165 20V60 M75 120H110 M135 120H170 M75 155H110']], [['M85 150C25 85 75 25 120 25C165 25 215 85 155 150V180H85Z',true],['M85 205H155 M120 55V110']]];
    drawing(icon,drawings[i%3]);return card.el;
  });
  // Normalize the starting rotations once on the timeline, before any caller seeks backward.
  const init=()=>cards.forEach((card,i)=>H.tl.set(card,{x:0,y:i*28,z:-i*50,rotationZ:i*3,immediateRender:true},0));
  // shortcut: fan geometry is tuned for three choices; size it from count when another layout is needed.
  function spread(at) {init();cards.forEach((card,i)=>H.tl.fromTo(card,{x:0,y:i*28,z:-i*50,rotationZ:i*3},{x:(i-1)*40,y:-180+i*340,z:-Math.abs(i-1)*45,rotationZ:(i-1)*8,duration:1.8,ease:'power2.inOut',immediateRender:false},at));}
  function select(index,at) {
    if(!Number.isInteger(index)||index<0||index>=cards.length)throw new RangeError('card index out of range');
    init();
    cards.forEach((card,i)=>H.tl.to(card,{x:i===index?0:(i-index)*80,y:i===index?90:280,z:i===index?230:-140,rotationZ:i===index?0:(i-index)*8,duration:1.2,ease:'power3.inOut'},at));
  }
  return {...s,cards,spread,select};
};
})();
