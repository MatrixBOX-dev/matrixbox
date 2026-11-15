import os
import json
import binascii
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

@ampule.route("/system/fm/upload", method="POST")
def _fm_upload(request):
    # Drag-and-drop upload (see fm.html). request.body is always decoded as
    # UTF-8 text by ampule's request parser (and would also be corrupted by
    # its NUL-byte truncation if sent raw), so arbitrary binary file content
    # can't go through as-is -- the browser base64-encodes it first (pure
    # ASCII, always valid UTF-8, never contains a NUL byte), and this
    # decodes it back to real bytes before writing. binascii.a2b_base64()
    # is the same proven pattern web_interface.py's /repl route already
    # uses for the same reason.
    #
    # Large files are sent in sequential chunks (X-Append absent/0 for the
    # first chunk, which creates/truncates the file; "1" for every chunk
    # after, which appends) rather than as one request, since this device's
    # RAM can't hold a multi-MB file (plus its base64 and decoded copies)
    # all at once -- each chunk's memory footprint is bounded by the
    # chunk size instead of the whole file.
    path = _norm(request.headers.get("x-path", ""))
    append = request.headers.get("x-append", "0") in ("1", "true")
    try:
        data = binascii.a2b_base64(request.body) if request.body else b""
        _hide_display()
        with open(path, "ab" if append else "wb") as f:
            f.write(data)
        display.root_group.hidden = False
        refresh()
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
#listing-wrap{flex:1;min-height:0;position:relative;display:flex;flex-direction:column}
#listing{flex:1;overflow-y:auto;padding:0;min-height:0}
#listing-wrap.dragover{outline:2px dashed var(--accent);outline-offset:-2px}
#listing-wrap.dragover #listing{background:var(--surface2)}
#drop-hint{display:none;position:absolute;inset:0;align-items:center;justify-content:center;pointer-events:none;background:rgba(124,111,255,.1);color:var(--accent);font-size:.9rem;font-weight:700;z-index:5}
#listing-wrap.dragover #drop-hint{display:flex}
#upload-bar{display:none;background:var(--surface);padding:8px 14px;border-bottom:1px solid var(--border);font-size:.78rem;color:var(--muted);flex-shrink:0;align-items:center;gap:10px}
#upload-bar .ubar-track{flex:1;height:6px;border-radius:4px;background:var(--surface2);overflow:hidden}
#upload-bar .ubar-fill{height:100%;width:0;background:var(--accent);transition:width .15s}
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
<div id="upload-bar"><span id="upload-label">Uploading...</span><div class="ubar-track"><div class="ubar-fill" id="upload-fill"></div></div></div>
<div id="listing-wrap"><div id="listing"></div><div id="drop-hint">&#x2B07; Drop files or a folder here</div></div>
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
 document.getElementById("listing-wrap").style.display="flex";
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
  document.getElementById("listing-wrap").style.display="none";
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

// ---- Drag & drop upload -------------------------------------------------
// request.body on this server is always decoded as UTF-8 text (and a raw
// binary body would also get corrupted by a NUL-byte-truncation quirk in
// the receive loop -- see lib/ampule.py), so files are base64-encoded here
// and decoded back to bytes by /system/fm/upload. Each file is sent in
// fixed-size chunks (append=false for the first, true for the rest)
// instead of one request, since the device can't hold a whole multi-MB
// file (plus its base64 and decoded copies) in RAM at once -- only the
// current chunk's memory footprint matters that way, not the file's.
var UPLOAD_CHUNK = 4096;

function arrayBufferToBase64(buf){
 var bytes=new Uint8Array(buf),binary="",step=0x8000;
 for(var i=0;i<bytes.length;i+=step){
  binary+=String.fromCharCode.apply(null,bytes.subarray(i,i+step));
 }
 return btoa(binary);
}

function apiUpload(path,b64,append){
 var h={"X-Path":path};
 if(append)h["X-Append"]="1";
 return fetch("/system/fm/upload",{method:"POST",headers:h,body:b64}).then(function(r){return r.json()});
}

function uploadFileChunked(file,destPath,onChunk){
 return file.arrayBuffer().then(function(buf){
  var bytes=new Uint8Array(buf),total=bytes.length,offset=0;
  function nextChunk(){
   var end=Math.min(offset+UPLOAD_CHUNK,total);
   var slice=bytes.subarray(offset,end);
   var b64=arrayBufferToBase64(slice.buffer.slice(slice.byteOffset,slice.byteOffset+slice.byteLength));
   return apiUpload(destPath,b64,offset>0).then(function(d){
    if(d.error)throw new Error(d.error);
    offset=end;
    if(onChunk)onChunk(offset,total);
    if(offset<total)return nextChunk();
   });
  }
  return total===0?apiUpload(destPath,"",false):nextChunk();
 });
}

// readEntries() can return entries in batches and must be called
// repeatedly until it returns an empty array -- a single call is not
// guaranteed to return everything in the directory.
function readAllDirEntries(reader){
 return new Promise(function(resolve,reject){
  var all=[];
  function readBatch(){
   reader.readEntries(function(batch){
    if(!batch.length){resolve(all);return}
    all=all.concat(batch);
    readBatch();
   },reject);
  }
  readBatch();
 });
}

// Walks a dropped file/directory entry, collecting every file found (with
// its path relative to the dropped item) into fileList, and every
// directory found (so they can be created on the device before any file
// inside them is uploaded) into dirList.
function walkEntry(entry,relPath,fileList,dirList){
 if(entry.isFile){
  return new Promise(function(resolve){
   entry.file(function(file){fileList.push({file:file,rel:relPath+entry.name});resolve()},function(){resolve()});
  });
 }
 if(entry.isDirectory){
  var myRel=relPath+entry.name;
  dirList.push(myRel);
  return readAllDirEntries(entry.createReader()).then(function(children){
   var p=Promise.resolve();
   children.forEach(function(child){
    p=p.then(function(){return walkEntry(child,myRel+"/",fileList,dirList)});
   });
   return p;
  });
 }
 return Promise.resolve();
}

function showUploadBar(label,pct){
 var bar=document.getElementById("upload-bar");
 bar.style.display="flex";
 document.getElementById("upload-label").textContent=label;
 document.getElementById("upload-fill").style.width=pct+"%";
}
function hideUploadBar(){document.getElementById("upload-bar").style.display="none"}

function uploadEntries(entries){
 var fileList=[],dirList=[];
 var walk=Promise.resolve();
 entries.forEach(function(entry){
  walk=walk.then(function(){return walkEntry(entry,"",fileList,dirList)});
 });
 walk.then(function(){
  // shortest paths (parents) first, so a subdirectory's own mkdir never
  // runs before the directory that will contain it
  dirList.sort(function(a,b){return a.split("/").length-b.split("/").length});
  var mk=Promise.resolve();
  dirList.forEach(function(rel){
   mk=mk.then(function(){
    return api("/system/fm/mkdir",cwd.replace(/\\/$/,"")+"/"+rel).catch(function(){});
   });
  });
  return mk;
 }).then(function(){
  var total=fileList.length,done=0;
  if(!total){hideUploadBar();return}
  showUploadBar("Uploading 1 / "+total,0);
  var up=Promise.resolve();
  fileList.forEach(function(item){
   up=up.then(function(){
    showUploadBar("Uploading "+(done+1)+" / "+total+": "+item.rel,Math.round(done/total*100));
    var fp=cwd.replace(/\\/$/,"")+"/"+item.rel;
    return uploadFileChunked(item.file,fp,function(sent,fileTotal){
     var filePct=fileTotal?sent/fileTotal:1;
     showUploadBar("Uploading "+(done+1)+" / "+total+": "+item.rel,Math.round((done+filePct)/total*100));
    });
   }).then(function(){done++});
  });
  return up;
 }).then(function(){
  hideUploadBar();
  doList(cwd);
 }).catch(function(e){
  hideUploadBar();
  alert("Upload failed: "+(e&&e.message?e.message:e));
  doList(cwd);
 });
}

function initDnD(){
 var wrap=document.getElementById("listing-wrap");
 ["dragenter","dragover"].forEach(function(evt){
  wrap.addEventListener(evt,function(e){
   if(!e.dataTransfer||!e.dataTransfer.types||e.dataTransfer.types.indexOf("Files")<0)return;
   e.preventDefault();e.stopPropagation();wrap.classList.add("dragover");
  });
 });
 ["dragleave","dragend"].forEach(function(evt){
  wrap.addEventListener(evt,function(e){
   if(e.target===wrap||!wrap.contains(e.relatedTarget))wrap.classList.remove("dragover");
  });
 });
 wrap.addEventListener("drop",function(e){
  e.preventDefault();e.stopPropagation();
  wrap.classList.remove("dragover");
  if(document.getElementById("listing-wrap").style.display==="none")return; // editor open, not browsing
  var items=e.dataTransfer&&e.dataTransfer.items;
  if(!items||!items.length)return;
  var entries=[];
  for(var i=0;i<items.length;i++){
   var entry=items[i].webkitGetAsEntry&&items[i].webkitGetAsEntry();
   if(entry)entries.push(entry);
  }
  if(entries.length)uploadEntries(entries);
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
initDnD();
if(location.hash.length>1)router();else go("/");
</script>"""
    return (200, {}, web_interface._shell(content, "File Manager", "/system/fm", app=in_app))
