import bpy
import bmesh
from bpy.types import Operator
from bpy.props import FloatProperty, BoolProperty, EnumProperty
from mathutils import Vector
import math

class MESH_OT_edge_slide_by_distance(Operator):
    """Slide edges by exact distance using Blender's native edge slide"""
    bl_idname = "mesh.edge_slide_by_distance"
    bl_label = "Edge Slide by Distance"
    bl_options = {'REGISTER', 'UNDO'}
    
    distance: FloatProperty(
        name="Distance",
        description="Distance to slide edges (positive or negative)",
        default=0.01,
        soft_min=-10.0,
        soft_max=10.0,
        unit='LENGTH',
        subtype='DISTANCE',
        precision=4
    )
    
    use_even: BoolProperty(
        name="Even",
        description="Make the edge loop slide evenly",
        default=False
    )
    
    use_clamp: BoolProperty(
        name="Clamp",
        description="Clamp within the edge boundaries",
        default=True
    )
    
    flipped: BoolProperty(
        name="Flipped",
        description="Flip the slide direction",
        default=False
    )
    
    measurement_method: EnumProperty(
        name="Measure",
        description="How to measure the slide distance",
        items=[
            ('PERPENDICULAR', 'Perpendicular', 'Perpendicular distance to boundary'),
            ('ALONG_SURFACE', 'Along Surface', 'Distance along the surface'),
            ('AVERAGE', 'Average', 'Average of all edge distances')
        ],
        default='PERPENDICULAR'
    )
    
    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return (obj is not None and 
                obj.type == 'MESH' and 
                obj.mode == 'EDIT')
    
    def invoke(self, context, event):
        # Check if edges are selected
        obj = context.active_object
        mesh = obj.data
        bm = bmesh.from_edit_mesh(mesh)
        
        selected_edges = [e for e in bm.edges if e.select]
        if not selected_edges:
            self.report({'WARNING'}, "Please select an edge loop first")
            return {'CANCELLED'}
        
        # Show dialog
        return context.window_manager.invoke_props_dialog(self, width=350)
    
    def draw(self, context):
        layout = self.layout
        
        col = layout.column()
        
        # Distance input
        col.prop(self, "distance")
        
        # Show current unit system
        unit_system = context.scene.unit_settings.system
        if unit_system != 'NONE':
            col.label(text=f"Using {unit_system.lower()} units", icon='INFO')
        
        # Options
        col.separator()
        row = col.row()
        row.prop(self, "use_even")
        row.prop(self, "use_clamp")
        
        col.prop(self, "flipped")
        col.prop(self, "measurement_method")
        
        # Help text
        col.separator()
        box = col.box()
        box.label(text="Tips:", icon='INFO')
        box.label(text="• Positive: slide in one direction")
        box.label(text="• Negative: slide in opposite direction")
        box.label(text="• Works with any edge orientation")
    
    def execute(self, context):
        obj = context.active_object
        mesh = obj.data
        
        # Get BMesh
        bm = bmesh.from_edit_mesh(mesh)
        selected_edges = [e for e in bm.edges if e.select]
        
        if not selected_edges:
            self.report({'WARNING'}, "No edges selected")
            return {'CANCELLED'}
        
        # Calculate the slide factor
        factor = self.calculate_slide_factor(bm, selected_edges, self.distance)
        
        if factor is None:
            self.report({'WARNING'}, "Cannot calculate slide factor")
            return {'CANCELLED'}
        
        # Report what we're doing
        self.report({'INFO'}, f"Sliding {abs(self.distance):.4f} units | Factor: {factor:.4f}")
        
        # Execute Blender's native edge slide
        try:
            bpy.ops.transform.edge_slide(
                value=factor,
                use_even=self.use_even,
                flipped=self.flipped,
                use_clamp=self.use_clamp,
                mirror=False,
                snap=False,
                release_confirm=True
            )
        except Exception as e:
            self.report({'ERROR'}, f"Edge slide failed: {str(e)}")
            return {'CANCELLED'}
        
        return {'FINISHED'}
    
    def calculate_slide_factor(self, bm, selected_edges, distance):
        """Calculate the factor needed for the desired distance"""
        
        # Analyze the edge loop structure
        slide_data = self.analyze_edge_slide(bm, selected_edges)
        
        if not slide_data:
            return None
        
        # Convert distance to factor based on measurement method
        if self.measurement_method == 'PERPENDICULAR':
            # Use perpendicular distance to boundaries
            max_dist = slide_data['perpendicular_distance']
        elif self.measurement_method == 'ALONG_SURFACE':
            # Use distance along the surface
            max_dist = slide_data['surface_distance']
        else:  # AVERAGE
            # Use average of all methods
            max_dist = slide_data['average_distance']
        
        if max_dist == 0:
            return 0
        
        # Calculate factor
        # Positive distance = positive factor, negative distance = negative factor
        factor = distance / max_dist
        
        # Clamp if requested
        if self.use_clamp:
            factor = max(-1.0, min(1.0, factor))
        
        return factor
    
    def analyze_edge_slide(self, bm, selected_edges):
        """Analyze the edge slide geometry"""
        
        # Find boundary edges (what we're sliding between)
        boundaries = self.find_slide_boundaries(bm, selected_edges)
        
        if not boundaries:
            return None
        
        # Calculate distances
        perp_distances = []
        surface_distances = []
        
        for edge in selected_edges:
            # Skip edges that can't slide
            if len(edge.link_faces) != 2:
                continue
            
            # Calculate distance for this edge
            dist_data = self.calculate_edge_distances(edge, boundaries)
            if dist_data:
                perp_distances.append(dist_data['perpendicular'])
                surface_distances.append(dist_data['surface'])
        
        if not perp_distances:
            return None
        
        # Aggregate distances
        return {
            'perpendicular_distance': sum(perp_distances) / len(perp_distances),
            'surface_distance': sum(surface_distances) / len(surface_distances),
            'average_distance': (sum(perp_distances) + sum(surface_distances)) / (2 * len(perp_distances))
        }
    
    def find_slide_boundaries(self, bm, selected_edges):
        """Find the boundary edges that we're sliding between"""
        boundaries = []
        
        # Create a set for quick lookup
        selected_set = set(selected_edges)
        
        for edge in selected_edges:
            if len(edge.link_faces) != 2:
                continue
            
            # Check each linked face for parallel edges
            for face in edge.link_faces:
                for face_edge in face.edges:
                    if face_edge not in selected_set and face_edge != edge:
                        # Check if this edge is roughly parallel
                        if self.are_edges_parallel(edge, face_edge, threshold=0.8):
                            boundaries.append(face_edge)
        
        return list(set(boundaries))  # Remove duplicates
    
    def are_edges_parallel(self, edge1, edge2, threshold=0.8):
        """Check if two edges are roughly parallel"""
        dir1 = (edge1.verts[1].co - edge1.verts[0].co).normalized()
        dir2 = (edge2.verts[1].co - edge2.verts[0].co).normalized()
        
        # Check dot product (1 = parallel, -1 = anti-parallel, 0 = perpendicular)
        dot = abs(dir1.dot(dir2))
        return dot > threshold
    
    def calculate_edge_distances(self, edge, boundaries):
        """Calculate distances from edge to boundaries"""
        
        if not boundaries:
            return None
        
        edge_center = (edge.verts[0].co + edge.verts[1].co) / 2
        edge_dir = (edge.verts[1].co - edge.verts[0].co).normalized()
        
        min_perp_dist = float('inf')
        min_surface_dist = float('inf')
        
        for boundary in boundaries:
            boundary_center = (boundary.verts[0].co + boundary.verts[1].co) / 2
            
            # Vector from edge to boundary
            to_boundary = boundary_center - edge_center
            
            # Perpendicular distance (remove component along edge direction)
            perp_component = to_boundary - (to_boundary.dot(edge_dir) * edge_dir)
            perp_dist = perp_component.length
            
            # Surface distance (actual distance)
            surface_dist = to_boundary.length
            
            # Keep track of minimum distances
            if perp_dist < min_perp_dist:
                min_perp_dist = perp_dist
            if surface_dist < min_surface_dist:
                min_surface_dist = surface_dist
        
        if min_perp_dist == float('inf'):
            return None
        
        return {
            'perpendicular': min_perp_dist,
            'surface': min_surface_dist
        }


def register():
    bpy.utils.register_class(MESH_OT_edge_slide_by_distance)

def unregister():
    bpy.utils.unregister_class(MESH_OT_edge_slide_by_distance)