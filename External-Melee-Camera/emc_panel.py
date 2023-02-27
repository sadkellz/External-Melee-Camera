import bpy
import pymem
from .emc_common import pattern_scan_all, set_global_vars
from bpy.props import (IntProperty, StringProperty, BoolProperty, PointerProperty)
from bpy.types import (Panel, PropertyGroup)
from .emc_op import menu_sync_camera, menu_quick_save, menu_quick_load, menu_img_sequence, menu_img_preview, \
    menu_saveslot_1, menu_saveslot_2, menu_saveslot_3, menu_saveslot_4, menu_saveslot_5, menu_saveslot_6, \
    menu_loadslot_1, menu_loadslot_2, menu_loadslot_3, menu_loadslot_4, menu_loadslot_5, menu_loadslot_6, \
    menu_current_frame


class control_properties(PropertyGroup):

    is_media_sync: BoolProperty(
        name="Media Controls",
        description="",
        default=False
        )

    is_sync_player: BoolProperty(
        name="Player Positions",
        description="",
        default=False
        )

    slippi_path: StringProperty(
        name="",
        description=" 'C:\\Users\\*yourname*\\AppData\\Roaming\\Slippi Launcher\\playback\\User\\ScreenShots' ",
        default="",
        maxlen=1024,
        subtype='DIR_PATH'
        )

    selected_slot: IntProperty(
        default=1
    )

    frame_number: IntProperty(
        default=0,
    )


GALE01 = None
pm = None
is_on = False


def check_exists():
    try:
        pymem.Pymem("Slippi Dolphin.exe")
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
    panel_timer = None

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
            pm = pymem.Pymem("Slippi Dolphin.exe")
            GALE01 = find_gale01(pm)
            set_global_vars(pm)

        elif GALE01 is not None:
            is_on = True

        # Sync Camera
        cam_box = layout.box()
        cam_box.enabled = is_on
        cam_row1 = cam_box.row()
        cam_row1.scale_y = 2
        cam_row1.operator('wm.sync_cam', icon_value=71)
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
        sequence_box = layout.box()
        sequence_box.enabled = is_on
        sequence_box.operator('wm.ss_seq')
        sequence_box.operator('wm.prev_seq')
        layout.separator()

        # Directory
        sequence_box.label(text='Screenshot Directory:')
        sequence_box.prop(mytool, 'slippi_path')


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

        state_row1.operator("wm.save_slot_1", text="1")
        state_row1.operator("wm.save_slot_2", text="2")
        state_row1.operator("wm.save_slot_3", text="3")

        state_col1.separator(factor=0.75)

        state_row2 = state_col1.row()
        state_row2.alignment = 'Center'.upper()

        state_row2.operator("wm.save_slot_4", text="4")
        state_row2.operator("wm.save_slot_5", text="5")
        state_row2.operator("wm.save_slot_6", text="6")

        state_col1.separator(factor=0.75)

        state_box2 = state_split.box()
        state_box2.alignment = 'Center'.upper()
        state_box2.label(text='Load States', icon_value=707)
        state_col2 = state_box2.column()
        state_col2.alignment = 'Center'.upper()
        state_row3 = state_col2.row()
        state_row3.alignment = 'Center'.upper()

        state_row3.operator("wm.load_slot_1", text="1")
        state_row3.operator("wm.load_slot_2", text="2")
        state_row3.operator("wm.load_slot_3", text="3")

        state_col2.separator(factor=0.75)

        state_row4 = state_col2.row()
        state_row4.alignment = 'Center'.upper()

        state_row4.operator("wm.load_slot_4", text="4")
        state_row4.operator("wm.load_slot_5", text="5")
        state_row4.operator("wm.load_slot_6", text="6")

        state_col2.separator(factor=0.75)


classes = (
    control_properties,
    emc_control_panel,
    state_panel,
    menu_sync_camera,
    menu_quick_save,
    menu_quick_load,
    menu_img_sequence,
    menu_img_preview,
    menu_saveslot_1,
    menu_saveslot_2,
    menu_saveslot_3,
    menu_saveslot_4,
    menu_saveslot_5,
    menu_saveslot_6,
    menu_loadslot_1,
    menu_loadslot_2,
    menu_loadslot_3,
    menu_loadslot_4,
    menu_loadslot_5,
    menu_loadslot_6,
    menu_current_frame
    )
