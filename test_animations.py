"""Animation presentation contract tests using a minimal DOM (not visual tests)."""
import json
import unittest
from pathlib import Path
import quickjs

STUB = r'''
const nodes=[];
class Element {
 constructor(tag){this.tagName=tag;this.children=[];this.style={};this.hidden=false;this.open=false;this.textContent='';this.events={};this.classList={remove(){},add(){}};nodes.push(this)}
 append(...n){this.children.push(...n)} prepend(...n){this.children.unshift(...n)} replaceChildren(...n){this.children=n}
 setAttribute(){} addEventListener(k,f){this.events[k]=f} showModal(){this.open=true} close(){this.open=false} focus(){}
 animate(){let finish;const finished=new Promise(r=>finish=r);const a={finished,finish};animations.push(a);return a}
}
const animations=[];let reduce=false;
const window=globalThis;const document={body:new Element('body'),hidden:false,createElement:t=>new Element(t),addEventListener(){}};
const matchMedia=()=>({matches:reduce});const setTimeout=()=>1,clearTimeout=()=>{};
const item={id:'a',name:'Test prize',value:500,img:'test.svg'};
window.MESH_ITEMS=[item];
let done=false,failure='';
function run(j){done=false;MeshFX.waiting(j.action);MeshFX.result(j,[{id:'c',drops:[['a',100]]}]).then(()=>done=true,e=>failure=String(e))}
'''

class AnimationTests(unittest.TestCase):
    def setUp(self):
        self.ctx=quickjs.Context()
        self.ctx.eval(STUB)
        self.ctx.eval(Path('animations.js').read_text())

    def drain(self):
        while self.ctx.execute_pending_job():
            pass
        self.assertEqual(self.ctx.eval('failure'), '')

    def test_open_skip_preserves_server_prize(self):
        self.ctx.eval("run({action:'open',case_id:'c',prize:{item}})")
        self.assertFalse(self.ctx.eval('done'))
        self.ctx.eval("nodes.find(n=>n.textContent==='Показать результат').onclick()")
        self.drain()
        self.assertTrue(self.ctx.eval('done'))
        self.assertIn('Test prize',self.ctx.eval("nodes.find(n=>n.className==='fx-status').textContent"))

    def test_reduced_motion(self):
        self.ctx.eval("reduce=true;run({action:'open',case_id:'c',prize:{item}})")
        self.drain()
        self.assertTrue(self.ctx.eval('done'))
        self.assertEqual(self.ctx.eval('animations.length'),0)

    def test_upgrade_success_and_failure(self):
        for success in (True,False):
            self.ctx.eval('run({action:"upgrade",source:item,target:item,chance:5,success:'+json.dumps(success)+',prize:{item}})')
            self.ctx.eval('animations[animations.length-1].finish()')
            self.drain()
            self.assertTrue(self.ctx.eval('done'))
            self.assertEqual(self.ctx.eval("nodes.find(n=>n.tagName==='h2').textContent"),'Апгрейд успешен' if success else 'Апгрейд не удался')

    def test_error_allows_close(self):
        self.ctx.eval("MeshFX.waiting('open');MeshFX.error('Network error')")
        self.assertFalse(self.ctx.eval("nodes.find(n=>n.textContent==='Готово').hidden"))
        self.assertEqual(self.ctx.eval("nodes.find(n=>n.className==='fx-status').textContent"),'Network error')

if __name__=='__main__':unittest.main()
