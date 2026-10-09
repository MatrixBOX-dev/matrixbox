# Departures Plus - clock arithmetic, HTTP and departure parsing.
from __main__ import pool
import time, json
import dp_cfg

_MON = "JanFebMarAprMayJunJulAugSepOctNovDec"


def mono_ms():
    # Integer milliseconds. time.monotonic() is a 30-bit float on the device and
    # loses sub-second precision after a few hours of uptime.
    return time.monotonic_ns() // 1000000


def _days(y, m, d):
    # Days since 1970-01-01 (proleptic Gregorian).
    if m <= 2: y -= 1
    era = y // 400
    yoe = y - era * 400
    doy = (153 * (m + (-3 if m > 2 else 9)) + 2) // 5 + d - 1
    doe = yoe * 365 + yoe // 4 - yoe // 100 + doy
    return era * 146097 + doe - 719468


def iso_secs(s):
    # "2026-10-09T02:16:00" -> seconds, read as a naive local time
    return _days(int(s[0:4]), int(s[5:7]), int(s[8:10])) * 86400 + int(s[11:13]) * 3600 + int(s[14:16]) * 60 + int(s[17:19])


def hdr_secs(v):
    # "Fri, 09 Oct 2026 02:15:17 +0200" -> seconds in the server's local time.
    p = v.strip().split()
    mon = _MON.find(p[2]) // 3 + 1
    h = p[4].split(":")
    secs = _days(int(p[3]), mon, int(p[1])) * 86400 + int(h[0]) * 3600 + int(h[1]) * 60 + int(h[2])
    if len(p) > 5 and p[5] == "GMT": secs += 7200   # same assumption the stock app makes
    return secs


def split_secs(secs):
    # -> (hour, minute, weekday 0=Mon, day, month)
    days = secs // 86400
    rem = secs - days * 86400
    z = days + 719468
    era = z // 146097
    doe = z - era * 146097
    yoe = (doe - doe // 1460 + doe // 36524 - doe // 146096) // 365
    doy = doe - (365 * yoe + yoe // 4 - yoe // 100)
    mp = (5 * doy + 2) // 153
    d = doy - (153 * mp + 2) // 5 + 1
    m = mp + (3 if mp < 10 else -9)
    return rem // 3600, (rem % 3600) // 60, (days + 3) % 7, d, m


class Net:
    def __init__(self):
        self.t_off = None      # server local seconds minus monotonic seconds
        self.last = {}         # what the most recent request did, for /api/debug

    def now(self):
        if self.t_off is None: return None
        return self.t_off + mono_ms() // 1000

    def get(self, host, port, path, limit=60000):
        """Plain HTTP/1.0 GET. Returns the body as str, or None."""
        info = {"path": path, "at": mono_ms() // 1000, "bytes": 0, "error": "", "date": ""}
        self.last = info
        req = ("GET " + path + " HTTP/1.0\r\nHost: " + host + "\r\nUser-Agent: DeparturesPlus/" + dp_cfg.VERSION +
               " (MatrixBOX)\r\nAccept: application/json\r\nConnection: close\r\n\r\n")
        data = bytearray()
        try:
            with pool.socket() as s:
                s.settimeout(6)
                s.connect((host, int(port)))
                s.sendall(req.encode("utf-8"))
                buf = bytearray(1024)
                while len(data) < limit:
                    n = s.recv_into(buf)
                    if not n: break
                    data += buf[:n]
        except Exception as e:
            info["error"] = "socket: " + str(e)
            if not data: return None
        info["bytes"] = len(data)
        try:
            raw = bytes(data)
            cut = raw.find(b"\r\n\r\n")
            skip = 4
            if cut < 0:
                cut = raw.find(b"\n\n")
                skip = 2
            if cut < 0:
                info["error"] = "no header end"
                return None
            # The server ends its status line with a bare \n, so split on \n and trim.
            for line in raw[:cut].decode("utf-8").split("\n"):
                line = line.strip()
                if line[:5].lower() == "date:":
                    info["date"] = line[5:].strip()
                    try: self.t_off = hdr_secs(line[5:]) - mono_ms() // 1000
                    except Exception as e: info["error"] = "date: " + str(e)
            body = raw[cut + skip:].decode("utf-8")
            info["body"] = body[:120]
            return body
        except Exception as e:
            info["error"] = "decode: " + str(e)
            return None


def clean_dest(d, strip_prefix, strip=()):
    d = str(d)
    cut = d.find("(")
    if cut > 0: d = d[:cut]
    for s in strip:
        if s: d = d.replace(s, "")
    d = d.strip()
    if strip_prefix:
        for p in ("S+U ", "U ", "S "):
            if d[:len(p)] == p and len(d) > len(p) + 1:
                d = d[len(p):]
                break
    return d


def parse(body, st, cfg):
    """-> (departures, message). A departure is [when, line, mode, dest, delay, cancelled, color, direction, live].
    message is None, "loading", "nodata" or "msg:<text from the server>"."""
    try: j = json.loads(body)
    except Exception:
        # A very long list cut off by the size limit: keep the complete entries.
        cut = body.rfind('}, {"destination"')
        if cut < 0: return None, "nodata"
        try: j = json.loads(body[:cut + 1] + "]}")
        except Exception: return None, "nodata"
    deps = j.get("departures") if isinstance(j, dict) else None
    if not isinstance(deps, list):
        msg = str(j.get("msg", "")) if isinstance(j, dict) else ""
        if "oading" in msg: return None, "loading"
        return None, ("msg:" + msg[:40]) if msg else "nodata"
    # "U2 S7" only these lines, "-M4" not this one, "U7:1" / "-U7:2" the same for one direction only
    inc = []; exc = []
    for x in str(st.get("lines", "")).upper().replace(",", " ").split():
        neg = x[:1] in ("-", "!")
        if neg: x = x[1:]
        p = x.split(":")
        try: rd = int(p[1]) if len(p) > 1 else 0
        except Exception: rd = 0
        if p[0]: (exc if neg else inc).append((p[0], rd))
    modes = [x.strip() for x in str(st.get("modes", "")).split(",") if x.strip()]
    wdir = int(st.get("dir", 0) or 0)
    strip = [x.strip() for x in str(cfg.get("strip", "")).split(",") if x.strip()]
    cut = int(cfg.get("line_len", 0) or 0)
    out = []
    for d in deps:
        try:
            ln = d.get("line") or {}
            line = str(ln.get("id", "") or ln.get("designation", ""))
            if line == "0": line = ""
            mode = str(ln.get("transport_mode", ""))
            if modes and mode not in modes: continue
            dc = int(d.get("direction_code", 0) or 0)
            key = line.upper().replace(" ", "")
            if inc and not [1 for r in inc if r[0] == key and (not r[1] or not dc or r[1] == dc)]: continue
            if [1 for r in exc if r[0] == key and (not r[1] or r[1] == dc)]: continue
            if wdir and dc and dc != wdir: continue
            delay = d.get("delay") or 0
            try: delay = int(delay)
            except Exception: delay = 0
            canc = 1 if d.get("cancelled") else 0
            if cut: line = line[:cut]
            out.append([iso_secs(d["expected"]), line, mode,
                        clean_dest(d.get("destination", ""), cfg["strip_prefix"], strip), delay, canc, d.get("color") or "", dc,
                        0 if d.get("deviations") == "#" else 1])     # the server marks timetable-only times with "#"
        except Exception:
            pass
    out.sort(key=lambda x: x[0])
    return out[:60], None
