"""Mock of the T-Skylt departures data server, for testing the "Data server"
setting of the departures app without hitting data.t-skylt.se.

Serves the three endpoints the app calls on its data server, in the same
shape the real server returns:

    GET /get_departures?country=..&operator=..&station=..
        {"timestamp": .., "departures": [{"line": {"id", "transport_mode"},
          "expected": "YYYY-MM-DDTHH:MM:SS", "destination", "direction_code",
          "delay"}, ...]}
    GET /search_stop?country=..&operator=..&station=<query>
        {"Station name": "station id", ...}
    GET /get_deviations?country=..&operator=..&station=..
        ["deviation text", ...]

The Date header is sent in local time with its UTC offset ("+0200"), like the
real server: the app computes minutes-left from it, and treats a "GMT" Date as
UTC+2 regardless of season.

Usage:
    python3 tools/mock_data_server.py [--port 9000]

Then set Settings > Data server on the device to <this computer's IP>:9000.
"""
import argparse, json, time
from email.utils import formatdate
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlsplit, parse_qs

STATIONS = {
    "Mock Hauptbahnhof": "mock:1",
    "Mock Alexanderplatz": "mock:2",
    "Mock Hafen": "mock:3",
}

# line id, transport_mode, destination, direction_code, headway minutes, first offset
LINES = [
    ("U2", "METRO", "Pankow", "1", 5, 1),
    ("U2", "METRO", "Ruhleben", "2", 5, 3),
    ("S5", "TRAIN", "Strausberg Nord", "1", 10, 2),
    ("RE1", "TRAIN", "Frankfurt (Oder)", "2", 30, 7),
    ("M4", "TRAM", "Zingster Str.", "1", 7, 4),
    ("100", "BUS", "Michelangelostr.", "2", 6, 0),
    ("N2", "BUS", "Ruhleben", "1", 30, 12),
    ("F10", "SHIP", "Kladow", "1", 60, 15),
]

DEVIATIONS = [
    "Mock: U2 Bauarbeiten zwischen Pankow und Vinetastr.",
    "Mock: S5 Ersatzverkehr am Wochenende",
]

def departures(window=90, limit=30):
    now = time.time()
    out = []
    for line_id, mode, dest, direction, headway, first in LINES:
        t = now + first * 60
        n = 0
        while t < now + window * 60:
            delay = "+2" if n == 1 and mode == "TRAIN" else ""
            expected = t + (120 if delay else 0)
            out.append({
                "line": {"id": line_id, "transport_mode": mode},
                "expected": time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(expected)),
                "destination": dest,
                "direction_code": direction,
                "delay": delay,
            })
            t += headway * 60
            n += 1
    out.sort(key=lambda d: d["expected"])
    return out[:limit]  # keep the payload small, the device parses it in RAM

class Handler(BaseHTTPRequestHandler):
    server_version = "MockTSkylt/1.0"

    def date_time_string(self, timestamp=None):
        # local time + offset ("Sun, 18 Oct 2026 15:21:49 +0200"), not GMT
        return formatdate(timestamp, localtime=True)

    def do_GET(self):
        url = urlsplit(self.path)
        q = {k: v[0] for k, v in parse_qs(url.query).items()}
        print("  <- %s  User=%r  From=%r" % (self.path, self.headers.get("User"), self.headers.get("From")), flush=True)
        if url.path == "/get_departures":
            body = {"timestamp": int(time.time()), "departures": departures()}
        elif url.path == "/search_stop":
            s = q.get("station", "").lower()
            body = {name: sid for name, sid in STATIONS.items() if s in name.lower()} or STATIONS
        elif url.path == "/get_deviations":
            body = DEVIATIONS
        else:
            self.send_error(404)
            return
        data = json.dumps(body).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Connection", "close")
        self.end_headers()
        self.wfile.write(data)

if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--port", type=int, default=9000)
    args = ap.parse_args()
    print("Mock T-Skylt data server on 0.0.0.0:%d" % args.port, flush=True)
    ThreadingHTTPServer(("0.0.0.0", args.port), Handler).serve_forever()
