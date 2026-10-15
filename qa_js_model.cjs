/* Execute the actual offline HTML script in a small DOM harness.
   This checks numerical and control behavior, not browser layout or rendering. */
const fs=require("fs"),path=require("path"),vm=require("vm"),assert=require("assert");
const root=__dirname,html=fs.readFileSync(path.join(root,"BRIDLE-Thermal-Lab-v0.5.html"),"utf8");
let selectedBlob=null;
class Element{
  constructor(tag,attrs="",body=""){
    this.tagName=tag;this.attrs={};this.listeners={};this.dataset={};
    for(const m of attrs.matchAll(/([a-zA-Z][\w-]*)(?:="([^"]*)")?/g))this.attrs[m[1]]=m[2]===undefined?true:m[2];
    this.options=[...body.matchAll(/<option value="([^"]*)"/g)].map(m=>m[1]);
    this._value=this.attrs.value||this.options[0]||"";
    this.checked=this.attrs.checked===true;this.textContent="";this.innerHTML="";
    this.style={};this.className="";
    this.classList={add:(v)=>{this.className+=" "+v;}};
    for(const [k,v] of Object.entries(this.attrs))if(k.startsWith("data-"))this.dataset[k.slice(5)]=v;
  }
  get value(){return String(this._value);}
  set value(v){this._value=this.tagName==="select"&&!this.options.includes(String(v))?"":String(v);}
  addEventListener(name,fn){(this.listeners[name]??=[]).push(fn);}
  setAttribute(name,v){this.attrs[name]=String(v);}
  click(){this.fire("click");}
  fire(name){for(const fn of this.listeners[name]||[])fn({target:this});}
}
const elements=new Map();
for(const m of html.matchAll(/<([a-z]+)\b([^>]*\bid="[^"]+"[^>]*)>/g)){
  const id=/\bid="([^"]+)"/.exec(m[2])[1];
  let body="";
  if(m[1]==="select"){const end=html.indexOf("</select>",m.index);body=html.slice(m.index,end);}
  elements.set(id,new Element(m[1],m[2],body));
}
const buttons=[...html.matchAll(/<button\b([^>]*data-preset="[^"]+"[^>]*)>/g)].map(m=>new Element("button",m[1]));
const document={
  getElementById:id=>{assert(elements.has(id),"Missing DOM element "+id);return elements.get(id);},
  querySelectorAll:selector=>{assert.equal(selector,"[data-preset]");return buttons;},
  createElement:tag=>new Element(tag)
};
const scope={document,console,Blob,Math,Number,Infinity,JSON,setTimeout:fn=>fn(),
  URL:{createObjectURL:b=>{selectedBlob=b;return "blob:harness";},revokeObjectURL:()=>{}}};
scope.window=scope;
vm.createContext(scope);
const script=/<script>([\s\S]*?)<\/script>/.exec(html)[1];
vm.runInContext(script,scope,{timeout:30000});
const api=scope.bridleModel,reference=JSON.parse(fs.readFileSync(path.join(root,"results/model-results.json"),"utf8"));
const cases=[];
for(const row of reference.local_cases){
  const p={shared:row.shared,main:row.main,reserve:row.reserve,sw:row.mode==="switch",low:row.mode==="high"?0.4:0.02,horizon:12};
  const got=api.simulate(p);
  assert(Math.abs(got.peak-row.affected_peak)<0.0005,row.label+" affected peak");
  assert(Math.abs(got.other-row.other_peak)<0.0005,row.label+" other peak");
  cases.push({label:row.label,affected:got.peak,other:got.other});
}
function preset(name){buttons.find(b=>b.dataset.preset===name).click();}
preset("reserve");assert.equal(elements.get("peak-main").textContent,"1.205");
assert(elements.get("interpretation").innerHTML.includes("never activates"));
preset("window");assert(elements.get("status").textContent.includes("Within window"));
assert(elements.get("all-time").innerHTML.includes("exceeds"));
preset("shared");assert(elements.get("status").textContent.includes("exceeded"));
preset("larger");assert(elements.get("all-time").innerHTML.includes("satisfies"));
elements.get("main").value="0.21";elements.get("main").fire("input");
assert.equal(api.getCurrent().params.main,0.21);
assert.equal(elements.get("main-value").textContent,"0.21");
preset("switched");elements.get("switch").checked=false;elements.get("switch").fire("change");
assert.equal(elements.get("peak-main").textContent,"1.852");
preset("reserve");elements.get("export").click();assert(selectedBlob);
assert(!elements.get("chart").innerHTML.includes("NaN"));
assert(!/\b(?:fetch|XMLHttpRequest|WebSocket)\b/.test(script));
async function finish(){
  const csv=await selectedBlob.text();
  assert(csv.includes("theta_5")&&csv.split("\n").length>1000);
  const eventual=api.eventual(.5);
  assert(Math.abs(eventual-reference.exponential_reserve.current_theta_infinity)<1e-7);
  const result={method:"Actual HTML script executed in a minimal DOM harness",
    limitation:"No real-browser layout, pointer interaction or rendering check completed",
    numerical_cases:cases,checks:["All eight JS cases match adaptive Python peaks within 0.0005","Preset state and displayed statistics","Finite-window late-failure warning","Shared-fault warning","Larger-reserve all-time result","Range and switch controls","Trajectory CSV contents","Finite SVG coordinates","No scripted network access","All-time quadrature matches gamma solution within 1e-7"]};
  fs.writeFileSync(path.join(root,"results/javascript-checks.json"),JSON.stringify(result,null,2));
  console.log(JSON.stringify(result,null,2));
}
finish().catch(e=>{console.error(e);process.exit(1);});
