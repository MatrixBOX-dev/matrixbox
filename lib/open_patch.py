from __main__ import *
import builtins
_real_open = open   # keep original


print("Patching open")

class AutoWriteFile:
    def __init__(self, *args, **kwargs):
        try: display.root_group.hidden = True; refresh()
        except: print("Disp fail")

        self._f = _real_open(*args, **kwargs)
        self._run_hook(args, kwargs)


    def _run_hook(self, args, kwargs):
        pass 

    # proxy all attributes to the real file
    def __getattr__(self, name):
        return getattr(self._f, name)

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        try: display.root_group.hidden = False; refresh()
        except: print("Disp fail")

        return self._f.__exit__(*exc)

# override builtins.open
def open_hook(path="/", mode="r", *args, **kwargs):
    if "w" in mode or "a" in mode or "x" in mode:
        return AutoWriteFile(path, mode, *args, **kwargs)
    return _real_open(path, mode, *args, **kwargs)

builtins.open = open_hook