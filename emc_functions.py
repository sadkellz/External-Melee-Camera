import ctypes
import math
import struct
import time
import bpy
from . emc_common import *


def sync_blender_cam():
    # Define Camera and Origin
    org = bpy.data.objects['Origin']
    cam = bpy.data.objects['Camera']

    # Vector translation of object world matrix, change axis of orientation.
    org_loc = org.matrix_world.translation.yzx
    cam_loc = cam.matrix_world.translation.yzx
    # Negate y and x to align with melee's look at -x.
    org_loc[0] = org_loc[0] * -1
    org_loc[2] = org_loc[2] * -1
    cam_loc[0] = cam_loc[0] * -1
    cam_loc[2] = cam_loc[2] * -1
    # fov in mm, unsure of the true unit of measurement in melee.
    fov = (math.degrees(cam.data.angle))
    loc_data = [org_loc, cam_loc]

    # Pack matrix into big endian bytes. (">f")
    mat_bytes = b''
    for r in loc_data:
        for c in r:
            mat_bytes += struct.pack(">f", c)

    # Add fov data to the end of camera data.
    mat_bytes += struct.pack(">f", fov)
    addr = 0x0000000080443040
    buf = mat_bytes
    pm.write_bytes(addr, buf, len(buf))


def sync_blender_cam_freelook():
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


def sync_player_control():
    if bpy.context.screen.is_animation_playing:
        anim_byte = 0
    else:
        anim_byte = 1
    # Frame advance boolean in memory.
    addr = 0x0000000080469D68
    buf = struct.pack(">b", anim_byte)
    pm.write_bytes(addr, buf, len(buf))


def save_state():
    fnc_type = 'ctypes.c_int'
    fnc_args = ''
    # Go to frame start.
    bpy.ops.screen.frame_jump(end=False)
    call_native_func(SaveState, fnc_type, fnc_args)


def load_state():
    fnc_type = 'ctypes.c_int'
    fnc_args = ''
    # Go to frame start.
    bpy.ops.screen.frame_jump(end=False)
    call_native_func(LoadState, fnc_type, fnc_args)


def take_screenshot():
    fnc_type = 'ctypes.c_int, ctypes.c_bool'
    fnc_args = '1, False'
    call_native_func(ScreenShot, fnc_type, fnc_args)


def frame_step():
    fnc_type = 'ctypes.c_int'
    fnc_args = ''
    call_native_func(FrameStep, fnc_type, fnc_args)
