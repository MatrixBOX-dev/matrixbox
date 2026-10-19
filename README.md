# MatrixBOX

This is the official source code for the [MatrixBOX][matrixbox.app] firmware,
the OS running on the device. In addition to the firmware, this also contains
all official apps for the device, including the "Departures" app by [T-skylt].

## Set up the device

There are two ways to set up the device: one remotely over WiFi via the
device's hotspot, and the other by connecting it to a computer.

### Wireless setup

1. Connect to WiFi shown on screen (e.g. `matrixbox-0a1`)
2. Browse to: 192.168.4.1
3. Select your SSID (wireless network name) and wifi password
4. When online, the device is assigned an IP address by your router, shown on
   the display

### Offline setup

1. To unlock the file system, hold down the button while connecting the device
   to a computer
2. You can now manually edit `settings.txt`, adding your WiFi credentials to
   the `ssid` and `password` fields in the JSON object
3. The file system will lock upon reboot

## Making custom apps

1. The device runs [CircuitPython], a fork of Python for microcontrollers
2. To get an idea of how to program an app you can study the provided apps like
   [clock] or [paint]
3. A new app is recognized on the device as a directory in the root folder
   (e.g. `/appname`) with a `__init__.py` file inside
4. If you use a coding agent to write your apps, you can refer it to
   `system_prompt.md` for general guidelines

### Third-party apps

Apps don't have to live in this repo. Any public GitHub repo with a
`manifest.json` can be installed from the Apps page by entering its URL:

- `github.com/owner/repo` or `owner/repo`: manifest at the repo root
- `owner/repo/some/dir` or `github.com/owner/repo/tree/main/some/dir`: app in
  a subdirectory
- `owner/repo@branch`: another branch than the default one

```json
{
  "name": "My App",
  "description": "What it does",
  "version": "0.1",
  "emoji": "🎵",
  "files": ["__init__.py", "code.py", "myapp.html"]
}
```

- `files` lists everything the device downloads, and must include
  `__init__.py`
- `version` decides when an update is offered: bump it to ship a new version
- The app is installed as `/<owner>-<repo>`, or `/<owner>-<dir>` for an app in
  a subdirectory (a `matrixbox-` prefix is dropped), so open files relative to
  the app directory
- `emoji` is optional

Updates are manual: "Check for updates" on the Apps page compares each
installed app's version with its repo, and Update downloads all files again.

Apps can also be added to the Community list on the Apps page by opening a PR
adding them to [`thirdparty.json`](./thirdparty.json). An entry is only
`repo` (plus optional `path` and `ref`) and the `name`, `description` and
`emoji` shown before it's installed; versions always come from the app's own
manifest, so releasing an update never needs a change here. See
[matrixbox-lastfm] for an example.

## Recover your device

If you lose access to your device, e.g. by files getting corrupted while
transferring, you can recover it either via our flashing tool or via the console
port.

### ⚠️ Flash your device

The code can be flashed onto a MatrixBOX at [matrixbox.app/flash][flash]. Follow
the instructions on the page.

### Console port

The USB port also works as a serial console straight into CircuitPython, so
you can reach the device even if its filesystem is in a broken state and it
never shows up as a drive.

#### macOS or Linux

List your serial devices to find the one that appeared when you plugged in
the device (`/dev/tty.usbmodem*` on macOS, `/dev/ttyACM*` on Linux), then
connect with `screen`. The baud rate is ignored over USB, but `screen`
requires one, so any value works:

```sh
ls /dev/tty.usbmodem* # or /dev/ttyACM* on Linux
screen /dev/tty.usbmodemC3F0204E994B1 115200
```

#### Windows

Open Device Manager and look under "Ports (COM & LPT)" for the device's COM
port (e.g. `COM3`). Connect to it with a serial terminal such as [PuTTY],
using connection type "Serial" and that COM port; the speed field is ignored
over USB, so any value works.

No third-party app is strictly required: PowerShell can talk to the port
directly via .NET, though it's less pleasant for interactive use than a real
terminal:

```powershell
$port = New-Object System.IO.Ports.SerialPort COM3,115200
$port.Open()
$port.Write("`x03") # Ctrl+C, stop whatever is running
Start-Sleep -Milliseconds 200
$port.WriteLine('open("/unlock", "w").close()')
$port.WriteLine('import microcontroller; microcontroller.reset()')
$port.Close()
```

#### Using the console

Once connected, press Ctrl+C to stop whatever is running and drop into the
REPL, then leave [`boot.py`] the marker file it checks for to unlock the
drive, and reset (the drive's enabled/writable state over USB is fixed at
boot, so this is required either way):

```python
open("/unlock", "w").close()
import microcontroller
microcontroller.reset()
```

## Contribute

If you wish to contribute to this project, simply open a PR here. You can also
reach us at

- [@matrixbox.app] on Instagram
- [matrixbox.app]
- [info@matrixbox.app][email]

## Other resources

- [matrixbox-simulator] - A tool to emulate the device in your terminal
  including host the web server locally. Helps speed up app development and
  preview web content
- [gif-resizer] - A tool to resize GIF's so they can render properly on the
  device

[@matrixbox.app]: https://www.instagram.com/matrixbox.app
[CircuitPython]: https://circuitpython.org/
[PuTTY]: https://en.wikipedia.org/wiki/PuTTY
[T-skylt]: https://shop.t-skylt.se/
[`boot.py`]: ./boot.py
[clock]: ./apps/clock
[email]: mailto:info@matrixbox.app
[flash]: https://matrixbox.app/flash/
[gif-resizer]: https://github.com/MatrixBOX-dev/gif-resizer
[matrixbox-lastfm]: https://github.com/bombsimon/matrixbox-lastfm
[matrixbox-simulator]: https://github.com/MatrixBOX-dev/simulator
[matrixbox.app]: https://matrixbox.app
[paint]: ./apps/paint
