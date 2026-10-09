# Departures Plus - configuration, strings and line colours.
# Pure data and helpers, no hardware access.
import json

VERSION = "0.8.0"
APP = "departuresplus"
CFG_FILE = "departuresplus.json"

DEFAULTS = {
    "stations": [],          # [{name, country, operator, id, walk, on, lines, dir, modes, fb_operator, fb_id}]
    "mode": "rotate",        # rotate | merged
    "tag": 1,                # merged list: first letters of the station next to each departure
    "intro": 2,              # seconds in steps of 0.5, 0 = off
    "intro_single": 0,       # with one station only: show its title again after every round
    "dwell": 7,              # seconds of departures per page
    "pages": 1,              # up to N pages of departures per station, one after the other
    "page_trans": "auto",    # how a page turns: auto (sideways, or up when stations move sideways) or any page change
    "trans": "scroll",       # scroll (up) | down | left | right | dissolve | blinds | wipe | random | cut
    "list_anim": "off",      # off | roll | scroll | down | left | right: departures that move up slide there
    "skip": 0,               # skip a station with nothing leaving within N min, 0 = never
    "pager": "dots",         # dots | bar | off
    "font": "normal",        # compact | normal | large
    "max_rows": 0,           # 0 = as many as fit
    "badge": "fill",         # fill | invert (white box, coloured name) | text | mono
    "badge_ink": "auto",     # auto | black | white: the text inside a signet
    "bus_color": 1,
    "time_fmt": "min",       # min | tick | plain | clock
    "now_text": "",          # empty = "now"
    "now_hide": 0,           # show no time at all while a departure is leaving
    "min_text": "",
    "nodeps_text": "",
    "delay": "incl",         # incl | plus
    "delay_color": "red",    # red | tone: the "+3" of the plus style
    "live": "off",           # off | wave | dot | bar: a mark behind real-time departures; tick: their ' pulses; approx: "~" in front of timetable ones
    "live_anim": 1,          # the mark moves
    "blink": "time",         # off | time | dest | line | row: what blinks while a departure is leaving
    "walk": "dim",           # show | dim | hide
    "strip_prefix": 1,       # drop "S+U ", "U ", "S " in front of destinations
    "strip": "",             # comma separated text to remove from destinations
    "abbr": "",              # comma separated long=short pairs, used when a destination does not fit
    "line_len": 0,           # cut line names to N characters, 0 = off
    "line_col": 3,           # the line column is at least N characters wide, 0 = as narrow as the lines shown
    "gap": 3,                # pixels between the line column and the destination
    "walk_text": "",         # walking time on the station title, % is the number of minutes
    "days_text": "",         # seven weekday names, Monday first, comma separated
    "status": "on",          # on | off: the row at the bottom
    "st_clock": 1,
    "st_icon": 0,            # small clock symbol in front of the time
    "st_date": "wday",       # off | date | wday
    "st_ticker": 1,
    "ticker_color": "white", # white | tone
    "ticker_text": "",       # always in the ticker
    "ticker_gapless": 1,     # an endless belt; 0 = a round leaves the screen before the next one starts
    "ticker_sep": "+++",     # stands between two texts
    "ticker_dev": 1,         # show the operator's service messages in the ticker
    "ticker_speed": "normal",  # fast | normal | slow
    "tone": "amber",         # see dp_draw.TONES, or "custom" with tone_hex
    "tone_hex": "#ff9900",
    "margin_l": 0,           # unused columns at the left and right edge
    "margin_r": 0,
    "brightness": 2,         # 1..3
    "invert": 0,             # the whole panel lit, the text dark
    "button": "next",        # next | power
    "sleep": 0,              # display off while nothing departs
    "sched": 0,              # daily on/off times
    "sched_on": "06:00",
    "sched_off": "23:00",
    "sched_days": "",        # Mon..Sun separated by ";": "" = the times above, "off", or "06:30-22:00"
    "flip": 0,               # turn the picture by 180 degrees
    "tx_power": 0,           # Wi-Fi transmit power in dBm, 0 = leave the board's own setting
    "poll": 30,              # seconds between requests per station
    "host": "data.t-skylt.se",
    "port": 90,
}

CHOICES = {
    "mode": ("rotate", "merged"), "trans": ("scroll", "down", "left", "right", "dissolve", "blinds", "wipe", "random", "cut"),
    "page_trans": ("auto", "scroll", "down", "left", "right", "dissolve", "blinds", "wipe", "random", "cut"),
    "list_anim": ("off", "roll", "scroll", "down", "left", "right", "dissolve", "blinds", "wipe"), "pager": ("dots", "bar", "off"),
    "font": ("compact", "normal", "large"), "badge": ("fill", "invert", "text", "mono"),
    "time_fmt": ("min", "tick", "plain", "clock"), "delay": ("incl", "plus"), "walk": ("show", "dim", "hide"),
    "status": ("on", "off"), "st_date": ("off", "date", "wday"), "ticker_color": ("white", "tone"),
    "tone": ("amber", "orange", "yellow", "white", "warm", "red", "green", "blue", "cyan", "pink", "custom"),
    "button": ("next", "power"), "ticker_speed": ("fast", "normal", "slow"),
    "blink": ("off", "time", "dest", "line", "row"), "live": ("off", "wave", "dot", "bar", "tick", "approx"), "delay_color": ("red", "tone"), "badge_ink": ("auto", "black", "white"),
}
LIMITS = {"intro": (0, 10), "dwell": (3, 60), "pages": (1, 3), "skip": (0, 60), "brightness": (1, 3), "poll": (20, 600),
          "port": (1, 65535), "max_rows": (0, 16), "line_len": (0, 6), "line_col": (0, 6), "gap": (0, 12), "tx_power": (0, 20), "margin_l": (0, 12), "margin_r": (0, 12)}
STRLEN = {"ticker_text": 160, "abbr": 240, "strip": 120, "sched_days": 100, "tone_hex": 7, "walk_text": 24, "days_text": 70, "ticker_sep": 12, "nodeps_text": 60}

# Fixed words. Each can be replaced with the setting named <key>_text.
STR = {"now": "now", "now_s": "0", "cancel": "cancelled", "cancel_s": "canc.", "min": "min", "walk": "% MIN WALK",
       "days": "Mon,Tue,Wed,Thu,Fri,Sat,Sun", "nodeps": "No departures", "nodata": "No data",
       "loading": "Loading...", "setup": "Set up at:"}
# Settings saved before 0.5 had a display language instead of free texts: (walk, days, now, nodeps).
OLD_LANG = {"de": ("% MIN ZU FUSS", "Mo,Di,Mi,Do,Fr,Sa,So", "sofort", "Keine Abfahrten"),
            "sv": ("% MIN ATT GÅ", "Mån,Tis,Ons,Tor,Fre,Lör,Sön", "nu", "Inga avgångar")}

# Applied in order, only while a destination is too wide for its column.
ABBR = (("Zoologischer Garten", "Zoo"), ("Straße", "Str."), ("straße", "str."), ("Platz", "Pl."),
        ("platz", "pl."), ("Rathaus", "Rath."), ("Bahnhof", "Bhf"), ("bahnhof", "bhf"), ("Hauptbhf", "Hbf"),
        ("centrum", "C"), ("strand", "str."), ("Station", "Stn"))

TONE_BOX = -1   # "no known colour": draw the signet in the board's own LED tone
_tabs = {}      # "de/vbb" -> {key: 0xRRGGBB}, read from colors.txt when an operator first shows up


def _table(op):
    t = _tabs.get(op)
    if t is None:
        t = {}
        try:
            with open("colors.txt") as f:
                for row in f:
                    cut = row.find("|")
                    if cut < 0 or op not in row[:cut].split(","): continue
                    for part in row[cut + 1:].split():
                        kv = part.split("=")
                        pre = ""
                        for k in kv[0].split(","):
                            if "/" in k: pre = k[:k.find("/") + 1]      # "METRO/10,11" means METRO/10 and METRO/11
                            else: k = pre + k
                            t[k] = int(kv[1], 16)
                    break
        except Exception as e:
            print("departuresplus: colors.txt,", e)
        _tabs[op] = t
    return t


def line_color(country, operator, line, mode, api_color):
    """Returns (rgb as shown on a monitor or TONE_BOX, rounded corners). The screen converts it for the LED panel."""
    line = str(line).upper().replace(" ", "")
    pill = mode in ("BUS", "TRAM") or (line[:1] == "S" and line[1:2].isdigit())
    t = _table(country + "/" + operator)
    c = t.get(mode + "/" + line)
    if c is None: c = t.get(line)
    if c is None and api_color:
        try:
            a = str(api_color).replace("#", "").split("~")[0]      # "f00~fff~": signet and text colour
            if len(a) == 3: a = a[0] * 2 + a[1] * 2 + a[2] * 2
            if len(a) == 6: c = int(a, 16)
        except Exception: pass
    if c is None: c = t.get("@" + mode)
    return (TONE_BOX if c is None else c), pill


def pairs(text):
    """ "Hauptbahnhof=Hbf, Flughafen=Flugh." -> [("Hauptbahnhof", "Hbf"), ...] """
    out = []
    for p in str(text).split(","):
        kv = p.split("=")
        if len(kv) == 2 and kv[0].strip(): out.append((kv[0].strip(), kv[1].strip()))
    return out


def hhmm(text, fallback):
    """ "6:30" -> 390 minutes after midnight """
    try:
        p = str(text).split(":")
        return max(0, min(1439, int(p[0]) * 60 + int(p[1])))
    except Exception:
        return fallback


def _clean_station(s):
    out = {"name": str(s.get("name", ""))[:40], "country": str(s.get("country", "")), "operator": str(s.get("operator", "")),
           "id": str(s.get("id", "")), "on": 1 if s.get("on", 1) else 0, "lines": str(s.get("lines", ""))[:80],
           "modes": str(s.get("modes", "")).upper()[:40],
           "fb_operator": str(s.get("fb_operator", ""))[:20], "fb_id": str(s.get("fb_id", ""))[:60]}
    try: out["walk"] = max(0, min(60, int(s.get("walk", 0))))
    except Exception: out["walk"] = 0
    try: out["dir"] = max(0, min(2, int(s.get("dir", 0))))
    except Exception: out["dir"] = 0
    try: out["pages"] = max(0, min(3, int(s.get("pages", 0))))      # 0 = the general setting
    except Exception: out["pages"] = 0
    return out


def merge(cfg, new):
    """Copies known keys from `new` into `cfg`, coercing and clamping. Returns changed keys."""
    changed = []
    for k in new:
        if k not in DEFAULTS: continue
        v = new[k]; d = DEFAULTS[k]
        try:
            if k == "stations":
                if not isinstance(v, list): continue
                v = [_clean_station(s) for s in v if isinstance(s, dict) and s.get("id")][:10]
            elif k in CHOICES:
                v = str(v)
                if k == "status" and v in ("clock", "ticker"):      # settings saved by 0.2
                    cfg["st_ticker"] = 1 if v == "ticker" else 0
                    v = "on"
                if k == "blink" and v in ("0", "1"): v = "time" if v == "1" else "off"
                if v not in CHOICES[k]: continue
            elif k == "intro":
                v = round(float(v) * 2) / 2
                if v == int(v): v = int(v)
                v = max(0, min(10, v))
            elif isinstance(d, int):
                v = int(float(v))
                if k in LIMITS: v = max(LIMITS[k][0], min(LIMITS[k][1], v))
            else:
                v = str(v).replace("\n", " ")[:STRLEN.get(k, 64)]
        except Exception:
            continue
        if cfg.get(k) != v:
            cfg[k] = v; changed.append(k)
    return changed


def load():
    cfg = {}
    for k in DEFAULTS:
        cfg[k] = list(DEFAULTS[k]) if isinstance(DEFAULTS[k], list) else DEFAULTS[k]
    try:
        with open(CFG_FILE) as f: j = json.loads(f.read())
        merge(cfg, j)
        o = OLD_LANG.get(j.get("lang"))
        if o and "walk_text" not in j:
            cfg["walk_text"] = o[0]; cfg["days_text"] = o[1]
            if not cfg["now_text"]: cfg["now_text"] = o[2]
            if not cfg["nodeps_text"]: cfg["nodeps_text"] = o[3]
    except Exception as e:
        print("departuresplus: no saved config,", e)
    return cfg


def save(cfg):
    try:
        with open(CFG_FILE, "w") as f: f.write(json.dumps(cfg))
        return True
    except Exception as e:
        print("departuresplus: could not save,", e)   # USB-connected boards are read-only to their own code
        return False
