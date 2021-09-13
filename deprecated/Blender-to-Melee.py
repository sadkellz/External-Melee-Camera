import bpy
import struct
from ctypes import *
from ctypes.wintypes import *
#from bpy import context
#from mathutils import Vector
from bpy.props import BoolProperty

        # Toggle Function...
bpy.types.WindowManager.my_operator_toggle = bpy.props.BoolProperty()

class Melee_Dev_Cam_ControlPanel(bpy.types.Panel):
    bl_label = "Blender Camera to Melee"
    bl_idname = "OBJECT_PT_dolphinfreelook"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    def draw(self, context):
        wm = context.window_manager
        label = "Sync Media Controls" if wm.my_operator_toggle else "Sync Media Controls"
        layout = self.layout
        layout.row().label(text="Camera in Memory:")
            # Always 0000XXXX 0000000080443040 where X = PID, seems like you could be able to change this.
            # A more elegant solution is a must
        layout.row().prop(context.scene, "cam_mem_address")
        layout.prop(wm, 'my_operator_toggle', text=label, toggle=True)
        layout.separator(factor=2)
        layout.row().operator("wm.start_consistent_matrix_sender_operator")
        layout.row().label(text="Press Q to quit going live.")

        # Toggle Function...
def update_function(self, context):
    if self.my_operator_toggle:
        bpy.ops.sync.mc('INVOKE_DEFAULT')
    return

        # Toggle Function...
bpy.types.WindowManager.my_operator_toggle = bpy.props.BoolProperty(
                                                 default = False,
                                                 update = update_function)

        # ctypes k32 memory bullshit put into a function, so you can write to multiple addresses. https://docs.microsoft.com/en-us/windows/win32/api/memoryapi/nf-memoryapi-writeprocessmemory
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

        # Vector translation of object world matrix, change axis of orientation.
    org_loc = org.matrix_world.translation.yzx
    cam_loc = cam.matrix_world.translation.yzx
    
        # Negate y and x to align with melee's look at -x.
    org_loc[0] = org_loc[0] * -1
    org_loc[2] = org_loc[2] * -1
    cam_loc[0] = cam_loc[0] * -1
    cam_loc[2] = cam_loc[2] * -1

        # fov in mm, unsure of the true unit of measurement in melee.
    fov = cam.data.lens
        # List object vector data
    loc_data = [org_loc, cam_loc]
        # Pack list into big endian bytes. (">f")
    mat_bytes = b''
    for r in loc_data:
        for c in r:
            mat_bytes += struct.pack(">f", c)

        # Add fov data to to end of camera data.
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

        # Definitions for process_ops
    DevCamAddress = bpy.context.scene.cam_mem_address
    pid = int(DevCamAddress[:8], 16)
        # Address of where data will be written
    addr = 0x0000000080469D68
    buf = struct.pack(">b", anim_byte)
    bufSize = buf
    bytesWritten = c_ulonglong()
    process_ops(pid, addr, buf, bufSize, bytesWritten)   

        # Timer which defines how often data will be written to Dolphin.
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
        # 0.05 seems to be a good in-between for fps/performance.
        self._timer = wm.event_timer_add(0.05, window=context.window)
        wm.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def cancel(self, context):
        wm = context.window_manager
        wm.event_timer_remove(self._timer)

        # Sync Blender media controls. Sync is done by connecting frame advance on/off from melee, to the function that checks if an animation is playing (Blender).
class Sync_Media_Controls(bpy.types.Operator):
    bl_idname = "sync.mc"
    bl_label = "Sync Media Controls"

    def modal(self, context, event):
        if not context.window_manager.my_operator_toggle:
            context.window_manager.event_timer_remove(self._timer)
            return {'FINISHED'}

        if event.type == 'TIMER':
            sync_player_control()
        return {'PASS_THROUGH'}

    def invoke(self, context, event):
        wm = context.window_manager
        # This timer does not need to be fast.
        self._timer = wm.event_timer_add(1.0, window=context.window)
        wm.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def cancel(self, context):
        wm = context.window_manager
        wm.event_timer_remove(self._timer)

def register():
    bpy.utils.register_class(ConsistentMatrixSender)
    bpy.utils.register_class(Sync_Media_Controls)
    bpy.utils.register_class(Melee_Dev_Cam_ControlPanel)
    bpy.types.Scene.cam_mem_address = bpy.props.StringProperty(name="")

def unregister():
    bpy.utils.unregister_class(ConsistentMatrixSender)
    bpy.utils.register_class(Sync_Media_Controls)

if __name__ == "__main__":
    register()