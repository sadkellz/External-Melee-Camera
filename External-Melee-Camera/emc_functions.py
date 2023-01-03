import bpy
import math
import struct
from .emc_common import pm, GALE01, SAVE_STATE, \
    LOAD_STATE, SCREEN_SHOT, FRAME_STEP, CAM_TYPE, \
    PLAYER_ONE, PLAYER_TWO, PLAYER_THREE, PLAYER_FOUR,\
    LOAD_STATE_SLOT, SAVE_STATE_SLOT, CURRENT_FRAME


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
    current_type = pm.read_int(GALE01 + CAM_TYPE)
    if current_type != int(8):
        pm.write_int(GALE01 + CAM_TYPE, 8)

def set_player_pos():
    P1 = bpy.data.objects['PLAYER_1']
    P2 = bpy.data.objects['PLAYER_2']
    P3 = bpy.data.objects['PLAYER_3']
    P4 = bpy.data.objects['PLAYER_4']

    p1_loc = P1.matrix_world.translation
    p2_loc = P2.matrix_world.translation
    p3_loc = P3.matrix_world.translation
    p4_loc = P4.matrix_world.translation

    P1_BYTES = pm.read_bytes(GALE01 + PLAYER_ONE, 12)
    P2_BYTES = pm.read_bytes(GALE01 + PLAYER_TWO, 12)
    P3_BYTES = pm.read_bytes(GALE01 + PLAYER_THREE, 12)
    P4_BYTES = pm.read_bytes(GALE01 + PLAYER_FOUR, 12)

    p1_loc.xzy = struct.unpack(">fff", P1_BYTES)
    p2_loc.xzy = struct.unpack(">fff", P2_BYTES)
    p3_loc.xzy = struct.unpack(">fff", P3_BYTES)
    p4_loc.xzy = struct.unpack(">fff", P4_BYTES)

def sync_blender_cam(addr):
    # Define Camera and Origin
    org = bpy.data.objects['Origin']
    cam = bpy.data.objects['Camera']

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
    mat_bytes = b''
    for r in loc_data:
        for c in r:
            mat_bytes += struct.pack(">f", c)
    # Check if camera type is 'Dev'
    check_cam_type()
    # Add fov data to the end of camera data.
    mat_bytes += struct.pack(">f", fov)
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
    pm.write_bytes(addr, buf, len(buf))


def sync_blender_cam_freelook_r():
    cam = bpy.data.objects['Camera']
    cam_rot = cam.matrix_world.to_quaternion().to_matrix()

    mat_bytes = b''
    for r in cam_rot:
        for c in r:
            mat_bytes += struct.pack("<f", c)

    addr = 0x0000000003C5F470
    buf = mat_bytes
    pm.write_bytes(addr, buf, len(buf))
'''


def sync_player_control(addr):
    if bpy.context.screen.is_animation_playing:
        anim_byte = 0
    else:
        anim_byte = 1
    buf = struct.pack(">b", anim_byte)
    pm.write_bytes(addr, buf, len(buf))


def save_state():
    fnc_type = 'ctypes.c_int'
    fnc_args = ''
    # Go to frame start.
    bpy.ops.screen.frame_jump(end=False)
    call_native_func(SAVE_STATE, fnc_type, fnc_args)


def load_state():
    fnc_type = 'ctypes.c_int'
    fnc_args = '1'
    # Go to frame start.
    bpy.ops.screen.frame_jump(end=False)
    call_native_func(LOAD_STATE, fnc_type, fnc_args)


def take_screenshot():
    fnc_type = 'ctypes.c_int'
    fnc_args = ''
    call_native_func(SCREEN_SHOT, fnc_type, fnc_args)


def frame_step():
    fnc_type = 'ctypes.c_int'
    fnc_args = ''
    call_native_func(FRAME_STEP, fnc_type, fnc_args)


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