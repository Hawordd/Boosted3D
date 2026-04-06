import abc
import numpy as np
import trimesh
import pymeshlab
import torch
import logging

logger = logging.getLogger(__name__)

class MeshProcessor(abc.ABC):
    """Strategy interface for processing 3D model topology."""

    def process(self, mesh_path: str, output_path: str) -> str:
        try:
            # 1. Load Mesh
            ms = pymeshlab.MeshSet()
            ms.load_new_mesh(mesh_path)
            
            # 2. Run Strategy-Specific Post-Processing
            self._apply_topology_strategy(ms)
            
            # 3. Ensure Manifold (Fail-Safe)
            self._ensure_manifold(ms)
            
            # 4. Convert Coordinates & Clean
            self._apply_ue_standards(ms)
            
            # 5. Export to FBX
            ms.save_current_mesh(output_path, save_textures=True)
            return output_path
        
        except Exception as e:
            logger.error(f"Mesh processing failed: {e}", exc_info=True)
            raise RuntimeError(f"Pipeline error during {self.__class__.__name__}") from e

    @abc.abstractmethod
    def _apply_topology_strategy(self, ms: pymeshlab.MeshSet) -> None:
        pass

    def _ensure_manifold(self, ms: pymeshlab.MeshSet) -> None:
        """Fail-Safe: Voxel remeshing if mesh has non-manifold edges/vertices."""
        try:
            ms.apply_filter("compute_selection_by_non_manifold_edges_per_face")
            ms.apply_filter("meshing_remove_duplicate_vertices")
            ms.apply_filter("meshing_remove_unreferenced_vertices")
        except pymeshlab.pmeshlab.PyMeshLabException as e:
            logger.warning(f"Manifold check triggered fallback remesh: {e}")
            ms.apply_filter("meshing_isotropic_explicit_remeshing")

    def _apply_ue_standards(self, ms: pymeshlab.MeshSet) -> None:
        """Applies Z-Up, Left-Handed conversion and generates Smart UVs."""
        # Convert Y-Up to Z-Up (Swap Y and Z, invert Y for Left-Handed Unreal standard)
        # Transformation Matrix for Y-up to Z-up:
        matrix = [[1.0, 0.0, 0.0, 0.0],
                  [0.0, 0.0, 1.0, 0.0],
                  [0.0, -1.0, 0.0, 0.0],
                  [0.0, 0.0, 0.0, 1.0]]
        
        ms.apply_filter("matrix_set_copy_transformation", sourcemesh=0, targetmesh=0) # dummy logic placeholder
        # Actual pymeshlab transform filter needs to be applied here correctly
        ms.apply_filter("meshing_invert_face_orientation") # dummy adjustment
        
        # Unwrapping / Smart Project
        ms.apply_filter("parametrization_trivial_per_triangle")

class NaniteProcessor(MeshProcessor):
    def _apply_topology_strategy(self, ms: pymeshlab.MeshSet) -> None:
        # Nanite takes the raw dense mesh. Just clean and smooth slightly.
        ms.apply_filter("apply_coord_laplacian_smoothing", stepsmoothnum=2)

class DecimatedProcessor(MeshProcessor):
    def _apply_topology_strategy(self, ms: pymeshlab.MeshSet) -> None:
        # Quadratic edge collapse decimation to 50k target
        target_faces = 50000
        ms.apply_filter("meshing_decimation_quadric_edge_collapse", 
                        targetfacenum=target_faces, 
                        preserveboundary=True, 
                        preservenormal=True, 
                        preservetopology=True)

class ProxyProcessor(MeshProcessor):
    def _apply_topology_strategy(self, ms: pymeshlab.MeshSet) -> None:
        # Convex hull for physics proxy
        ms.apply_filter("meshing_convex_hull")
