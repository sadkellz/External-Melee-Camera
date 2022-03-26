import bpy
from . emc_functions import *

class syncCamera(bpy.types.Operator):
    """A timer that consistently writes to Dolphins memory"""
    bl_idname = "wm.sync_cam"
    bl_label = "Sync Camera"
    _timer = None

    def modal(self, context, event):
        if event.type in {'Q'}:
            self.cancel(context)
            return {'CANCELLED'}

        if event.type == 'TIMER':
            #sync_blender_cam()
            sync_blender_cam_freelook()
            sync_blender_cam_freelook_r()
            if context.scene.my_tool.is_media_sync:
                sync_player_control()
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


class screenshotSequence(bpy.types.Operator):
    """Creates an image sequence for the duration of the frame range."""
    bl_idname = "wm.ss_seq"
    bl_label = "Image Sequence"
    _timer = None

    def start_seq(self, context):
        self.app.window(best_match='Faster Melee - Slippi(2.3.6) - Playback', visible_only=False).restore()
        self.app['Faster Melee - Slippi (2.3.6) - PlaybackDialog']['ScrShot'].invoke()
        if context.scene.my_tool.is_paused:
            self.dlg.menu_select("Emulation->Frame Advance")

        while True:
            size = sum(f.stat().st_size for f in ROOT_DIRECTORY.glob('**/*') if f.is_file())
            time.sleep(0.5)
            size2 = sum(f.stat().st_size for f in ROOT_DIRECTORY.glob('**/*') if f.is_file())
            if size == size2:
                break
        bpy.ops.screen.frame_offset(delta=1)

    def modal(self, context, event):
        scene = context.scene
        if event.type in {'SPACE'} or scene.frame_current > scene.frame_end - 1:
            self.cancel(context)
            return {'CANCELLED'}

        if event.type == 'TIMER':
            self.start_seq(context)
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


class loadState(bpy.types.Operator):
    """Loads the slot 1 save state."""
    bl_idname = "wm.save_state"
    bl_label = "Load Save State"

    def execute(self, context):
        load_save_state()
        return {'FINISHED'}
