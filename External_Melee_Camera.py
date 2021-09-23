import math
import struct
import time
from pywinauto import Application
from ctypes import *
from ctypes.wintypes import *
from pathlib import Path
import psutil
# ------------------
import bpy
from bpy.props import (EnumProperty, BoolProperty,PointerProperty,)
from bpy.types import (Panel, PropertyGroup,)
# ------------------------------------------------------------------------
#    Functions
# ------------------------------------------------------------------------ 

        # ctypes k32 memory bullshit put into a function, so you can repurpose for multiple functions.
        # https://docs.microsoft.com/en-us/windows/win32/api/memoryapi/nf-memoryapi-writeprocessmemory
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

def dol_pid():
        # psutil to automatically grab Dolphins PID.
    process_name = "Slippi Dolphin"
    pid = None

    for proc in psutil.process_iter():
        if process_name in proc.name():
            pid = proc.pid
    return pid

def util_dol():
    pid = dol_pid()
    app = Application(backend="uia").connect(process=pid)
    dlg = app['Faster Melee - Slippi(2.3.6) - Playback']
        # Changes focus and sends key.
    return dlg

def sync_blender_cam(pid):
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
        # List object vector data
    loc_data = [org_loc, cam_loc]
        # Pack matrix into big endian bytes. (">f")
    mat_bytes = b''
    for r in loc_data:
        for c in r:
            mat_bytes += struct.pack(">f", c)
        # Add fov data to to end of camera data.
    mat_bytes += struct.pack(">f", fov)
    addr = 0x0000000080443040
    buf = mat_bytes
    bufSize = mat_bytes
    bytesWritten = c_ulonglong()
    process_ops(pid, addr, buf, bufSize, bytesWritten)

def sync_player_control(pid):
        # Check if animation is playing.
    if bpy.context.screen.is_animation_playing:
        anim_byte = 0
    else:
        anim_byte = 1
        # Location of frame advance boolean in memory.
    addr = 0x0000000080469D68
    buf = struct.pack(">b", anim_byte)
    bufSize = buf
    bytesWritten = c_ulonglong()
    process_ops(pid, addr, buf, bufSize, bytesWritten)   

# ------------------------------------------------------------------------
#    Operators
# ------------------------------------------------------------------------

class Sync_Cam_Pos(bpy.types.Operator):
    """A Timer that consistently writes to Dolphins memory"""
    bl_idname = "wm.sync_cam"
    bl_label = "Sync Camera"
    _timer = None
    _pid = dol_pid()

    def modal(self, context, event):
        if event.type in {'Q'}:
            self.cancel(context)
            return {'CANCELLED'}

        if event.type == 'TIMER':
            sync_blender_cam(self._pid)
        return {'PASS_THROUGH'}

    def execute(self, context):
        wm = context.window_manager
        # 0.05 seems to be a good in-between for fps/performance.
        self._timer = wm.event_timer_add(0.01, window=context.window)
        wm.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def cancel(self, context):
        wm = context.window_manager
        wm.event_timer_remove(self._timer)

        # Sync Blender media controls. Sync is done by connecting frame advance on/off from melee, to the function that checks if an animation is playing (Blender).
class Sync_Media_Controls(bpy.types.Operator):
    bl_idname = "sync.mc"
    bl_label = "Sync Media Controls"
    _timer = None
    _pid = dol_pid()
    def modal(self, context, event):
        if not context.window_manager.sync_m_toggle:
            context.window_manager.event_timer_remove(self._timer)
            return {'FINISHED'}

        if event.type == 'TIMER':
            sync_player_control(self._pid)
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

class Screenshot_Sequence(bpy.types.Operator):
    """Creates an Image Sequence of the Frame Range."""
    bl_idname = "wm.ss_seq"
    bl_label = "Image Sequence"
    _timer = None
    
    _root_directory = Path('C://Users//fores//AppData//Roaming//Slippi Launcher//playback//User//ScreenShots//GALE01')
    _pid = dol_pid()
    _app = Application(backend="uia").connect(process=_pid)
    _dlg = _app['Faster Melee - Slippi(2.3.6) - Playback']

    def seq_while_pause(self):
        self._app.window(best_match='Faster Melee - Slippi(2.3.6) - Playback', visible_only=False).restore()
        self._app['Faster Melee - Slippi (2.3.6) - PlaybackDialog']['ScrShot'].invoke()
        self._dlg.minimize()
        while True:
            size = sum(f.stat().st_size for f in self._root_directory.glob('**/*') if f.is_file())
            time.sleep(0.5)
            size2 = sum(f.stat().st_size for f in self._root_directory.glob('**/*') if f.is_file())
            if size == size2:
                break
        bpy.ops.screen.frame_offset(delta=1)

    def seq_while_play(self):
        self._app.window(best_match='Faster Melee - Slippi(2.3.6) - Playback', visible_only=False).restore()
        self._app['Faster Melee - Slippi (2.3.6) - PlaybackDialog']['ScrShot'].invoke()
        self._dlg.menu_select("Emulation->Frame Advance")
        self._dlg.minimize()
        while True:
            size = sum(f.stat().st_size for f in self._root_directory.glob('**/*') if f.is_file())
            time.sleep(0.5)
            size2 = sum(f.stat().st_size for f in self._root_directory.glob('**/*') if f.is_file())
            if size == size2:
                break
        bpy.ops.screen.frame_offset(delta=1)

    def modal(self, context, event):
        scene = context.scene

        if event.type in {'SPACE'} or scene.frame_current > scene.frame_end - 1:
            self.cancel(context)
            return {'CANCELLED'}

        if event.type == 'TIMER':
            if (context.scene.my_tool.is_paused == True):
                self.seq_while_play()
            else:
                self.seq_while_pause()
            bpy.context.view_layer.update()
        return {'PASS_THROUGH'}

    def execute(self, context):
        scene = context.scene
        wm = context.window_manager
        self._timer = wm.event_timer_add(0.1, window=context.window)
        wm.modal_handler_add(self)
        scene.frame_set(scene.frame_start)
        return {'RUNNING_MODAL'}

    def cancel(self, context):
        wm = context.window_manager
        wm.event_timer_remove(self._timer)

class Multi_Op(bpy.types.Operator):
    bl_idname = "multi.op"
    bl_label = "Multiple Operators"
    action: EnumProperty(
    items=[
        ('LOAD', 'load state', 'load state'),
     ]
    )

    def execute(self, context):
        if self.action == 'LOAD':
            self.sync_frame_end()
        return {'FINISHED'}

    @staticmethod
    def sync_frame_end():
        _dlg = util_dol()
        # Go to frame start.
        bpy.ops.screen.frame_jump(end=False)
        # Changes focus and sends key.
        _dlg.menu_select("Emulation -> Load State")
        _dlg.Load_State.MenuItem14.select()
        time.sleep(0.01)

# ------------------------------------------------------------------------
#    Scene Properties
# ------------------------------------------------------------------------

class MyProperties(PropertyGroup):

    is_paused: BoolProperty(
        name="Frame Advance",
        description="Change operation of Img Seq if Melee is paused/unpaused.",
        default = False
        )

# ------------------------------------------------------------------------
#    Panel in Object Mode
# ------------------------------------------------------------------------

class EMC_Control_Panel(Panel):
    bl_label = "External Melee Camera"
    bl_idname = "OBJECT_PT_dolphinfreelook"
    bl_space_type = "VIEW_3D"   
    bl_region_type = "UI"
    bl_category = "Melee Control Panel"
    bl_context = "objectmode"

    @classmethod
    def poll(self,context):
        return context.object is not None

    def draw(self, context):
        layout = self.layout
        wm = context.window_manager
        label_sync = "Sync Media Controls" if wm.sync_m_toggle else "Sync Media Controls"
        mytool = context.scene.my_tool

        layout.operator("wm.sync_cam")
        layout.prop(wm, 'sync_m_toggle', text=label_sync, toggle=True)
        layout.operator('multi.op', text='Load Save State').action = 'LOAD'
        layout.operator("wm.ss_seq")
        layout.prop(mytool, "is_paused")
        layout.separator()

    def update_function(self, context):
        if self.sync_m_toggle:
            bpy.ops.sync.mc('INVOKE_DEFAULT')
        return
    
    bpy.types.WindowManager.sync_m_toggle = bpy.props.BoolProperty(
                                                 default = False,
                                                 update = update_function)

# ------------------------------------------------------------------------
#    Registration
# ------------------------------------------------------------------------

classes = (
    MyProperties,
    EMC_Control_Panel,
    Sync_Cam_Pos,
    Sync_Media_Controls,
    Multi_Op,
    Screenshot_Sequence,
    )

def register():
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)

    bpy.types.Scene.my_tool = PointerProperty(type=MyProperties)

def unregister():
    from bpy.utils import unregister_class
    for cls in reversed(classes):
        unregister_class(cls)
    del bpy.types.Scene.my_tool

if __name__ == "__main__":
    register()
