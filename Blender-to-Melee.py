import bpy
import struct
from ctypes import *
from ctypes.wintypes import *
from bpy.props import BoolProperty
from mathutils import Vector

class Melee_Dev_Cam_ControlPanel(bpy.types.Panel):
    bl_label = "Blender Camera to Melee"
    bl_idname = "OBJECT_PT_dolphinfreelook"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'

    def draw(self, context):
        layout = self.layout
    
        layout.row().label(text="Camera in Memory:")
        # Always 0000XXXX 0000000080443040 where X = PID, seems like you could be able to change this.
        layout.row().prop(context.scene, "cam_mem_address")
        layout.row().prop(context.scene, "player_toggle")
        layout.separator(factor=2)
        layout.row().operator("wm.start_consistent_matrix_sender_operator")
        layout.row().label(text="Press Q to quit going live.")

def blender_to_dolphin():
    # Define Camera and Origin
    cam = bpy.data.objects['Camera']
    org = bpy.data.objects['Origin']

    # Change Axis Orientation
    org_loc = org.location.xzy
    cam_loc = cam.location.xzy
    org_loc[0] = cam_loc[0] * -1
    cam_loc[0] = cam_loc[0] * -1

    # fov in mm, unsure of the true unit of measurement in melee.
    fov = cam.data.lens
    
    # List object vector data
    loc_data = [org_loc, cam_loc]
    
    # Pack list into big endian bytes. (">f")
    mat_bytes = b''
    
    for r in loc_data:
        for c in r:
            mat_bytes += struct.pack(">f", c)
    
    # Add fov data to struct.pack
    mat_bytes += struct.pack(">f", fov)
    
    OpenProcess = windll.kernel32.OpenProcess
    WriteProcessMemory = windll.kernel32.WriteProcessMemory
    CloseHandle = windll.kernel32.CloseHandle

    WriteProcessMemory.argtypes = [HANDLE,LPCVOID,LPVOID,c_size_t,POINTER(c_size_t)]

    PROCESS_ALL_ACCESS = 0x1F0FFF

    # The location in memory where Melee's developer camera begins.
    DevCamAddress = bpy.context.scene.cam_mem_address
    pid = int(DevCamAddress[:8], 16)
    address = int(DevCamAddress[8:], 16)

    bufferSize = len(mat_bytes)
    buffer = c_char_p(mat_bytes)
    bytesWritten = c_ulonglong()

    processHandle = OpenProcess(PROCESS_ALL_ACCESS, False, pid)
    WriteProcessMemory(processHandle, address, buffer, bufferSize, byref(bytesWritten))

    CloseHandle(processHandle)
    
'''def sync_player_control():
    anim = 1
    anim_byte = b''
    anim_byte += struct.pack("b", anim)

    OpenProcess = windll.kernel32.OpenProcess
    WriteProcessMemory = windll.kernel32.WriteProcessMemory
    CloseHandle = windll.kernel32.CloseHandle

    WriteProcessMemory.argtypes = [HANDLE,LPCVOID,LPVOID,c_size_t,POINTER(c_size_t)]

    PROCESS_ALL_ACCESS = 0x1F0FFF

    DevCamAddress = bpy.context.scene.cam_mem_address
    pid = int(DevCamAddress[:8], 16)
    address = int("0000000080479D68", 16)
    bufferSize = len(anim_byte)
    buffer = c_char_p(anim_byte)
    bytesWritten = c_ulonglong()

    processHandle = OpenProcess(PROCESS_ALL_ACCESS, False, pid)
    WriteProcessMemory(processHandle, address, buffer, bufferSize, byref(bytesWritten))

    CloseHandle(processHandle)

def check_anim_state():
    # Check if animation is playing.
    if bpy.context.screen.is_animation_playing:
        anim = 1
    else:
        anim = 0
    return anim
'''
class ConsistentMatrixSender(bpy.types.Operator):
    """Fires up the interval to consistently write to memory"""
    bl_idname = "wm.start_consistent_matrix_sender_operator"
    bl_label = "Go Live!"

    _timer = None

    @classmethod
    def poll(cls, context):
        return len(context.scene.cam_mem_address) == 24

    def modal(self, context, event):
        if event.type in {'Q'}:
            self.cancel(context)
            return {'CANCELLED'}

        if event.type == 'TIMER':
            blender_to_dolphin()
        return {'PASS_THROUGH'}

    def execute(self, context):
        wm = context.window_manager
        self._timer = wm.event_timer_add(0.05, window=context.window)
        wm.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def cancel(self, context):
        wm = context.window_manager
        wm.event_timer_remove(self._timer)

def register():
    bpy.utils.register_class(ConsistentMatrixSender)
    bpy.utils.register_class(Melee_Dev_Cam_ControlPanel)
    
    bpy.types.Scene.player_toggle = bpy.props.BoolProperty(
        name="Sync Media Controls?",
        default= False)

    bpy.types.Scene.cam_mem_address = bpy.props.StringProperty(name="")

def unregister():
    bpy.utils.unregister_class(ConsistentMatrixSender)

if __name__ == "__main__":
    register()