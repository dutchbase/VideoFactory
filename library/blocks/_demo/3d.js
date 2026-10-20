// Demo-only fixtures for the approved portrait geometry. Real scenes use their own cue times.
window.Demo3D = {
  make(name,H,root) {
    const R=Blocks.room3d;
    const b=name==='room3d'?R.scene(H,root):Blocks[name](H,root);
    if(name==='room3d') {
      const slab=R.solid(H,b.camera,740,740,160);b.object=slab.el;
      H.mk('h2','b-head3d',slab.front,'DEPTH');R.drawing(slab.front,[['M35 65H140V20L220 110L140 200V155H35Z',true]]);
      b.camera.style.transform='translateZ(-260px) rotateX(-14deg) rotateY(-22deg)';
    }
    if(name==='cube3d') {
      H.mk('h2','b-head3d',b.front,'YOUR NEXT STEP');R.drawing(b.front,[['M35 65H140V20L220 110L140 200V155H35Z',true]]);
      H.mk('h2','b-head3d',b.next,'MAKE ROOM');R.drawing(b.next,[['M40 195V30H185V195Z',true],['M40 30L145 55V195 M115 120H135']]);
    }
    if(name==='cards3d')H.mk('h1','b-headline3d',b.el,'PICK YOUR TASK');
    if(name==='promptLayers3d')H.mk('h1','b-headline3d',b.el,'BUILD YOUR PROMPT');
    const pose=name==='cards3d'?[-18,-12,-160]:name==='promptLayers3d'?[-12,-18,-260]:[-14,-22,-260];
    H.tl.set(b.camera,{rotationX:pose[0],rotationY:pose[1],rotationZ:0,z:pose[2],force3D:true,immediateRender:true},0);
    H.tl.set(b.shadow,{x:0,scaleX:1,immediateRender:true},0);
    if(b.object)H.tl.set(b.object,{rotationY:0,immediateRender:true},0);
    if(b.cards)b.cards.forEach((card,i)=>H.tl.set(card,{x:0,y:i*28,z:-i*50,rotationZ:i*3,immediateRender:true},0));
    if(b.layers)b.layers.forEach((layer,i)=>H.tl.set(layer,{x:0,y:i*154,z:i*20,immediateRender:true},0));
    return b;
  },
  animate(name,H,b,t) {
    const tl=H.tl;
    if(name==='room3d') {
      tl.fromTo(b.object,{rotationY:0},{rotationY:-35,duration:2,ease:'power2.inOut',immediateRender:false},t+.4);
      tl.to(b.camera,{rotationX:0,rotationY:0,z:-400,duration:2},t+3);
      tl.to(b.object,{rotationY:25,duration:1.6},t+6.4);
    }
    if(name==='cube3d') {
      tl.fromTo(b.camera,{z:-260,rotationX:-14,rotationY:-22},{z:-520,rotationX:-12,rotationY:-18,duration:1.8,ease:'power2.inOut',immediateRender:false},t+.4);
      b.turn(t+3,1.2);tl.to(b.shadow,{scaleX:.8,x:60,duration:1.2},t+3);
      tl.to(b.camera,{z:-300,rotationX:0,rotationY:0,duration:1.8,ease:'power2.inOut'},t+4.6);
      tl.to(b.camera,{rotationX:-7,rotationY:12,duration:1.4,ease:'power2.inOut'},t+7.4);
    }
    if(name==='cards3d') {
      b.spread(t+.4);b.select(1,t+2.9);
      tl.to(b.shadow,{scaleX:.85,x:40,duration:1.2},t+2.9);
      tl.fromTo(b.camera,{rotationX:-18,rotationY:-12,z:-160},{rotationX:0,rotationY:0,z:-220,duration:1.6,ease:'power2.inOut',immediateRender:false},t+4.5);
      b.cards.forEach((card,i)=>{if(i!==1)tl.to(card,{y:340,z:-220,rotationZ:0,duration:1.1},t+7.2)});
      tl.to(b.camera,{rotationX:-5,rotationY:6,duration:1.1,ease:'power2.inOut'},t+7.2);
    }
    if(name==='promptLayers3d') {
      b.explode(t+.4);tl.fromTo(b.camera,{rotationX:-12,rotationY:-18,z:-260},{rotationX:-6,rotationY:-26,z:-430,duration:2,ease:'power2.inOut',immediateRender:false},t+.4);
      b.assemble(t+2.9);tl.to(b.shadow,{scaleX:.9,x:35,duration:1.5},t+2.9);
      tl.to(b.camera,{rotationX:0,rotationY:0,z:-40,duration:1.8,ease:'power2.inOut'},t+6);
      tl.to(b.camera,{rotationX:-5,rotationY:7,duration:.8,ease:'power2.inOut'},t+9.2);
    }
  }
};
