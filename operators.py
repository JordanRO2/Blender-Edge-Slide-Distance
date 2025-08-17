import bpy
import bmesh
from bpy.types import Operator
from bpy.props import FloatProperty, BoolProperty, EnumProperty, StringProperty
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
            ('AVERAGE', 'Average', 'Use average distance across the loop'),
            ('MINIMUM', 'Minimum', 'Use minimum distance in the loop'),
            ('MAXIMUM', 'Maximum', 'Use maximum distance in the loop'),
            ('FIRST', 'First Selected', 'Use distance of first selected edge')
        ],
        default='AVERAGE'
    )
    
    # Removed unit_system as Blender handles this automatically with unit='LENGTH'
    
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
        
        # Distance input - Blender automatically shows units based on scene settings
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
        box.label(text="• Positive: slide toward first boundary")
        box.label(text="• Negative: slide toward opposite boundary")
        box.label(text="• Even: maintains edge loop spacing")
    
    def execute(self, context):
        obj = context.active_object
        mesh = obj.data
        
        # Store original selection
        bm = bmesh.from_edit_mesh(mesh)
        selected_edges = [e for e in bm.edges if e.select]
        
        if not selected_edges:
            self.report({'WARNING'}, "No edges selected")
            return {'CANCELLED'}
        
        # The distance property already handles unit conversion when unit='LENGTH' is set
        distance = self.distance
        
        # Calculate the slide range (max distance in each direction)
        slide_data = self.analyze_edge_loop(bm, selected_edges)
        
        if not slide_data:
            self.report({'WARNING'}, "Cannot analyze selected edge loop. Make sure you have a valid edge loop selected.")
            return {'CANCELLED'}
        
        # Calculate the factor based on distance
        factor = self.distance_to_factor(slide_data['distances'], distance)
        
        # Report analysis with proper unit display
        unit_scale = context.scene.unit_settings.scale_length
        self.report({'INFO'}, f"Loop width: {slide_data['avg_width']:.4f} | Sliding: {distance:.4f} | Factor: {factor:.4f}")
        
        # Execute Blender's native edge slide
        try:
            # Call native edge slide with calculated factor
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
    
    
    def analyze_edge_loop(self, bm, selected_edges):
        """Analyze the edge loop to determine slide distances"""
        # Ensure we have a proper edge loop
        if not self.is_edge_loop(selected_edges):
            # Try to find edge loops within selection
            loops = self.find_edge_loops(selected_edges)
            if not loops:
                return None
            selected_edges = loops[0]  # Use first loop found
        
        distances = {'positive': [], 'negative': []}
        widths = []
        
        for edge in selected_edges:
            # Get slide range for this edge
            dist_data = self.get_edge_slide_range(bm, edge)
            if dist_data:
                distances['positive'].append(dist_data['positive'])
                distances['negative'].append(dist_data['negative'])
                widths.append(dist_data['positive'] + dist_data['negative'])
        
        if not distances['positive']:
            return None
        
        # Aggregate based on measurement method
        if self.measurement_method == 'AVERAGE':
            result_distances = {
                'positive': sum(distances['positive']) / len(distances['positive']),
                'negative': sum(distances['negative']) / len(distances['negative'])
            }
        elif self.measurement_method == 'MINIMUM':
            result_distances = {
                'positive': min(distances['positive']),
                'negative': min(distances['negative'])
            }
        elif self.measurement_method == 'MAXIMUM':
            result_distances = {
                'positive': max(distances['positive']),
                'negative': max(distances['negative'])
            }
        else:  # FIRST
            result_distances = {
                'positive': distances['positive'][0],
                'negative': distances['negative'][0]
            }
        
        avg_width = sum(widths) / len(widths) if widths else 0
        
        return {
            'distances': result_distances,
            'avg_width': avg_width,
            'edge_count': len(selected_edges)
        }
    
    def is_edge_loop(self, edges):
        """Check if edges form a proper loop"""
        # Simple check: each vertex should connect to exactly 2 edges
        vert_count = {}
        for edge in edges:
            for vert in edge.verts:
                vert_count[vert] = vert_count.get(vert, 0) + 1
        
        # In a proper loop, each vertex appears exactly twice
        return all(count == 2 for count in vert_count.values())
    
    def find_edge_loops(self, edges):
        """Find edge loops within selected edges"""
        loops = []
        processed = set()
        
        for edge in edges:
            if edge in processed:
                continue
            
            loop = self.build_loop_from_edge(edge, edges, processed)
            if loop and len(loop) > 2:
                loops.append(loop)
        
        return loops
    
    def build_loop_from_edge(self, start_edge, all_edges, processed):
        """Build an edge loop starting from given edge"""
        loop = [start_edge]
        processed.add(start_edge)
        
        # Follow loop in both directions
        for direction in [0, 1]:
            current_vert = start_edge.verts[direction]
            prev_edge = start_edge
            
            while True:
                # Find next edge in loop
                next_edge = None
                for edge in current_vert.link_edges:
                    if edge in all_edges and edge not in processed:
                        next_edge = edge
                        break
                
                if not next_edge:
                    break
                
                loop.append(next_edge)
                processed.add(next_edge)
                
                # Move to next vertex
                current_vert = next_edge.other_vert(current_vert)
                prev_edge = next_edge
        
        return loop
    
    def get_edge_slide_range(self, bm, edge):
        """Calculate the slide range for a single edge"""
        # Edge must have exactly 2 faces to be slideable
        if len(edge.link_faces) != 2:
            return None
        
        face1, face2 = edge.link_faces
        
        # For quads, find parallel edges
        if len(face1.edges) == 4 and len(face2.edges) == 4:
            return self.get_quad_slide_range(edge, face1, face2)
        else:
            # Handle triangles and n-gons
            return self.get_general_slide_range(edge, face1, face2)
    
    def get_quad_slide_range(self, edge, face1, face2):
        """Get slide range for edge between two quads"""
        parallel1 = self.find_opposite_edge_in_face(edge, face1)
        parallel2 = self.find_opposite_edge_in_face(edge, face2)
        
        if not (parallel1 or parallel2):
            return None
        
        edge_center = (edge.verts[0].co + edge.verts[1].co) / 2
        
        dist1 = 0
        dist2 = 0
        
        if parallel1:
            p1_center = (parallel1.verts[0].co + parallel1.verts[1].co) / 2
            dist1 = (p1_center - edge_center).length
        
        if parallel2:
            p2_center = (parallel2.verts[0].co + parallel2.verts[1].co) / 2
            dist2 = (p2_center - edge_center).length
        
        return {
            'positive': dist1 if dist1 > 0 else dist2,
            'negative': dist2 if dist2 > 0 else dist1
        }
    
    def get_general_slide_range(self, edge, face1, face2):
        """Get slide range for edge in non-quad topology"""
        edge_center = (edge.verts[0].co + edge.verts[1].co) / 2
        
        # Find furthest vertices in each face
        max_dist1 = 0
        max_dist2 = 0
        
        for vert in face1.verts:
            if vert not in edge.verts:
                dist = (vert.co - edge_center).length
                max_dist1 = max(max_dist1, dist)
        
        for vert in face2.verts:
            if vert not in edge.verts:
                dist = (vert.co - edge_center).length
                max_dist2 = max(max_dist2, dist)
        
        # Conservative estimate
        return {
            'positive': max_dist1 * 0.7,
            'negative': max_dist2 * 0.7
        }
    
    def find_opposite_edge_in_face(self, edge, face):
        """Find the opposite edge in a face (for quads)"""
        if len(face.edges) != 4:
            return None
        
        edge_verts = set(edge.verts)
        
        for face_edge in face.edges:
            if face_edge == edge:
                continue
            
            # Opposite edge shares no vertices with our edge
            if not (set(face_edge.verts) & edge_verts):
                return face_edge
        
        return None
    
    def distance_to_factor(self, distances, distance):
        """Convert distance to edge slide factor (-1 to 1)"""
        # Determine which direction we're sliding
        if distance >= 0:
            max_dist = distances['positive']
        else:
            max_dist = distances['negative']
        
        if max_dist == 0:
            return 0
        
        # Calculate factor maintaining sign
        factor = distance / max_dist
        
        # Clamp to valid range if requested
        if self.use_clamp:
            factor = max(-1.0, min(1.0, factor))
        
        return factor


def register():
    bpy.utils.register_class(MESH_OT_edge_slide_by_distance)

def unregister():
    bpy.utils.unregister_class(MESH_OT_edge_slide_by_distance)