import pymem
from pathlib import Path

SaveState = 0x8F3B30
LoadState = 0x8F2430
ScreenShot = 0x8851C0
FrameStep = 0x1F8380
FreeLook = None

ROOT_DIRECTORY = Path('C://Users//fores//AppData//Roaming//Slippi Launcher//playback//User//ScreenShots//GALE01')
pm = pymem.Pymem("Dolphin.exe")


# Injects a python interpreter, so we can call functions from Dolphins main thread via offset
def call_native_func(fnc_ptr, fnc_type, fnc_args):
    pm.inject_python_interpreter()
    fnc_adr = '0x' + format((pm.base_address + fnc_ptr), "08X")
    shell_code = """import ctypes
functype = ctypes.CFUNCTYPE({})
func = functype({})
func({})""".format(fnc_type, fnc_adr, fnc_args)
    pm.inject_python_shellcode(shell_code)
