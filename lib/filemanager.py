import os
import json
import ampule
from __main__ import display, refresh
def _hide_display():
    try:
        from __main__ import display
        display.root_group.hidden = True
    except: pass

def _show_display(msg=None, color="green"):
    try:
        from __main__ import display, pprint, refresh
        display.root_group.hidden = False
        if msg:
            pprint(msg, line=0, color=color)
        refresh()
    except: pass

def _ls(path):
    items = []
    for name in sorted(os.listdir(path)):
        fp = path.rstrip("/") + "/" + name
        try:
            s = os.stat(fp)
            is_dir = s[0] & 0x4000
            items.append({"n": name, "d": 1 if is_dir else 0, "s": s[6] if not is_dir else 0})
        except:
            items.append({"n": name, "d": 0, "s": 0})
    return items

def _norm(p):
    parts = []
    for seg in p.replace("\\", "/").split("/"):
        if seg == "..":
            if parts: parts.pop()
        elif seg and seg != ".":
            parts.append(seg)
    return "/" + "/".join(parts)

@ampule.route("/fm/ls", method="POST")
def _fm_ls(request):
    path = _norm(request.headers.get("x-path", "/"))
    try:
        return (200, {}, json.dumps({"path": path, "items": _ls(path)}))
    except Exception as e:
        return (200, {}, json.dumps({"error": str(e)}))

@ampule.route("/fm/read", method="POST")
def _fm_read(request):
    path = _norm(request.headers.get("x-path", ""))
    try:
        with open(path, "r") as f:
            return (200, {}, json.dumps({"path": path, "text": f.read()}))
    except Exception as e:
        return (200, {}, json.dumps({"error": str(e)}))

@ampule.route("/fm/write", method="POST")
def _fm_write(request):
    path = _norm(request.headers.get("x-path", ""))
    try:
        _hide_display()
        
        with open(path, "w") as f:
            display.root_group.hidden = True; refresh()
            f.write(request.body)
        _show_display("Saved: " + path.split("/")[-1])
        display.root_group.hidden = False
        return (200, {}, json.dumps({"ok": True}))
    except Exception as e:
        _show_display(str(e), "red")
        return (200, {}, json.dumps({"error": str(e)}))

@ampule.route("/fm/mkdir", method="POST")
def _fm_mkdir(request):
    path = _norm(request.headers.get("x-path", ""))
    try:
        _hide_display()
        os.mkdir(path)
        _show_display("Created: " + path.split("/")[-1])
        return (200, {}, json.dumps({"ok": True}))
    except Exception as e:
        _show_display(str(e), "red")
        return (200, {}, json.dumps({"error": str(e)}))

@ampule.route("/fm/del", method="POST")
def _fm_del(request):
    path = _norm(request.headers.get("x-path", ""))
    if path == "/":
        return (200, {}, json.dumps({"error": "Cannot delete root"}))
    try:
        s = os.stat(path)
        _hide_display()
        if s[0] & 0x4000:
            _rmdir(path)
        else:
            os.remove(path)
        _show_display("Deleted: " + path.split("/")[-1])
        return (200, {}, json.dumps({"ok": True}))
    except Exception as e:
        _show_display(str(e), "red")
        return (200, {}, json.dumps({"error": str(e)}))

def _rmdir(path):
    for name in os.listdir(path):
        fp = path.rstrip("/") + "/" + name
        s = os.stat(fp)
        if s[0] & 0x4000:
            _rmdir(fp)
        else:
            os.remove(fp)
    os.rmdir(path)

@ampule.route("/fm", method="GET")
def _fm_page(request):
    return (200, {}, """<!DOCTYPE html>
<html lang="en"><head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>File Manager</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{background:#0c0c0c;color:#ccc;font-family:'Segoe UI',system-ui,sans-serif;height:100vh;display:flex;flex-direction:column;overflow:hidden}
#toolbar{background:#1a1a2e;padding:6px 12px;display:flex;align-items:center;gap:8px;border-bottom:1px solid #333;flex-shrink:0}
#toolbar span{color:#7c7cff;font-weight:700;font-size:.85rem}
.tbtn{color:#888;text-decoration:none;font-size:.78rem;padding:4px 10px;border-radius:6px;background:#222;border:1px solid #333;cursor:pointer}
.tbtn:hover{color:#fff;border-color:#7c7cff}
#path-bar{background:#111;padding:5px 12px;border-bottom:1px solid #292929;font-size:.8rem;color:#7c7cff;display:flex;align-items:center;gap:4px;flex-shrink:0;flex-wrap:wrap}
#path-bar span{cursor:pointer;padding:2px 4px;border-radius:4px}
#path-bar span:hover{background:#222}
#listing{flex:1;overflow-y:auto;padding:0}
.row{display:flex;align-items:center;padding:8px 14px;border-bottom:1px solid #1a1a1a;cursor:pointer;gap:10px;font-size:.88rem}
.row:hover{background:#151528}
.row.selected{background:#1e1e3a}
.row .icon{width:20px;text-align:center;flex-shrink:0;font-size:1rem}
.row .name{flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.row .size{color:#666;font-size:.75rem;width:60px;text-align:right;flex-shrink:0}
.row .acts{display:flex;gap:4px;flex-shrink:0}
.abtn{background:#222;border:1px solid #333;color:#888;font-size:.7rem;padding:3px 8px;border-radius:5px;cursor:pointer}
.abtn:hover{color:#fff;border-color:#7c7cff}
.abtn.del:hover{color:#ff5050;border-color:#ff5050}
#editor{display:none;flex-direction:column;flex:1;overflow:hidden}
#editor-bar{background:#1a1a2e;padding:6px 12px;display:flex;align-items:center;gap:8px;border-bottom:1px solid #333;flex-shrink:0}
#editor-bar span{color:#e8e8e8;font-size:.82rem;flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
#editor-area{flex:1;background:#0c0c0c;color:#e0e0e0;border:none;padding:10px 14px;font-family:'Cascadia Mono','Fira Code','Consolas',monospace;font-size:.84rem;resize:none;outline:none;tab-size:4;line-height:1.5}
#modal-bg{display:none;position:fixed;inset:0;background:rgba(0,0,0,.6);z-index:100;align-items:center;justify-content:center}
#modal{background:#1a1a2e;border:1px solid #333;border-radius:10px;padding:18px;width:280px}
#modal h3{font-size:.9rem;color:#7c7cff;margin-bottom:12px}
#modal input{width:100%;background:#111;border:1px solid #333;color:#e8e8e8;padding:8px;border-radius:6px;font-size:.85rem;outline:none;margin-bottom:10px}
#modal input:focus{border-color:#7c7cff}
#modal-btns{display:flex;gap:8px;justify-content:flex-end}
</style>
</head><body>
<div id="toolbar">
<span>&#x1F4C1; File Manager</span>
<div style="flex:1"></div>
<button class="tbtn" onclick="newFile()">&#x2795; File</button>
<button class="tbtn" onclick="newDir()">&#x1F4C1;+ Dir</button>
<a class="tbtn" href="/">Home</a>
</div>
<div id="path-bar"></div>
<div id="listing"></div>
<div id="editor">
<div id="editor-bar">
<span id="editor-name"></span>
<button class="tbtn" onclick="saveFile()" id="saveBtn">&#x1F4BE; Save</button>
<button class="tbtn" onclick="closeEditor()">&#x2715; Close</button>
</div>
<textarea id="editor-area" spellcheck="false"></textarea>
</div>
<div id="modal-bg" onclick="closeModal()">
<div id="modal" onclick="event.stopPropagation()">
<h3 id="modal-title"></h3>
<input id="modal-input" autocomplete="off">
<div id="modal-btns">
<button class="tbtn" onclick="closeModal()">Cancel</button>
<button class="tbtn" id="modal-ok" style="background:#7c7cff;color:#000;border-color:#7c7cff">OK</button>
</div>
</div>
</div>
<script>
var cwd="/";
function api(ep,path,body){
 var h={"X-Path":path||"/"};
 var opts={method:"POST",headers:h};
 if(body!==undefined){opts.body=body}
 return fetch(ep,opts).then(function(r){return r.json()});
}
function fmtSize(b){
 if(b<1024)return b+" B";
 if(b<1048576)return (b/1024|0)+" KB";
 return (b/1048576).toFixed(1)+" MB";
}
function renderPath(){
 var el=document.getElementById("path-bar");
 var parts=cwd.split("/").filter(Boolean);
 var html='<span onclick="go(\\'/'+'\\')">&#x1F4C0; /</span>';
 var p="";
 for(var i=0;i<parts.length;i++){
  p+="/"+parts[i];
  html+=' / <span onclick="go(\\''+p+'\\')">'+parts[i]+'</span>';
 }
 el.innerHTML=html;
}
function enc(p){return p.split("/").map(encodeURIComponent).join("/");}
function go(path){location.hash=enc(path||"/");}
function doList(path){
 cwd=path||"/";
 document.getElementById("editor").style.display="none";
 document.getElementById("listing").style.display="block";
 renderPath();
 api("/fm/ls",cwd).then(function(d){
  if(d.error){alert(d.error);return}
  var el=document.getElementById("listing");
  var html="";
  if(cwd!=="/"){
   html+='<div class="row" ondblclick="go(\\''+parentDir()+'\\')" onclick="go(\\''+parentDir()+'\\')"><span class="icon">&#x1F4C2;</span><span class="name" style="color:#7c7cff">..</span><span class="size"></span><span class="acts"></span></div>';
  }
  for(var i=0;i<d.items.length;i++){
   var it=d.items[i];
   var fp=cwd.replace(/\\/$/,"")+"/" +it.n;
   if(it.d){
    html+='<div class="row" ondblclick="go(\\''+fp+'\\')" onclick="go(\\''+fp+'\\')"><span class="icon">&#x1F4C1;</span><span class="name" style="color:#7c7cff">'+it.n+'</span><span class="size"></span><span class="acts"><button class="abtn del" onclick="event.stopPropagation();del(\\''+fp+'\\')">&#x1F5D1;</button></span></div>';
   }else{
    html+='<div class="row" ondblclick="edit(\\''+fp+'\\')" onclick="sel(this)"><span class="icon">&#x1F4C4;</span><span class="name">'+it.n+'</span><span class="size">'+fmtSize(it.s)+'</span><span class="acts"><button class="abtn" onclick="event.stopPropagation();edit(\\''+fp+'\\')">&#x270D;</button> <button class="abtn del" onclick="event.stopPropagation();del(\\''+fp+'\\')">&#x1F5D1;</button></span></div>';
   }
  }
  el.innerHTML=html;
 });
}
function parentDir(){
 var p=cwd.replace(/\\/$/,"");
 var i=p.lastIndexOf("/");
 return i<=0?"/":p.substring(0,i);
}
function sel(row){
 var prev=document.querySelector(".row.selected");
 if(prev)prev.classList.remove("selected");
 row.classList.add("selected");
}
function edit(fp){location.hash="f:"+enc(fp);}
function openEditor(fp){
 cwd=fp.substring(0,fp.lastIndexOf("/"))||"/";
 api("/fm/read",fp).then(function(d){
  if(d.error){alert(d.error);return}
  document.getElementById("listing").style.display="none";
  document.getElementById("editor").style.display="flex";
  document.getElementById("editor-name").textContent=fp;
  document.getElementById("editor-area").value=d.text;
  document.getElementById("editor-area").dataset.path=fp;
 });
}
function saveFile(){
 var ta=document.getElementById("editor-area");
 var btn=document.getElementById("saveBtn");
 btn.textContent="Saving...";
 api("/fm/write",ta.dataset.path,ta.value).then(function(d){
  if(d.error){alert(d.error);btn.textContent="\\u1F4BE Save";}
  else{btn.textContent="\\u2705 Saved";setTimeout(function(){btn.innerHTML="&#x1F4BE; Save"},1500);}
 });
}
function closeEditor(){go(cwd);}
function del(fp){
 var name=fp.split("/").pop();
 if(!confirm("Delete "+name+"?"))return;
 api("/fm/del",fp).then(function(d){
  if(d.error)alert(d.error);
  else doList(cwd);
 });
}
function showModal(title,cb){
 document.getElementById("modal-title").textContent=title;
 var inp=document.getElementById("modal-input");
 inp.value="";
 document.getElementById("modal-bg").style.display="flex";
 inp.focus();
 document.getElementById("modal-ok").onclick=function(){
  var v=inp.value.trim();
  if(v)cb(v);
  closeModal();
 };
 inp.onkeydown=function(e){if(e.key==="Enter"){document.getElementById("modal-ok").click()}};
}
function closeModal(){document.getElementById("modal-bg").style.display="none"}
function newFile(){
 showModal("New file name:",function(name){
  var fp=cwd.replace(/\\/$/,"")+"/"+name;
  api("/fm/write",fp,"").then(function(d){
   if(d.error)alert(d.error);
   else{edit(fp);}
  });
 });
}
function newDir(){
 showModal("New directory name:",function(name){
  var fp=cwd.replace(/\\/$/,"")+"/"+name;
  api("/fm/mkdir",fp).then(function(d){
   if(d.error)alert(d.error);
   else doList(cwd);
  });
 });
}
document.addEventListener("keydown",function(e){
 if(e.ctrlKey&&e.key==="s"){
  e.preventDefault();
  if(document.getElementById("editor").style.display==="flex")saveFile();
 }
});
function router(){
 var h=decodeURIComponent(location.hash.slice(1));
 if(h.slice(0,2)==="f:")openEditor(h.slice(2));
 else doList(h||"/");
}
window.addEventListener("hashchange",router);
if(location.hash.length>1)router();else go("/");
</script>
</body></html>""")
