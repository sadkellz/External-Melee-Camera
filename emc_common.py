import pymem
from pathlib import Path

ROOT_DIRECTORY = Path('C://Users//fores//AppData//Roaming//Slippi Launcher//playback//User//ScreenShots//GALE01')
pm = pymem.Pymem("Dolphin.exe")

EMU_SIZE = 0x2000000
EMU_DIST = 0x10000

SAVE_STATE = 0x8F4D20
LOAD_STATE = 0x8F4310
SCREEN_SHOT = 0x8851C0
FRAME_STEP = 0x8EB220
FREE_LOOK = None

CAM_START = 0x453040
PAUSE_BIT = 0x479D68
