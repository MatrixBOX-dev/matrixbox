import os
import ampule
import load_settings
import web_interface

_cmd_buf = []
_cmd_env = None


def _cmd_print(*args, **kwargs):
    sep = kwargs.get("sep", " ")
    text = sep.join(str(a) for a in args)
    _cmd_buf.append(text)
    print(text)


def _wrap_text(text, max_w, strlen, font):
    # word-wrap to pixel width, same approach as apps/dictaphone's wrap_text
    words = text.split(" ")
    result = []
    current = ""
    for w in words:
        test = (current + " " + w).strip()
        if strlen(test, font) <= max_w:
            current = test
        else:
            if current:
                result.append(current)
            current = w
            while strlen(current, font) > max_w and len(current) > 1:
                current = current[:-1]
    if current:
        result.append(current)
    return result


def _make_wrapped_pprint(real_pprint, strlen, display, font_mini):
    def _wrapped(string, line=None, color="white", font=None, **kwargs):
        f = font if font is not None else font_mini
        max_lines = display.height // f["fontheight"]
        base = line if isinstance(line, int) else 0
        for i, wl in enumerate(_wrap_text(str(string), display.width - 2, strlen, f)[:max_lines]):
            real_pprint(wl, line=base + i, color=color, font=f, **kwargs)
    return _wrapped


def _run_command(command):
    """Shared eval/exec logic for both the POST and GET handlers."""
    global _cmd_buf, _cmd_env
    if _cmd_env is None:
        from __main__ import __dict__ as _main_dict
        _cmd_env = dict(_main_dict)
        _cmd_env["print"] = _cmd_print
        real_pprint = _main_dict.get("pprint")
        strlen = _main_dict.get("strlen")
        display = _main_dict.get("display")
        font_mini = _main_dict.get("font_mini")
        if real_pprint and strlen and display and font_mini:
            _cmd_env["pprint"] = _make_wrapped_pprint(real_pprint, strlen, display, font_mini)
    _cmd_buf = []
    try:
        result = eval(command, _cmd_env)
        if result is not None:
            _cmd_buf.append(repr(result))
    except SyntaxError:
        try:
            exec(command, _cmd_env)
        except Exception as e:
            _cmd_buf.append(str(e))
    except Exception as e:
        _cmd_buf.append(str(e))
    return "\n".join(_cmd_buf)


@ampule.route('/system/cmd', method='POST')
def execute_command(request):
    return (200, {}, _run_command(request.body))


@ampule.route("/system/cmd", method="GET")
def _cmd(request):
    # Reached from the shared navbar's menu in both home and in-app
    # contexts, same as /system/settings -- see web_interface.navbar().
    in_app = bool(load_settings.app_running)
    content = """<style>
body{display:flex;flex-direction:column;height:100vh;overflow:hidden;padding-bottom:0!important}
.page{max-width:none!important;margin:0!important;padding:0!important;flex:1;display:flex;flex-direction:column;min-height:0;overflow:hidden}
#console-output{flex:1;overflow-y:auto;padding:14px 16px;font-size:.85rem;line-height:1.6;white-space:pre-wrap;word-break:break-all;cursor:text;font-family:'Cascadia Mono','Fira Code','Consolas',monospace;color:var(--text)}
#input-row{display:flex;align-items:stretch;padding:10px 14px;background:var(--surface);border-top:1px solid var(--border);flex-shrink:0;gap:8px}
#command-input{flex:1;background:var(--surface2);border:1.5px solid var(--border);border-radius:var(--r);outline:none;color:var(--text);font-family:'Cascadia Mono','Fira Code','Consolas',monospace;font-size:.88rem;caret-color:var(--accent);padding:9px 12px}
#command-input:focus{border-color:var(--accent);box-shadow:0 0 0 3px rgba(124,111,255,.15)}
#command-button{flex-shrink:0;padding-top:0;padding-bottom:0}
</style>
<div id="console-output">Welcome to the terminal. Enter Python commands to execute directly in the interpreter.\n\nRunning: """ + os.uname().version + """\n\n</div>
<div id="input-row">
<input id="command-input" type="text" placeholder="Enter command..." autocomplete="off" autofocus>
<button id="command-button" class="btn btn-sm">Execute</button>
</div>
<script>
    let outputConsole = document.getElementById('console-output');
    let commandInput = document.getElementById('command-input');
    let commandButton = document.getElementById('command-button');

    console.log('JavaScript is running...');

    commandButton.addEventListener('click', async () => {
        console.log('Button clicked...');
        let command = commandInput.value;
        console.log('Command:', command);

        if (command) {
            console.log('Sending command to server...');
            const endpoint = 'cmd';

            try {
                const response = await fetch(endpoint, {
                    method: 'POST',
                    body: command,
                });

                if (!response.ok) {
                    throw new Error('HTTP error! Status: ' + response.status);
                }

                const data = await response.text();
                console.log('Response from server:', data);

                var p=document.createElement('span');p.textContent='>>> '+command+'\\n';outputConsole.appendChild(p);
                if (data) { var e=document.createElement('span');e.textContent=data+'\\n';outputConsole.appendChild(e); }
                commandInput.value = '';
                outputConsole.scrollTop = outputConsole.scrollHeight;
            } catch (error) {
                console.error('Error sending command:', error);
                var er=document.createElement('span');er.textContent='Error: '+error+'\\n';outputConsole.appendChild(er);
            }
        }
    });

    commandInput.addEventListener('keydown', function(ev) {
        if (ev.keyCode == 13) { commandButton.click(); }
    });
</script>"""
    return (200, {}, web_interface._shell(content, "Terminal", "/system/cmd", app=in_app))
