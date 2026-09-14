import time

import ampule
import web_components
import web_interface

from __main__ import (
    macid,
    pprint,
    render_home_screen,
    savesettings,
    settings,
    wifi,
)

# All WiFi radio management: connecting, AP/hotspot fallback, connection
# status, and the shared "this device isn't on WiFi yet" UI + connect flow,
# usable from any app or route via wlan.is_connected() / wlan.setup_content()
# / wlan.setup_page(). Routes live under /system/wifi/... so they're
# auto-promoted (see ampule.py) and reachable from inside any app.
#
# Expected usage from an app:
#
#     import wlan
#
#     def main_loop():
#         while True:
#             if not wlan.is_connected():
#                 wlan.show_setup_on_led()
#                 continue
#
#             ...  # normal app behavior
#
#     @ampule.route('/', method='GET')
#     def index(request):
#         if not wlan.is_connected():
#             return wlan.setup_page()
#
#         return (200, {}, normal_app_page())
#
# wlan.config_card() is the full picker+power+channel card shared by the
# home page and /system/settings; wlan.credentials_fields() is just the
# network/password part, reused by wlan.setup_content()'s standalone page.
#
# apps/departures has its own separate copy, untouched for now.
#
# web_interface is imported eagerly since this module is only ever
# imported from inside web_interface.py's own execution.
#
# macid, the boot-time socket/tx_power bring-up, and the shared HTTP
# session (pool/socket/requests) stay in main.py -- fetch_data.py reads
# macid via a `from __main__ import *` that runs before web_interface.py
# (and this module) are ever loaded, and pool/socket/requests are plain
# HTTP/TCP plumbing used directly by nearly every app, not WiFi-radio setup.


STATUS = ""


def connect_to_network(timeout=False, silent=False, save=False):
    # Never draws. save=True only for an explicit user-initiated connect --
    # boot/retry reuse stored settings and have nothing new to persist.
    global STATUS

    if silent and wifi.radio.connected:
        return time.monotonic()

    STATUS = ""
    print("Connecting...")

    try:
        channel = settings.get("channel", 0)
        if channel:
            wifi.radio.connect(
                str(settings["ssid"]),
                str(settings["password"]),
                channel=int(channel),
                timeout=timeout,
            )
        else:
            wifi.radio.connect(
                str(settings["ssid"]), str(settings["password"]), timeout=timeout
            )
        if save and wifi.radio.connected:
            if not savesettings(settings):
                STATUS = "Connected, but couldn't save settings (read-only filesystem)"

    except Exception as e:
        if "unknown failure" in str(e).lower():
            e = "Router distance!"
        if "no network with" in str(e).lower():
            e = "Wrong WiFi name"
        if "authentication failure" in str(e).lower():
            e = "Wrong password"

        print(e)
        STATUS = str(e)

    return time.monotonic()


def start_hotspot():
    try:
        wifi.radio.start_ap(ssid=macid)
        render_home_screen()
    except Exception as e:
        pprint(str(e))


def is_connected():
    return wifi.radio.connected


def show_setup_on_led():
    # Show wifi name and device IP for setup instructions.
    # One space per pixel so name and IP align.
    pprint("1. Connect to WiFi", line=1)
    pprint(f"       {macid}", line=2, color="yellow")
    pprint("2. Go to", line=3)
    pprint(f"       http://{wifi.radio.ipv4_address_ap!s}", line=4)


def _current_options(current_ssid=""):
    """No-scan option list: stored ssid (if any) plus "Enter manually..."."""
    if current_ssid:
        return (
            f"<option value='{current_ssid}' selected>{current_ssid}</option>"
            "<option value='__manual__'>Enter manually&hellip;</option>"
        )
    return "<option value='__manual__' selected>Enter manually&hellip;</option>"


def _scan_options(current_ssid=""):
    """<option> tags from a live scan, plus "Enter manually...". Keeps
    current_ssid as its own selected option if not found in range."""
    networks = ""
    matched_current = False
    for network in wifi.radio.start_scanning_networks(start_channel=1, stop_channel=14):
        selected = ""
        if network.ssid == current_ssid:
            selected = "selected"
            matched_current = True
        networks += f"<option value='{network.ssid}' data-ch='{network.channel}' {selected}>{network.ssid} (ch {network.channel})</option>"
    wifi.radio.stop_scanning_networks()

    if current_ssid and not matched_current:
        networks = (
            f"<option value='{current_ssid}' selected>{current_ssid} (not found)</option>"
            + networks
        )

    networks += "<option value='__manual__'>Enter manually&hellip;</option>"
    return networks


def credentials_fields(current_ssid=""):
    """Network picker + password field, shared by the AP-setup page and
    /system/settings. Only auto-scans while disconnected -- scanning while
    connected can drop the radio off its own AP, so once connected only
    the rescan button (⟳) scans."""
    options = (
        _scan_options(current_ssid)
        if not wifi.radio.connected
        else _current_options(current_ssid)
    )
    return f"""<label for="ssid">Network</label>
<div class="pw-wrap">
<select id="ssid" name="ssid">{options}</select>
<button type="button" class="pw-toggle" id="ssid_rescan" title="Rescan for networks" aria-label="Rescan for networks">&#x21bb;</button>
</div>
<input type="text" id="ssid_manual" placeholder="Network name" value="" style="display:none;margin-top:6px">
<script>
(function() {{
    var _ssid = document.getElementById("ssid");
    var _manual = document.getElementById("ssid_manual");
    var _rescanBtn = document.getElementById("ssid_rescan");
    function _sendSSID(v, ch) {{
        v = v.replace(/#/g, "%23");
        fetch("/system/wifi/ssid?v=" + v + "&channel=" + (ch || ""), {{ method: "POST" }});
    }}
    function _applySelection(focusManual) {{
        var opt = _ssid.options[_ssid.selectedIndex];
        if (opt.value === "__manual__") {{
            _manual.style.display = "block";
            // only steal focus on "change" -- "click" also fires on reopen and would block re-selecting
            if (focusManual) _manual.focus();
            return;
        }}
        _manual.style.display = "none";
        _sendSSID(opt.value, opt.getAttribute("data-ch") || "");
    }}
    _ssid.addEventListener("change", function() {{ _applySelection(true); }});
    _ssid.addEventListener("click", function() {{ _applySelection(false); }});
    _manual.addEventListener("blur", function() {{
        if (_manual.value) _sendSSID(_manual.value, "");
    }});
    _rescanBtn.addEventListener("click", function() {{
        var current = _ssid.options[_ssid.selectedIndex].value;
        if (current === "__manual__") current = _manual.value;
        _rescanBtn.disabled = true;
        _rescanBtn.classList.add("spinning");
        fetch("/system/wifi/scan?current=" + encodeURIComponent(current))
            .then(function(r) {{ return r.text(); }})
            .then(function(html) {{
                _ssid.innerHTML = html;
                _applySelection(false);
            }})
            .finally(function() {{
                _rescanBtn.disabled = false;
                _rescanBtn.classList.remove("spinning");
            }});
    }});
    if (_ssid.options[_ssid.selectedIndex].value !== "__manual__") _applySelection(false);
}})();
</script>
<label for="password">Password</label>
{web_components.password_field("password", "password", "Enter password")}
<script>
document.getElementById("password").addEventListener("blur", function(e) {{
    var p = e.target.value.replace(/#/g, "%23");
    fetch("/system/wifi/password?v=" + encodeURIComponent(p), {{ method: "POST" }});
}});
</script>"""


def status_banner():
    """Last STATUS error on its own, for pages that don't show the full config_card()."""
    wifi_error = str(STATUS)
    return f'<p class="error-msg">{wifi_error}</p>' if wifi_error else ""


def config_card():
    """Full WiFi card (picker, power, channel, connect, error) shared by home and /system/settings."""
    try:
        power = int(float(settings.get("wifi_power", 9)))
    except:
        power = 9
    try:
        channel = int(settings.get("channel", 0))
    except:
        channel = 0
    channel_label = "Auto" if channel == 0 else str(channel)
    error_html = status_banner()
    return f"""<div class="card"><div class="section-title">WiFi</div>
{credentials_fields(settings.get("ssid", ""))}
<label for="wifi_power">WiFi Power</label>
<div class="range-wrap">
<input type="range" id="wifi_power" min="7" max="20" step="1" value="{power}" oninput="document.getElementById('v_wifi_power').textContent=this.value" onchange="fetch('/system/wifi/power?v='+this.value,{{method:'POST'}})">
<span class="range-val" id="v_wifi_power">{power}</span>
</div>
<label for="channel">Channel</label>
<div class="range-wrap">
<input type="range" id="channel" min="0" max="13" step="1" value="{channel}" title="0 = auto-detect" oninput="var v=parseInt(this.value);document.getElementById('v_channel').textContent=v===0?'Auto':v;" onchange="fetch('/system/wifi/ssid?channel='+this.value,{{method:'POST'}})">
<span class="range-val" id="v_channel">{channel_label}</span>
</div>
<div style="font-size:.75rem;color:var(--muted);margin-top:3px">2.4GHz only &mdash; valid channels are 1&ndash;13 (1&ndash;11 in North America). Leave on Auto unless you're connecting to a hidden network or want a faster reconnect by skipping the scan.</div>
<button class="btn btn-full" style="margin-top:10px" onclick="fetch('/system/wifi/connect').then(function(){{location.reload()}})">Connect</button>
{error_html}
</div>"""


def setup_content():
    wifi_error = str(STATUS)
    error_html = f'<p class="error-msg">{wifi_error}</p>' if wifi_error else ""
    return f"""<div class="logo">
    <h1>WiFi Setup</h1>
    <p>Connect to a wireless network</p>
</div>
<div class="card">
    {credentials_fields(settings.get("ssid", ""))}
    <button class="btn btn-full" onclick="fetch('/system/wifi/connect').then(function(){{location.reload()}})">Connect</button>
    {error_html}
</div>"""


def setup_page(title="WiFi Setup"):
    # Convenience for the common case: an app that already uses
    # web_interface's header()/footer() can just return wlan.setup_page().
    return (
        200,
        {},
        web_interface.header(title, app=True)
        + setup_content()
        + web_interface.footer(),
    )


@ampule.route("/system/wifi/scan", method="GET")
def _scan(request):
    current = web_interface.url_decoder(request.params.get("current", ""))
    options = _scan_options(current)
    return (200, {}, options)


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


@ampule.route("/system/wifi/power", method="POST")
def _set_power(request):
    if request.params and "v" in request.params:
        settings["wifi_power"] = float(request.params["v"])
        wifi.radio.tx_power = settings["wifi_power"]
    return (200, {}, "")


@ampule.route("/system/wifi/password", method="POST")
def _set_password(request):
    if request.params and "v" in request.params:
        settings["password"] = web_interface.url_decoder(request.params["v"])
    return (200, {}, "")


@ampule.route("/system/wifi/connect", method="GET")
def _connect(_):
    connect_to_network(save=True)
    render_home_screen()
    return (200, {}, """<meta http-equiv="refresh" content="0; url=../" />""")
