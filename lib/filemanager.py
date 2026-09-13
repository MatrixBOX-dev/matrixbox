import os
import json
import ampule
import load_settings
import web_interface
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

@ampule.route("/system/fm/ls", method="POST")
def _fm_ls(request):
    path = _norm(request.headers.get("x-path", "/"))
    try:
        return (200, {}, json.dumps({"path": path, "items": _ls(path)}))
    except Exception as e:
        return (200, {}, json.dumps({"error": str(e)}))

@ampule.route("/system/fm/read", method="POST")
def _fm_read(request):
    path = _norm(request.headers.get("x-path", ""))
    try:
        with open(path, "r") as f:
            return (200, {}, json.dumps({"path": path, "text": f.read()}))
    except Exception as e:
        return (200, {}, json.dumps({"error": str(e)}))

@ampule.route("/system/fm/write", method="POST")
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

@ampule.route("/system/fm/mkdir", method="POST")
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

@ampule.route("/system/fm/del", method="POST")
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

@ampule.route("/system/fm", method="GET")
def _fm_page(request):
    # Reached from the shared navbar's menu in both home and in-app
    # contexts, same as /system/settings -- see web_interface.navbar().
    in_app = bool(load_settings.app_running)
    content = """<style>
body{display:flex;flex-direction:column;height:100vh;overflow:hidden;padding-bottom:0!important}
.page{max-width:none!important;margin:0!important;padding:12px 0 0!important;flex:1;display:flex;flex-direction:column;min-height:0;overflow:hidden}
#toolbar{background:var(--surface);padding:8px 14px;display:flex;align-items:center;gap:8px;border-bottom:1px solid var(--border);flex-shrink:0}
#toolbar span{color:var(--text);font-weight:700;font-size:.85rem}
#path-bar{background:var(--surface);padding:6px 14px;border-bottom:1px solid var(--border);font-size:.8rem;color:var(--muted);display:flex;align-items:center;gap:4px;flex-shrink:0;flex-wrap:wrap}
#path-bar span{cursor:pointer;padding:2px 6px;border-radius:6px}
#path-bar span:hover{color:var(--text);background:var(--surface2)}
#listing{flex:1;overflow-y:auto;padding:0;min-height:0}
.row{display:flex;align-items:center;padding:9px 14px;border-bottom:1px solid var(--border);cursor:pointer;gap:10px;font-size:.88rem}
.row:hover{background:var(--surface2)}
.row .icon{width:20px;text-align:center;flex-shrink:0;font-size:1rem}
.row .name{flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;color:var(--text)}
.row .size{color:var(--muted);font-size:.75rem;width:60px;text-align:right;flex-shrink:0}
.row .acts{display:flex;gap:4px;flex-shrink:0}
.abtn{background:var(--surface2);border:1px solid var(--border);color:var(--muted);font-size:.7rem;padding:4px 9px;border-radius:6px;cursor:pointer}
.abtn:hover{color:var(--text);border-color:var(--accent)}
.abtn.del:hover{color:#ff6060;border-color:#ff6060}
#editor{display:none;flex-direction:column;flex:1;overflow:hidden;min-height:0}
#editor-bar{background:var(--surface);padding:8px 14px;display:flex;align-items:center;gap:8px;border-bottom:1px solid var(--border);flex-shrink:0}
#editor-bar span{color:var(--text);font-size:.82rem;flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
#editor-area{flex:1;background:var(--bg);color:var(--text);border:none;padding:12px 14px;font-family:'Cascadia Mono','Fira Code','Consolas',monospace;font-size:.84rem;resize:none;outline:none;tab-size:4;line-height:1.5}
#modal-bg{display:none;position:fixed;inset:0;background:rgba(0,0,0,.6);z-index:200;align-items:center;justify-content:center}
#modal{background:var(--surface2);border:1px solid var(--border);border-radius:var(--r-lg);padding:18px;width:280px;box-shadow:var(--shadow)}
#modal h3{font-size:.9rem;color:var(--text);margin-bottom:12px}
#modal input{width:100%;background:var(--surface);border:1px solid var(--border);color:var(--text);padding:9px 10px;border-radius:var(--r);font-size:.85rem;outline:none;margin-bottom:10px}
#modal input:focus{border-color:var(--accent)}
#modal-btns{display:flex;gap:8px;justify-content:flex-end}
</style>
<div id="toolbar">
<span>&#x1F4C1; File Manager</span>
<div style="flex:1"></div>
<button class="btn btn-sm" onclick="newFile()">&#x2795; File</button>
<button class="btn btn-sm" onclick="newDir()">&#x1F4C1;+ Dir</button>
</div>
<div id="path-bar"></div>
<div id="listing"></div>
<div id="editor">
<div id="editor-bar">
<span id="editor-name"></span>
<button class="btn btn-sm btn-success" onclick="saveFile()" id="saveBtn">&#x1F4BE; Save</button>
<button class="btn btn-sm btn-ghost" onclick="closeEditor()">&#x2715; Close</button>
</div>
<textarea id="editor-area" spellcheck="false"></textarea>
</div>
<div id="modal-bg" onclick="closeModal()">
<div id="modal" onclick="event.stopPropagation()">
<h3 id="modal-title"></h3>
<input id="modal-input" autocomplete="off">
<div id="modal-btns">
<button class="btn btn-sm btn-ghost" onclick="closeModal()">Cancel</button>
<button class="btn btn-sm" id="modal-ok">OK</button>
</div>
</div>
</div>
<script>
// Folder navigation pushes a history entry per hash change, so back/forward
// fires popstate here -- but hashchange (below) already re-renders the
// right view for that. Left alone, the shared shell's own popstate handler
// (meant for the home page's SPA nav) would also fire, re-fetching this
// full document and nesting a second navbar inside the current one.
window.addEventListener('popstate', function(e){ e.stopImmediatePropagation(); }, true);
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
 var html='<span onclick="go(\\'/'+'\\')">&#x1F4C0;</span>';
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
 api("/system/fm/ls",cwd).then(function(d){
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
    html+='<div class="row" onclick="edit(\\''+fp+'\\')"><span class="icon">&#x1F4C4;</span><span class="name">'+it.n+'</span><span class="size">'+fmtSize(it.s)+'</span><span class="acts"><button class="abtn del" onclick="event.stopPropagation();del(\\''+fp+'\\')">&#x1F5D1;</button></span></div>';
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
function edit(fp){location.hash="f:"+enc(fp);}
function openEditor(fp){
 cwd=fp.substring(0,fp.lastIndexOf("/"))||"/";
 renderPath();
 api("/system/fm/read",fp).then(function(d){
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
 api("/system/fm/write",ta.dataset.path,ta.value).then(function(d){
  if(d.error){alert(d.error);btn.textContent="\\u1F4BE Save";}
  else{btn.textContent="\\u2705 Saved";setTimeout(function(){btn.innerHTML="&#x1F4BE; Save"},1500);}
 });
}
function closeEditor(){go(cwd);}
function del(fp){
 var name=fp.split("/").pop();
 if(!confirm("Delete "+name+"?"))return;
 api("/system/fm/del",fp).then(function(d){
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
  api("/system/fm/write",fp,"").then(function(d){
   if(d.error)alert(d.error);
   else{edit(fp);}
  });
 });
}
function newDir(){
 showModal("New directory name:",function(name){
  var fp=cwd.replace(/\\/$/,"")+"/"+name;
  api("/system/fm/mkdir",fp).then(function(d){
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
</script>"""
    return (200, {}, web_interface._shell(content, "File Manager", "/system/fm", app=in_app, back=True))
