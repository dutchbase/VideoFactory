"""Approved 3D blocks work outside the source video, for the house brand and independent callers."""
import json
import random
import re
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parent.parent
BLOCKS=ROOT/'library/blocks'
IDS=('room-3d','cube-3d','cards-3d','prompt-layers-3d')
API={'room-3d':'room3d','cube-3d':'cube3d','cards-3d':'cards3d','prompt-layers-3d':'promptLayers3d'}

class Files(unittest.TestCase):
    def test_block_packages(self):
        import libcore
        for name in IDS:
            with self.subTest(block=name):
                metadata=BLOCKS/name/'block.md'
                self.assertTrue(metadata.is_file(),f'missing {name}')
                data=libcore.frontmatter(metadata.read_text())
                self.assertEqual(data['id'],name)
                for file in data['files']:
                    self.assertTrue((metadata.parent/file).is_file(),file)
                for dependency in data['depends']:
                    self.assertTrue((BLOCKS/dependency/'block.md').is_file(),dependency)
                self.assertTrue((metadata.parent/'demo.html').is_file())

    def test_local_brand_assets(self):
        for name in IDS:
            for path in (BLOCKS/name).glob('*'):
                if path.suffix not in {'.js','.css','.html'}:continue
                text=path.read_text()
                self.assertIsNone(re.search(r'#[0-9a-fA-F]{3,8}\b|\brgba?\(|\bhsla?\(',text),str(path))
                self.assertIsNone(re.search(r'gradient\(|blur\(|setInterval\(|setTimeout\(|requestAnimationFrame\(|Date.now\(|Math.random\(',text),str(path))
                self.assertNotIn('https://',text,str(path))

class Browser(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from playwright.sync_api import sync_playwright
        cls.pw=sync_playwright().start();cls.browser=cls.pw.chromium.launch()
    @classmethod
    def tearDownClass(cls):cls.browser.close();cls.pw.stop()

    def load(self,name):
        path=BLOCKS/name/'demo.html';self.assertTrue(path.is_file(),f'missing demo: {name}')
        p=self.browser.new_page(viewport={'width':1080,'height':1920});errors=[]
        p.on('pageerror',lambda e:errors.append(str(e)));p.goto(path.as_uri())
        p.evaluate('()=>document.fonts.ready')
        for block in ['cube-3d','cards-3d','prompt-layers-3d']:
            p.add_script_tag(path=str(BLOCKS/block/(block+'.js')))
        self.assertEqual(errors,[])
        self.assertTrue(p.evaluate('!!(window.__timelines && window.__timelines.main)'))
        return p,errors

    def seek(self,p,t):p.evaluate('async t=>{window.__timelines.main.seek(t);await new Promise(requestAnimationFrame);await new Promise(requestAnimationFrame)}',t)

    def test_standalone_brand_and_seek(self):
        for name in IDS:
            p,errors=self.load(name)
            try:
                if name=='cards-3d':
                    strokes=p.locator('.b-card-icon svg').evaluate_all("els=>els.map(e=>getComputedStyle(e).stroke)")
                    self.assertTrue(strokes and all(stroke!='none' for stroke in strokes),strokes)
                for brand in ['videofactory']:
                    p.add_script_tag(path=str(ROOT/'brands'/brand/'tokens.js'))
                    p.add_script_tag(path=str(ROOT/'_runtime/hf-bridge.js'));p.evaluate('()=>document.fonts.ready')
                    times=[0,.6,2,3.6,4.3,6.6,8.4,9.9];images={}
                    for t in times:self.seek(p,t);images[t]=p.screenshot()
                    random.Random(17).shuffle(times)
                    for t in times:
                        self.seek(p,t);self.assertTrue(images[t]==p.screenshot(),(name,brand,t))
                self.assertEqual(errors,[])
                self.assertTrue(p.evaluate('window.__timelines.main.paused()'))
            finally:p.close()

    def test_raw_api_seek_without_demo_fixture(self):
        for name,action in [('cube-3d','b.turn(1,1.2)'),('cards-3d','b.spread(1);b.select(1,3.5)'),('cards-3d','b.select(1,1)'),('prompt-layers-3d','b.explode(1);b.assemble(4)')]:
            p,errors=self.load(name)
            try:
                p.evaluate("""([name,action])=>{window.__timelines.main.kill();const root=document.getElementById('stage');root.replaceChildren();const tl=gsap.timeline({paused:true}),b=Blocks[name](Blocks.core(tl),root);if(name==='cube3d'){b.front.textContent='FRONT';b.next.textContent='NEXT';}new Function('b',action)(b);tl.set(b.el,{visibility:'visible'},10);window.__timelines.main=tl}""",[API[name],action])
                times=[0,.4,1.6,3,4.6,6,9.9];images={}
                for t in times:self.seek(p,t);images[t]=p.screenshot()
                for t in reversed(times):
                    self.seek(p,t);self.assertTrue(images[t]==p.screenshot(),(name,action,t))
                self.assertEqual(errors,[])
            finally:p.close()

    def test_constructor_only_dom_and_independence(self):
        p,errors=self.load('prompt-layers-3d')
        try:
            result=p.evaluate('''()=>{
              const results=[];
              for(const name of ['cube3d','cards3d','promptLayers3d']){
                const root=document.createElement('div');document.body.append(root);
                const ta=gsap.timeline({paused:true}),tb=gsap.timeline({paused:true});
                const a=Blocks[name](Blocks.core(ta),root),b=Blocks[name](Blocks.core(tb),root);
                results.push(ta.getChildren().length===0 && tb.getChildren().length===0 && a.el!==b.el);
                const target=name==='cube3d'?b.object:name==='cards3d'?b.cards[0]:b.layers[0];
                const before=getComputedStyle(target).transform;
                if(name==='cube3d')a.turn(0,1);
                if(name==='cards3d')a.spread(0);
                if(name==='promptLayers3d')a.explode(0);
                ta.seek(.8);results.push(before===getComputedStyle(target).transform);
                root.remove();ta.kill();tb.kill();
              }return results;
            }''')
            self.assertTrue(all(result),result);self.assertEqual(errors,[])
        finally:p.close()

    def test_physical_faces_keep_their_dimensions(self):
        p,_=self.load('cards-3d')
        try:
            dimensions=p.locator('.b-solid > .b-face3d').evaluate_all("els=>els.map(e=>[e.offsetWidth,e.offsetHeight,parseFloat(e.style.width),parseFloat(e.style.height)])")
            self.assertTrue(all(w==expected_w and h==expected_h for w,h,expected_w,expected_h in dimensions),dimensions)
            small=p.evaluate("""()=>{const root=document.createElement('div');document.body.append(root);const H=Blocks.core(gsap.timeline({paused:true})),space=Blocks.room3d.scene(H,root),s=Blocks.room3d.solid(H,space.camera,10,10,1);return [...s.el.children].map(e=>[e.offsetWidth,e.offsetHeight,parseFloat(e.style.width),parseFloat(e.style.height)])}""")
            self.assertTrue(all(w==expected_w and h==expected_h for w,h,expected_w,expected_h in small),small)
        finally:p.close()

    def test_indices_durations_and_literal_text(self):
        p,_=self.load('cube-3d')
        try:
            result=p.evaluate('''()=>{
              const H=Blocks.core(gsap.timeline({paused:true})),root=document.createElement('div');
              const cube=Blocks.cube3d(H,root),cards=Blocks.cards3d(H,root,{cards:['<script>bad</script>','A','B']});
              const checks=[cards.el.querySelectorAll('script').length===0,cards.el.textContent.includes('<script>')];
              for(const run of [()=>cube.turn(0,0),()=>cube.turn(0,-1),()=>cube.turn(0,Infinity),()=>cube.turn(0,NaN),()=>cards.select(-1,0),()=>cards.select(3,0),()=>cards.select(.5,0)]){
                try{run();checks.push(false)}catch(e){checks.push(e instanceof RangeError)}
              }
              for(const dimensions of [[0,10,10],[10,-1,10],[10,10,Infinity],[NaN,10,10]]){
                const before=root.children.length;
                try{Blocks.room3d.solid(H,root,...dimensions);checks.push(false)}catch(e){checks.push(e instanceof RangeError && root.children.length===before)}
              }H.tl.kill();return checks;
            }''')
            self.assertTrue(all(result),result)
        finally:p.close()

if __name__=='__main__':unittest.main()
