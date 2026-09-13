import ampule
import web_interface

import __main__
from __main__ import connect_to_network, settings, wifi

# Shared "this device isn't on WiFi yet" UI + connect flow. Any route,
# home or app, can do:
#
#     import wifi_setup
#     if wifi_setup.needs_setup():
#         return (200, {}, header("WiFi Setup", app=True) + wifi_setup.render_wifi_setup() + footer())
#
# (or wifi_setup.page() for the common case of wrapping render_wifi_setup()
# in web_interface's own header()/footer()). Starting the device's own AP
# hotspot needs no app-facing equivalent -- main.py's boot loop already
# does that unconditionally, before any app can run, whenever the device
# isn't connected. This module only covers what happens once someone is
# actually browsing the resulting page: pick a network, enter a password,
# connect.
#
# The three actions below live under /system/wifi/..., so route()'s
# /system/ auto-promotion (see ampule.py) makes them reachable from inside
# any app with no per-app registration -- the same mechanism /system/fm,
# /system/cmd and /system/settings already rely on.
#
# web_interface.py's own home screen now uses this (see _apps_content());
# apps/departures' separate implementation is untouched and still has its
# own copy, left alone until this gets tried out on an app.
#
# web_interface is imported eagerly (not lazily inside each function)
# because this module is only ever imported from inside web_interface.py's
# own execution (its `import wifi_setup` line), so the name resolves to
# that in-progress module object immediately; the attributes used below
# (header, footer, url_decoder) are only actually looked up when a request
# comes in, long after web_interface.py has finished executing.


def needs_setup():
    return not wifi.radio.connected


def render_wifi_setup():
    def scan():
        networks = ""
        for network in wifi.radio.start_scanning_networks(
            start_channel=1, stop_channel=14
        ):
            networks += f"<option value='{network.ssid}' data-ch='{network.channel}'>{network.ssid} (ch {network.channel})</option>"
        wifi.radio.stop_scanning_networks()
        return networks

    networks = scan()
    wifi_error = str(__main__.wifi_status)
    error_html = f'<p class="error-msg">{wifi_error}</p>' if wifi_error else ""
    return f"""<div class="logo">
    <h1>WiFi Setup</h1>
    <p>Connect to a wireless network</p>
</div>
<div class="card">
    <label for="ssid">Network</label>
    <select id="ssid" name="ssid">{networks}</select>
    <script>
    var _ssid = document.getElementById("ssid");
    function _sendSSID(el) {{
        var opt = el.options[el.selectedIndex];
        var v = opt.value.replace(/#/g, "%23");
        var ch = opt.getAttribute("data-ch") || "";
        fetch("/system/wifi/ssid?v=" + v + "&channel=" + ch, {{ method: "POST" }});
    }}
    _ssid.addEventListener("change", function() {{ _sendSSID(_ssid); }});
    _ssid.addEventListener("click",  function() {{ _sendSSID(_ssid); }});
    if (_ssid.options.length) _sendSSID(_ssid);
    </script>
    <label for="password">Password</label>
    <input type="text" id="password" name="password" placeholder="Enter password">
    <script>
    document.getElementById("password").addEventListener("blur", function(e) {{
        var p = e.target.value.replace(/#/g, "%23");
        fetch("/system/wifi/password?v=" + encodeURIComponent(p), {{ method: "POST" }});
    }});
    </script>
    <button class="btn btn-full" onclick="fetch('/system/wifi/connect').then(function(){{location.reload()}})">Connect</button>
    {error_html}
</div>"""


def page(title="WiFi Setup"):
    # Convenience for the common case: an app that already uses
    # web_interface's header()/footer() can just return wifi_setup.page().
    return (
        200,
        {},
        web_interface.header(title, app=True)
        + render_wifi_setup()
        + web_interface.footer(),
    )


@ampule.route("/system/wifi/ssid", method="POST")
def _set_ssid(request):
    if request.params and "v" in request.params:
        settings["ssid"] = web_interface.url_decoder(request.params["v"])
    if request.params and "channel" in request.params:
        try:
            settings["channel"] = int(request.params["channel"])
        except:
            pass
    return (200, {}, "")


@ampule.route("/system/wifi/password", method="POST")
def _set_password(request):
    if request.params and "v" in request.params:
        settings["password"] = web_interface.url_decoder(request.params["v"])
    return (200, {}, "")


@ampule.route("/system/wifi/connect", method="GET")
def _connect(_):
    connect_to_network()
    return (200, {}, """<meta http-equiv="refresh" content="0; url=../" />""")
