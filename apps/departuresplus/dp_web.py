# Departures Plus - settings page and the JSON API (also what Home Assistant talks to).
import ampule, json
import load_settings
import dp_cfg

_app = None
_HEX = "0123456789abcdefABCDEF"
_LIGHT = ("brightness", "tone", "tone_hex", "ticker_color", "invert")          # changes that only need new colours, not new layers


def unquote(s):
    s = str(s).replace("+", " ")
    if "%" not in s: return s
    out = bytearray()
    b = s.encode("utf-8")
    i = 0
    n = len(b)
    while i < n:
        c = b[i]
        if c == 37 and i + 2 < n and chr(b[i + 1]) in _HEX and chr(b[i + 2]) in _HEX:
            out.append(int(chr(b[i + 1]) + chr(b[i + 2]), 16))
            i += 3
        else:
            out.append(c)
            i += 1
    try: return bytes(out).decode("utf-8")
    except Exception: return s


def _json(obj):
    return (200, {}, json.dumps(obj))


def _apply(changes, persist):
    changed = dp_cfg.merge(_app.cfg, changes)
    saved = None
    if changed:
        if persist: saved = dp_cfg.save(_app.cfg)
        if "stations" in changed: _app.cache = {}       # filters are applied when departures are read, so read them again
        if all(k in _LIGHT for k in changed):
            _app.scr.set_palette(_app.cfg)
            _app.t_sec = 0
        else:
            _app.restart()
    return changed, saved


def _legacy(p):
    # The T-Skylt Home Assistant integration written for the stock app toggles with
    # /?onoff=active and reads its state from form fields in the page. Answer in that dialect
    # so its power, brightness, sleep and clock/countdown entities keep working.
    c = _app.cfg
    if "onoff" in p: _app.set_power(not _app.power)
    if "brightness" in p:
        try: _apply({"brightness": int(p["brightness"]) + 1}, False)
        except Exception: pass
    if "sleep" in p: _apply({"sleep": 0 if c["sleep"] else 1}, False)
    if "clocktime" in p: _apply({"time_fmt": "min" if c["time_fmt"] == "clock" else "clock"}, False)
    def chk(i, on): return '<input type="checkbox" id="' + i + '"' + (" checked" if on else "") + ">"
    return (200, {}, "<html><body>v. " + dp_cfg.VERSION + chk("onoff", _app.power) + chk("sleep", c["sleep"]) +
            chk("clocktime", c["time_fmt"] == "clock") + chk("abc", 1) + chk("LISTCOLOR", c["badge"] != "mono") +
            chk("FONTMINI", c["font"] == "compact") + '<select id="brightness"><option value="' + str(c["brightness"] - 1) +
            '" selected></option></select></body></html>')


def init(app):
    global _app
    _app = app

    @ampule.route("/exit", method="GET")
    def _exit(request):
        load_settings.app_running = False
        return (200, {}, '<meta http-equiv="refresh" content="0; url=../" />')

    @ampule.route("/", method="GET")
    def _index(request):
        p = request.params
        if "aiohttp" in request.headers.get("user-agent", "") or "onoff" in p or "brightness" in p:
            return _legacy(p)
        from web_interface import header, footer
        with open("settings.html") as f: page = f.read()
        return (200, {}, header("Departures Plus", app=True) + page + footer())

    @ampule.route("/api/config", method="GET")
    def _cfg_get(request):
        return _json(dp_cfg.DEFAULTS if "defaults" in request.params else _app.cfg)

    @ampule.route("/api/config", method="POST")
    def _cfg_post(request):
        try: new = json.loads(request.body)
        except Exception: return _json({"ok": False, "error": "bad json"})
        changed, saved = _apply(new, True)
        return _json({"ok": True, "changed": changed, "saved": saved})

    @ampule.route("/api/state", method="GET")
    def _state(request):
        return _json(_app.state())

    @ampule.route("/api/debug", method="GET")
    def _debug(request):
        return _json(_app.debug())

    @ampule.route("/api/set", method="GET")
    def _set(request):
        # Runtime changes, e.g. from Home Assistant. Nothing is written to flash unless save=1.
        p = {}
        for k in request.params: p[k] = unquote(request.params[k])
        out = {"ok": True}
        if "power" in p: _app.set_power(p["power"] not in ("0", "off", "false"))
        if "pin" in p:
            try: _app.pin = int(p["pin"])
            except Exception: _app.pin = -1
            if _app.pin >= len(_app.active()): _app.pin = -1
            if _app.pin >= 0 and _app.shown and _app.cfg["mode"] == "rotate": _app.show(_app.pin)
        if "next" in p and _app.shown: _app.next_station()
        changes = {}
        for k in p:
            if k in dp_cfg.DEFAULTS and k != "stations": changes[k] = p[k]
        if changes:
            changed, saved = _apply(changes, p.get("save") == "1")
            out["changed"] = changed
            out["saved"] = saved
        out["state"] = _app.state()
        return _json(out)

    @ampule.route("/api/message", method="GET")
    def _message(request):
        # text=...&ttl=60 shows a message for 60 seconds, ttl=0 keeps it until cleared or restarted.
        # Several messages run in the ticker together, each until its own time is up.
        # wake=1 lights the ticker of a switched-off display for as long as the message runs.
        p = request.params
        if "clear" in p:
            cid = unquote(p.get("id", ""))
            _app.msgs = [m for m in _app.msgs if cid and m[0] != cid]
        else:
            try: ttl = int(p.get("ttl", "60"))
            except Exception: ttl = 60
            _app.message(unquote(p.get("text", "")), ttl, unquote(p.get("id", "")), p.get("wake", "0") not in ("0", "", "false", "off"))
        _app.t_sec = 0
        return _json({"ok": True, "messages": [m[1] for m in _app.msgs]})

    @ampule.route("/api/search", method="GET")
    def _search(request):
        p = request.params
        c = _app.cfg
        q = p.get("q", "").replace(" ", "%20")
        body = _app.net.get(c["host"], c["port"], "/search_stop?country=" + p.get("country", "") + "&operator=" + p.get("operator", "") + "&station=" + q, limit=30000)
        if body is None:        # the server did not answer in time: usually this one operator's source is down
            return _json({"ok": False, "results": [], "error": _app.net.last.get("error") or "no answer"})
        more = False
        try:
            try: j = json.loads(body)
            except Exception:
                # a long list cut off by the size limit: keep the complete entries
                j = json.loads(body[:body.rfind('", "') + 1] + "}")
                more = True
            res = [{"name": k, "id": str(j[k])} for k in j if str(j[k]) != "0"]     # "No stations found!": 0
            res.sort(key=lambda x: x["name"])
            return _json({"ok": True, "results": res[:40], "more": more or len(res) > 40})
        except Exception as e:
            return _json({"ok": False, "results": [], "error": str(e)})
