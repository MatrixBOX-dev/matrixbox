from __main__ import *
ampule.routes.clear()

_sp = []
for i in range(12):
    try: _sp.append(palette[i])
    except: _sp.append(0)

import code

for i in range(12):
    try: palette[i] = _sp[i]
    except: pass
