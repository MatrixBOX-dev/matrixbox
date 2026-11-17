import json, time, gc, math, os, struct
import storage
import displayio
from __main__ import *
import load_settings
from check_button import check_if_button_pressed
from web_interface import header as web_header, footer as web_footer

# `from __main__ import *` above only copies whatever window/display/palette
# etc. objects existed in __main__'s namespace at this exact moment -- it's a
# one-time snapshot, not a live reference. flights/__init__.py just rebuilt
# all of these (init_display(bit_depth=5)) before importing this file, so
# normally the snapshot above would already be current -- but relying on
# that cross-module propagation having landed correctly turned out to be
# fragile (unlike pprint()/clearscreen()/refresh(), which are always safe
# since they're defined in load_screen.py and read its own live globals
# regardless of which module calls them). Fetching these directly from
# load_screen itself guarantees this file draws into the Bitmap/Group that
# are actually on screen right now, not a stale, orphaned pre-rebuild one.
import load_screen
window = load_screen.window
display = load_screen.display
palette = load_screen.palette
matrix = load_screen.matrix
rf_group = load_screen.rf_group
tile_groupgroup = load_screen.tile_groupgroup

microcontroller.cpu.frequency = 240000000

# Blank the LED matrix for the duration of any disk write, then restore.
#
# Writing to this device's flash draws current at the same moment the LED
# matrix driver is also actively refreshing pixels; per the user, the
# combined simultaneous draw causes voltage spikes intense enough to
# sometimes corrupt the write in progress -- this matches corruption
# observed earlier in this app's own settings/basemap files. Hiding the
# display (root_group.hidden = True) during the write removes the matrix
# driver's contribution to that current draw. This is not a new technique
# invented here -- it's the exact same mitigation lib/filemanager.py's
# "Save"/"New file"/"Delete" filesystem actions already use successfully
# (see _hide_display()/_show_display() there); this just applies it to
# this app's own two disk writes (settings.json and the basemap bitmap).
class _blank_for_disk_write:
    def __enter__(self):
        try:
            display.root_group.hidden = True
            display.refresh()
        except Exception:
            pass
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        try:
            display.root_group.hidden = False
            display.refresh()
        except Exception:
            pass
        return False  # never suppress the original exception, if any

# Dim the shared LED palette for the duration of this app's session only.
# Full-brightness colors were too bright and drew too much current,
# especially for near-full-screen content like map mode. main.py's
# initialize_app() already backs up palette[0..11] before launching an app
# and restores it in a finally block after the app exits, so mutating the
# live `palette` object here is automatically undone afterward -- this does
# NOT touch lib/load_screen.py or affect any other app/skin.
#
# _DIM_MIN enforces a visibility floor (below ~22 per channel this panel
# can't show a lit pixel at all), but it must be applied by scaling each
# color's channels together (preserving their ratio/hue), NOT by clamping
# each channel independently up to the floor. An earlier version did the
# latter, which badly distorted highly saturated colors: e.g. green
# (0,100,10) dimmed to (0,33,3) then had its near-zero blue channel forced
# all the way up to 22, yielding (0,33,22) -- a washed-out cyan/yellow-ish
# color rather than green. Scaling the whole triplet up only when its
# brightest channel would otherwise fall below the floor keeps hues intact.
_DIM_FACTOR = 3
_DIM_MIN = 22
_ORIGINAL_PALETTE = {
    0: (0, 0, 0), 1: (50, 50, 0), 2: (15, 15, 15), 3: (0, 59, 122),
    4: (100, 0, 0), 5: (20, 20, 20), 6: (20, 20, 40), 7: (0, 100, 10),
    8: (0, 0, 100), 9: (0, 30, 3), 11: (50, 30, 0), 12: (0, 0, 100),
}
def _dim_rgb(rgb):
    if all(c == 0 for c in rgb):
        return rgb
    scaled = tuple(c / _DIM_FACTOR for c in rgb)
    if max(scaled) >= _DIM_MIN:
        return tuple(round(c) for c in scaled)
    factor = _DIM_MIN / max(rgb)
    return tuple(round(c * factor) for c in rgb)

for _i, _rgb in _ORIGINAL_PALETTE.items():
    palette[_i] = _dim_rgb(_rgb)
del _i, _rgb

# Index 6 isn't used by anything else in this app (map mode's color
# quantizer only ever uses 0,1,2,3,5,7,9,11) -- repurpose it as a dedicated
# very dim neutral grey exclusively for grayscale map mode's parks/forest.
# With the panel's bit_depth at 6 values this low are visible; raise it if
# it disappears, lower it to save more power.
palette[6] = (10, 10, 10)


# ── Settings ────────────────────────────────────────────────────────────────
SETTINGS_FILE = "flights_settings.json"

DEFAULT_SETTINGS = {
    "airport": "ARN",
    "mode": "departures",   # "departures", "arrivals", "both", or "map"
    "refresh": 60,          # seconds between API calls
    "api_endpoint": "https://api.swedavia.se/flightinfo/v2",  # base URL only; airport/mode/date are appended
    "api_key": "25efc6c73b5b44428059e7dfc8348242",
    "font": "small",        # "mini", "small", or "large"
    "show_title": 1,        # 0 = hide title row
    "tz_offset": 1,         # UTC offset in hours (1 = Stockholm CET, 2 = CEST)
    # "map" mode (live aircraft positions over a basemap, FR24-style)
    "map_lat": 59.6519,     # center latitude
    "map_lon": 17.9186,     # center longitude
    "map_zoom": 8,          # Web Mercator zoom level (also sets the basemap's area)
    "map_radius_nm": 150,   # aircraft search radius, nautical miles
    "map_grayscale": 0,     # 1 = request a grayscale-quantized basemap from the proxy
    # OpenSky works anonymously, but only at a much lower rate limit. Setting
    # both of these enables OAuth2 client-credentials auth (see
    # _get_opensky_token()) for a higher limit; leave either blank to stay
    # anonymous.
    "opensky_client_id": "",
    "opensky_client_secret": "",
}

settings_pv = dict(DEFAULT_SETTINGS)

# Tells the web page (and the serial log) what happened to the settings on
# the last load/save, so "my choice wasn't remembered" is visible instead of
# silent.
settings_note = ""

# The map tiles are rendered by this server, which is always the same one.
MAP_PROXY_URL = "http://data.t-skylt.se:8099"

SETTINGS_TMP = SETTINGS_FILE + ".new"

def _fs_readonly():
    try:
        return storage.getmount("/").readonly
    except Exception:
        return False

def save_settings():
    """Persist settings_pv. Returns (ok, message).

    The data is written to a temporary file, read back and compared, and only
    then swapped over the real file, so a failed or interrupted write can never
    leave the real settings file empty (which used to silently reset the app
    to its defaults, i.e. departures mode, on the next start). If the board's
    filesystem is mounted read-only (USB drive mode: boot without the button
    held to get write access) nothing can be saved, and that is reported."""
    global settings_note
    if _fs_readonly():
        settings_note = "NOT SAVED: filesystem is read-only (USB drive mode). Reboot the MatrixBOX without holding the button."
        print("flights:", settings_note)
        return False, settings_note
    data = json.dumps(settings_pv)
    err = "unknown error"
    for attempt in range(2):
        try:
            with _blank_for_disk_write():
                with open(SETTINGS_TMP, "w") as f:
                    f.write(data)
                with open(SETTINGS_TMP) as f:
                    if f.read() != data:
                        raise OSError("read-back mismatch")
                try: os.remove(SETTINGS_FILE)
                except OSError: pass
                os.rename(SETTINGS_TMP, SETTINGS_FILE)
            settings_note = "Settings saved."
            return True, settings_note
        except Exception as e:
            err = type(e).__name__ + " " + str(e)
            print("flights save_settings error (attempt", attempt, "):", err)
    settings_note = "NOT SAVED: " + err
    return False, settings_note

def load_pv_settings():
    global settings_note
    saved = None
    why = ""
    # The .new file is only ever a complete, verified copy; it is left behind
    # only if power was lost between removing the old file and renaming it.
    for name in (SETTINGS_FILE, SETTINGS_TMP):
        try:
            with open(name) as f:
                saved = json.load(f)
            break
        except Exception as e:
            why = why or (name + ": " + type(e).__name__)
    if saved is not None:
        for k in DEFAULT_SETTINGS:
            if k in saved:
                settings_pv[k] = saved[k]
        settings_note = "Loaded saved settings."
    else:
        settings_note = "Using defaults (" + why + ")"
    print("flights:", settings_note, "mode =", settings_pv["mode"])
    # Heal values that older versions saved still URL-encoded
    for k in ("api_endpoint", "api_key", "airport"):
        settings_pv[k] = ampule.url_decoder(str(settings_pv.get(k, "")))

load_pv_settings()

# ── Display helpers ──────────────────────────────────────────────────────────
DISPLAY_WIDTH  = settings["width"]
DISPLAY_HEIGHT = settings["height"]

_FONT_MAP  = {"mini": font_mini, "small": font_small, "large": font_large}
_COLOR_MAP = {"white": 5, "yellow": 1, "red": 4, "green": 7, "black": 0, "orange": 11}
_MODE_LABEL = {"departures": "DEP", "arrivals": "ARR", "both": "D+A"}

def _cur_font():
    return _FONT_MAP.get(settings_pv.get("font", "small"), font_small)

def _row_height():
    """Pixel height of one row including any inter-row gap."""
    fh = _cur_font()["fontheight"]
    return fh + (1 if settings_pv.get("font") == "mini" else 0)

def _rows():
    return DISPLAY_HEIGHT // _row_height()

def _render_row(string, y_px, color="white", font=None):
    """Render text directly to window bitmap at pixel-Y y_px."""
    if font is None:
        font = _cur_font()
    fh  = font["fontheight"]
    c   = _COLOR_MAP.get(color, 5)
    px  = 0
    for ch in str(string):
        if ch not in font:
            if ch == " ":
                px += max(2, fh // 2)
            if px >= window.width:
                break
            continue
        glyph = font[ch]
        gw    = glyph[0]
        if isinstance(glyph[1], int):
            for w in range(gw):
                sx = px + w
                if sx >= window.width:
                    break
                inv_w = gw - w
                for h in range(fh):
                    sy = y_px + h
                    if sy < 0:
                        continue
                    if sy >= window.height:
                        break
                    if (glyph[h + 1] >> inv_w) & 1:
                        window[sx, sy] = c
        px += gw
        if px >= window.width:
            break

# Dedicated palette slots for the startup splash below -- distinct from the
# dimmed app palette (indices 0-12, see _ORIGINAL_PALETTE above) so the
# shimmer's brighter greys aren't fighting over the same entries. Must stay
# within 0-15: the shared `window` Bitmap was created with a value count of
# 16 (see load_screen.py), so pixel values of 16+ are out of range even
# though the Palette itself has 20 slots.
_SPLASH_BASE, _SPLASH_1, _SPLASH_2, _SPLASH_PEAK = 10, 13, 14, 15

def splash():
    """Startup splash: 'MATRIXBOX' (font_mini, orange) centered above
    'Flights' (font_large, dark grey) -- both centered horizontally, the
    pair centered as one block vertically. Flights' letters get a one-shot
    diagonal shimmer (a 5px-wide band of brighter greys) sweeping across
    them half a second later."""
    logo_text = "MATRIXBOX"
    flight_text = "Flights"
    mini_fh = font_mini["fontheight"]
    large_fh = font_large["fontheight"]
    gap = 2  # px between the two lines

    logo_w = strlen(logo_text, font_mini)
    flight_w = strlen(flight_text, font_large)
    y_top = (DISPLAY_HEIGHT - (mini_fh + gap + large_fh)) // 2
    logo_x, logo_y = (DISPLAY_WIDTH - logo_w) // 2, y_top
    flight_x, flight_y = (DISPLAY_WIDTH - flight_w) // 2, y_top + mini_fh + gap

    palette[_SPLASH_BASE] = (15, 15, 15)
    palette[_SPLASH_1]    = (35, 35, 35)
    palette[_SPLASH_2]    = (55, 55, 55)
    palette[_SPLASH_PEAK] = (80, 80, 80)

    window.fill(0)

    # "MATRIXBOX", orange, font_mini -- its keys are lowercase only (same
    # convention pprint() in lib/load_screen.py uses for this font).
    px = logo_x
    for ch in logo_text.lower():
        if ch not in font_mini:
            px += 3
            continue
        glyph = font_mini[ch]
        gw = glyph[0]
        for w in range(gw):
            sx = px + w
            inv_w = gw - w
            for h in range(mini_fh):
                if (glyph[h + 1] >> inv_w) & 1:
                    window[sx, logo_y + h] = _COLOR_MAP["orange"]
        px += gw

    # "Flights", dark grey, font_large -- pixel positions recorded so the
    # shimmer below only has to touch these, not scan the whole screen.
    pixels = []
    px = flight_x
    for ch in flight_text:
        if ch not in font_large:
            px += 6
            continue
        glyph = font_large[ch]
        gw = glyph[0]
        for w in range(gw):
            sx = px + w
            inv_w = gw - w
            for h in range(large_fh):
                if (glyph[h + 1] >> inv_w) & 1:
                    sy = flight_y + h
                    window[sx, sy] = _SPLASH_BASE
                    pixels.append((sx, sy))
        px += gw
    display.refresh()

    time.sleep(0.2)

    # The band is 5 shades wide (brightest in the middle, tapering at each
    # edge) and sweeps once along lines of constant (x - y) -- a diagonal
    # line of pixels all at the same x-y value lights up together, and
    # incrementing `center` moves that diagonal line left-to-right across
    # the text, like a reflection of light passing over the letters.
    shades = (_SPLASH_1, _SPLASH_2, _SPLASH_PEAK, _SPLASH_2, _SPLASH_1)
    half = len(shades) // 2
    diag = [x - y for x, y in pixels]
    d_min, d_max = min(diag), max(diag)
    for center in range(d_min - half, d_max + half + 1):
        for (x, y), d in zip(pixels, diag):
            offset = d - center
            window[x, y] = shades[offset + half] if -half <= offset <= half else _SPLASH_BASE
        display.refresh()
        time.sleep(0.03)

    # The loop above only resets a pixel once the band has swept all the way
    # past it -- for the pixels at the trailing edge (d == d_max) that only
    # happens on the very last iteration, which *lights* them one final
    # time rather than clearing them, leaving a couple of stray bright
    # pixels after the sweep "finishes". Force every pixel back to the base
    # grey explicitly so the end state is always clean.
    for x, y in pixels:
        window[x, y] = _SPLASH_BASE
    display.refresh()


# ── Flight data ──────────────────────────────────────────────────────────────
# IATA → short city name (used when font is mini for wider columns)
_CITY = {
    "ARN":"Stockholm", "CPH":"Copenhagen", "OSL":"Oslo",     "HEL":"Helsinki",
    "LHR":"London",    "LGW":"Gatwick",    "STN":"Stansted",  "MAN":"Manchester",
    "CDG":"Paris",     "ORY":"Paris-Orly",  "AMS":"Amsterdam","BRU":"Brussels",
    "FRA":"Frankfurt", "MUC":"Munich",      "DUS":"Dusseldorf","HAM":"Hamburg",
    "MAD":"Madrid",    "BCN":"Barcelona",   "LIS":"Lisbon",   "OPO":"Porto",
    "FCO":"Rome",      "MXP":"Milan",       "VCE":"Venice",   "NAP":"Naples",
    "ATH":"Athens",    "IST":"Istanbul",    "DXB":"Dubai",    "DOH":"Doha",
    "JFK":"New York",  "EWR":"Newark",      "BOS":"Boston",   "ORD":"Chicago",
    "LAX":"Los Angeles","SFO":"San Francisco","YYZ":"Toronto","YVR":"Vancouver",
    "NRT":"Tokyo",     "HND":"Tokyo-Haneda","ICN":"Seoul",    "PEK":"Beijing",
    "PVG":"Shanghai",  "SIN":"Singapore",   "BKK":"Bangkok",  "KUL":"Kuala Lumpur",
    "SYD":"Sydney",    "MEL":"Melbourne",   "DEN":"Denver",   "MIA":"Miami",
    "GVA":"Geneva",    "ZRH":"Zurich",      "VIE":"Vienna",   "PRG":"Prague",
    "WAW":"Warsaw",    "BUD":"Budapest",    "BEG":"Belgrade", "SOF":"Sofia",
    "OTP":"Bucharest", "KBP":"Kyiv",        "LED":"St Petersburg","SVO":"Moscow",
    "TXL":"Berlin",    "BER":"Berlin",      "CGN":"Cologne",  "STR":"Stuttgart",
    "PMI":"Mallorca",  "AGP":"Malaga",      "ALC":"Alicante", "TFS":"Tenerife",
    "LPA":"Gran Canaria","HER":"Heraklion",  "RHO":"Rhodes",  "CFU":"Corfu",
    "SKG":"Thessaloniki","JMK":"Mykonos",   "JSI":"Skiathos", "KGS":"Kos",
    "RIX":"Riga",      "TLL":"Tallinn",     "VNO":"Vilnius",  "GDN":"Gdansk",
}
flights = []          # list of dicts: {flight, dest_or_origin, time, status}
last_fetch = 0
fetch_error = ""

# ── Map mode state (live aircraft over a basemap) ─────────────────────────────

planes = []            # list of dicts: {lat, lon, track, flight, velocity}
last_planes_fetch = 0
planes_error = ""
basemap_error = ""
# Raw OpenSky result count + the bbox used, kept purely for the web status
# line -- distinguishes "fetch worked but genuinely zero aircraft in this
# (possibly tiny, at high zoom) view" from a real fetch failure, which
# otherwise look identical from the LED matrix alone.
last_planes_raw_count = None
last_planes_bbox = None
# OpenSky's "X-Rate-Limit-Remaining" (credits left in the current bucket) and
# "X-Rate-Limit-Retry-After-Seconds" (only present once exhausted, on a 429)
# response headers -- sent on every /states/all response, anonymous or
# authenticated -- surfaced on the web status line so the API key's actual
# benefit (or an anonymous quota running low) is visible rather than only
# showing up later as a sudden string of fetch failures.
last_opensky_rate_remaining = None
last_opensky_rate_retry_after = None
# Timestamp of the most recent successful fetch_planes() call, used to
# dead-reckon each aircraft's CURRENT position between fetches (see
# _extrapolate_position()) -- lets the display reposition planes every
# ~1s (see the main loop) without needing to re-poll OpenSky that often.
_planes_fetched_at = 0.0
# (lat, lon, zoom) the current `planes` list was fetched for, rounded the
# same way _viewport_key() does. Lets _update_plane_sprites() detect "the
# view changed since the last successful fetch" and hide stale aircraft
# instead of mis-projecting them against the new center (see that
# function's docstring for why this matters).
_planes_viewport_key = None

def _viewport_key():
    return (round(settings_pv.get("map_lat", 0), 4),
            round(settings_pv.get("map_lon", 0), 4),
            settings_pv.get("map_zoom", 8))

# ── API fetch (Swedavia FlightInfo v2) ────────────────────────────────────────
# Clock sync from HTTP Date response headers (device RTC may be unset/wrong)
_utc_epoch = 0      # UTC seconds at last sync (0 = not synced yet)
_utc_mono  = 0.0    # time.monotonic() at last sync

_MONTHS = {"Jan":1,"Feb":2,"Mar":3,"Apr":4,"May":5,"Jun":6,
           "Jul":7,"Aug":8,"Sep":9,"Oct":10,"Nov":11,"Dec":12}

def _sync_time(date_hdr):
    """Sync the clock from an HTTP Date header:
    'Thu, 06 Nov 2026 22:29:33 GMT'. Returns True on success."""
    global _utc_epoch, _utc_mono
    try:
        p = date_hdr.split()
        hh, mi, ss = [int(x) for x in p[4].split(":")]
        _utc_epoch = time.mktime(
            (int(p[3]), _MONTHS[p[2]], int(p[1]), hh, mi, ss, 0, 0, 0))
        _utc_mono  = time.monotonic()
        return True
    except:
        return False

def _local_epoch():
    """Local time in epoch seconds, from the HTTP-synced clock when
    available, otherwise the device RTC. tz_offset is applied."""
    off = settings_pv.get("tz_offset", 0) * 3600
    if _utc_epoch:
        return _utc_epoch + off + int(time.monotonic() - _utc_mono)
    return time.mktime(time.localtime()) + off

def _local_now():
    """Local time tuple (see _local_epoch)."""
    return time.localtime(_local_epoch())

def _date_str(t):
    return "{:04d}-{:02d}-{:02d}".format(t[0], t[1], t[2])

def _now_hhmm():
    """Current local time as HH:MM."""
    try:
        t = _local_now()
        return "{:02d}:{:02d}".format(t[3], t[4])
    except:
        return ""

def _filter_future(raw, now_hhmm):
    """Keep only flights at or after now_hhmm (HH:MM string comparison)."""
    if not now_hhmm:
        return raw
    result = []
    for f in raw:
        if f["time"] >= now_hhmm:
            result.append(f)
    return result

def _utc_to_local_hhmm(t_val):
    """Convert an ISO UTC timestamp ('2026-11-06T12:20:00Z') to local HH:MM."""
    try:
        h = (int(t_val[11:13]) + settings_pv.get("tz_offset", 0)) % 24
        return "{:02d}:".format(h) + t_val[14:16]
    except:
        return "??:??"

def _base_endpoint():
    """Return the API base URL, stripping any /{airport}/{mode}/{date} suffix
    left over from older saved settings."""
    base = settings_pv.get("api_endpoint", "").rstrip("/")
    for m in ("/arrivals/", "/departures/"):
        if m in base:
            base = base.split(m)[0].rsplit("/", 1)[0]
    return base

# A fresh socketpool.SocketPool + TLS context + adafruit_requests.Session on
# every single fetch call is a known memory-fragmentation trap on
# constrained chips like the ESP32-S2 (each allocates real C-level socket
# resources that don't get reused). With three fetch functions now sharing
# the same network stack (fetch_flights, fetch_basemap, fetch_planes), that
# pattern reliably exhausts available RAM. Build the session once and reuse
# it everywhere instead.
#
# The underlying socketpool.SocketPool is created ONCE and kept in `_pool`,
# separately from `_session`. This matters: adafruit_requests/
# adafruit_connection_manager cache one ConnectionManager (which tracks
# which real OS sockets are open/free) PER SocketPool object -- keyed by
# object identity, not by e.g. wifi.radio. An earlier version of
# _get_session() called socketpool.SocketPool(wifi.radio) again every time
# _invalidate_session() had cleared `_session`, creating a BRAND NEW
# SocketPool object (and therefore a brand new, separate ConnectionManager)
# each time, while the PREVIOUS ConnectionManager -- and whatever real
# sockets it still had open -- was simply abandoned with no way to close
# it, since nothing kept a reference to the old pool anymore. Each
# exception-triggered reconnect was silently leaking however many sockets
# the old session still held, which (confirmed against
# lib/adafruit_connection_manager.py's actual socket-tracking/closing
# logic) matches "out of sockets" errors appearing over time. Reusing the
# same `_pool` object on every reconnect keeps resolving to the SAME
# ConnectionManager, so its socket bookkeeping stays correct and complete
# across reconnects instead of fragmenting into orphaned, un-closeable
# pools.
_pool = None
_session = None

def _get_session():
    global _pool, _session
    if _pool is None:
        import socketpool
        _pool = socketpool.SocketPool(wifi.radio)
    if _session is None:
        import ssl
        import adafruit_requests as requests_lib
        _session = requests_lib.Session(_pool, ssl.create_default_context())
    return _session

def _invalidate_session():
    """Force the next _get_session() call to build a brand new Session
    (reusing the existing `_pool`, never creating a new one -- see above).

    Call this whenever a request raises -- adafruit_requests.Session can be
    left in a half-read or otherwise corrupted state by a failed/aborted
    request (e.g. a timeout mid-response, or a server closing the
    connection unexpectedly), and a corrupted Session can then silently
    fail on every subsequent call forever. That exactly matches "aircraft
    positions never update again after some point": if fetch_planes() once
    throws, the shared session could get stuck, and since 'planes' is only
    overwritten on a *successful* fetch, the last good positions would
    stay frozen on screen with no further errors visible except via the
    status line. Discarding the session on any exception is cheap insurance
    against that failure mode.

    Also force-closes any sockets the connection manager still considers
    open for `_pool` (even ones not yet marked "available"/idle) as a
    safety net: whatever went wrong may have left a socket connected but
    neither closed nor freed, which would otherwise sit there as a real,
    permanently leaked OS socket."""
    global _session
    _session = None
    if _pool is not None:
        try:
            import adafruit_connection_manager
            adafruit_connection_manager.connection_manager_close_all(_pool)
        except Exception as e:
            print("flights socket cleanup error:", type(e).__name__, e)

def _release_sockets():
    """Close every outbound socket this app's pool holds. Called after each
    fetch (success or failure).

    adafruit_connection_manager deliberately keeps a finished connection
    open ("keep-alive") so the next request to the same host can reuse it.
    This app talks to up to three different hosts (OpenSky over TLS, the
    basemap proxy, Swedavia over TLS), and the ESP32-S2 only has a handful
    of sockets in total -- shared with the web server's listening socket and
    the browser connection currently being served. A few lingering
    keep-alive sockets are enough to make the next connect fail with
    "Out of sockets". Fetches here are infrequent (tens of seconds apart),
    so reconnecting each time costs little, and it guarantees nothing
    lingers between fetches."""
    if _pool is None:
        return
    try:
        import adafruit_connection_manager
        adafruit_connection_manager.connection_manager_close_all(_pool)
    except Exception:
        pass
    gc.collect()

# ── Map mode (live aircraft over a basemap) ───────────────────────────────────
# The basemap (coastlines/roads around map_lat/map_lon) rarely changes -- it's
# only re-fetched from the conversion proxy when location/zoom/size change.
# Aircraft positions change every refresh and are plotted with simple Web
# Mercator math, so they never require a new map image.
#
# The basemap lives in RAM only -- it is never written to flash. The
# downloaded BMP is small (~5KB at 128x32, ~17KB at 128x128) and is only
# needed to (re)paint the `window` bitmap, so a disk round-trip bought
# nothing: the "do I already have this map" check below was already
# RAM-only (it resets every boot), which means the file was never reused
# after a restart anyway. Skipping the write also removes a display
# blank-out and a flash write on every map change, plus the corruption and
# free-space problems this device's flash has had.
_basemap_cache_key = None
_basemap_data = None   # the downloaded BMP bytes for _basemap_cache_key
# Set True whenever fetch_basemap() actually downloads new data (vs. a
# cache hit) -- tells render_map() a background redraw is actually needed.
# See render_map()'s docstring for the full rationale.
_basemap_dirty = True
_basemap_next_try = 0  # time.monotonic() before which a failed fetch isn't retried

def _basemap_key():
    return [round(settings_pv.get("map_lat", 0), 4),
            round(settings_pv.get("map_lon", 0), 4),
            settings_pv.get("map_zoom", 8),
            DISPLAY_WIDTH, DISPLAY_HEIGHT,
            settings_pv.get("map_grayscale", 0)]

def fetch_basemap(force=False):
    """Download a freshly rendered, palette-quantized basemap bitmap from the
    conversion proxy -- but only when location/zoom/size actually changed (or
    force=True), since the proxy call and image transfer are comparatively
    expensive and the backdrop is static between settings changes."""
    global basemap_error, _basemap_cache_key, _basemap_dirty, _basemap_next_try
    global _basemap_data
    proxy = MAP_PROXY_URL

    key = _basemap_key()
    if not force and _basemap_data is not None and _basemap_cache_key == key:
        return True  # already have the right basemap in RAM
    if not force and time.monotonic() < _basemap_next_try:
        return False  # recently failed; don't hammer the proxy every tick
    _basemap_next_try = 0

    r = None
    try:
        session = _get_session()
        url = "{}/basemap?lat={}&lon={}&zoom={}&w={}&h={}&grayscale={}".format(
            proxy, key[0], key[1], key[2], key[3], key[4], int(key[5]))
        r = session.get(url, timeout=20)
        if r.status_code != 200:
            basemap_error = "HTTP " + str(r.status_code)
            _basemap_next_try = time.monotonic() + 10
            return False
        data = r.content
        r.close()
        r = None
        if data[0:2] != b"BM":
            raise ValueError("proxy did not return a BMP")
        _basemap_data = data
        _basemap_cache_key = key
        _basemap_dirty = True  # new data -- render_map() must redraw the background
        basemap_error = ""
        return True
    except Exception as e:
        basemap_error = str(e)
        _basemap_next_try = time.monotonic() + 10
        _invalidate_session()
        print("flights basemap fetch error:", type(e).__name__, e)
        return False
    finally:
        # Runs on every path (including the early HTTP-error return): an
        # unclosed response keeps its socket permanently "in use", which is
        # what eventually shows up as "Out of sockets".
        if r is not None:
            try: r.close()
            except Exception: pass
        _release_sockets()

# ── OpenSky OAuth2 (optional) ─────────────────────────────────────────────────
# OpenSky's anonymous access works fine but is rate-limited; configuring a
# client_id/client_secret (from an OpenSky account's "API client", see the
# "Live map" settings) raises that limit considerably. OpenSky exclusively
# uses the OAuth2 client-credentials flow -- see
# https://openskynetwork.github.io/opensky-api/rest.html#authentication --
# so credentials must first be exchanged for a short-lived bearer token
# rather than being sent directly on every states/all request.
OPENSKY_TOKEN_URL = ("https://auth.opensky-network.org/auth/realms/"
                      "opensky-network/protocol/openid-connect/token")
# Tokens are valid for 30 minutes; refresh a bit early so an in-flight
# states/all request never races an about-to-expire token.
_OPENSKY_TOKEN_MARGIN_S = 60

_opensky_token = None
_opensky_token_expiry = 0.0  # time.monotonic() after which _opensky_token is stale
_opensky_auth_error = ""     # "" while unconfigured or last auth succeeded

def _url_form_encode(s):
    """Percent-encode a string for use as an application/x-www-form-urlencoded
    value. adafruit_requests only auto-encodes `data=dict(...)`, which just
    concatenates values with no escaping -- not safe here since OAuth2
    client secrets can contain '+', '/', '=' etc. that would otherwise
    corrupt the POST body."""
    out = []
    for ch in str(s):
        if ch.isalpha() or ch.isdigit() or ch in "-_.~":
            out.append(ch)
        elif ch == " ":
            out.append("+")
        else:
            for b in ch.encode("utf-8"):
                out.append("%{:02X}".format(b))
    return "".join(out)

def _opensky_invalidate_token():
    global _opensky_token, _opensky_token_expiry
    _opensky_token = None
    _opensky_token_expiry = 0.0

def _get_opensky_token():
    """Return a cached/fresh OpenSky OAuth2 bearer token for the configured
    opensky_client_id/opensky_client_secret, or None if no credentials are
    configured or the token request failed. Callers should treat None as
    "fall back to an anonymous request" rather than a hard failure."""
    global _opensky_token, _opensky_token_expiry, _opensky_auth_error
    client_id     = settings_pv.get("opensky_client_id", "").strip()
    client_secret = settings_pv.get("opensky_client_secret", "").strip()
    if not client_id or not client_secret:
        _opensky_invalidate_token()
        _opensky_auth_error = ""
        return None
    now = time.monotonic()
    if _opensky_token and now < _opensky_token_expiry:
        return _opensky_token
    r = None
    try:
        session = _get_session()
        body = "grant_type=client_credentials&client_id={}&client_secret={}".format(
            _url_form_encode(client_id), _url_form_encode(client_secret))
        r = session.post(OPENSKY_TOKEN_URL, data=body,
                          headers={"Content-Type": "application/x-www-form-urlencoded"},
                          timeout=15)
        if r.status_code != 200:
            _opensky_auth_error = "auth HTTP " + str(r.status_code)
            _opensky_invalidate_token()
            return None
        resp = r.json()
        r.close()
        r = None
        token = resp.get("access_token")
        if not token:
            _opensky_auth_error = "auth: no access_token in response"
            _opensky_invalidate_token()
            return None
        expires_in = resp.get("expires_in") or 1800
        _opensky_token = token
        _opensky_token_expiry = now + max(10, int(expires_in) - _OPENSKY_TOKEN_MARGIN_S)
        _opensky_auth_error = ""
        return token
    except Exception as e:
        _opensky_auth_error = "auth: " + type(e).__name__ + " " + str(e)
        _opensky_invalidate_token()
        _invalidate_session()
        print("flights OpenSky auth error:", type(e).__name__, e)
        return None
    finally:
        if r is not None:
            try: r.close()
            except Exception: pass
        _release_sockets()

def fetch_planes():
    """Query OpenSky Network's bounding-box API for aircraft within the
    visible map viewport (see _viewport_bbox). Uses an OAuth2 bearer token
    (see _get_opensky_token()) when opensky_client_id/opensky_client_secret
    are configured, for a higher rate limit; otherwise falls back to
    OpenSky's anonymous access. (airplanes.live/adsb.one now require prior
    registration/API access and reject anonymous requests with a 403 or a
    "please contact us" error -- OpenSky's public REST API genuinely works
    anonymously, at reduced but perfectly adequate resolution for this
    refresh cadence.)"""
    global planes, planes_error, last_planes_fetch, last_planes_raw_count
    global last_planes_bbox, _planes_fetched_at, _planes_viewport_key
    global last_opensky_rate_remaining, last_opensky_rate_retry_after
    r = None
    ok = False
    try:
        session = _get_session()
        lamin, lomin, lamax, lomax = _viewport_bbox()
        last_planes_bbox = (round(lamin, 3), round(lomin, 3), round(lamax, 3), round(lomax, 3))
        url = "https://opensky-network.org/api/states/all?lamin={}&lomin={}&lamax={}&lomax={}".format(
            lamin, lomin, lamax, lomax)
        token = _get_opensky_token()
        headers = {"Authorization": "Bearer " + token} if token else {}
        r = session.get(url, headers=headers, timeout=15)
        if r.status_code == 401 and token:
            # The cached token was rejected (e.g. expired early, or revoked
            # server-side) -- discard it and retry exactly once with a
            # freshly minted one before falling back to an error.
            r.close()
            r = None
            _opensky_invalidate_token()
            token = _get_opensky_token()
            r = session.get(url, headers={"Authorization": "Bearer " + token} if token else {},
                             timeout=15)
        # Present on every /states/all response (success, 401, or 429),
        # anonymous or authenticated -- read it before any branch below
        # closes/replaces `r`.
        rl = r.headers.get("x-rate-limit-remaining")
        last_opensky_rate_remaining = int(rl) if rl is not None and rl.lstrip("-").isdigit() else None
        ra = r.headers.get("x-rate-limit-retry-after-seconds")
        last_opensky_rate_retry_after = int(ra) if ra is not None and ra.lstrip("-").isdigit() else None
        if r.status_code == 200:
            data = r.json()
            r.close()
            r = None
            states = data.get("states") or []
            last_planes_raw_count = len(states)
            out = []
            # Each state vector: [icao24, callsign, origin_country,
            # time_position, last_contact, longitude, latitude,
            # baro_altitude, on_ground, velocity, true_track, ...]
            for sv in states:
                try:
                    sv_lon, sv_lat, sv_track = sv[5], sv[6], sv[10]
                    if sv_lat is None or sv_lon is None:
                        continue
                    out.append({
                        "lat":      float(sv_lat),
                        "lon":      float(sv_lon),
                        "track":    float(sv_track or 0),
                        "velocity": float(sv[9] or 0),  # ground speed, m/s
                        "flight":   str(sv[1] or "").strip(),
                    })
                except:
                    continue
            planes = out
            planes_error = ""
            # These two must update together, atomically with `planes`
            # itself -- see _update_plane_sprites()'s staleness check.
            _planes_fetched_at = time.monotonic()
            _planes_viewport_key = _viewport_key()
            ok = True
        else:
            planes_error = "HTTP " + str(r.status_code)
            if r.status_code == 429 and last_opensky_rate_retry_after is not None:
                planes_error += " (retry after {}s)".format(last_opensky_rate_retry_after)
            last_planes_raw_count = None
    except Exception as e:
        planes_error = str(e)
        last_planes_raw_count = None
        _invalidate_session()
        print("flights planes fetch error:", type(e).__name__, e)
    finally:
        if r is not None:
            try: r.close()
            except Exception: pass
        _release_sockets()
    now = time.monotonic()
    if ok:
        last_planes_fetch = now
    else:
        # Retry in ~5s rather than waiting out the whole refresh interval:
        # while the view has changed and no fetch has succeeded yet, the
        # stale-view guard keeps every aircraft hidden, so a single failed
        # attempt would otherwise leave the map empty for a full minute.
        last_planes_fetch = now - settings_pv["refresh"] + 5

_EARTH_RADIUS_M = 6371000.0

def _extrapolate_position(p, elapsed_s):
    """Dead-reckon this aircraft's estimated CURRENT lat/lon, `elapsed_s`
    seconds after it was last fetched, from its last known
    lat/lon/track/groundspeed. OpenSky is only polled on the slower
    settings_pv["refresh"] cadence (to stay within its free/anonymous
    usage), but the main loop calls this every ~1s so aircraft still
    visibly move in between real data fetches, using simple flat-earth
    dead reckoning (perfectly adequate over the few tens of seconds
    between fetches -- no need for great-circle math at this precision)."""
    velocity = p.get("velocity") or 0.0
    if velocity <= 0 or elapsed_s <= 0:
        return p["lat"], p["lon"]
    dist_m = velocity * elapsed_s
    track_rad = math.radians(p["track"])
    dlat = (dist_m * math.cos(track_rad)) / _EARTH_RADIUS_M
    lat_rad = math.radians(p["lat"])
    dlon = (dist_m * math.sin(track_rad)) / (_EARTH_RADIUS_M * max(0.01, math.cos(lat_rad)))
    return p["lat"] + math.degrees(dlat), p["lon"] + math.degrees(dlon)

def _merc_xy(lat, lon, zoom):
    """Web Mercator pixel coordinates at the given zoom (256px tiles)."""
    lat = max(min(lat, 85.05112878), -85.05112878)
    n = 256 * (2 ** zoom)
    x = (lon + 180.0) / 360.0 * n
    sin_lat = math.sin(math.radians(lat))
    y = (0.5 - math.log((1 + sin_lat) / (1 - sin_lat)) / (4 * math.pi)) * n
    return x, y

def _project(lat, lon):
    """Pixel offset of (lat, lon) in the on-screen map viewport, relative to
    the configured center and zoom. Works for any user-chosen location --
    the basemap image and this projection always share the same center/zoom.

    Uses DISPLAY_WIDTH/DISPLAY_HEIGHT (the real panel dimensions from
    settings), NOT window.width/window.height -- window is a padded SQUARE
    safety buffer sized to fit any rotation (see _max_dim in
    lib/load_screen.py), which is larger than the real visible area on any
    non-square panel (e.g. 128x32 or 128x64). Centering on window's
    dimensions instead of the real display size was the cause of the
    basemap/aircraft appearing vertically offset -- the computed "center"
    landed well below the panel's actual visible rows."""
    zoom = settings_pv.get("map_zoom", 8)
    cx, cy = _merc_xy(settings_pv.get("map_lat", 0), settings_pv.get("map_lon", 0), zoom)
    px, py = _merc_xy(lat, lon, zoom)
    return int(px - cx + DISPLAY_WIDTH / 2), int(py - cy + DISPLAY_HEIGHT / 2)

def _merc_to_latlon(x, y, zoom):
    """Inverse of _merc_xy: pixel coordinates -> (lat, lon)."""
    n = 256 * (2 ** zoom)
    lon = x / n * 360.0 - 180.0
    # atan(sinh(z)) via atan/exp (the Gudermannian identity) -- avoids
    # relying on math.sinh, which isn't confirmed present on every
    # CircuitPython build, unlike atan/exp which are universally available.
    z = math.pi * (1 - 2 * y / n)
    lat_rad = 2 * math.atan(math.exp(z)) - math.pi / 2
    return math.degrees(lat_rad), lon

def _viewport_bbox(pad=1.3):
    """Lat/lon bounding box of what's actually visible on screen (plus a
    little padding so aircraft near the edge are fetched before they slide
    into view). Deriving the aircraft search area from the *visible*
    viewport -- rather than from map_radius_nm alone -- matters: at typical
    zoom levels the screen only shows a small fraction of a map_radius_nm
    circle (e.g. zoom 8 on a 128x64 panel shows ~40 x 20nm, far smaller
    than a 150nm search radius), so without this, fetched aircraft almost
    always land outside the drawable area and never appear. map_radius_nm
    is still applied as a safety cap, mainly relevant at very low zoom
    levels where the visible area would otherwise be huge.

    Uses DISPLAY_WIDTH/DISPLAY_HEIGHT -- see _project()'s docstring for why
    window.width/window.height would be wrong here on non-square panels."""
    zoom = settings_pv.get("map_zoom", 8)
    lat0 = settings_pv.get("map_lat", 0)
    lon0 = settings_pv.get("map_lon", 0)
    cx, cy = _merc_xy(lat0, lon0, zoom)
    half_w = DISPLAY_WIDTH / 2 * pad
    half_h = DISPLAY_HEIGHT / 2 * pad
    lat1, lon1 = _merc_to_latlon(cx - half_w, cy - half_h, zoom)
    lat2, lon2 = _merc_to_latlon(cx + half_w, cy + half_h, zoom)
    lamin, lamax = min(lat1, lat2), max(lat1, lat2)
    lomin, lomax = min(lon1, lon2), max(lon1, lon2)
    max_deg = settings_pv.get("map_radius_nm", 150) / 60.0
    lamin = max(lamin, lat0 - max_deg)
    lamax = min(lamax, lat0 + max_deg)
    lomin = max(lomin, lon0 - max_deg)
    lomax = min(lomax, lon0 + max_deg)
    return lamin, lomin, lamax, lomax

def _draw_basemap():
    """Copy the in-RAM basemap bitmap (_basemap_data) into the window
    framebuffer.

    Deliberately does NOT use displayio.OnDiskBitmap: on this firmware build
    it doesn't support __getitem__ (pixel read), and bitmaptools.blit isn't
    available either, so there's no supported way to get pixel data out of
    it. Instead, parse the (proxy-controlled, always uncompressed 8-bit
    indexed) BMP directly -- see mapproxy/server.py, which always writes
    this exact format -- and copy index values straight into window[x,y].
    The basemap's palette indices are pre-quantized by the proxy to match
    this device's own palette (see load_screen.py), so a raw index copy
    is enough; no color conversion needed here.

    Only called when the basemap is new (fetch_basemap() actually
    downloaded something) or the status overlay text needs to change -- see
    render_map(). Aircraft are NOT drawn into this bitmap at all; they're
    separate displayio.TileGrid sprites layered on top (see
    _update_plane_sprites()), so moving a plane never requires touching
    this bitmap or redrawing the background.
    """
    try:
        data = _basemap_data
        if data is None or data[0:2] != b"BM":
            raise ValueError("no basemap in memory")
        data_start = struct.unpack_from("<I", data, 10)[0]
        width      = struct.unpack_from("<i", data, 18)[0]
        height_raw = struct.unpack_from("<i", data, 22)[0]
        bpp        = struct.unpack_from("<H", data, 28)[0]
        compression = struct.unpack_from("<I", data, 30)[0]
        if bpp != 8 or compression != 0:
            raise ValueError("expected uncompressed 8-bit indexed BMP")
        top_down = height_raw < 0
        height = abs(height_raw)
        row_stride = (width + 3) & ~3  # rows padded to a 4-byte boundary
        # DISPLAY_WIDTH/HEIGHT, not window.width/height -- window is a
        # padded square safety buffer, larger than the real visible area
        # on non-square panels (see _project()'s docstring).
        w = min(width, DISPLAY_WIDTH)
        h = min(height, DISPLAY_HEIGHT)
        for row in range(h):
            file_row = row if top_down else (height - 1 - row)
            base = data_start + file_row * row_stride
            for x in range(w):
                window[x, row] = data[base + x]
    except Exception as e:
        print("flights basemap draw error:", type(e).__name__, e)
        window.fill(0)
        return False
    return True


# ── Aircraft sprites (TileGrid overlay, not drawn into `window`) ─────────────
# Planes move every refresh but the basemap underneath them does not (see
# fetch_basemap()'s cache). Previously each aircraft was plotted as a raw
# pixel directly into the shared `window` bitmap, which meant the ENTIRE
# background had to be redrawn from the BMP on every single refresh just to
# erase the old plane positions before drawing the new ones -- wasteful,
# and increasingly so as refresh rate goes up.
#
# displayio's compositing model has a purpose-built answer for exactly this
# ("move a small image over a background without redrawing it"): a
# displayio.TileGrid with a transparent palette index. Moving a plane is
# just changing that TileGrid's .x/.y -- displayio handles compositing it
# over whatever is underneath without the app ever touching `window`'s
# pixels. A small, fixed pool of TileGrids is created once and reused
# across refreshes (hidden when not needed) rather than creating/destroying
# TileGrids per frame, which would churn memory on this very constrained
# device.
#
# At this resolution, a literal airplane silhouette (as FR24 uses) still
# isn't fully resolvable, but a recognizable schematic top-down plane
# shape is -- a long fuselage, wide wings crossing it, and a smaller tail
# crossbar near the back -- closer to a real plane's silhouette than a
# solid dart/arrowhead (an earlier version used a filled triangle, which
# read as a plain directional arrow rather than a plane; a filled
# cross/wings shape was found to look much more like an actual aircraft).
    # Pixel-art patterns, like the font glyphs: N and NE are drawn by hand
    # ('#' = lit) and the other six are 90-degree rotations of those two.
    # They are expanded once into one wide spritesheet bitmap; a TileGrid
    # shows one of them by tile index.
_PLANE_ICON_SIZE = 11
_PLANE_ICON_DIRS = 8   # N, NE, E, SE, S, SW, W, NW (45-degree compass buckets)
_PLANE_SLOTS = 16       # reusable TileGrid pool size -- plenty for this panel size

# Row-major 11x11 bit patterns (1 = lit pixel), one per compass direction,
# in N,NE,E,SE,S,SW,W,NW order matching bucket = round(track/45) % 8.
_PLANE_N = (
    "...........",
    ".....#.....",
    ".....#.....",
    "....###....",
    "..#######..",
    ".#...#...#.",
    ".....#.....",
    ".....#.....",
    ".....#.....",
    "....#.#....",
    "...........",
)
_PLANE_NE = (
    "...........",
    ".........#.",
    ".##.....#..",
    "...#.#.#...",
    "....###....",
    ".....###...",
    "....#.#....",
    "..##...#...",
    "...#....#..",
    "........#..",
    "...........",
)

def _rot90(rows):
    """Rotate a square pattern 90 degrees clockwise."""
    n = len(rows)
    return tuple("".join(rows[n - 1 - x][y] for x in range(n)) for y in range(n))

def _plane_patterns():
    """N, NE, E, SE, S, SW, W, NW, all derived from the two drawn above."""
    out = []
    n, ne = _PLANE_N, _PLANE_NE
    for _ in range(4):
        out.append(n)
        out.append(ne)
        n, ne = _rot90(n), _rot90(ne)
    return out

_plane_bitmap = None
_plane_tilegrids = []

def _remove_plane_layer():
    """Remove every sprite from tile_groupgroup, keeping only the shared
    background tile_group (index 0). tile_groupgroup outlives this app, so
    sprites left in it would stay visible over the main menu."""
    global _plane_bitmap
    while len(tile_groupgroup) > 1:
        tile_groupgroup.pop()
    _plane_tilegrids.clear()
    _plane_bitmap = None

def _init_plane_sprites():
    """Build the aircraft spritesheet bitmap/palette and the reusable
    TileGrid pool, once. Safe to call multiple times (no-ops after the
    first). Appends the TileGrids to `tile_groupgroup` (the same Group that
    already holds the background `tile_group`, see lib/load_screen.py) so
    they render on top of whatever basemap is currently in `window`."""
    global _plane_bitmap, _plane_tilegrids
    if _plane_bitmap is not None:
        return
    _remove_plane_layer()  # drop sprites left behind by an earlier run that crashed
    _plane_bitmap = displayio.Bitmap(_PLANE_ICON_SIZE * _PLANE_ICON_DIRS, _PLANE_ICON_SIZE, 2)
    for d, pattern in enumerate(_plane_patterns()):
        x0 = d * _PLANE_ICON_SIZE
        for y, row in enumerate(pattern):
            for x, ch in enumerate(row):
                if ch == "#":
                    _plane_bitmap[x0 + x, y] = 1
    plane_palette = displayio.Palette(2)
    plane_palette[0] = 0x000000
    plane_palette.make_transparent(0)
    # Darker orange, like the plane drawn for this app, at this app's dimmed
    # brightness. This sprite has its OWN local Palette, not the shared one.
    plane_palette[1] = (80,20,0)
    palette[5] = (10,10,10)
    for _ in range(_PLANE_SLOTS):
        tg = displayio.TileGrid(
            _plane_bitmap, pixel_shader=plane_palette,
            tile_width=_PLANE_ICON_SIZE, tile_height=_PLANE_ICON_SIZE)
        tg.hidden = True
        tile_groupgroup.append(tg)
        _plane_tilegrids.append(tg)

def _update_plane_sprites():
    """Position/orient/show exactly len(planes) of the reusable sprite
    TileGrids (hiding any unused slots), without touching `window` at all.

    Called every ~1s by the main loop (far more often than fetch_planes()
    itself), using _extrapolate_position() to dead-reckon each aircraft's
    position between real data fetches -- this is what makes positions
    visibly update at least once a second without hammering OpenSky.

    If the current map view (_viewport_key()) doesn't match the view
    `planes` was actually fetched for (_planes_viewport_key), every sprite
    is hidden instead of shown: without this, moving/zooming the map (or a
    fetch_planes() call failing right after such a change) would otherwise
    re-project stale aircraft -- real for the OLD view -- against the NEW
    center, scattering them to wrong or off-screen positions and making it
    look like aircraft had simply vanished or glitched rather than that a
    fresh fetch for the new view just hasn't completed yet."""
    _init_plane_sprites()
    stale = _planes_viewport_key is None or _planes_viewport_key != _viewport_key()
    n = 0 if stale else min(len(planes), _PLANE_SLOTS)
    elapsed = time.monotonic() - _planes_fetched_at
    for i in range(_PLANE_SLOTS):
        tg = _plane_tilegrids[i]
        if i < n:
            p = planes[i]
            lat, lon = _extrapolate_position(p, elapsed)
            x, y = _project(lat, lon)
            tg.x = x - _PLANE_ICON_SIZE // 2
            tg.y = y - _PLANE_ICON_SIZE // 2
            bucket = int(round((p["track"] % 360) / 45.0)) % _PLANE_ICON_DIRS
            tg[0] = bucket
            tg.hidden = False
        else:
            tg.hidden = True

# Tracks the last overlay/error message drawn (see render_map()) so a
# redraw is forced whenever that message appears, changes, or clears --
# independent of _basemap_dirty, which only tracks the basemap image
# itself. Without this, a stale error message could linger on screen
# forever once aircraft movement stopped forcing a full redraw every frame.
_last_overlay_msg = None

def render_map():
    """Render the 'map' mode frame: cached basemap backdrop (redrawn only
    when it actually changes) + live plane sprites (repositioned every
    call, independent of the backdrop)."""
    global _basemap_dirty, _last_overlay_msg
    ok = fetch_basemap()  # cheap no-op unless location/zoom/size changed; sets _basemap_dirty on a real refetch
    msg = (basemap_error or "No basemap") if not ok else (planes_error or None)
    if _basemap_dirty or msg != _last_overlay_msg:
        if ok:
            _draw_basemap()
        else:
            window.fill(0)
        if msg:
            _render_row(msg, 0, color="red")
        _basemap_dirty = False
        _last_overlay_msg = msg
    _update_plane_sprites()
    display.refresh()

def fetch_flights():
    global flights, last_fetch, fetch_error
    api_endpoint = settings_pv.get("api_endpoint", "")
    api_key      = settings_pv.get("api_key", "")
    if not api_endpoint:
        # No endpoint configured yet — demo data filtered by current local time
        demo = [
            {"flight": "SK 123", "dest": "OSL", "time": "18:40", "status": "On time"},
            {"flight": "AY 666", "dest": "HEL", "time": "18:55", "status": "Boarding"},
            {"flight": "LH 456", "dest": "FRA", "time": "19:10", "status": "Delayed"},
            {"flight": "SK 001", "dest": "CPH", "time": "19:25", "status": "On time"},
            {"flight": "BA 123", "dest": "LHR", "time": "19:40", "status": "On time"},
            {"flight": "FR 789", "dest": "BCN", "time": "20:05", "status": "On time"},
            {"flight": "TK 010", "dest": "IST", "time": "20:30", "status": "Cancelled"},
        ]
        flights = _filter_future(demo, _now_hhmm())
        last_fetch = time.monotonic()
        fetch_error = ""
        return

    try:
        session  = _get_session()

        # Swedavia API: GET {base}/{AIRPORT}/{arrivals|departures}/{YYYY-MM-DD}
        airport  = settings_pv["airport"]
        mode     = settings_pv["mode"]
        base     = _base_endpoint()

        headers = {
            "Accept": "application/json",
            "Cache-Control": "no-cache",
            "Ocp-Apim-Subscription-Key": api_key,
        }

        modes = ["arrivals", "departures"] if mode == "both" else [mode]

        def _parse_items(data, m, out):
            for item in data.get("flights", []):
                leg = item.get("flightLegIdentifier", {})
                loc = item.get("locationAndStatus", {})
                if not isinstance(loc, dict):
                    loc = {}
                if loc.get("flightLegStatus") == "DEL":
                    continue  # flight removed from schedule

                if m == "departures":
                    dest  = leg.get("arrivalAirportIata", "???")
                    t_val = str((item.get("departureTime") or {}).get("scheduledUtc", ""))
                else:
                    dest  = leg.get("departureAirportIata", "???")
                    t_val = str((item.get("arrivalTime") or {}).get("scheduledUtc", ""))

                # Remarks text takes priority over status code
                remarks = item.get("remarksEnglish", [])
                if remarks and isinstance(remarks, list):
                    status = remarks[0].get("text", "")
                else:
                    status = loc.get("flightLegStatusEnglish", "")

                out.append({
                    "flight": str(item.get("flightId", "???")),
                    "dest":   dest,
                    "time":   _utc_to_local_hhmm(t_val),
                    "status": status,
                })

        raw = []
        for m in modes:
            data = None
            status_code = 0
            for attempt in (0, 1):
                date_str = _date_str(_local_now())
                url      = base + "/" + airport + "/" + m + "/" + date_str
                had_sync = bool(_utc_epoch)
                r        = session.get(url, headers=headers, timeout=15)
                # Sync clock from the response Date header (sent even on errors)
                _sync_time(r.headers.get("date") or r.headers.get("Date", ""))
                status_code = r.status_code
                print("flights GET", url, "->", status_code)
                if status_code == 200:
                    data = r.json()
                    r.close()
                    break
                r.close()
                if had_sync:
                    break
                # Clock was just synced — retry once with the corrected date
            if data is None:
                raise Exception("HTTP " + str(status_code))
            _parse_items(data, m, raw)
            data = None
            gc.collect()

        raw.sort(key=lambda x: x["time"])
        now_hhmm = _now_hhmm()
        today    = _filter_future(raw, now_hhmm)
        print("flights:", len(raw), "flights today,", len(today),
              "upcoming after", now_hhmm)

        # Late in the day the rest of today's board may be (nearly) empty —
        # top it up with the first flights of tomorrow.
        if len(today) < _rows():
            date2 = _date_str(time.localtime(_local_epoch() + 86400))
            raw2  = []
            for m in modes:
                url = base + "/" + airport + "/" + m + "/" + date2
                r   = session.get(url, headers=headers, timeout=15)
                print("flights GET", url, "->", r.status_code)
                if r.status_code == 200:
                    _parse_items(r.json(), m, raw2)
                r.close()
            raw2.sort(key=lambda x: x["time"])
            for f2 in raw2:
                f2["day"] = 1   # tomorrow: its HH:MM must not be compared against today's clock
            take = max(0, 20 - len(today))
            today += raw2[:take]
            print("flights: added", min(take, len(raw2)),
                  "flights from tomorrow", date2)

        flights = today
        last_fetch = time.monotonic()
        fetch_error = ""
        gc.collect()

    except Exception as e:
        fetch_error = str(e)
        _invalidate_session()
        print("flights fetch error:", type(e).__name__, e)
        # Back off before retrying. last_fetch used to be left untouched on
        # failure, so the main loop's "(now - last_fetch) >= refresh" check
        # stayed true and re-ran this fetch every ~50ms -- a tight retry
        # loop that burned through sockets and produced the burst of
        # identical "Out of sockets" errors.
        last_fetch = time.monotonic() - settings_pv["refresh"] + 10
    finally:
        _release_sockets()

# ── Render ────────────────────────────────────────────────────────────────────
BOARD_FLIGHTS = 4      # like an airport board: show only the next few flights
_last_board_hhmm = ""  # minute the board was last drawn for (see main loop)

def _upcoming_flights(limit):
    """The next `limit` flights by LOCAL time. `flights` was filtered when it
    was fetched, but time keeps moving between fetches, so filter again at
    draw time -- otherwise a flight that has already left would stay on the
    board until the next refresh. Tomorrow's flights (day == 1) are always
    "upcoming" and keep their order after today's."""
    now_hhmm = _now_hhmm()
    out = []
    for fl in flights:
        if fl.get("day", 0) == 1 or not now_hhmm or fl["time"] >= now_hhmm:
            out.append(fl)
            if len(out) >= limit:
                break
    return out

def render():
    global _last_board_hhmm, _basemap_dirty
    f      = _cur_font()
    row_h  = _row_height()
    rows   = _rows()
    show_title = settings_pv.get("show_title", 1)
    window.fill(0)
    _last_board_hhmm = _now_hhmm()
    _basemap_dirty = True   # the map must repaint its background if we switch back
    # Plane sprites (map mode) live in the same display group; hide them so
    # they don't float over the flight board after switching modes.
    for tg in _plane_tilegrids:
        tg.hidden = True

    if show_title:
        visible = rows - 1
        mode_label = _MODE_LABEL.get(settings_pv["mode"], settings_pv["mode"].upper())
        header = settings_pv["airport"] + " " + mode_label
        _render_row(header, (rows - 1) * row_h, color="yellow", font=f)
    else:
        visible = rows

    shown = _upcoming_flights(max(1, min(BOARD_FLIGHTS, visible)))

    if not shown:
        if fetch_error:
            msg = "No data"
        elif last_fetch:
            msg = "No flights"
        else:
            msg = "Loading..."
        _render_row(msg, 0, color="white", font=f)
        display.refresh()
        return

    for i, flight in enumerate(shown):
        line_text = _flight_line(flight)
        y = i * row_h

        color = "white"
        status = flight.get("status", "").lower()
        if "delay" in status or "late" in status:
            color = "yellow"
        elif "cancel" in status:
            color = "red"

        _render_row(line_text, y, color=color, font=f)

    display.refresh()

def _pad(s, n):
    s = s[:n]
    return s + " " * (n - len(s))

# Remark abbreviations for display
_STATUS_ABBREV = {
    "on time":   "",
    "landed":    "LND",
    "boarding":  "BRD",
    "delayed":   "DLY",
    "cancelled": "CXL",
    "canceled":  "CXL",
    "diverted":  "DIV",
    "expected":  "EXP",
    "departed":  "DEP",
}

def _abbrev_status(s):
    sl = s.lower().strip()
    for key, abbr in _STATUS_ABBREV.items():
        if key in sl:
            return abbr
    return s[:3].upper() if s else ""

def _flight_line(flight):
    """Format one row: TIME  CITY  FLIGHT  REMARKS
    Mini font uses full city name; small/large use 3-char IATA code."""
    t      = flight["time"][:5]
    iata   = flight["dest"]
    rem    = _abbrev_status(flight.get("status", ""))
    font_name = settings_pv.get("font", "small")
    if font_name == "mini":
        via = _CITY.get(iata[:3].upper(), iata)  # full city name or fallback to IATA
        flt = flight["flight"]                   # full flight number incl. space
        if rem:
            return t + " " + via + " " + flt + " " + rem
        return t + " " + via + " " + flt
    else:
        via = iata[:3]
        flt = _pad(flight["flight"].replace(" ", ""), 5)
        if rem:
            return t + " " + via + " " + flt + " " + rem
        return t + " " + via + " " + flt

# ── Web interface ─────────────────────────────────────────────────────────────
with open("flights.html") as f:
    _html_tpl = f.read()

def make_html():
    mode = settings_pv["mode"]
    cur_fnt = settings_pv.get("font", "small")
    sel_mini  = "selected" if cur_fnt == "mini"  else ""
    sel_small = "selected" if cur_fnt == "small" else ""
    sel_large = "selected" if cur_fnt == "large" else ""
    chk_title = "checked" if settings_pv.get("show_title", 1) else ""
    tz_off    = str(settings_pv.get("tz_offset", 0))
    chk_gray  = "checked" if settings_pv.get("map_grayscale", 0) else ""
    if settings_pv["mode"] == "map":
        status_txt = "Basemap: " + (basemap_error or "OK") + " | Planes: " + \
            (planes_error or (str(len(planes)) + " nearby"))
        # Raw OpenSky count + bbox, to distinguish a real fetch failure from
        # "this fetch worked but genuinely found zero aircraft" (very
        # possible at high zoom, where the visible area may be just a few
        # km across and OpenSky's free coverage is comparatively sparse).
        if last_planes_raw_count is not None:
            status_txt += " (raw: {} in bbox {})".format(last_planes_raw_count, last_planes_bbox)
        # OpenSky's credit balance for this bucket (applies whether
        # anonymous or authenticated -- an API key just raises the daily
        # quota, see DEFAULT_SETTINGS), so a quota running low is visible
        # here rather than only showing up later as sudden fetch failures.
        if last_opensky_rate_remaining is not None:
            status_txt += " | OpenSky credits left: " + str(last_opensky_rate_remaining)
        # Only mention OpenSky auth at all once credentials are configured --
        # otherwise this line would misleadingly look like an error on an
        # app that is working fine anonymously.
        if settings_pv.get("opensky_client_id", "").strip():
            status_txt += " | OpenSky auth: " + (_opensky_auth_error or "OK")
    else:
        status_txt = "Last fetch: " + str(int(time.monotonic() - last_fetch)) + "s ago" if last_fetch else "Not fetched yet"
        if fetch_error:
            status_txt = "Error: " + fetch_error
    body = (_html_tpl
        .replace("{MODE}",      mode)
        .replace("{AIRPORT}",   settings_pv["airport"])
        .replace("{REFRESH}",   str(settings_pv["refresh"]))
        .replace("{SEL_MINI}",  sel_mini)
        .replace("{SEL_SMALL}", sel_small)
        .replace("{SEL_LARGE}", sel_large)
        .replace("{CHK_TITLE}",  chk_title)
        .replace("{TZ_OFFSET}",  tz_off)
        .replace("{ENDPOINT}",  settings_pv.get("api_endpoint", ""))
        .replace("{APIKEY}",    settings_pv.get("api_key", ""))
        .replace("{CHK_GRAYSCALE}", chk_gray)
        .replace("{MAP_LAT}",     str(settings_pv.get("map_lat", 0)))
        .replace("{MAP_LON}",     str(settings_pv.get("map_lon", 0)))
        .replace("{MAP_ZOOM}",    str(settings_pv.get("map_zoom", 8)))
        .replace("{MAP_RADIUS}",  str(settings_pv.get("map_radius_nm", 150)))
        .replace("{OPENSKY_CLIENT_ID}",     settings_pv.get("opensky_client_id", ""))
        .replace("{OPENSKY_CLIENT_SECRET}", settings_pv.get("opensky_client_secret", ""))
        .replace("{NOTE}",      settings_note)
        .replace("{STATUS}",    status_txt))
    return web_header("flights", app=True) + body + web_footer()

_pending_planes = False   # set by index(): viewport changed, refetch aircraft
_pending_redraw = False   # set by index(): settings changed, redraw + refetch

@ampule.route("/", method="GET")
def index(request):
    global _pending_planes, _pending_redraw, _basemap_next_try
    p = request.params
    changed = False
    # Snapshot viewport-affecting values before applying any changes, so we
    # can tell afterward whether the aircraft VIEWPORT actually changed
    # (not just whether the save button was pressed -- the web form always
    # re-submits map_lat/lon/zoom/radius on every save regardless of what
    # the user actually touched). A cosmetic-only change (e.g. toggling
    # grayscale) shouldn't trigger a redundant OpenSky re-fetch: besides
    # being wasteful, an unlucky transient failure or momentarily-empty
    # result on that redundant fetch would silently blank out aircraft
    # that were showing just fine a moment ago, for a reason entirely
    # unrelated to what the user actually changed.
    old_mode = settings_pv["mode"]
    old_viewport = _viewport_key(), settings_pv.get("map_radius_nm", 150)
    old_opensky_creds = (settings_pv.get("opensky_client_id", ""),
                          settings_pv.get("opensky_client_secret", ""))
    if "airport" in p:
        # ampule leaves request params URL-encoded — decode free-text values
        settings_pv["airport"] = ampule.url_decoder(p["airport"]).strip().upper()[:4]; changed = True
    if "mode" in p and p["mode"] in ("departures", "arrivals", "both", "map"):
        settings_pv["mode"] = p["mode"]; changed = True
    if "refresh" in p:
        try: settings_pv["refresh"] = max(10, min(300, int(p["refresh"]))); changed = True
        except: pass
    if "font" in p and p["font"] in ("mini", "small", "large"):
        settings_pv["font"] = p["font"]; changed = True
    if "show_title" in p:
        settings_pv["show_title"] = 1 if p["show_title"] == "1" else 0; changed = True
    if "tz" in p:
        try: settings_pv["tz_offset"] = max(-12, min(14, int(p["tz"]))); changed = True
        except: pass
    if "endpoint" in p:
        settings_pv["api_endpoint"] = ampule.url_decoder(p["endpoint"]).strip(); changed = True
    if "apikey" in p:
        settings_pv["api_key"] = ampule.url_decoder(p["apikey"]).strip(); changed = True
    if "map_lat" in p:
        try: settings_pv["map_lat"] = max(-85.0, min(85.0, float(p["map_lat"]))); changed = True
        except: pass
    if "map_lon" in p:
        try: settings_pv["map_lon"] = max(-180.0, min(180.0, float(p["map_lon"]))); changed = True
        except: pass
    if "map_zoom" in p:
        try: settings_pv["map_zoom"] = max(2, min(14, int(float(p["map_zoom"])))); changed = True
        except: pass
    if "map_radius" in p:
        try: settings_pv["map_radius_nm"] = max(5, min(250, int(float(p["map_radius"])))); changed = True
        except: pass
    if "map_grayscale" in p:
        settings_pv["map_grayscale"] = 1 if p["map_grayscale"] == "1" else 0; changed = True
    if "opensky_client_id" in p:
        settings_pv["opensky_client_id"] = ampule.url_decoder(p["opensky_client_id"]).strip(); changed = True
    if "opensky_client_secret" in p:
        settings_pv["opensky_client_secret"] = ampule.url_decoder(p["opensky_client_secret"]).strip(); changed = True
    if changed:
        save_ok, save_msg = save_settings()
        # Do NOT fetch anything from the network in here. This handler runs
        # while the browser's own connection (plus the listening socket) is
        # still open, and the ESP32-S2 has very few sockets in total -- an
        # outbound connection made at this moment is the most likely one to
        # fail with "Out of sockets". Just record what needs doing; the main
        # loop performs it right after ampule.listen() returns, once this
        # request's socket has been closed.
        if settings_pv["mode"] == "map":
            new_viewport = _viewport_key(), settings_pv.get("map_radius_nm", 150)
            mode_just_became_map = (old_mode != "map")
            new_opensky_creds = (settings_pv.get("opensky_client_id", ""),
                                  settings_pv.get("opensky_client_secret", ""))
            # Also refetch if nothing has ever been fetched yet, if the
            # data on hand is stale from a long stretch spent in a
            # non-map mode (planes aren't re-fetched at all while mode
            # != "map" -- see the main loop -- so its age is unbounded), or
            # if the OpenSky credentials changed (so a bad key is reflected
            # immediately rather than only on the next scheduled refresh).
            if (new_viewport != old_viewport or mode_just_became_map
                    or _planes_viewport_key is None
                    or new_opensky_creds != old_opensky_creds):
                _pending_planes = True
        _pending_redraw = True
        _basemap_next_try = 0   # user changed something: don't wait out an old backoff
        return (200, {}, ("OK: " if save_ok else "ERR: ") + save_msg)
    return (200, {}, make_html())

@ampule.route("/exit", method="GET")
def do_exit(request):
    load_settings.app_running = False
    return (200, {}, """<meta http-equiv="refresh" content="0; url=../" />""")

# ── Main loop ─────────────────────────────────────────────────────────────────
splash()
# Initial fetch + render
if settings_pv["mode"] == "map":
    fetch_planes()
    render_map()
else:
    fetch_flights()
    render()
last_board_check = time.monotonic()
last_map_tick = time.monotonic()
MAP_TICK_INTERVAL = 1.0  # reposition aircraft sprites at least this often

while load_settings.app_running:
    now    = time.monotonic()
    mode   = settings_pv["mode"]

    if check_if_button_pressed() == 2:   # long press leaves the app, as in the other apps
        load_settings.app_running = False
        break

    # Work queued by the web handler (see index()), run here -- after the
    # request's own socket has been closed -- so outbound connections don't
    # compete with the browser connection for the device's few sockets.
    if _pending_redraw:
        _pending_redraw = False
        if mode == "map":
            if _pending_planes:
                _pending_planes = False
                fetch_planes()
            render_map()
            last_map_tick = time.monotonic()
        else:
            _pending_planes = False
            fetch_flights()
            render()
        now = time.monotonic()

    if mode == "map":
        # Data (network) and visual (sprite reposition) updates run on
        # deliberately different cadences: fetch_planes() only needs to
        # run as often as settings_pv["refresh"] allows (an actual
        # OpenSky API call, kept infrequent to stay within its anonymous
        # usage limits), but the on-screen aircraft positions should
        # still visibly update about once a second in between -- achieved
        # by dead-reckoning (see _extrapolate_position()) rather than by
        # fetching more often. render_map() (called every tick here) is
        # cheap: it does no network I/O beyond a fast cache check unless
        # the basemap itself actually needs refetching.
        if (now - last_planes_fetch) >= settings_pv["refresh"]:
            fetch_planes()
        if (now - last_map_tick) >= MAP_TICK_INTERVAL:
            render_map()
            last_map_tick = now
    else:
        # Periodic data refresh
        if (now - last_fetch) >= settings_pv["refresh"]:
            fetch_flights()
            render()
            last_board_check = now
        # The board is static (like an airport display), but it's relative
        # to the clock: once a minute, redraw so flights that have already
        # left drop off and the next one moves up.
        elif (now - last_board_check) >= 1.0:
            last_board_check = now
            if _now_hhmm() != _last_board_hhmm:
                render()

    # Handle web requests
    try:
        ampule.listen(socket)
    except: pass

    time.sleep(0.05)

# Leaving the app: take the plane layer out of the shared display group (it
# outlives this app) and blank the map, so nothing lingers over the main menu.
_remove_plane_layer()
window.fill(0)
try: display.refresh()
except Exception: pass
_release_sockets()