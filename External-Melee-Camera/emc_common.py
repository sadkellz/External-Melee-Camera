import bpy
import pymem
from pymem.ptypes import RemotePointer

pm = pymem.Pymem("Slippi Dolphin.exe")
INDEX_PTR = 0x01CF0088


def get_ptr(base, offsets):
    remote_pointer = RemotePointer(pm.process_handle, base)
    for offset in offsets:
        if offset != offsets[-1]:
            remote_pointer = RemotePointer(pm.process_handle, remote_pointer.value + offset)
        else:
            return remote_pointer.value + offset


FRAME_INDEX = get_ptr(pm.base_address + INDEX_PTR, [0xC])
EMU_SIZE = 0x2000000
EMU_DIST = 0x10000
SAVE_STATE = 0x8F5E00
LOAD_STATE = 0x8F53F0
SCREEN_SHOT = 0x885BA0
FRAME_STEP = 0x1F8AC0
# Dolphin freelook
# FREE_LOOK = None
CAM_START = 0x453040
PAUSE_BIT = 0x479D68
CAM_TYPE = 0x452C6F


# Finds the specific page with the size of EMU_SIZE.
def pattern_scan_all(handle, pattern, *, return_multiple=False):
    next_region = 0
    found = []

    while next_region < 0x7FFFFFFF0000:
        next_region, page_found = pymem.pattern.scan_pattern_page(
            handle,
            next_region,
            pattern,
            return_multiple=return_multiple
        )

        if not return_multiple and page_found:
            if (next_region - page_found) == int(EMU_SIZE):
                return page_found

        if page_found:
            if (next_region - page_found) == int(EMU_SIZE):
                found += page_found

    if not return_multiple:
        return None

    return found


# Finds 'GALE01' in memory.
# This is used to jump to specific functions in Melee ie: GALE01 + CAM_START
def find_gale01():
    handle = pm.process_handle
    byte_pattern = bytes.fromhex("47 41 4C 45 30 31 00 02")
    found = pattern_scan_all(handle, byte_pattern)
    return found


GALE01 = find_gale01()
