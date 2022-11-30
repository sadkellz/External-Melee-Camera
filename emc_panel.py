from bpy.props import (EnumProperty, BoolProperty, PointerProperty,)
from bpy.types import (Panel, PropertyGroup)
from . emc_functions import *
from . emc_op import *
from pathlib import PureWindowsPath


class controlProperties(PropertyGroup):

    is_paused: BoolProperty(
        name="Frame Advance",
        description="Change operations of image seq if Melee is dev paused/un-paused.",
        default=False
        )

    is_media_sync: BoolProperty(
        name="Sync Media Controls",
        description="",
        default=False
        )


class emcControlPanel(Panel):
    bl_label = "External Melee Camera"
    bl_idname = "OBJECT_PT_external_melee_camera"
    bl_space_type = "VIEW_3D"   
    bl_region_type = "UI"
    bl_category = "Melee Control Panel"
    bl_context = "objectmode"

    @classmethod
    def poll(self, context):
        return context.object is not None

    def draw(self, context):
        layout = self.layout
        wm = context.window_manager
        mytool = context.scene.my_tool
        layout.operator("wm.sync_cam")
        layout.separator()
        layout.operator('wm.save_state')
        layout.operator('wm.load_state')
        layout.separator()
        layout.operator("wm.ss_seq")
        layout.operator("wm.prev_seq")
        layout.prop(mytool, "is_paused")
        layout.prop(mytool, "is_media_sync")
        layout.separator()
        layout.row().label(text="Slippi Directory: ")
        layout.row().prop(context.scene, "EMC_root_directory")


ROOT_DIRECTORY = PureWindowsPath(EMC_root_directory)

classes = (
    controlProperties,
    emcControlPanel,
    syncCamera,
    menuSavestate,
    menuLoadstate,
    screenshotSequence,
    menuPreview,
    )
