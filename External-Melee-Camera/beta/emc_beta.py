import bpy
from bpy.utils import register_class, unregister_class
import math
import struct
import pymem
from bpy.props import (IntProperty, StringProperty, BoolProperty, PointerProperty, FloatVectorProperty, EnumProperty)
from bpy.types import (Panel, PropertyGroup)
import time
import subprocess
import os
from pathlib import Path
from pymem.ptypes import RemotePointer

bl_info = {
    "name": "External-Melee-Camera",
    "author": "KELLZ",
    "version": (2, 0, 0),
    "blender": (3, 3, 2),
    "warning": "Requires installation of dependencies",
    "category": "Tools",
    "description": "Control Melee's Camera from Blender.",
    "wiki_url": "https://github.com/sadkellz/External-Melee-Camera",
}

##################################################
#                     COMMON                     #
##################################################


# Page size to look for in pattern_scan_all, as there could be multiple pages with GALE01.
EMU_SIZE = 0x2000000
EMU_DIST = 0x10000
# Dolphin specific patterns of their respective functions.
GET_STATE_PAT = b'\\x48\\x83\\xEC\\x28\\x80\\x3D...\\x00\\x00\\x74\\x0A\\xB8\\x03'
SAVE_STATE_PAT = b'\\x48\\x89\\x5C\\x24\\x10\\x55\\x48\\x8B\\xEC\\x48\\x83\\xEC\\x50\\x48\\x8D\\x4D\\xE0'

LOAD_STATE_PAT = b'\\x48\\x89\\x5C\\x24\\x08\\x57\\x48\\x83\\xEC\\x70\\x48\\x8B\\x05....' \
                 b'\\x48\\x33\\xC4\\x48\\x89\\x44\\x24\\x60\\x8B\\xD9\\x48\\x8D\\x4C\\x24\\x30\\xE8....'

SCREEN_SHOT_PAT = b'\\x40\\x53\\x48\\x83\\xEC\\x50\\x48\\x8B\\x05....\\x48\\x33\\' \
                  b'xC4\\x48\\x89\\x44\\x24\\x40\\x48\\x8B\\x05....'

FRAME_STEP_PAT = b'\\x48\\x83\\xEC\\x28\\xE8....\\x83\\xF8\\x01\\x75\\x19\\x88\\' \
                 b'x05....\\xE8....\\xB9\\x02\\x00\\x00\\x00\\x48\\x83\\xC4\\x28\\' \
                 b'xE9....\\x80\\x3D....\\x00\\x75\\x0E\\xB9\\x01\\x00\\x00\\x00\\x48\\' \
                 b'x83\\xC4\\x28\\xE9....\\x48\\x83\\xC4\\x28\\xC3'

SAVE_STATE_SLOT_PAT = b'\\x48\\x89\\x5C\\x24\\x18\\x48\\x89\\x74\\x24\\x20\\x57\\x48\\x83\\' \
                      b'xEC\\x60\\x48\\x8B\\x05....\\x48\\x33\\xC4\\x48\\x89\\x44\\x24\\x50\\x0F\\xB6\\xF2'

LOAD_STATE_SLOT_PAT = b'\\x48\\x89\\x5C\\x24\\x10\\x57\\x48\\x83\\xEC\\x60\\x48\\x8B\\x05' \
                      b'....\\x48\\x33\\xC4\\x48\\x89\\x44\\x24\\x50\\x8B\\xF9'

DUMP_FRAMES_PAT = b'\\x48\\x89\\x5C\\x24\\x10\\x48\\x89\\x74\\x24\\x18\\x48\\x89\\x7C\\x24\\' \
                  b'x20\\x55\\x41\\x54\\x41\\x55\\x41\\x56\\x41\\x57\\x48\\x8D\\x6C\\x24\\xC9\\' \
                  b'x48\\x81\\xEC\\xF0\\x00\\x00\\x00\\x48\\x8B\\x05\\xAD\\xC6\\x15\\x01'

FRAME_COUNT_PAT = b'\\xFF\\x05\\x95\\x21\\x1D\\x01\\x8B\\x05\\x73\\x05\\x1D\\x01\\xA8\\x01\\x74\\x18'

LOCK_PTR_PAT = b'\\x48\\x8B\\x0D....\\xE8....\\x90\\x48\\x8B\\x54\\x24\\x38\\x48\\x83\\xFA\\x10'

# FREE_LOOK = None

SAVE_STATE = None
LOAD_STATE = None
SAVE_STATE_SLOT = None
LOAD_STATE_SLOT = None
CURRENT_FRAME = None
FRAME_STEP = None
EMU_FRAME = None
SCREEN_SHOT = None
SCREEN_LOCK = None
LOCK_PTR = 0x0189BAB8

# Melee specific offsets. These will always be found x distance away from GALE01 (start of emu).
CAM_START = 0x453040
CAM_TYPE = 0x452C6F
GLOBAL_TIMER = 0x479D60
CPU_UPTIME = 0x4D7423
PAUSE_BIT = 0x479D68
PLAYER_ONE = 0x453080
PLAYER_TWO = 0x453F10
PLAYER_THREE = 0x454DA0
PLAYER_FOUR = 0x455C30

DEV_PAUSE = 0x479D68
FRAME_ADV = 0x479D6A
GAME_HUD = 0x4D6D58
STAGE_FLAGS = 0x453000
BG_COLOUR = 0x452C70

global is_freeze
is_freeze = 0


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


# Subtracting base address as 'call_native_func()' will add it. Trying to stick to the format of using base + offset.
def find_dolphin_funcs(dol, byte_pattern):
    handle = dol.process_handle
    module = pymem.process.module_from_name(dol.process_handle, "Dolphin.exe")
    found = (pymem.pattern.pattern_scan_module(handle, module, byte_pattern, return_multiple=False) - dol.base_address)
    return found


def get_ptr(dol, base, offsets):
    remote_pointer = RemotePointer(dol.process_handle, base)
    for offset in offsets:
        if offset != offsets[-1]:
            remote_pointer = RemotePointer(dol.process_handle, remote_pointer.value + offset)
        else:
            return remote_pointer.value + offset


# Setting variables of functions by finding their byte pattern in the main Dolphin thread.
# Doing it this way so that when Dolphin closes, the panel will relocate the functions.
def set_global_vars(dol):
    global SAVE_STATE, LOAD_STATE, SAVE_STATE_SLOT, LOAD_STATE_SLOT, \
        CURRENT_FRAME, FRAME_STEP, EMU_FRAME, SCREEN_SHOT, SCREEN_LOCK

    SAVE_STATE = find_dolphin_funcs(dol, SAVE_STATE_PAT)
    LOAD_STATE = find_dolphin_funcs(dol, LOAD_STATE_PAT)
    SAVE_STATE_SLOT = find_dolphin_funcs(dol, SAVE_STATE_SLOT_PAT)
    LOAD_STATE_SLOT = find_dolphin_funcs(dol, LOAD_STATE_SLOT_PAT)
    CURRENT_FRAME = GALE01 + GLOBAL_TIMER
    FRAME_STEP = find_dolphin_funcs(dol, FRAME_STEP_PAT)
    # EMU_FRAME = find_dolphin_funcs(dol, EMU_FRAME_PAT)
    SCREEN_SHOT = find_dolphin_funcs(dol, SCREEN_SHOT_PAT)
    # LOCK_PTR = find_dolphin_funcs(dol, LOCK_PTR_PAT)
    SCREEN_LOCK = get_ptr(dol, LOCK_PTR, [0xC0])
    return SAVE_STATE, LOAD_STATE, SAVE_STATE_SLOT, LOAD_STATE_SLOT, \
        CURRENT_FRAME, FRAME_STEP, EMU_FRAME, SCREEN_SHOT, SCREEN_LOCK


def set_pm():
    pm = pymem.Pymem("Dolphin.exe")
    handle = pm.process_handle
    byte_pattern = bytes.fromhex("47 41 4C 45 30 31 00 02")
    GALE01 = pattern_scan_all(handle, byte_pattern)
    return GALE01


##################################################
#                   FUNCTIONS                    #
##################################################


# Injects a python interpreter, so we can call functions from Dolphins main thread via offset
# Reusable shellcode using fstring formats
def call_native_func(fnc_ptr, fnc_type, fnc_args):
    pm.inject_python_interpreter()
    fnc_adr = '0x' + format((pm.base_address + fnc_ptr), "08X")
    shell_code = """import ctypes
functype = ctypes.CFUNCTYPE({})
func = functype({})
func({})""".format(fnc_type, fnc_adr, fnc_args)
    pm.inject_python_shellcode(shell_code)


def check_cam_type():
    current_type = pm.read_bytes((GALE01 + CAM_TYPE), 1)
    if current_type != b'\x08':
        pm.write_bytes((GALE01 + CAM_TYPE), b'\x08', 1)


def find_spawned_players():
    player_states = {
        "P1": (GALE01 + PLAYER_ONE),
        "P2": (GALE01 + PLAYER_TWO),
        "P3": (GALE01 + PLAYER_THREE),
        "P4": (GALE01 + PLAYER_FOUR)
    }

    spawned_players = []

    for player, state_address in player_states.items():
        player_state = pm.read_bytes(state_address, 4)

        if player_state == b'\x00\x00\x00\x02':
            spawned_players.append(player)

    return spawned_players


def set_player_pos(self, context, spawned_players):
    player_objects = {
        'P1': bpy.data.objects['PLAYER_1'],
        'P2': bpy.data.objects['PLAYER_2'],
        'P3': bpy.data.objects['PLAYER_3'],
        'P4': bpy.data.objects['PLAYER_4']
    }

    player_addresses = {
        'P1': (GALE01 + PLAYER_ONE + 0x10),
        'P2': (GALE01 + PLAYER_TWO + 0x10),
        'P3': (GALE01 + PLAYER_THREE + 0x10),
        'P4': (GALE01 + PLAYER_FOUR + 0x10)
    }

    for player in spawned_players:
        obj = player_objects[player]
        loc = obj.matrix_world.translation
        player_bytes = pm.read_bytes(player_addresses[player], 12)
        loc.xzy = struct.unpack(">fff", player_bytes[:12])
        obj.hide_viewport = not bpy.context.scene.my_tool.is_sync_player

    context.view_layer.update()


# Define Camera and Origin
org = bpy.data.objects['Origin']
cam = bpy.data.objects['Camera']


def sync_blender_cam(addr):
    # Vector translation of object world matrix, change axis of orientation.
    org_loc = org.matrix_world.translation.xzy
    cam_loc = cam.matrix_world.translation.xzy

    org_loc[0] = org_loc[0]
    org_loc[2] = org_loc[2] * -1
    cam_loc[0] = cam_loc[0]
    cam_loc[2] = cam_loc[2] * -1

    # fov in mm, unsure of the true unit of measurement in melee.
    fov = (math.degrees(cam.data.angle))
    loc_data = [org_loc, cam_loc]

    # Pack matrix into big endian bytes. (">f")
    # Add fov data to the end of camera data.
    mat_bytes = b''.join(
        struct.pack(">f", c) for r in loc_data for c in r) + struct.pack(">f", fov)
    pm.write_bytes(addr, mat_bytes, len(mat_bytes))


# This is an artifact of previous revisions where it used Dolphins freelook matrix instead of Melee's camera.
# In Melee, characters will get culled if past the cameras view. Because of this, characters in freelook could
# seemingly disappear if this culling occurs.
#
# The downside of this, is losing the ability to roll the camera. Melee's camera is restricted to an orbit view setup,
# with no roll.
'''def sync_blender_cam_freelook():
    # viewrotation
    # inv_viewrotation
    # translation_vector
    # 3C5F470 - viewrotation[9]
    # 3C5F498 - inv_viewrotation[9]
    # 3C5F4C0 - translation_vector[3]

    cam = bpy.data.objects['Camera']
    cam_loc = cam.matrix_world.translation.xzy
    loc_data = [cam_loc]

    mat_bytes = b''
    for r in loc_data:
        for c in r:
            mat_bytes += struct.pack("<f", c)

    addr = 0x0000000003C5F4C0
    buf = mat_bytes
    dol.write_bytes(addr, buf, len(buf))


def sync_blender_cam_freelook_r():
    cam = bpy.data.objects['Camera']
    cam_rot = cam.matrix_world.to_quaternion().to_matrix()

    mat_bytes = b''
    for r in cam_rot:
        for c in r:
            mat_bytes += struct.pack("<f", c)

    addr = 0x0000000003C5F470
    buf = mat_bytes
    dol.write_bytes(addr, buf, len(buf))
'''


def sync_player_control(addr):
    if bpy.context.screen.is_animation_playing:
        anim_byte = 0
    else:
        anim_byte = 1
    buf = struct.pack(">b", anim_byte)
    pm.write_bytes(addr, buf, len(buf))


def save_state_oldest():
    fnc_type = 'ctypes.c_int'
    fnc_args = ''
    # Go to frame start.
    bpy.ops.screen.frame_jump(end=False)
    call_native_func(SAVE_STATE, fnc_type, fnc_args)


def load_state_last():
    fnc_type = 'ctypes.c_int'
    fnc_args = '1'
    # Go to frame start.
    bpy.ops.screen.frame_jump(end=False)
    call_native_func(LOAD_STATE, fnc_type, fnc_args)


def frame_step():
    fnc_type = 'ctypes.c_int'
    fnc_args = ''
    call_native_func(FRAME_STEP, fnc_type, fnc_args)


def take_screenshot():
    fnc_type = 'ctypes.c_int'
    fnc_args = ''
    call_native_func(SCREEN_SHOT, fnc_type, fnc_args)


def save_slot_state(slot):
    fnc_type = 'None, ctypes.c_int, ctypes.c_bool'
    fnc_args = '{}, False'.format(slot)
    # Go to frame start.
    bpy.ops.screen.frame_jump(end=False)
    call_native_func(SAVE_STATE_SLOT, fnc_type, fnc_args)


def load_slot_state(slot):
    fnc_type = 'None, ctypes.c_int, ctypes.c_bool'
    fnc_args = '{}, False'.format(slot)
    # Go to frame start.
    bpy.ops.screen.frame_jump(end=False)
    call_native_func(LOAD_STATE_SLOT, fnc_type, fnc_args)


def get_current_frame():
    frame_bytes = pm.read_bytes(CURRENT_FRAME, 4)
    frame = struct.unpack('>i', frame_bytes)
    # struct.unpack returns a tuple.
    # game start is -124, but the global timer will start at 1 for all scenes.
    frame = (frame[0] - 124)
    return frame


def get_directory_size(directory):
    total_size = 0

    for path, dirs, files in os.walk(directory):
        for file in files:
            file_path = os.path.join(path, file)
            total_size += os.path.getsize(file_path)

    return total_size


def get_slippi_path():
    cmd = 'wmic process where "name=\'Dolphin.exe\'" get ExecutablePath'
    proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
    output_bytes = proc.stdout.read()  # Read the output as bytes
    output_str = output_bytes.decode('utf-8')  # Decode bytes to string

    # Extract the path from the output
    path_start = output_str.find('C:\\')
    path_end = output_str.find('.exe') + 4  # Include the .exe extension
    path = output_str[path_start:path_end]
    path = path.replace('Dolphin.exe', 'User\\ScreenShots')
    return path


def get_player_data(port, flag, val):
    # Start here: 0x453080 + B0 -> points to addr -> 0x80D06320
    # from 0x80D06320 + 0x60
    # Omit the first byte by slicing the bytes string

    # Read pointer for where entity data is
    port = port + 0xB0
    ent_data_ptr = pm.read_bytes(GALE01 + port, 4)[1:]
    ent_data_ptr = int.from_bytes(ent_data_ptr, 'big')
    ent_data_start = GALE01 + ent_data_ptr
    char_data_ptr = pm.read_bytes(ent_data_start + flag, val)


def write_player_data(port, flag, byte):
    # Start here: 0x453080 + B0 -> points to addr -> 0x80D06320
    # from 0x80D06320 + 0x60
    # Omit the first byte by slicing the bytes string

    # Read pointer for where entity data is
    port = port + 0xB0
    ent_data_ptr = pm.read_bytes(GALE01 + port, 4)[1:]
    ent_data_ptr = int.from_bytes(ent_data_ptr, 'big')
    ent_data_start = GALE01 + ent_data_ptr
    byte = struct.pack(">b", byte)
    pm.write_bytes(ent_data_start + flag, byte, len(byte))


##################################################
#                   OPERATORS                    #
##################################################


def find_spawned_players():
    player_states = {
        "P1": (GALE01 + PLAYER_ONE),
        "P2": (GALE01 + PLAYER_TWO),
        "P3": (GALE01 + PLAYER_THREE),
        "P4": (GALE01 + PLAYER_FOUR)
    }

    spawned_players = []

    for player, state_address in player_states.items():
        player_state = pm.read_bytes(state_address, 4)

        if player_state == b'\x00\x00\x00\x02':
            spawned_players.append(player)

    return spawned_players


def set_player_pos():
    for player in spawned_players:
        obj = player_objects[player]
        loc = obj.matrix_world.translation
        player_bytes = pm.read_bytes(player_addresses[player], 12)
        loc.xzy = struct.unpack(">fff", player_bytes[:12])

    return 0


class menu_sync_camera(bpy.types.Operator):
    """A timer to writes to Dolphin's memory."""
    bl_idname = "wm.sync_cam"
    bl_label = "Sync Camera"
    _timer = None

    def modal(self, context, event):
        if event.type in {'Q'}:
            self.cancel(context)
            return {'CANCELLED'}

        if event.type == 'TIMER':
            sync_blender_cam((GALE01 + CAM_START))
            frame = get_current_frame()
            context.scene.my_tool.frame_number = frame

            if context.scene.my_tool.is_media_sync:
                sync_player_control((GALE01 + PAUSE_BIT))
        return {'PASS_THROUGH'}

    def execute(self, context):
        scene = context.scene
        check_cam_type()
        wm = context.window_manager
        self._start_time = time.time()
        self._timer = wm.event_timer_add(0, window=context.window)
        wm.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def cancel(self, context):
        wm = context.window_manager
        wm.event_timer_remove(self._timer)


def frame_adv():
    addr = GALE01 + FRAME_ADV
    byte = 0x1
    buf = struct.pack(">b", byte)
    pm.write_bytes(addr, buf, len(buf))


def img_seq(context):
    timeout_seconds = 2  # Adjust this timeout value as needed
    start_time = time.time()

    while True:
        is_lock = pm.read_bytes(SCREEN_LOCK, 1)
        time.sleep(0.01)

        if is_lock == b'\x00':
            take_screenshot()
            time.sleep(0.05)
            # frame_step()
            # Wait until is_lock becomes '\x01'
            while is_lock != b'\x01':
                is_lock = pm.read_bytes(SCREEN_LOCK, 1)
                time.sleep(0.01)
                # Check if timeout has been reached
                if time.time() - start_time > timeout_seconds:
                    print('Timeout reached while waiting for is_lock to become \x01')
                    break

            if is_lock == b'\x01':
                # Break out of the loop and continue with the rest of the code
                break
            else:
                print('3: Timed out waiting for is_lock to become \x01')
                break

    if is_freeze:
        bpy.ops.screen.frame_offset(delta=1)
    else:
        frame_adv()
        bpy.ops.screen.frame_offset(delta=1)


def prev_seq(context):
    # frame_step()
    bpy.ops.screen.frame_offset(delta=1)
    time.sleep(0.1)


class menu_img_sequence(bpy.types.Operator):
    """Creates an image sequence for the duration of the frame range."""
    bl_idname = "wm.ss_seq"
    bl_label = "Image Sequence"
    _timer = None

    def modal(self, context, event):
        scene = context.scene
        if event.type in {'SPACE'} or scene.frame_current > scene.frame_end - 1:
            self.cancel(context)
            return {'CANCELLED'}

        if event.type == 'TIMER':
            img_seq(context)
            # bpy.context.view_layer.update()
        return {'PASS_THROUGH'}

    def execute(self, context):
        scene = context.scene
        wm = context.window_manager
        self._timer = wm.event_timer_add(0, window=context.window)
        wm.modal_handler_add(self)
        load_state_last()
        time.sleep(0.1)
        scene.frame_set(scene.frame_start)
        return {'RUNNING_MODAL'}

    def cancel(self, context):
        wm = context.window_manager
        wm.event_timer_remove(self._timer)


class menu_quick_load(bpy.types.Operator):
    """Loads the last state saved."""
    bl_idname = "wm.quick_load"
    bl_label = "Quick Load"

    def execute(self, context):
        load_state_last()
        return {'FINISHED'}


class menu_quick_save(bpy.types.Operator):
    """Saves to the oldest state."""
    bl_idname = "wm.quick_save"
    bl_label = "Quick Save"

    def execute(self, context):
        save_state_oldest()
        return {'FINISHED'}


# State slots
def save_slot_operator(slot_number):
    class SaveSlotOperator(bpy.types.Operator):
        """Save State Slot"""
        bl_idname = f"wm.save_slot_{slot_number}"
        bl_label = f"{slot_number}"

        def execute(self, context):
            context.scene.my_tool.selected_slot = slot_number
            save_slot_state(slot_number)
            return {'FINISHED'}

    bpy.utils.register_class(SaveSlotOperator)
    return SaveSlotOperator


save_slots = []


def load_slot_operator(slot_number):
    class LoadSlotOperator(bpy.types.Operator):
        """Load State Slot"""
        bl_idname = f"wm.load_slot_{slot_number}"
        bl_label = f"{slot_number}"

        def execute(self, context):
            context.scene.my_tool.selected_slot = slot_number
            load_slot_state(slot_number)
            return {'FINISHED'}

    bpy.utils.register_class(LoadSlotOperator)
    return LoadSlotOperator


load_slots = []


class menu_img_preview(bpy.types.Operator):
    """Steps through the current frame range."""
    bl_idname = "wm.prev_seq"
    bl_label = "Preview Sequence"
    _timer = None

    def modal(self, context, event):
        scene = context.scene
        if event.type in {'SPACE'} or scene.frame_current > scene.frame_end - 1:
            self.cancel(context)
            return {'CANCELLED'}

        if event.type == 'TIMER':
            prev_seq(context)
            bpy.context.view_layer.update()
        return {'PASS_THROUGH'}

    def execute(self, context):
        scene = context.scene
        wm = context.window_manager
        self._timer = wm.event_timer_add(0, window=context.window)
        wm.modal_handler_add(self)
        # load_state_last()
        # time.sleep(0.5)
        scene.frame_set(scene.frame_start)
        return {'RUNNING_MODAL'}

    def cancel(self, context):
        wm = context.window_manager
        wm.event_timer_remove(self._timer)


class menu_current_frame(bpy.types.Operator):
    bl_idname = "wm.frame"
    bl_label = "Current Frame"
    is_running = False
    _timer = None

    def modal(self, context, event):
        if event.type == 'TIMER':
            frame = get_current_frame()
            context.scene.my_tool.frame_number = frame
        return {'PASS_THROUGH'}

    def execute(self, context):
        wm = context.window_manager
        self._timer = wm.event_timer_add(1, window=context.window)
        wm.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def cancel(self, context):
        wm = context.window_manager
        wm.event_timer_remove(self._timer)


op_classes = (
    menu_sync_camera,
    menu_quick_save,
    menu_quick_load,
    menu_img_sequence,
    menu_img_preview,
    menu_current_frame
)


##################################################
#                     PANEL                      #
##################################################


class control_properties(PropertyGroup):

    def update_sync_player(self, context):
        global player_objects
        global player_addresses
        player_objects = {
            'P1': bpy.data.objects['PLAYER_1'],
            'P2': bpy.data.objects['PLAYER_2'],
            'P3': bpy.data.objects['PLAYER_3'],
            'P4': bpy.data.objects['PLAYER_4']
        }

        player_addresses = {
            'P1': (GALE01 + PLAYER_ONE + 0x10),
            'P2': (GALE01 + PLAYER_TWO + 0x10),
            'P3': (GALE01 + PLAYER_THREE + 0x10),
            'P4': (GALE01 + PLAYER_FOUR + 0x10)
        }
        if self.is_sync_player:
            global spawned_players
            spawned_players = find_spawned_players()
            bpy.app.timers.register(set_player_pos)

            for player in spawned_players:
                obj = player_objects[player]
                obj.hide_viewport = not bpy.context.scene.my_tool.is_sync_player
        else:
            for player in player_objects:
                obj = player_objects[player]
                obj.hide_viewport = not bpy.context.scene.my_tool.is_sync_player

    def toggl_pause(self, context):
        addr = GALE01 + DEV_PAUSE
        value = self.sna_pause
        byte = 1 if value else 0
        buf = struct.pack(">b", byte)
        pm.write_bytes(addr, buf, len(buf))

    def toggl_hud(self, context):
        addr = GALE01 + GAME_HUD
        value = self.sna_hud
        byte = 1 if value else 0
        buf = struct.pack(">b", byte)
        pm.write_bytes(addr, buf, len(buf))

    def toggl_fx(self, context):
        addr = GALE01 + STAGE_FLAGS
        value = self.sna_fx
        byte = 0x10 if value else 0
        buf = struct.pack(">b", byte)
        pm.write_bytes(addr, buf, len(buf))

    def toggl_bg(self, context):
        addr = GALE01 + STAGE_FLAGS + 0x1
        value = self.sna_bg
        byte = 0x4 if value else 0
        buf = struct.pack(">b", byte)
        pm.write_bytes(addr, buf, len(buf))

    def toggl_stagevisprop(self, context):
        addr = GALE01 + STAGE_FLAGS + 0x1
        value = self.sna_stagevisprop
        byte = 0x10 if value else 0
        buf = struct.pack(">b", byte)
        pm.write_bytes(addr, buf, len(buf))

    def toggl_vis(self, context):
        addr = GALE01 + STAGE_FLAGS
        value = self.sna_vis
        byte = 0x80 if value else 0
        buf = struct.pack(">B", byte)
        print(hex(addr), value, byte)
        pm.write_bytes(addr, buf, len(buf))

    def toggl_colour(self, context):
        addr = GALE01 + BG_COLOUR
        colour_vector = self.sna_colour
        hex_colour = [int(value * 255) for value in colour_vector]
        colour_hex_list = [hex(value)[2:].zfill(2) for value in hex_colour]
        buf = struct.pack(">BBB", *hex_colour)
        pm.write_bytes(GALE01 + BG_COLOUR, buf, len(buf))

    # I am a mess
    def update_colls(self, context):
        player_addresses = {
            'P1': (PLAYER_ONE),
            'P2': (PLAYER_TWO),
            'P3': (PLAYER_THREE),
            'P4': (PLAYER_FOUR)
        }

        if self.sna_colbub:
            global spawned_players
            spawned_players = find_spawned_players()

            for player in spawned_players:
                if player in player_addresses:
                    write_player_data(player_addresses[player], 0x225C, 2)
        else:
            for player in spawned_players:
                if player in player_addresses:
                    write_player_data(player_addresses[player], 0x225C, 1)

    def player_1_update(self, context):
        selected_enum_value = self.sna_player_1

        if selected_enum_value == "VISIBLE":
            # Handle the Visible case
            write_player_data(PLAYER_ONE, 0x225C, 1)

        elif selected_enum_value == "HIDDEN":
            # Handle the Hidden case
            write_player_data(PLAYER_ONE, 0x225C, 0)

        elif selected_enum_value == "COLLISION":
            write_player_data(PLAYER_ONE, 0x225C, 2)
            # Handle the Collision case

        elif selected_enum_value == "OVERLAY":
            write_player_data(PLAYER_ONE, 0x225C, 3)
            # Handle the Overlay case

        else:
            # Handle the default case
            print("Unknown enum value")

    def player_2_update(self, context):
        selected_enum_value = self.sna_player_2

        if selected_enum_value == "VISIBLE":
            # Handle the Visible case
            write_player_data(PLAYER_TWO, 0x225C, 1)

        elif selected_enum_value == "HIDDEN":
            # Handle the Hidden case
            write_player_data(PLAYER_TWO, 0x225C, 0)

        elif selected_enum_value == "COLLISION":
            write_player_data(PLAYER_TWO, 0x225C, 2)
            # Handle the Collision case

        elif selected_enum_value == "OVERLAY":
            write_player_data(PLAYER_TWO, 0x225C, 3)
            # Handle the Overlay case

        else:
            # Handle the default case
            print("Unknown enum value")

    def player_3_update(self, context):
        selected_enum_value = self.sna_player_3

        if selected_enum_value == "VISIBLE":
            # Handle the Visible case
            write_player_data(PLAYER_THREE, 0x225C, 1)

        elif selected_enum_value == "HIDDEN":
            # Handle the Hidden case
            write_player_data(PLAYER_THREE, 0x225C, 0)

        elif selected_enum_value == "COLLISION":
            write_player_data(PLAYER_THREE, 0x225C, 2)
            # Handle the Collision case

        elif selected_enum_value == "OVERLAY":
            write_player_data(PLAYER_THREE, 0x225C, 3)
            # Handle the Overlay case

        else:
            # Handle the default case
            print("Unknown enum value")

    def player_4_update(self, context):
        selected_enum_value = self.sna_player_4

        if selected_enum_value == "VISIBLE":
            # Handle the Visible case
            write_player_data(PLAYER_FOUR, 0x225C, 1)

        elif selected_enum_value == "HIDDEN":
            # Handle the Hidden case
            write_player_data(PLAYER_FOUR, 0x225C, 0)

        elif selected_enum_value == "COLLISION":
            write_player_data(PLAYER_FOUR, 0x225C, 2)
            # Handle the Collision case

        elif selected_enum_value == "OVERLAY":
            write_player_data(PLAYER_FOUR, 0x225C, 3)
            # Handle the Overlay case

        else:
            # Handle the default case
            print("Unknown enum value")

    def seq_freeze(self, context):
        global is_freeze
        if self.sna_freeze:
            is_freeze = 1
        else:
            is_freeze = 0

    is_media_sync: BoolProperty(
        name="Media Controls",
        description="",
        default=False
    )

    is_sync_player: BoolProperty(
        name="Player Positions",
        description="",
        default=False,
        update=update_sync_player
    )

    selected_slot: IntProperty(
        default=1
    )

    frame_number: IntProperty(
        default=0,
    )

    sna_pause: BoolProperty(
        name="Freeze",
        description="",
        default=False,
        update=toggl_pause
    )

    sna_hud: BoolProperty(
        name="HUD",
        description="",
        default=False,
        update=toggl_hud
    )

    sna_fx: BoolProperty(
        name="Particles & FX",
        description="",
        default=False,
        update=toggl_fx
    )

    sna_bg: BoolProperty(
        name="Disable",
        description="",
        default=False,
        update=toggl_bg
    )

    sna_stagevisprop: BoolProperty(
        name="Disable",
        description="",
        default=False,
        update=toggl_stagevisprop
    )

    sna_colour: FloatVectorProperty(
        name="Disable",
        description="",
        subtype="COLOR",
        # default=False,
        update=toggl_colour
    )

    sna_vis: BoolProperty(
        name="Hide All",
        description="",
        default=False,
        update=toggl_vis
    )

    sna_colbub: BoolProperty(
        name="Collision Bubbles",
        description="",
        default=False,
        update=update_colls
    )

    sna_player_1: EnumProperty(
        name='Player 1',
        items=[
            ('VISIBLE', 'Visible', '', 0, 0),
            ('HIDDEN', 'Hidden', '', 0, 1),
            ('COLLISION', 'Collision', '', 0, 2),
            ('OVERLAY', 'Collision Overlay', '', 0, 3),
        ],
        description="",
        default=None,
        update=player_1_update
    )

    sna_player_2: EnumProperty(
        name='Player 2',
        items=[
            ('VISIBLE', 'Visible', '', 0, 0),
            ('HIDDEN', 'Hidden', '', 0, 1),
            ('COLLISION', 'Collision', '', 0, 2),
            ('OVERLAY', 'Collision Overlay', '', 0, 3),
        ],
        description="",
        default=None,
        update=player_2_update
    )

    sna_player_3: EnumProperty(
        name='Player 3',
        items=[
            ('Visible', 'Visible', '', 0, 0),
            ('Hidden', 'Hidden', '', 0, 1),
            ('Collision', 'Collision', '', 0, 2),
            ('Collision Overlay', 'Collision Overlay', '', 0, 3),
        ],
        description="",
        default=None,
        update=player_3_update
    )

    sna_player_4: EnumProperty(
        name='Player 4',
        items=[
            ('Visible', 'Visible', '', 0, 0),
            ('Hidden', 'Hidden', '', 0, 1),
            ('Collision', 'Collision', '', 0, 2),
            ('Collision Overlay', 'Collision Overlay', '', 0, 3),
        ],
        description="",
        default=None,
        update=player_4_update
    )

    sna_freeze: BoolProperty(
        name="Toggle Freeze",
        description="",
        default=False,
        update=seq_freeze
    )


GALE01 = None
pm = None
is_on = False


def check_exists():
    try:
        pymem.Pymem("Dolphin.exe")
        return True
    except pymem.exception.ProcessNotFound:
        return False


# Finds 'GALE01' in memory.
# This is used to jump to specific functions in Melee ie: GALE01 + CAM_START
def find_gale01(dol):
    handle = dol.process_handle
    byte_pattern = bytes.fromhex("47 41 4C 45 30 31 00 02")
    found = pattern_scan_all(handle, byte_pattern)
    return found


class emc_control_panel(Panel):
    bl_label = 'External Melee Camera'
    bl_idname = 'OBJECT_PT_external_melee_camera'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Melee Control Panel'
    bl_context = 'objectmode'
    last_check_time = 0
    check_interval = 2  # Check every 2 seconds

    def draw(self, context):
        global is_on
        global pm
        global GALE01
        layout = self.layout
        mytool = context.scene.my_tool
        exist = check_exists()
        # Grey out the add-on functions if Dolphin isn't open
        if not exist:
            row = layout.row()
            row.scale_y = 2.0
            row.label(text="Slippi Dolphin is not running!", icon='ERROR')
            is_on = False
            GALE01 = None

        elif exist and GALE01 is None:
            row = layout.row()
            row.scale_y = 2.0
            row.label(text="Waiting for Melee!", icon='ERROR')
            is_on = False
            pm = pymem.Pymem("Dolphin.exe")
            GALE01 = find_gale01(pm)
            set_global_vars(pm)

        elif GALE01 is not None:
            is_on = True

        # Sync Camera
        cam_box = layout.box()
        cam_box.enabled = is_on
        cam_row1 = cam_box.row()
        cam_row1.scale_y = 2

        # Create the operator button
        cam_row1.operator("wm.sync_cam", icon_value=71)

        cam_row2 = cam_box.row()
        cam_row2.alignment = 'Center'.upper()
        cam_row2.prop(mytool, 'is_media_sync')
        cam_row2.prop(mytool, 'is_sync_player')
        layout.separator()

        # Frame Display
        cam_box.alignment = 'Expand'.upper()
        frame_row = cam_box.row()
        frame_row.alignment = 'Center'.upper()
        frame_row.label(text=f'Frame: {context.scene.my_tool.frame_number}')

        # Quick Save/Load
        quick_state_box = layout.box()
        quick_state_box.enabled = is_on
        quick_state_box.operator('wm.quick_save')
        quick_state_box.operator('wm.quick_load')
        layout.separator()

        # Image Sequence
        seq_box = layout.box()
        seq_box.alert = False
        seq_box.enabled = True
        seq_box.active = True
        seq_box.use_property_split = False
        seq_box.use_property_decorate = False
        seq_box.alignment = 'Center'.upper()
        seq_box.scale_x = 1.0
        seq_box.scale_y = 1.0
        if not True: seq_box.operator_context = "EXEC_DEFAULT"
        seq_row1 = seq_box.row(heading='', align=False)
        seq_row1.alert = False
        seq_row1.enabled = True
        seq_row1.active = True
        seq_row1.use_property_split = False
        seq_row1.use_property_decorate = False
        seq_row1.scale_x = 1.0
        seq_row1.scale_y = 1.0
        seq_row1.alignment = 'Expand'.upper()
        if not True: seq_row1.operator_context = "EXEC_DEFAULT"
        seq_row1.label(text='Sequencer', icon_value=157)
        seq_row2 = seq_box.row(heading='', align=True)
        seq_row2.alert = False
        seq_row2.enabled = True
        seq_row2.active = True
        seq_row2.use_property_split = False
        seq_row2.use_property_decorate = False
        seq_row2.scale_x = 1.0
        seq_row2.scale_y = 1.0
        seq_row2.alignment = 'Expand'.upper()
        if not True: seq_row2.operator_context = "EXEC_DEFAULT"
        seq_row2.operator('wm.ss_seq')
        seq_row3 = seq_row2.row(heading='', align=True)
        seq_row3.alert = False
        seq_row3.enabled = True
        seq_row3.active = False
        seq_row3.use_property_split = False
        seq_row3.use_property_decorate = False
        seq_row3.scale_x = 1.0
        seq_row3.scale_y = 1.0
        seq_row3.alignment = 'Expand'.upper()
        if not True: seq_row3.operator_context = "EXEC_DEFAULT"
        seq_row3.prop(mytool, 'sna_freeze', text='', icon_value=66, emboss=True)
        seq_box.operator('wm.prev_seq')
        layout.separator()


class state_panel(Panel):
    bl_label = 'Dolphin States'
    bl_idname = 'OBJECT_PT_state_panel'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_context = ''
    bl_order = 0
    bl_parent_id = 'OBJECT_PT_external_melee_camera'

    @classmethod
    def poll(cls, context):
        return not (False)

    def draw_header(self, context):
        layout = self.layout

    def draw(self, context):
        layout = self.layout
        exist = check_exists()
        # Grey out the add-on functions if Dolphin isn't open
        if not exist:
            layout.enabled = False
        else:
            layout.enabled = True
        state_split = layout.split(factor=0.5, align=False)
        state_split.alignment = 'Center'.upper()

        state_box1 = state_split.box()
        state_box1.alignment = 'Center'.upper()
        state_box1.label(text='Save States', icon_value=706)

        state_col1 = state_box1.column()
        state_col1.alignment = 'Center'.upper()
        state_row1 = state_col1.row()
        state_row1.alignment = 'Center'.upper()
        # First row of save states
        for save_slot in save_slots[0:3]:
            state_row1.operator(save_slot.bl_idname, text=save_slot.bl_label)

        state_col1.separator(factor=0.75)

        state_row2 = state_col1.row()
        state_row2.alignment = 'Center'.upper()
        # Second row of save states
        for save_slot in save_slots[3:7]:
            state_row2.operator(save_slot.bl_idname, text=save_slot.bl_label)

        state_col1.separator(factor=0.75)

        state_box2 = state_split.box()
        state_box2.alignment = 'Center'.upper()
        state_box2.label(text='Load States', icon_value=707)
        state_col2 = state_box2.column()
        state_col2.alignment = 'Center'.upper()
        state_row3 = state_col2.row()
        state_row3.alignment = 'Center'.upper()

        # First row of load states
        for load_slot in load_slots[0:3]:
            state_row3.operator(load_slot.bl_idname, text=load_slot.bl_label)

        state_col2.separator(factor=0.75)

        state_row4 = state_col2.row()
        state_row4.alignment = 'Center'.upper()
        # Second row of load states
        for load_slot in load_slots[3:7]:
            state_row4.operator(load_slot.bl_idname, text=load_slot.bl_label)

        state_col2.separator(factor=0.75)


class melee_properties_panel(bpy.types.Panel):
    bl_label = 'Melee Properties Manager'
    bl_idname = 'OBJECT_PT_melee_properties_panel'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_context = ''
    bl_order = 0
    bl_parent_id = 'OBJECT_PT_external_melee_camera'

    @classmethod
    def poll(cls, context):
        return not (False)

    def draw_header(self, context):
        layout = self.layout

    def draw(self, context):
        # probably should huck spawned_players into check_exists
        exist = check_exists()
        layout = self.layout
        if not exist:
            layout.enabled = False
        else:
            layout.enabled = True
        mytool = context.scene.my_tool
        prop_box = layout.box()
        prop_box.alignment = 'Expand'.upper()
        prop_box.scale_x = 1.0
        prop_box.scale_y = 1.0
        if not False: prop_box.operator_context = "EXEC_DEFAULT"
        prop_box.label(text='In-Game Toggles', icon_value=117)
        prop_column = prop_box.column(heading='', align=False)
        prop_column.scale_x = 1.0
        prop_column.scale_y = 1.0
        prop_column.alignment = 'Center'.upper()
        if not True: prop_column.operator_context = "EXEC_DEFAULT"
        toggle_row = prop_column.row(heading='', align=False)
        toggle_row.scale_x = 1.0
        toggle_row.scale_y = 1.8
        toggle_row.alignment = 'Expand'.upper()
        if not True: toggle_row.operator_context = "EXEC_DEFAULT"
        toggle_row.prop(mytool, 'sna_pause', icon_value=498)
        toggle_row.prop(mytool, 'sna_hud', text='HUD', icon_value=760)
        toggle_row.prop(mytool, 'sna_fx', text='Particles & FX', icon_value=93)
        prop_column.separator(factor=2.0)
        prop_column.label(text='Stage:', icon_value=755)
        stage_row = prop_column.row(heading='', align=False)
        stage_row.scale_x = 1.0
        stage_row.scale_y = 1.8
        stage_row.alignment = 'Expand'.upper()
        if not True: stage_row.operator_context = "EXEC_DEFAULT"
        stage_row.prop(mytool, 'sna_bg', text='Disable', icon_value=68, emboss=True, toggle=True)
        stage_row.prop(mytool, 'sna_stagevisprop', text='Visuals', icon_value=638, emboss=True)
        bg_colour_grid = prop_column.grid_flow(columns=2, row_major=False, even_columns=False, even_rows=False,
                                               align=False)
        bg_colour_grid.alignment = 'Expand'.upper()
        bg_colour_grid.scale_x = 1.0
        bg_colour_grid.scale_y = 1.0
        if not True: bg_colour_grid.operator_context = "EXEC_DEFAULT"
        bg_colour_grid.label(text='Background Colour', icon_value=0)
        bg_colour_grid.prop(mytool, 'sna_colour', text='', icon_value=0, emboss=True)
        prop_column.separator(factor=2.0)
        prop_column.label(text='Characters', icon_value=173)
        row = prop_column.row(heading='', align=False)
        row.scale_x = 1.0
        row.scale_y = 1.8
        row.alignment = 'Expand'.upper()
        if not True: row.operator_context = "EXEC_DEFAULT"
        row.prop(mytool, 'sna_vis', text='Hide All', icon_value=257, emboss=True, toggle=True)
        row.prop(mytool, 'sna_colbub', text='Collision Bubbles', icon_value=467, emboss=True, toggle=True)
        prop_column.separator(factor=0.75)
        player_row = prop_column.row(heading='', align=False)
        player_row.alignment = 'Expand'.upper()
        if not True: player_row.operator_context = "EXEC_DEFAULT"
        player_row.prop(mytool, 'sna_player_1', text='', icon_value=231, emboss=True)
        player_row.prop(mytool, 'sna_player_2', text='', icon_value=231, emboss=True)
        player_row.prop(mytool, 'sna_player_3', text='', icon_value=231, emboss=True)
        player_row.prop(mytool, 'sna_player_4', text='', icon_value=231, emboss=True)


panel_classes = (
    control_properties,
    emc_control_panel,
    state_panel,
    melee_properties_panel,
)


def register():
    for cls in panel_classes:
        register_class(cls)
    for cls in op_classes:
        register_class(cls)
    bpy.types.Scene.my_tool = PointerProperty(type=control_properties)

    ####
    for slot_number in range(1, 7):
        save_slot = save_slot_operator(slot_number)
        save_slots.append(save_slot)

    for slot_number in range(1, 7):
        load_slot = load_slot_operator(slot_number)
        load_slots.append(load_slot)


def unregister():
    for cls in reversed(panel_classes):
        unregister_class(cls)
    for cls in reversed(op_classes):
        unregister_class(cls)
    del bpy.types.Scene.my_tool

    ####
    for save_slot in save_slots:
        bpy.utils.unregister_class(save_slot)
    save_slots.clear()

    for load_slot in load_slots:
        bpy.utils.unregister_class(load_slot)
    load_slots.clear()


if __name__ == "__main__":
    register()
