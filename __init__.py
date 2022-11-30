import bpy
from . emc_panel import *
from . emc_functions import *

bl_info = {
    "name": "External-Melee-Camera",
    "author": "KELLZ",
    "version": (1, 3, 0),
    "blender": (3, 2, 2),
    "warning": "Requires installation of dependencies",
    "category": "Tools",
    "description": "Control Melee's Camera from Blender.",
    "wiki_url": "https://github.com/sadkellz/External-Melee-Camera",
}


def register():
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)
    bpy.types.Scene.my_tool = PointerProperty(type=controlProperties)


def unregister():
    from bpy.utils import unregister_class
    for cls in reversed(classes):
        unregister_class(cls)
    del bpy.types.Scene.my_tool


if __name__ == "__main__":
    register()
