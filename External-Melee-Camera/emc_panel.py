from bpy.props import (StringProperty, BoolProperty, PointerProperty)
from bpy.types import (Panel, PropertyGroup)
from .emc_op import syncCamera, menuSavestate, menuLoadstate, screenshotSequence, menuPreview


class controlProperties(PropertyGroup):

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


class emcControlPanel(Panel):
    bl_label = 'External Melee Camera'
    bl_idname = 'OBJECT_PT_external_melee_camera'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Melee Control Panel'
    bl_context = 'objectmode'

    @classmethod
    def poll(self, context):
        return context.object is not None

    def draw(self, context):
        layout = self.layout
        mytool = context.scene.my_tool

        box1 = layout.box()
        row1 = box1.row()
        row1.scale_y = 2
        row1.operator('wm.sync_cam', icon_value=71)
        row2 = box1.row()
        row2.alignment = 'Center'.upper()
        row2.prop(mytool, 'is_media_sync')
        row2.prop(mytool, 'is_sync_player')

        layout.separator()

        box2 = layout.box()
        box2.operator('wm.quick_save')
        box2.operator('wm.quick_load')

        layout.separator()

        box3 = layout.box()
        box3.operator('wm.ss_seq')
        box3.operator('wm.prev_seq')

        layout.separator()

        box4 = layout.box()
        box4.label(text='Screenshot Directory:')
        box4.prop(mytool, 'slippi_path')

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
