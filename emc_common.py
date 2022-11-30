import bpy
import pymem
from pymem.ptypes import RemotePointer

# ROOT_DIRECTORY = Path('C://Users//fores//AppData//Roaming//Slippi Launcher//playback//User//ScreenShots//GALE01')
pm = pymem.Pymem("Slippi Dolphin.exe")
index_ptr = 0x01CF0088


def get_ptr(base, offsets):
    remote_pointer = RemotePointer(pm.process_handle, base)
    for offset in offsets:
        if offset != offsets[-1]:
            remote_pointer = RemotePointer(pm.process_handle, remote_pointer.value + offset)
        else:
            return remote_pointer.value + offset


FRAME_INDEX = get_ptr(pm.base_address + index_ptr, [0xC])
EMU_SIZE = 0x2000000
EMU_DIST = 0x10000

SAVE_STATE = 0x8F5E00
LOAD_STATE = 0x8F53F0
SCREEN_SHOT = 0x885BA0
FRAME_STEP = 0x1F8AC0
# Dolphin freelook
#FREE_LOOK = None

CAM_START = 0x453040
PAUSE_BIT = 0x479D68
