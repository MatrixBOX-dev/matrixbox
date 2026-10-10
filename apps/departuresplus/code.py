# Departures Plus - departure board for MatrixBOX with station rotation and line colours.
from __main__ import socket, display
import sys, time, gc
import ampule, load_settings
from check_button import check_if_button_pressed
import dp_app, dp_web

_root = display.root_group
app = dp_app.App()
dp_web.init(app)

while load_settings.app_running:
    ampule.listen(socket)
    b = check_if_button_pressed()
    if b == 2:
        load_settings.app_running = False
        break
    if b == 1: app.button()
    try:
        app.tick()
    except MemoryError:
        gc.collect()
    except Exception as e:
        app.note("tick: " + str(e))
        time.sleep(1)

app.hw(True)
try: display.root_group = _root     # older firmware does not restore its own screen on exit
except Exception: pass
for m in ("dp_app", "dp_web", "dp_draw", "dp_data", "dp_cfg"):
    try: del sys.modules[m]
    except Exception: pass
gc.collect()
