import os
import ampule

_cmd_buf = []
_cmd_env = None

def _cmd_print(*args, **kwargs):
    sep = kwargs.get("sep", " ")
    text = sep.join(str(a) for a in args)
    _cmd_buf.append(text)
    print(text)

@ampule.route('/system/cmd', method='POST')
def execute_command(request):
    global _cmd_buf, _cmd_env
    if _cmd_env is None:
        from __main__ import __dict__ as _main_dict
        _cmd_env = dict(_main_dict)
        _cmd_env["print"] = _cmd_print
    command = request.headers["x-command"]
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
    return (200, {}, "\n".join(_cmd_buf))


@ampule.route("/system/cmd", method="GET")
def _cmd(request):
    html = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>Console and Command</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{background:#0c0c0c;color:#ccc;font-family:'Cascadia Mono','Fira Code','Consolas',monospace;height:100vh;display:flex;flex-direction:column;overflow:hidden}
#toolbar{background:#1a1a2e;padding:6px 12px;display:flex;align-items:center;gap:10px;border-bottom:1px solid #333;flex-shrink:0}
#toolbar span{color:#7c7cff;font-weight:700;font-size:.85rem}
#toolbar a{color:#888;text-decoration:none;font-size:.8rem;padding:4px 10px;border-radius:6px;background:#222;border:1px solid #333}
#toolbar a:hover{color:#fff;border-color:#7c7cff}
#console-output{flex:1;overflow-y:auto;padding:10px 14px;font-size:.85rem;line-height:1.6;white-space:pre-wrap;word-break:break-all;cursor:text}
#input-row{display:flex;align-items:center;padding:6px 10px;background:#111;border-top:1px solid #333;flex-shrink:0;gap:6px}
#command-input{flex:1;background:transparent;border:none;outline:none;color:#e8e8e8;font-family:inherit;font-size:.88rem;caret-color:#7c7cff}
#command-button{background:#7c7cff;color:#000;border:none;padding:6px 14px;border-radius:6px;font-weight:700;font-size:.82rem;cursor:pointer}
</style>
</head>
<body>
<div id="toolbar"><span>MatrixBox Terminal</span><div style="flex:1"></div><a href="/">Home</a></div>
<div id="console-output">Welcome to the terminal. Enter Python commands to execute directly in the interpreter.\n\nRunning: """ + os.uname().version + """\n\n</div>
<div id="input-row">
<input id="command-input" type="text" placeholder="Enter command..." autocomplete="off" autofocus>
<button id="command-button">Execute</button>
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
                    headers: {
                        'Content-Type': 'application/json',
                        'X-Command': command,
                    },
                    body: null,
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
</script>
</body>
</html>"""
    return (200, {}, html)
