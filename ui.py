import bpy
from bpy.types import Menu, Panel

def draw_edge_menu(self, context):
    """Add operator to edge menu"""
    self.layout.separator()
    self.layout.operator("mesh.edge_slide_by_distance", text="Slide by Distance", icon='DRIVER_DISTANCE')

class VIEW3D_PT_edge_slide_distance(Panel):
    """Panel in the N-panel for edge sliding options"""
    bl_label = "Edge Slide Distance"
    bl_idname = "VIEW3D_PT_edge_slide_distance"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Tool"
    bl_context = "mesh_edit"
    
    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return (obj is not None and 
                obj.type == 'MESH' and 
                obj.mode == 'EDIT')
    
    def draw(self, context):
        layout = self.layout
        
        col = layout.column(align=True)
        col.label(text="Edge Slide by Distance:")
        
        # Main operator button
        row = col.row(align=True)
        row.scale_y = 1.5
        row.operator("mesh.edge_slide_by_distance", text="Slide by Distance", icon='DRIVER_DISTANCE')
        
        col.separator()
        
        # Instructions
        box = col.box()
        box.label(text="Instructions:", icon='INFO')
        box.scale_y = 0.8
        box.label(text="1. Select edge loop (Alt+Click)")
        box.label(text="2. Click 'Slide by Distance'")
        box.label(text="3. Enter exact distance")
        box.label(text="4. Positive = one direction")
        box.label(text="5. Negative = opposite direction")
        
        col.separator()
        
        # Shortcuts info
        box = col.box()
        box.label(text="Shortcut:", icon='HAND')
        box.label(text="Shift+Alt+G in Edit Mode")


def register():
    bpy.utils.register_class(VIEW3D_PT_edge_slide_distance)
    
    # Add to edge menu
    bpy.types.VIEW3D_MT_edit_mesh_edges.append(draw_edge_menu)
    
    # Add keyboard shortcut
    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon
    if kc:
        km = kc.keymaps.new(name='Mesh', space_type='EMPTY')
        kmi = km.keymap_items.new('mesh.edge_slide_by_distance', 'G', 'PRESS', shift=True, alt=True)
        kmi.active = True

def unregister():
    bpy.utils.unregister_class(VIEW3D_PT_edge_slide_distance)
    
    # Remove from edge menu
    bpy.types.VIEW3D_MT_edit_mesh_edges.remove(draw_edge_menu)
    
    # Remove keyboard shortcuts
    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon
    if kc:
        for km in kc.keymaps:
            for kmi in km.keymap_items:
                if kmi.idname == 'mesh.edge_slide_by_distance':
                    km.keymap_items.remove(kmi)