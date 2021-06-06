import bpy
import struct
from ctypes import *
from ctypes.wintypes import *
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
        layout.row().operator("wm.sync_player_operator")
        layout.separator(factor=2)
        layout.row().operator("wm.start_consistent_matrix_sender_operator")
        layout.row().label(text="Press Q to quit going live.")

def process_ops(pid, addr, buf, bufSize, bytesWritten):
    k32 = WinDLL('kernel32', use_last_error=True)
    PROCESS_ALL_ACCESS = 0x1F0FFF
    
    OpenProcess = k32.OpenProcess
    OpenProcess.argtypes = [DWORD,BOOL,DWORD]
    OpenProcess.restype = HANDLE

    processHandle = OpenProcess(PROCESS_ALL_ACCESS, False, pid)

    CloseHandle = k32.CloseHandle
    CloseHandle.argtypes = [HANDLE]
    CloseHandle.restype = BOOL

    WriteProcessMemory = k32.WriteProcessMemory
    WriteProcessMemory.argtypes = [HANDLE,LPCVOID,LPVOID,c_size_t,POINTER(c_size_t)]
    WriteProcessMemory.restype = BOOL
    WriteProcessMemory(processHandle, addr, c_char_p(buf), len(bufSize), byref(bytesWritten))
    
    CloseHandle(processHandle)

def sync_blender_cam():
        # Define Camera and Origin
    org = bpy.data.objects['Origin']
    cam = bpy.data.objects['Camera']

        # Change Axis Orientation
    org_loc = org.location.xzy
    cam_loc = cam.location.xzy
    org_loc[0] = org_loc[0] * -1
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
    
        # The location in memory where Melee's developer camera begins.
    DevCamAddress = bpy.context.scene.cam_mem_address
        # pid is the first 8 characters of UI
    pid = int(DevCamAddress[:8], 16)
        # addr is the last 16 characters of UI
    addr = int(DevCamAddress[8:], 16)
    buf = mat_bytes
    bufSize = mat_bytes
    bytesWritten = c_ulonglong()
    process_ops(pid, addr, buf, bufSize, bytesWritten)

def sync_player_control():
        # Check if animation is playing.
    if bpy.context.screen.is_animation_playing:
        anim_byte = 0
    else:
        anim_byte = 1

    DevCamAddress = bpy.context.scene.cam_mem_address
    pid = int(DevCamAddress[:8], 16)
    addr = 0x0000000080469D68
    buf = struct.pack(">b", anim_byte)
    bytesWritten = c_ulonglong()
    process_ops(pid, addr, buf, bytesWritten)   

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
            sync_blender_cam()
        return {'PASS_THROUGH'}

    def execute(self, context):
        wm = context.window_manager
        self._timer = wm.event_timer_add(0.05, window=context.window)
        wm.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def cancel(self, context):
        wm = context.window_manager
        wm.event_timer_remove(self._timer)

class Sync_Toggle_Options(bpy.types.Operator):
    """test"""
    bl_idname = "wm.sync_player_operator"
    bl_label = "Sync Media Controls?"

    _timer = None

    @classmethod
    def poll(cls, context):
        return bool(context.scene.player_toggle) == True

    def modal(self, context, event):
        if event.type in {'Q'}:
            self.cancel(context)
            return {'CANCELLED'}

        if event.type == 'TIMER':
            sync_player_control()
        return {'PASS_THROUGH'}

    def execute(self, context):
        wm = context.window_manager
        self._timer = wm.event_timer_add(0.1, window=context.window)
        wm.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def cancel(self, context):
        wm = context.window_manager
        wm.event_timer_remove(self._timer)

def register():
    bpy.utils.register_class(ConsistentMatrixSender)
    bpy.utils.register_class(Sync_Toggle_Options)
    bpy.utils.register_class(Melee_Dev_Cam_ControlPanel)
    bpy.types.Scene.cam_mem_address = bpy.props.StringProperty(name="")

def unregister():
    bpy.utils.unregister_class(ConsistentMatrixSender)
    bpy.utils.register_class(Sync_Toggle_Options)

if __name__ == "__main__":
    register()