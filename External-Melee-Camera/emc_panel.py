from bpy.props import (StringProperty, BoolProperty, PointerProperty)
from bpy.types import (Panel, PropertyGroup)
from .emc_op import syncCamera, menuSavestate, menuLoadstate, screenshotSequence, menuPreview


class controlProperties(PropertyGroup):

    is_media_sync: BoolProperty(
        name="Sync Media Controls",
        description="",
        default=False
        )

    slippi_path: StringProperty(
        name="Screenshot Directory",
        description=" 'C:\\Users\\*yourname*\\AppData\\Roaming\\Slippi Launcher\\playback\\User\\ScreenShots' ",
        default="",
        maxlen=1024,
        subtype='DIR_PATH'
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
        mytool = context.scene.my_tool
        layout.operator("wm.sync_cam")
        layout.separator()
        layout.operator('wm.save_state')
        layout.operator('wm.load_state')
        layout.separator()
        layout.operator("wm.ss_seq")
        layout.operator("wm.prev_seq")
        layout.prop(mytool, "is_media_sync")
        layout.separator()
        layout.prop(mytool, "slippi_path")
        layout.separator()


classes = (
    controlProperties,
    emcControlPanel,
    syncCamera,
    menuSavestate,
    menuLoadstate,
    screenshotSequence,
    menuPreview,
    )
