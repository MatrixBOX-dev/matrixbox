import sys
for _m in ("code", "dp_app", "dp_web", "dp_draw", "dp_data", "dp_cfg"):
    try: del sys.modules[_m]      # older firmware keeps an app's modules cached between launches
    except Exception: pass
import ampule
ampule.routes.clear()
import code
