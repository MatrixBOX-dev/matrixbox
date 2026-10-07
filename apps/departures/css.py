_css = """:root{--bg:#08080f;--surface:#111118;--surface2:#1c1c2a;--surface3:#26263a;--accent:#7c6fff;--accent2:#00d4ff;--text:#eeeef5;--muted:#7070a0;--border:rgba(120,120,255,.1);--r:10px;--r-lg:16px;--shadow:0 4px 24px rgba(0,0,0,.5)}
*{box-sizing:border-box;margin:0;padding:0}
body{background:var(--bg);color:var(--text);font-family:'Segoe UI',system-ui,-apple-system,sans-serif;min-height:100vh;padding-bottom:40px;font-size:14px;line-height:1.5}
.navbar{position:sticky;top:0;z-index:100;background:rgba(8,8,15,.85);border-bottom:1px solid var(--border);padding:0 14px;display:flex;align-items:center;height:46px;gap:4px;backdrop-filter:blur(16px);-webkit-backdrop-filter:blur(16px)}
.nav-title{font-weight:600;font-size:.9rem;color:var(--text);flex:1;padding-left:4px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.wifi-nav-form{flex-shrink:0}
.wifi-nav>summary{height:30px;display:flex;align-items:center;padding:0 8px;border:1px solid var(--border);border-radius:8px;color:var(--muted);font-size:.65rem;letter-spacing:.3px;white-space:nowrap;list-style:none;cursor:pointer}
.wifi-nav>summary::-webkit-details-marker{display:none}
.wifi-nav[open]>summary{color:var(--text);border-color:var(--accent)}
.wifi-nav-panel{position:absolute;right:14px;top:calc(100% + 8px);width:min(330px,calc(100% - 28px));max-height:calc(100vh - 68px);overflow-y:auto;padding:12px;background:var(--surface);border:1px solid var(--border);border-radius:var(--r-lg);box-shadow:var(--shadow);z-index:110}
.wifi-nav-panel .form-row{gap:8px}
.wifi-nav-panel .col{min-width:0}
.wifi-nav-panel label{font-size:.6rem}
.wifi-nav-panel .form-control{height:34px;padding:0 8px;font-size:.76rem}
.wifi-nav-panel .btn{height:30px}
.nav-info{color:var(--muted);font-size:.68rem;letter-spacing:.2px;text-align:right;line-height:1.4}
.nav-info span{display:block}
.sig{display:flex;align-items:center;gap:2px;margin:0 6px}
.sig i{display:block;width:5px;height:5px;background:rgba(112,112,160,.3);border-radius:1px}
.sig i.on{background:#00c853}
.nav-x{color:var(--muted);font-size:1rem;font-weight:700;text-decoration:none;width:32px;height:32px;display:flex;align-items:center;justify-content:center;border-radius:8px;border:1px solid var(--border);transition:color .15s,border-color .15s,background .15s;margin-left:4px;flex-shrink:0}
.nav-x:hover{color:#ff6060;border-color:rgba(255,96,96,.4);background:rgba(255,96,96,.08)}
.nav-led{color:var(--muted);font-size:.85rem;width:32px;height:32px;display:flex;align-items:center;justify-content:center;border-radius:8px;border:1px solid var(--border);transition:color .15s,border-color .15s,background .15s;margin-left:4px;cursor:pointer;background:none;flex-shrink:0}
.nav-led:hover{color:#ffd060;border-color:rgba(255,208,96,.4);background:rgba(255,208,96,.08)}
.nav-led.led-off{color:#ff4040;border-color:rgba(255,64,64,.35);background:rgba(255,64,64,.06)}
.nav-ro{color:#ff6060;font-size:.85rem;display:flex;align-items:center;margin:0 2px}
.page{max-width:480px;margin:0 auto;padding:16px 14px}
.brand-header{display:flex;align-items:center;justify-content:space-between;gap:12px;margin:0 6px 12px}
.brand-lockup{display:flex;align-items:center;gap:8px;color:var(--text);font:inherit;background:none;border:0;padding:0;cursor:pointer;text-align:left}
.brand-mark{width:34px;display:flex;flex-direction:column;align-items:center;line-height:1;flex-shrink:0}
.brand-mark>span{width:27px;height:31px;border:3px solid var(--text);border-radius:1px;display:flex;align-items:center;justify-content:center;font-size:1.35rem;font-weight:800}
.brand-mark small{font-size:.38rem;color:var(--text);letter-spacing:.1px;margin-top:2px}
.brand-name{font-size:1.45rem;font-weight:700;letter-spacing:-.6px}
.signup-link{font-family:Georgia,serif;font-size:1.15rem;font-style:italic;text-decoration:underline;color:var(--text);white-space:nowrap}
.signup-card{padding:16px 18px}
.signup-card input[type=email]{height:42px;font-size:1rem}
.email-collapsed .signup-link,.email-collapsed .signup-card{display:none}
.card{background:var(--surface);border:1px solid var(--border);border-radius:var(--r-lg);padding:16px;margin-bottom:10px;box-shadow:var(--shadow)}
.section-title{font-size:.65rem;color:var(--muted);text-transform:uppercase;letter-spacing:1.4px;font-weight:700;margin-bottom:12px;padding-bottom:8px;border-bottom:1px solid var(--border)}
.form-row{display:flex;gap:10px;flex-wrap:wrap;align-items:flex-end}
.col{flex:1;min-width:110px}
label,.control-label{display:block;font-size:.67rem;color:var(--muted);text-transform:uppercase;letter-spacing:.9px;margin:0 0 5px;font-weight:600}
input[type=text],select,.form-control{width:100%;height:38px;padding:0 12px;background:var(--surface2);border:1.5px solid var(--border);border-radius:var(--r);color:var(--text);font-size:.85rem;outline:none;transition:border-color .15s,box-shadow .15s;-webkit-appearance:none}
input[type=text]:focus,select:focus,.form-control:focus{border-color:var(--accent);box-shadow:0 0 0 3px rgba(124,111,255,.15)}
select option{background:var(--surface2)}
input:disabled,select:disabled{opacity:.35}
.btn{display:inline-flex;align-items:center;justify-content:center;gap:6px;height:38px;padding:0 16px;border:none;border-radius:var(--r);font-size:.85rem;font-weight:600;cursor:pointer;transition:opacity .15s,transform .1s,box-shadow .15s;color:#111;background:linear-gradient(135deg,#c8a800,#f5e040);box-shadow:0 2px 12px rgba(200,168,0,.35)}
.btn:hover{opacity:.88;transform:translateY(-1px)}
.btn:active{transform:translateY(0);opacity:1;box-shadow:none}
button:disabled,.btn:disabled{opacity:.3;cursor:not-allowed;transform:none;box-shadow:none}
.btn-sm{height:30px;padding:0 12px;font-size:.78rem}
.btn-full{width:100%;height:44px;font-size:.93rem;margin-top:10px}
.btn-danger{background:linear-gradient(135deg,#e03c3c,#ff6060)!important;color:#fff!important;box-shadow:0 2px 12px rgba(224,60,60,.3)}
.btn-success{background:linear-gradient(135deg,#00b050,#00e676)!important;color:#000!important;box-shadow:0 2px 12px rgba(0,176,80,.3)}
.btn-ghost{background:var(--surface2);border:1px solid var(--border);color:var(--text);box-shadow:none}
.btn-ghost:hover{border-color:var(--accent);background:var(--surface3)}
.btn-outline-secondary{background:transparent;border:1px solid var(--border);color:var(--muted);box-shadow:none}
.btn-outline-secondary:hover{border-color:var(--accent);color:var(--text);background:var(--surface3)}
.toggle-row{display:flex;align-items:center;justify-content:space-between;gap:12px;padding:10px 0;border-bottom:1px solid var(--border)}
.toggle-row:last-child{border-bottom:none}
.toggle-row .toggle-label{margin:0;font-size:.85rem;color:var(--text);text-transform:none;letter-spacing:0;font-weight:500;flex:1}
.switch{position:relative;display:inline-block;width:42px;height:24px;flex-shrink:0}
.switch input{opacity:0;width:0;height:0;position:absolute}
.switch .slider{position:absolute;cursor:pointer;inset:0;background:var(--surface3);border-radius:24px;transition:.2s;border:1px solid var(--border)}
.switch .slider:before{content:"";position:absolute;height:18px;width:18px;left:2px;top:2px;background:var(--muted);border-radius:50%;transition:.2s}
.switch input:checked+.slider{background:linear-gradient(135deg,var(--accent),var(--accent2));border-color:transparent}
.switch input:checked+.slider:before{transform:translateX(18px);background:#fff;box-shadow:0 1px 4px rgba(0,0,0,.4)}
.seg-toggle-cb{display:none}
.seg-toggle{display:flex;background:var(--surface2);border-radius:var(--r);padding:3px;gap:2px;border:1px solid var(--border);cursor:pointer;flex-shrink:0}
.seg-toggle div{flex:1;height:28px;display:flex;align-items:center;justify-content:center;padding:0 10px;border-radius:8px;font-size:.8rem;font-weight:600;color:var(--muted);white-space:nowrap;transition:all .15s}
.seg-toggle-cb+.seg-toggle div:first-child{background:linear-gradient(135deg,var(--accent),var(--accent2));color:#fff}
.seg-toggle-cb:checked+.seg-toggle div:first-child{background:none;color:var(--muted)}
.seg-toggle-cb:checked+.seg-toggle div:last-child{background:linear-gradient(135deg,var(--accent),var(--accent2));color:#fff}
.dropdown{position:relative;display:inline-block}
.dropbtn{height:38px;min-width:120px;background:var(--surface2);border:1.5px solid var(--border);color:var(--text);padding:0 12px;border-radius:var(--r);cursor:pointer;font-size:.85rem;transition:border-color .15s;display:inline-flex;align-items:center;gap:4px}
.dropbtn:hover{border-color:var(--accent)}
.dropdown-content{display:none;position:absolute;left:0;top:calc(100% + 4px);background:var(--surface2);border:1px solid var(--border);border-radius:var(--r);z-index:10;box-shadow:var(--shadow);padding:10px;min-width:170px}
.dropdown.open .dropdown-content{display:block}
.dd-grid{display:grid;grid-template-columns:repeat(5,1fr);gap:6px}
.dd-grid img{cursor:pointer;border-radius:5px;border:2px solid transparent;transition:border-color .15s;display:block}
.dd-grid img:hover,.dd-grid img.dd-sel{border-color:var(--accent)}
.dd-ops{margin-top:8px;border-top:1px solid var(--border);padding-top:8px}
.dd-ops a{display:block;padding:6px 8px;color:var(--text);text-decoration:none;font-size:.85rem;border-radius:7px;white-space:nowrap;transition:background .15s}
.dd-ops a:hover{background:var(--surface3);color:var(--accent2)}
.btn-check{display:none}
.btn-check+label.btn{display:inline-flex;opacity:.3;transition:opacity .15s}
.btn-check:checked+label.btn{opacity:1}
.color-swatch-btn{width:34px;height:34px;border-radius:9px;border:2px solid var(--border);cursor:pointer;transition:transform .1s,border-color .1s;flex-shrink:0;padding:0}
.color-swatch-btn:hover{transform:scale(1.08)}
.color-swatch-btn.active{border-color:var(--text);box-shadow:0 0 0 2px rgba(255,255,255,.15)}
.line-chip{display:inline-flex;align-items:center;gap:6px;height:32px;padding:0 12px 0 8px;border-radius:20px;border:2px solid var(--border);background:var(--surface2);color:var(--muted);cursor:pointer;font-size:.78rem;font-weight:600;transition:all .15s}
.line-chip .dot{width:12px;height:12px;border-radius:50%;flex-shrink:0}
.btn-check:checked+.line-chip{color:var(--text);border-color:var(--text)}
.form-check{padding:2px 0 2px 24px;position:relative}
.form-check-input{position:absolute;left:0;top:3px;accent-color:var(--accent)}
.form-check-label{font-size:.83rem;color:var(--text)}
table{width:100%;border-collapse:collapse;table-layout:fixed}
td{padding:9px 6px;border-bottom:1px solid var(--border);color:var(--text);font-size:.8rem;vertical-align:middle}
td:first-child{width:44%;color:var(--muted);font-size:.72rem;text-transform:uppercase;letter-spacing:.5px}
tr:last-child td{border-bottom:none}
details>summary{cursor:pointer;color:var(--muted);font-size:.7rem;text-transform:uppercase;letter-spacing:1.2px;font-weight:700;list-style:none;padding:4px 0}
details[open]>summary{margin-bottom:8px;color:var(--text)}
.wifi-nav>summary{height:30px;padding:0 8px;font-size:.65rem;letter-spacing:.3px}
.grp{margin-bottom:14px}
.grp:last-child{margin-bottom:0}
.grp-title{font-size:.65rem;text-transform:uppercase;letter-spacing:.9px;color:var(--muted);margin-bottom:8px;font-weight:700}
.tt-grid{display:grid;grid-template-columns:1fr 1fr;column-gap:16px}
.tt-grid .toggle-label{text-transform:capitalize}
a{color:var(--accent2);text-decoration:none}
a:hover{text-decoration:underline}
small{font-size:.8rem;color:var(--muted)}
.seg{display:flex;background:var(--surface2);border-radius:var(--r);padding:3px;gap:2px;border:1px solid var(--border)}
.seg button{flex:1;height:28px;padding:0 10px;border:none;border-radius:8px;font-size:.8rem;font-weight:600;cursor:pointer;background:none;color:var(--muted);transition:all .15s}
.seg button.on{background:linear-gradient(135deg,var(--accent),var(--accent2));color:#fff}
.scr-btn{height:30px;padding:0 12px;background:var(--surface2);color:var(--muted);border:1px solid var(--border);border-radius:8px;font-size:.8rem;font-weight:700;cursor:pointer;transition:all .15s}
.scr-btn.act{background:linear-gradient(135deg,#00b050,#00e676);color:#000;border-color:transparent}
.spin{display:inline-block;width:.8rem;height:.8rem;border:2px solid rgba(255,255,255,.35);border-top-color:#111;border-radius:50%;animation:sp .6s linear infinite}
.error-msg{color:#ff7070;font-size:.82rem;margin-top:10px;text-align:center}
@keyframes sp{to{transform:rotate(360deg)}}
@keyframes guide-pulse{0%,100%{box-shadow:0 0 0 0 rgba(124,111,255,0)}60%{box-shadow:0 0 0 5px rgba(124,111,255,.3)}}"""
