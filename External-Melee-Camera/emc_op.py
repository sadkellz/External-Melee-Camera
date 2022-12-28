import bpy
import time
import os
from pathlib import Path
from .emc_common import GALE01, CAM_START, PAUSE_BIT, CAM_TYPE
from .emc_functions import sync_blender_cam, sync_player_control,\
    take_screenshot, frame_step, load_state, save_state, set_player_pos


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
            sync_blender_cam((GALE01 + CAM_START))

            if context.scene.my_tool.is_sync_player:
                set_player_pos()

            if context.scene.my_tool.is_media_sync:
                sync_player_control((GALE01 + PAUSE_BIT))

        return {'PASS_THROUGH'}

    def execute(self, context):
        wm = context.window_manager
        self._timer = wm.event_timer_add(0.01, window=context.window)
        wm.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def cancel(self, context):
        wm = context.window_manager
        wm.event_timer_remove(self._timer)


def wait_for_screenshot(root_dir):
    while True:
        size = sum(f.stat().st_size for f in root_dir.glob('**/*') if f.is_file())
        time.sleep(0.5)
        size2 = sum(f.stat().st_size for f in root_dir.glob('**/*') if f.is_file())
        if size == size2:
            time.sleep(0.1)
            break


def img_seq(context, root_dir):
    take_screenshot()
    frame_step()
    wait_for_screenshot(root_dir)
    bpy.ops.screen.frame_offset(delta=1)


def prev_seq(context):
    frame_step()
    time.sleep(0.03)
    bpy.ops.screen.frame_offset(delta=1)


class screenshotSequence(bpy.types.Operator):
    """Creates an image sequence for the duration of the frame range."""
    bl_idname = "wm.ss_seq"
    bl_label = "Image Sequence"
    _timer = None

    def modal(self, context, event):
        scene = context.scene
        root_dir = Path(scene.my_tool.slippi_path)
        if event.type in {'SPACE'} or scene.frame_current > scene.frame_end - 1:
            self.cancel(context)
            return {'CANCELLED'}

        if event.type == 'TIMER':
            img_seq(context, root_dir)
            bpy.context.view_layer.update()
            time.sleep(0.7)
        return {'PASS_THROUGH'}

    def execute(self, context):
        scene = context.scene
        wm = context.window_manager
        self._timer = wm.event_timer_add(0.2, window=context.window)
        wm.modal_handler_add(self)
        load_state()
        time.sleep(0.5)
        scene.frame_set(scene.frame_start)
        return {'RUNNING_MODAL'}

    def cancel(self, context):
        wm = context.window_manager
        wm.event_timer_remove(self._timer)


class menuLoadstate(bpy.types.Operator):
    """Loads the last state saved."""
    bl_idname = "wm.quick_load"
    bl_label = "Quick Load"

    def execute(self, context):
        load_state()
        return {'FINISHED'}


class menuSavestate(bpy.types.Operator):
    """Saves to the oldest state."""
    bl_idname = "wm.quick_save"
    bl_label = "Quick Save"

    def execute(self, context):
        save_state()
        return {'FINISHED'}


class menuPreview(bpy.types.Operator):
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
        self._timer = wm.event_timer_add(0.2, window=context.window)
        wm.modal_handler_add(self)
        load_state()
        time.sleep(0.5)
        scene.frame_set(scene.frame_start)
        return {'RUNNING_MODAL'}

    def cancel(self, context):
        wm = context.window_manager
        wm.event_timer_remove(self._timer)
