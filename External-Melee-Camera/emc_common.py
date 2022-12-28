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
SAVE_STATE_PAT = b'...\x5C\x24\x10\x55\x48\x8B\xEC\x48\x83\xEC\x50\x48\x8D\x4D\xE0'
LOAD_STATE_PAT = b'...\x5C\x24\x08\x57\x48\x83\xEC\x70\x48\x8B\x05....\x48\x33\xC4\x48\x89\x44.\x60\x8B\xD9\x48\x8D\x4C.\x30\xE8....'
SCREEN_SHOT_PAT = b'\x40\x53\x48\x83\xEC\x50\x48\x8B\x05....\x48\x33\xC4\x48\x89\x44.\x40\x48\x8B\x05....'
FRAME_STEP_PAT = b'..\x5C\x24\x08\x57\x48\x83\xEC\x20\x48\x8B\xF9\xE8....\x83\xF8\x01\x0F\x94\xC3\xE8....\xE8....'
# FREE_LOOK = None
CAM_START = 0x453040
PAUSE_BIT = 0x479D68
CAM_TYPE = 0x452C6F
PLAYER_ONE = 0x453090
PLAYER_TWO = 0x453F20
PLAYER_THREE = 0x454DB0
PLAYER_FOUR = 0x455C40


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


def find_dolphin_funcs(byte_pattern):
    handle = pm.process_handle
    module = pymem.process.module_from_name(pm.process_handle, "Slippi Dolphin.exe")
    found = pymem.pattern.pattern_scan_module(handle, module, byte_pattern, return_multiple=False)
    return found

SAVE_STATE = find_dolphin_funcs(SAVE_STATE_PAT) - pm.base_address
LOAD_STATE = find_dolphin_funcs(LOAD_STATE_PAT) - pm.base_address
SCREEN_SHOT = find_dolphin_funcs(SCREEN_SHOT_PAT) - pm.base_address
FRAME_STEP = find_dolphin_funcs(FRAME_STEP_PAT) - pm.base_address
GALE01 = find_gale01()

