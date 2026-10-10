# Departures Plus - the state machine: which station is on screen, when to fetch, when to redraw.
# Only board objects come from __main__; older firmware does not re-export gc and friends.
from __main__ import display
import wifi, time, gc, json, microcontroller
import dp_cfg, dp_data, dp_draw
from dp_data import mono_ms
from dp_draw import C_TONE, C_DIM

def _pad2(n):
    return ("0" + str(n)) if n < 10 else str(n)


class App:
    def __init__(self):
        self.cfg = dp_cfg.load()
        self.net = dp_data.Net()
        self.scr = dp_draw.Screen(self.cfg)
        self.cache = {}        # station key -> {"deps", "t", "msg", "retry"}
        self.msgs = []         # [id, text, expires_ms or 0 for "until cleared", wakes the display]
        self.dev = []          # operator service messages
        self.dev_t = None
        self.power = True      # what the user or Home Assistant asked for
        self.shown = True      # the departures are on screen (power, schedule and sleep combined)
        self.vis = 1           # what the panel is doing: 0 dark, 1 everything, 2 only the ticker
        self.asleep = False
        self.notes = []
        self.pin = -1
        self.i = 0
        self.pg = 0            # page within the station
        self.npg = 1           # pages this station has right now
        self.phase = "none"
        self.t0 = mono_ms()
        self.sig = None
        self.ids = None
        self.clock_s = None
        self.tick_s = None
        self.tick_reset = False
        self.t_sec = 0
        self.t_tick = 0
        self.t_bar = 0
        self.blink = True
        self.t_spin = 0
        self.spin = 0
        self.t_pre = 0
        try: self.hw0 = (display.rotation, wifi.radio.tx_power)
        except Exception: self.hw0 = None
        try: self.restart()
        except Exception as e: self.note("start: " + str(e))     # the settings page still comes up, so the settings can be fixed

    # ---- helpers -------------------------------------------------------
    def note(self, text):
        print("departuresplus:", text)
        self.notes.append(str(mono_ms() // 1000) + " " + str(text)[:120])
        self.notes = self.notes[-8:]

    def S(self, k):
        o = self.cfg.get(k + "_text")
        if o: return o
        return dp_cfg.STR[k]

    def hw(self, restore=False):
        """Panel rotation and Wi-Fi power. `restore` puts back what the firmware had set."""
        if self.hw0 is None: return
        c = self.cfg
        try:
            rot = self.hw0[0] if restore else (self.hw0[0] + (180 if c["flip"] else 0)) % 360
            if display.rotation != rot: display.rotation = rot
            p = self.hw0[1] if (restore or c["tx_power"] < 7) else float(c["tx_power"])
            if wifi.radio.tx_power != p: wifi.radio.tx_power = p
        except Exception as e:
            self.note("hw: " + str(e))

    def active(self):
        return [s for s in self.cfg["stations"] if s.get("on", 1)]

    def key(self, st):
        return st["country"] + "|" + st["operator"] + "|" + st["id"]

    def narrow(self):
        return self.scr.W <= 64

    def rows_max(self):
        m = self.cfg["max_rows"]
        return min(self.scr.n, m) if m else self.scr.n

    def _get(self, st, operator, sid):
        c = self.cfg
        body = self.net.get(c["host"], c["port"], "/get_departures?country=" + st["country"] + "&operator=" + operator + "&station=" + sid)
        if body is None: return None, "nodata"
        return dp_data.parse(body, st, c)

    def _upcoming(self, deps):
        now = self.net.now()
        if deps is None or now is None: return False
        for d in deps:
            if d[0] - now > -20 and not d[5]: return True
        return False

    def fetch(self, st):
        gc.collect()
        k = self.key(st)
        e = self.cache.get(k)
        if e is None:
            e = {"deps": None, "t": 0, "msg": "loading", "retry": 0, "src": "main", "op": st["operator"], "loads": 0}
            self.cache[k] = e
        now = mono_ms()
        e["t"] = now
        deps, msg = self._get(st, st["operator"], st["id"])
        src = "main"; op = st["operator"]
        e["loads"] = e["loads"] + 1 if msg == "loading" else 0      # the server answers "Loading..." on a cold station
        # The fallback steps in when the main source has nothing coming up: an error,
        # a station that never finishes loading, or a list that has gone stale.
        if st.get("fb_id") and not self._upcoming(deps) and (msg != "loading" or e["loads"] >= 3):
            gc.collect()
            d2, m2 = self._get(st, st.get("fb_operator") or st["operator"], st["fb_id"])
            if self._upcoming(d2):
                deps = d2; msg = None; src = "fallback"; op = st.get("fb_operator") or st["operator"]
            elif deps is None and m2 == "loading":
                msg = "loading"
        if deps is not None and not deps and e["deps"] is None and e.get("n0", 0) < 2:
            e["n0"] = e.get("n0", 0) + 1      # an empty first answer is often a station the server is still loading: ask again soon
            deps = None; msg = "loading"
        if deps is None:
            if e["deps"] is None: e["msg"] = msg
            e["retry"] = now + ((4000 if e["loads"] < 3 else 15000) if msg == "loading" else 60000)
            return
        e["deps"] = deps; e["msg"] = None; e["retry"] = 0; e["src"] = src; e["op"] = op
        gc.collect()

    def stale(self, st):
        e = self.cache.get(self.key(st))
        if e is None: return True
        now = mono_ms()
        if e["retry"]: return now >= e["retry"]
        return now - e["t"] >= self.cfg["poll"] * 1000

    def ensure(self, st):
        if self.stale(st): self.fetch(st)

    def fetch_dev(self):
        act = self.active()
        if not act or not self.cfg["ticker_dev"] or not self.cfg["st_ticker"] or self.cfg["status"] == "off": return
        now = mono_ms()
        if self.dev_t is not None and now - self.dev_t < 600000: return
        self.dev_t = now
        st = act[0]
        body = self.net.get(self.cfg["host"], self.cfg["port"], "/get_deviations?country=" + st["country"] + "&operator=" + st["operator"] + "&station=" + st["id"], limit=6000)
        out = []
        try:
            j = json.loads(body)
            if isinstance(j, list):
                for m in j[:3]:
                    m = str(m).replace("\n", " ").strip()
                    if m: out.append(m[:110])
        except Exception:
            pass                      # several operators answer this with nothing at all
        self.dev = out

    # ---- rows ----------------------------------------------------------
    def time_str(self, mins, canc, when):
        if canc: return self.S("cancel_s") if self.narrow() else self.S("cancel")
        fmt = self.cfg["time_fmt"]
        if fmt == "clock":
            h, m, wd, d, mo = dp_data.split_secs(when)
            return _pad2(h) + ":" + _pad2(m)
        if mins == 0:
            if self.cfg["now_hide"]: return ""
            if self.cfg["now_text"]: return self.cfg["now_text"]
            return self.S("now_s") if self.narrow() else self.S("now")
        if fmt == "min" and self.narrow(): fmt = "plain"
        if fmt == "min": return str(mins) + " " + self.S("min")
        if fmt == "tick": return str(mins) + "'"
        return str(mins)

    def tag(self, st):
        return dp_data.clean_dest(st["name"], 1)[:3]

    def rows_for(self, stations, limit, merged=False, skip=0):
        """-> (rows, message key or None)"""
        now = self.net.now()
        c = self.cfg
        items = []
        msg = None
        for st in stations:
            e = self.cache.get(self.key(st))
            if e is None or e["deps"] is None:
                if msg is None: msg = e["msg"] if e else "loading"
                continue
            if now is None:
                if msg is None: msg = "loading"
                continue
            for d in e["deps"]:
                diff = d[0] - now
                if diff < -20: continue
                mins = (diff + 30) // 60
                if mins < 0: mins = 0
                late = mins < st["walk"] and not d[5]
                if late and c["walk"] == "hide": continue
                items.append((d[0], d, st, mins, late))
        if not items: return [], (msg or "nodeps")
        items.sort(key=lambda x: x[0])
        rows = []
        for when, d, st, mins, late in items[skip:skip + limit]:
            rgb, pill = dp_cfg.line_color(st["country"], self.cache[self.key(st)]["op"], d[1], d[2], d[6])
            if c["badge"] == "mono" or (d[2] in ("BUS", "TRAM") and not c["bus_color"]): rgb = None
            elif rgb == dp_cfg.TONE_BOX and c["badge"] not in ("fill", "invert"): rgb = None
            rows.append({"line": d[1], "dest": d[3], "time": self.time_str(mins, d[5], when), "mins": mins,
                         "dly": ("+" + str(d[4])) if (c["delay"] == "plus" and d[4] > 0 and not d[5]) else "",
                         "canc": d[5], "dim": bool(d[5]) or (late and c["walk"] == "dim"),
                         "blink": c["blink"] != "off" and mins == 0 and not d[5],
                         "rgb": rgb, "pill": pill, "live": d[8], "tag": self.tag(st) if (merged and c["tag"]) else ""})
        return rows, None

    def _sig(self, rows, msg):
        if msg: return msg
        t = str((self.net.now() or 0) // 60) if (self.cfg["srow_time"] and self.cfg["srow"] != "off") else ""
        return t + "|".join([r["line"] + r["dest"] + r["time"] + r["dly"] + ("d" if r["dim"] else "") + ("b" if r["blink"] else "") + ("l" if r["live"] else "") for r in rows])

    def _page(self, pg, count=1):
        act = self.active()
        n = self.rows_max()
        if self.cfg["mode"] == "merged": return self.rows_for(act, n * count, True, pg * n)
        return self.rows_for([act[self.i]], n * count, False, pg * n)

    def page_rows(self):
        rows, msg = self._page(self.pg)
        if self.pg and not rows:        # the later page has run empty
            self.pg = 0
            rows, msg = self._page(0)
        return rows, msg

    def npages(self):
        """Pages for what is on screen: the station's own number, or the general one."""
        act = self.active()
        if self.cfg["mode"] == "merged" or self.i >= len(act): return self.cfg["pages"]
        return act[self.i].get("pages", 0) or self.cfg["pages"]

    def more_pages(self):
        if self.pg + 1 >= self.npages(): return False
        rows, msg = self._page(self.pg + 1)
        return bool(rows)

    def turn(self, pg):
        """Another page of the same station. Stations change one way, pages the other."""
        self.pg = pg
        self.draw_page(self.scr.nxt)
        k = self.cfg["page_trans"]
        if k == "auto": k = "scroll" if self.cfg["trans"] in ("left", "right") else "left"
        self.scr.hold()       # the same station: its row stays where it is
        self.scr.flip(k, self.on_frame)
        self.pager()
        self.t0 = mono_ms()

    def draw_page(self, bmp):
        rows, msg = self.page_rows()
        act = self.active()
        if msg == "loading" and self.cfg["mode"] == "rotate" and self.i < len(act):
            self.draw_intro(bmp, act[self.i])       # the station's title with a small loading mark, not a bare "Loading..."
            self.scr.spinner(bmp, self.spin)
        elif msg: self.scr.draw_message(bmp, [(msg[4:] if msg[:4] == "msg:" else self.S(msg), C_DIM)])
        else: self.scr.draw_rows(bmp, rows, self.cfg, self.header())
        if self.cfg["fb_mark"] and not msg:
            act = self.active()
            sts = act if self.cfg["mode"] == "merged" else act[self.i:self.i + 1]
            if [1 for s in sts if (self.cache.get(self.key(s)) or {}).get("src") == "fallback"]: self.scr.mark(bmp)
        self.sig = self._sig(rows, msg)
        self.ids = None if msg else [r["line"] + "|" + r["dest"] for r in rows]
        self.npg = 1
        p = self.npages()
        if p > 1 and not msg:
            n = self.rows_max()
            self.npg = max(1, (len(self._page(0, p)[0]) + n - 1) // n)

    def update_page(self):
        """What the page shows has changed. Departures that moved up can slide there."""
        a = self.cfg["list_anim"]
        old = self.ids
        scr = self.scr
        if a == "off" or not old:
            self.draw_page(scr.cur)
            return
        self.draw_page(scr.nxt)
        new = self.ids
        k = 0
        if new and new != old:
            k = -1                      # changed, but not simply moved up
            for s in range(1, len(old)):
                if old[s:] == new[:len(old) - s]:
                    k = s               # moved up by s rows
                    break
        scr.hold()
        if a == "roll":
            if k > 0: scr.roll(k * scr.pitch, self.on_frame)
            else: scr.flip("cut")
        else: scr.flip(a if k else "cut", self.on_frame)

    def header(self):
        """The station row: (name, lines, time) or None."""
        c = self.cfg
        if c["srow"] == "off": return None
        act = self.active()
        if c["mode"] == "merged" or self.i >= len(act): name = c["srow_text"] or self.S("deps"); lines = []
        else:
            st = act[self.i]; name = st["name"]
            lines = self.title_lines(st) if c["srow_lines"] else []
        tm = ""
        now = self.net.now()
        if c["srow_time"] and now is not None:
            h, m, wd, d, mo = dp_data.split_secs(now)
            tm = _pad2(h) + ":" + _pad2(m)
        return (name, lines, tm)

    def draw_intro(self, bmp, st):
        lines = self.title_lines(st)
        w = st["walk"]
        self.scr.draw_intro(bmp, st["name"], lines[:8],        # the name exactly as it stands in the settings
                            self.S("walk").replace("%", str(w)) if w else "", (str(w) + " " + self.S("min").upper()) if w else "", self.cfg)

    def title_lines(self, st):
        seen = []
        e = self.cache.get(self.key(st))
        lines = []
        if e and e["deps"]:
            for d in e["deps"]:
                if d[1] and d[1] not in seen:
                    seen.append(d[1])
                    rgb, pill = dp_cfg.line_color(st["country"], e["op"], d[1], d[2], d[6])
                    if self.cfg["badge"] == "mono" or (d[2] in ("BUS", "TRAM") and not self.cfg["bus_color"]): rgb = None
                    lines.append((d[1], rgb, pill))
        return lines

    # ---- flow ----------------------------------------------------------
    def restart(self):
        self.hw()
        self.scr.build(self.cfg)
        gc.collect()
        self.clock_s = None; self.tick_s = None; self.sig = None
        self.asleep = False
        keep = [self.key(s) for s in self.cfg["stations"]]
        for k in list(self.cache):
            if k not in keep: del self.cache[k]      # stations that were removed
        self.i = 0 if self.pin < 0 else self.pin
        self.pg = 0; self.npg = 1
        act = self.active()
        if self.i >= len(act): self.i = 0
        self.phase = "none"
        self.vis = 1; self.shown = True      # a fresh screen shows everything; the next tick puts it back to dark or ticker-only
        self.t_sec = 0
        self.status_update(True)
        if not act:
            ip = str(wifi.radio.ipv4_address) if wifi.radio.ipv4_address else ""
            self.scr.draw_message(self.scr.cur, [("Departures Plus", C_TONE), (self.S("setup"), C_DIM), ("http://" + ip, C_DIM)])
            self.pager()
            display.refresh()
            return
        if self.cfg["mode"] == "merged":
            self.phase = "deps"
            self.draw_page(self.scr.cur)
            self.pager()
            display.refresh()
            self.t0 = mono_ms()
        else:
            self.show(self.i, False)

    def show(self, idx, animate=True):
        act = self.active()
        if not act: return
        self.i = idx % len(act)
        self.pg = 0
        st = act[self.i]
        scroll = self.cfg["trans"] if animate else "cut"
        if self.cfg["intro"] > 0 and (len(act) > 1 or self.phase == "none" or self.cfg["intro_single"]):
            self.phase = "intro"
            self.draw_intro(self.scr.nxt, st)
            self.scr.flip(scroll, self.on_frame)
            self.pager()
            display.refresh()
            if self.stale(st):         # fetch behind the still intro screen, then fill in the line signets
                self.fetch(st)
                self.draw_intro(self.scr.cur, st)
                display.refresh()
        else:
            self.ensure(st)
            self.phase = "deps"
            self.draw_page(self.scr.nxt)
            self.scr.flip(scroll, self.on_frame)
            self.pager()
            display.refresh()
        self.t0 = mono_ms()

    def on_frame(self):
        self.scr.step_ticker()

    def next_station(self):
        act = self.active()
        if len(act) < 2: return
        ni = (self.i + 1) % len(act)
        skip = self.cfg["skip"]
        now = self.net.now()
        if skip > 0 and now is not None:
            for s in range(1, len(act) + 1):
                c = (self.i + s) % len(act)
                e = self.cache.get(self.key(act[c]))
                if e is None or e["deps"] is None:
                    ni = c
                    break
                if any((0 <= d[0] - now <= skip * 60) and not d[5] for d in e["deps"]):
                    ni = c
                    break
        self.show(ni)

    def pager(self, prog=0.0):
        rot = self.cfg["mode"] == "rotate"
        self.scr.set_pager(self.cfg["pager"], len(self.active()) if rot else 1, self.i if rot else 0, prog, self.npg, self.pg)

    def status_update(self, force=False):
        if not self.scr.band: return False
        c = self.cfg
        changed = False
        now = self.net.now()
        cs = ""; date = ""
        if now is None:
            if c["st_clock"]: cs = "--:--"
        else:
            h, m, wd, d, mo = dp_data.split_secs(now)
            if c["st_clock"]: cs = _pad2(h) + ":" + _pad2(m)
            if c["st_date"] != "off":
                date = str(d) + "." + str(mo) + "."
                if c["st_date"] == "wday":
                    days = self.S("days").split(",")
                    if len(days) != 7: days = dp_cfg.STR["days"].split(",")
                    date = days[wd].strip() + " " + date
        ic = [(c["icon%d" % k], c["icon%d_c" % k]) for k in (1, 2, 3)]
        left = cs + "|" + date + "|" + str(ic)
        if left != self.clock_s or force:
            self.clock_s = left
            self.scr.set_left(cs, date, c["st_icon"] and c["st_clock"], ic, c["st_icons"], c["clock_pos"])
            changed = True
        self.prune()
        parts = []
        if self.vis == 2: parts = [m[1] for m in self.msgs if m[3]]
        elif c["st_ticker"]:
            if c["ticker_text"]: parts.append(c["ticker_text"])
            parts += [m[1] for m in self.msgs]       # all of them together, each until its own time is up
            if c["ticker_dev"]: parts += self.dev
        if parts != self.tick_s or self.tick_reset or force:
            self.scr.set_ticker(parts, self.tick_reset or force)     # the belt keeps running, only its contents change
            self.tick_s = parts
            self.tick_reset = False
            changed = True
        return changed

    def button(self):
        if self.cfg["button"] == "power": self.set_power(not self.power)
        elif self.shown and self.cfg["mode"] == "rotate": self.next_station()

    def set_power(self, on):
        self.power = bool(on)
        self.apply_shown()

    def sched_ok(self):
        c = self.cfg
        now = self.net.now()
        if not c["sched"] or now is None: return True
        h, m, wd, d, mo = dp_data.split_secs(now)
        t = h * 60 + m
        on = c["sched_on"]; off = c["sched_off"]
        days = c["sched_days"].split(";")
        spec = days[wd].strip() if wd < len(days) else ""
        if spec == "off": return False
        if "-" in spec:
            on = spec.split("-")[0]; off = spec.split("-")[1]
        a = dp_cfg.hhmm(on, 0)
        b = dp_cfg.hhmm(off, 1439)
        if a == b: return True
        return (a <= t < b) if a < b else (t >= a or t < b)

    def prune(self):
        t = mono_ms()
        self.msgs = [m for m in self.msgs if not m[2] or m[2] > t]

    def woken(self):
        """A ticker message that asked for it lights the ticker of a switched-off display while it runs."""
        if not self.scr.band or not self.cfg["st_ticker"]: return False
        self.prune()
        for m in self.msgs:
            if m[3]: return True
        return False

    def apply_shown(self):
        want = 1 if (self.power and self.sched_ok() and not self.asleep) else (2 if self.woken() else 0)
        if want == self.vis: return
        self.vis = want
        self.shown = want == 1
        self.scr.power(want)
        self.tick_reset = True   # ticker-only shows just the waking messages
        if want == 1:
            self.sig = None
            self.t_sec = 0
            self.t0 = mono_ms()
            if self.cfg["power_wait"]: self.cache = {}     # nothing was fetched while dark: wait for fresh data
            if self.cfg["mode"] == "rotate" and self.active():
                self.phase = "none"              # back on: start over with the first station and its title
                self.show(0 if self.pin < 0 else self.pin, False)
        elif want == 2:
            self.status_update()
            display.refresh()

    def message(self, text, ttl=60, mid="", wake=False):
        text = str(text).replace("\n", " ").strip()[:120]
        mid = str(mid) or text
        new = [mid, text, (mono_ms() + int(ttl) * 1000) if int(ttl) > 0 else 0, bool(wake)]
        for i in range(len(self.msgs)):
            if self.msgs[i][0] == mid:           # the same id again replaces the message where it stands
                self.msgs[i] = new
                new = None
                break
        if new: self.msgs.append(new)
        self.msgs = [m for m in self.msgs if m[1]][-10:]

    def poll_one(self, act):
        for st in act:
            if self.stale(st):
                self.fetch(st)        # one request per pass keeps the ticker moving
                self.t_sec = 0
                return True
        return False

    def tick(self):
        now = mono_ms()
        scr = self.scr
        act = self.active()
        second = now - self.t_sec >= 1000
        if second:
            self.t_sec = now
            if self.cfg["sleep"] and act and self.net.now() is not None:
                rows, msg = self.rows_for(act, 1, True)
                self.asleep = msg == "nodeps"
            else:
                self.asleep = False
            self.prune()
            self.apply_shown()
        dirty = False
        sp = self.cfg["ticker_speed"]
        if self.vis and now - self.t_tick >= (60 if sp == "slow" else 18 if sp == "fast" else 35):
            self.t_tick = now
            if scr.step_ticker(): dirty = True
        if not self.shown:
            if second and self.power and self.asleep: self.poll_one(act)   # keep looking for the first departure
            if self.vis == 2:
                if second and self.status_update(): dirty = True
                if dirty: display.refresh()
            return
        lv = self.cfg["live"]
        if lv == "tick" or lv in dp_draw.LIVE:
            if lv == "tick": lv = "dot"; ph = (now // 450) % 3          # pulses like the dot, always
            else: ph = (now // 450) % 3 if self.cfg["live_anim"] else 3
            if (lv, ph) != scr.anim:
                scr.set_anim(lv, ph)
                dirty = True
        bl = (now // 500) % 2 == 0
        if bl != self.blink:
            self.blink = bl
            scr.set_blink(bl)
            dirty = True
        if second:
            if self.status_update(): dirty = True
            if act and self.phase == "deps":
                rows, msg = self.page_rows()
                if self._sig(rows, msg) != self.sig:
                    self.update_page()
                    dirty = True
        if act:
            if self.cfg["mode"] == "merged":
                if self.cfg["pages"] > 1 and now - self.t0 >= self.cfg["dwell"] * 1000:
                    if self.more_pages(): self.turn(self.pg + 1)
                    elif self.pg: self.turn(0)
                    else: self.t0 = now
                    dirty = True
                else: self.poll_one(act)
            elif self.phase == "intro":
                if now - self.t0 >= self.cfg["intro"] * 1000:
                    self.phase = "deps"
                    self.draw_page(scr.nxt)
                    scr.flip(self.cfg["trans"], self.on_frame)
                    self.t0 = mono_ms()
                    dirty = True
            elif self.phase == "deps":
                due = now - self.t0 >= self.cfg["dwell"] * 1000
                if due and self.more_pages():
                    self.turn(self.pg + 1)
                    dirty = True
                elif due and len(act) > 1 and self.pin < 0:
                    self.next_station()
                    dirty = True
                elif due and self.cfg["intro_single"] and self.cfg["intro"] > 0 and (len(act) == 1 or self.pin >= 0):
                    self.show(self.i)
                    dirty = True
                elif due and self.npages() > 1:
                    if self.pg: self.turn(0)
                    else: self.t0 = now          # a single page for now: look again after the next round
                    dirty = True
                elif self.stale(act[self.i]):
                    self.fetch(act[self.i])
                    self.t_sec = 0
                elif len(act) > 1 and self.pin < 0 and self.cfg["dwell"] * 1000 - (now - self.t0) < 2500 and now - self.t_pre >= 3000:
                    # Load the next station just before its turn, so the ticker is held up only then.
                    self.t_pre = now
                    nx = act[(self.i + 1) % len(act)]
                    if self.stale(nx):
                        self.fetch(nx)
                        self.t_sec = 0
                if self.sig == "loading" and now - self.t_spin >= 300:
                    self.t_spin = now
                    self.spin += 1
                    scr.spinner(scr.cur, self.spin)
                    dirty = True
            if self.cfg["pager"] == "bar" and self.cfg["mode"] == "rotate" and now - self.t_bar >= 200:
                self.t_bar = now
                intro = self.cfg["intro"] * 1000 if len(act) > 1 else 0
                el = (mono_ms() - self.t0) + (intro if self.phase == "deps" else 0)
                self.pager(min(1.0, el / max(1, intro + self.cfg["dwell"] * 1000)))
                dirty = True
            self.fetch_dev()
        if dirty: display.refresh()

    def state(self):
        act = self.active()
        now = self.net.now()
        out = {"app": dp_cfg.APP, "version": dp_cfg.VERSION, "power": 1 if self.power else 0, "shown": 1 if self.shown else 0,
               "asleep": 1 if self.asleep else 0, "brightness": self.cfg["brightness"], "mode": self.cfg["mode"], "phase": self.phase,
               "index": self.i, "page": self.pg, "pinned": self.pin, "station": act[self.i]["name"] if act and self.i < len(act) else "",
               "time": (self.clock_s or "").split("|")[0], "ticker_text": self.cfg["ticker_text"], "messages": [m[1] for m in self.msgs], "width": self.scr.W, "height": self.scr.H, "stations": [],
               "woken": 1 if self.vis == 2 else 0,
               "uptime": int(time.monotonic() // 60)}
        try:
            out["temperature"] = round(microcontroller.cpu.temperature)
            out["tx_power"] = wifi.radio.tx_power
            out["rssi"] = wifi.radio.ap_info.rssi
        except Exception:
            pass
        for st in act:
            nxt = []
            e = self.cache.get(self.key(st))
            if e and e["deps"] and now is not None:
                for d in e["deps"]:
                    diff = d[0] - now
                    if diff < -20: continue
                    nxt.append({"line": d[1], "dest": d[3], "mins": max(0, (diff + 30) // 60), "mode": d[2]})
                    if len(nxt) >= 4: break
            out["stations"].append({"name": st["name"], "status": (e["msg"] or "ok") if e else "waiting",
                                    "source": e["src"] if e else "main", "operator": e["op"] if e else st["operator"], "next": nxt})
        return out

    def debug(self):
        return {"version": dp_cfg.VERSION, "uptime": mono_ms() // 1000, "free": gc.mem_free() if hasattr(gc, "mem_free") else -1, "clock_offset": self.net.t_off,
                "last_request": self.net.last, "notes": self.notes,
                "cache": [{"key": k, "count": len(v["deps"]) if v["deps"] is not None else None, "msg": v["msg"], "src": v["src"],
                           "age": (mono_ms() - v["t"]) // 1000} for k, v in self.cache.items()]}
