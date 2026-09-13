# Small, self-contained HTML component functions for the device's web UI.
# No hardware or __main__ imports, no route registration -- any app can
# `import web_components` cheaply, without pulling in web_interface's
# settings/bootloader/install-app routes as a side effect.
#
# Every component here expects the caller's page to include the CSS classes
# it renders (.toggle-row/.switch/.slider, .pw-wrap/.pw-toggle, .btn/.btn-full)
# -- see web_interface.css() or apps/departures/css.py for the shared rules.

def checkbox(field_id, checked, label, name=None, onchange="", zero_fallback=False):
    # Toggle-switch styling matching apps/departures' _chk().
    ck = " checked" if checked else ""
    name_attr = f' name="{name}" value="1"' if name else ""
    onchange_attr = f' onchange="{onchange}"' if onchange else ""
    hidden = f'<input type="hidden" name="{name}" value="0">' if zero_fallback and name else ""
    return f"""<div class="toggle-row">
<label for="{field_id}" class="toggle-label">{label}</label>
{hidden}<label class="switch"><input type="checkbox" id="{field_id}"{name_attr}{ck}{onchange_attr}><span class="slider"></span></label>
</div>"""

def save_button(label="Save Settings", form_id=None, onclick=None):
    # Fixed styling + emoji so every settings form saves with the same look.
    if onclick:
        return f'<button type="button" class="btn btn-full btn-success" onclick="{onclick}">&#128190; {label}</button>'
    form_attr = f' form="{form_id}"' if form_id else ""
    return f'<button type="submit" class="btn btn-full btn-success"{form_attr}>&#128190; {label}</button>'

def password_field(field_id, name, placeholder):
    return f"""<div class="pw-wrap">
<input type="password" id="{field_id}" name="{name}" placeholder="{placeholder}">
<button type="button" class="pw-toggle" aria-label="Show password" onclick="var i=document.getElementById('{field_id}');i.type=i.type==='password'?'text':'password';this.innerHTML=i.type==='password'?'&#128065;':'&#128584;'">&#128065;</button>
</div>"""
