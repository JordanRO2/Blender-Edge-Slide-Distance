
bl_info = {
    "name": "Edge Slide by Distance",
    "author": "JordanRO2 (Jordan Rodriguez)",
    "version": (1, 0, 0),
    "blender": (4, 5, 0),
    "location": "3D View > Edge Menu / G+G",
    "description": "Slide edges by exact distance instead of factor",
    "warning": "",
    "doc_url": "",
    "category": "Mesh",
}

import bpy
from . import operators
from . import ui

def register():
    operators.register()
    ui.register()

def unregister():
    operators.unregister()
    ui.unregister()

if __name__ == "__main__":
    register()