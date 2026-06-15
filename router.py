#!/usr/bin/env python3
"""
RUT_TRAILBLAZER Routing Engine (igraph Refactored)
Builds a network graph from pre-compiled topology data and calculates routes
using custom NumPy-vectorized weight metrics and igraph's high-speed C solver.
"""

import math
import os
import sqlite3
import numpy as np
import igraph as ig
from typing import Dict, List, Tuple, Any, Optional

# ROAD TYPE CONSTANTS (matching hierarchy from gis_processor.py)
LEVEL_C = "Level C Roads (Unmaintained Dirt)"
LEVEL_B = "Level B Roads (Gravel/Dirt)"
UNVERIFIED_TRAILS = "Unverified Trails / Two-Tracks"
PRIMITIVE_ROADS = "Primitive Roads"
RESIDENTIAL_SHORTCUTS = "Residential Shortcuts"
PAVED_ROADS = "Paved Roads / Highways"

# MULTIPLIER DICTIONARIES
STANDARD_MULTIPLIERS = {
    PAVED_ROADS: 1.0,
    RESIDENTIAL_SHORTCUTS: 1.5,
    LEVEL_B: 3.0,
    PRIMITIVE_ROADS: 4.0,
    LEVEL_C: 6.0,
    UNVERIFIED_TRAILS: 10.0
}

RUT_MULTIPLIERS = {
    LEVEL_C: 1.0,
    LEVEL_B: 1.2,
    UNVERIFIED_TRAILS: 1.5,
    PRIMITIVE_ROADS: 2.0,
    RESIDENTIAL_SHORTCUTS: 5.0,
    PAVED_ROADS: 1000.0  # Heavy penalty
}

ID_TO_ROAD_TYPE = [
    PAVED_ROADS,
    RESIDENTIAL_SHORTCUTS,
    LEVEL_B,
    PRIMITIVE_ROADS,
    LEVEL_C,
    UNVERIFIED_TRAILS
]

ROAD_TYPE_TO_ID = {
    PAVED_ROADS: 0,
    RESIDENTIAL_SHORTCUTS: 1,
    LEVEL_B: 2,
    PRIMITIVE_ROADS: 3,
    LEVEL_C: 4,
    UNVERIFIED_TRAILS: 5
}

def haversine_distance(coord1: Tuple[float, float], coord2: Tuple[float, float]) -> float:
    """
    Calculates the great-circle distance between two points on the Earth's surface
    using the Haversine formula. Returns distance in meters.
    """
    lon1, lat1 = coord1
    lon2, lat2 = coord2
    
    degrees_to_radians = math.pi / 180.0
    phi1 = lat1 * degrees_to_radians
    phi2 = lat2 * degrees_to_radians
    
    delta_phi = (lat2 - lat1) * degrees_to_radians
    delta_lambda = (lon2 - lon1) * degrees_to_radians
    
    a = (math.sin(delta_phi / 2.0) ** 2 +
         math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2)
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    
    earth_radius = 6371000.0
    return earth_radius * c

class RUTRouter:
    def __init__(self):
        self.graph = None
        self.vertices = None      # np.ndarray shape (V, 2)
        self.edges = None         # np.ndarray shape (E, 2)
        self.lengths = None       # np.ndarray shape (E,)
        self.road_types = None    # np.ndarray shape (E,)
        self.db_path = None
        self._coord_buffer = None  # Pre-allocated coordinate buffer to prevent heap fragmentation
        self.graph_components = None
        self.giant_component_idx = -1
        self.vertex_in_giant = None

    @property
    def is_loaded(self) -> bool:
        return self.graph is not None and self.vertices is not None

    def load_geojson(self, geojson_path: str) -> None:
        """
        Loads the GIS network data. Checks if pre-compiled NumPy/SQLite structures
        exist in the same directory, and compiles them if missing.
        """
        dir_name = os.path.dirname(geojson_path)
        if "subset" in os.path.basename(geojson_path).lower():
            npz_path = os.path.join(dir_name, "graph_topology_subset.npz")
            db_path = os.path.join(dir_name, "gis_attributes_subset.db")
        else:
            npz_path = os.path.join(dir_name, "graph_topology.npz")
            db_path = os.path.join(dir_name, "gis_attributes.db")

        if not os.path.exists(npz_path) or not os.path.exists(db_path):
            print("Compiled graph topology files missing. Running compilation...")
            import importlib.util
            spec = importlib.util.spec_from_file_location(
                "compile_graph",
                os.path.abspath(os.path.join(os.path.dirname(__file__), "../data-pipeline/compile_graph.py"))
            )
            compile_graph = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(compile_graph)
            compile_graph.compile_geojson(geojson_path, db_path, npz_path)

        self.load_compiled_graph(npz_path, db_path)

    def load_compiled_graph(self, npz_path: str, db_path: str) -> None:
        """
        Loads the compiled graph topology from a NumPy archive (.npz)
        and builds the igraph Graph.
        """
        print(f"Loading compiled graph topology from {npz_path}...")
        data = np.load(npz_path)
        self.vertices = data["vertices"]      # shape (V, 2)
        self.edges = data["edges"]            # shape (E, 2)
        self.lengths = data["lengths"]        # shape (E,)
        self.road_types = data["road_types"]  # shape (E,)
        self.db_path = db_path

        # Instantiate igraph Graph
        self.graph = ig.Graph(n=len(self.vertices), edges=self.edges)
        
        # Pre-allocate the coordinate buffer with shape (V, 2) to reuse for path geometries
        self._coord_buffer = np.zeros((len(self.vertices), 2), dtype=np.float32)
        
        # Compute weak connected components to identify the giant component
        self.graph_components = self.graph.connected_components(mode="weak")
        self.giant_component_idx = np.argmax([len(c) for c in self.graph_components])
        vertex_comp_indices = np.array(self.graph_components.membership)
        self.vertex_in_giant = (vertex_comp_indices == self.giant_component_idx)
        
        print(f"Graph topology loaded successfully. Vertices: {len(self.vertices)}, Edges: {len(self.edges)}")

    def _get_vectorized_weights(self, unorthodoxy_score: float) -> np.ndarray:
        """
        Calculates weights for all edges in one vectorized NumPy pass.
        """
        mult_std = np.array([STANDARD_MULTIPLIERS[t] for t in ID_TO_ROAD_TYPE], dtype=np.float32)
        mult_rut = np.array([RUT_MULTIPLIERS[t] for t in ID_TO_ROAD_TYPE], dtype=np.float32)
        
        # Interpolate multipliers based on score
        mult = (1.0 - unorthodoxy_score) * mult_std + unorthodoxy_score * mult_rut
        
        # Fetch the multiplier for each edge index
        edge_mults = mult[self.road_types]
        
        return self.lengths * edge_mults

    def find_nearest_node(self, coord: Tuple[float, float]) -> int:
        """
        Finds the closest node index in the graph to the given coordinate (lon, lat)
        using a vectorized NumPy Euclidean distance lookup, filtered to reject
        isolated vertices not in the giant connected component.
        """
        if self.vertices is None:
            raise ValueError("Graph has no nodes. Load data first.")
        
        lon, lat = coord
        # Vectorized Euclidean distance squared (fast approximation)
        dists = (self.vertices[:, 0] - lon) ** 2 + (self.vertices[:, 1] - lat) ** 2
        
        if self.vertex_in_giant is not None:
            # Heavily penalize or mask out vertices that do NOT belong to the main giant component body
            dists[~self.vertex_in_giant] = float('inf')
            
        nearest_idx = int(np.argmin(dists))
        return nearest_idx

    def resolve_edge_attributes(self, edge_ids: List[int]) -> List[Dict[str, Any]]:
        """
        Resolves string names and feature IDs for a list of edge IDs by querying SQLite.
        """
        if not self.db_path or not os.path.exists(self.db_path) or not edge_ids:
            return []
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Query in chunks to prevent SQLite parameter limits (max 999 parameters on older SQLite)
        chunk_size = 500
        resolved_dict = {}
        
        for i in range(0, len(edge_ids), chunk_size):
            chunk = edge_ids[i:i + chunk_size]
            placeholders = ",".join("?" for _ in chunk)
            query = f"SELECT edge_id, name, feature_id, road_type, length FROM edge_attributes WHERE edge_id IN ({placeholders})"
            cursor.execute(query, chunk)
            for row in cursor.fetchall():
                resolved_dict[row[0]] = {
                    "name": row[1],
                    "feature_id": row[2],
                    "road_type": row[3],
                    "length": row[4]
                }
        
        conn.close()
        
        # Map back in the exact order of edge_ids
        resolved = []
        for eid in edge_ids:
            if eid in resolved_dict:
                resolved.append(resolved_dict[eid])
            else:
                resolved.append({
                    "name": "Unnamed Route",
                    "feature_id": "unknown",
                    "road_type": PAVED_ROADS,
                    "length": 0.0
                })
        return resolved

    def calculate_route(self, start: Tuple[float, float], end: Tuple[float, float], unorthodoxy_score: float = 0.5) -> Dict[str, Any]:
        """
        Calculates an anti-efficiency route between start and end coordinates.
        Uses igraph and dynamic vectorized edge weights.
        """
        if not self.is_loaded:
            return {"status": "error", "message": "Graph data is not loaded."}

        unorthodoxy_score = max(0.0, min(1.0, unorthodoxy_score))

        start_node = self.find_nearest_node(start)
        end_node = self.find_nearest_node(end)
        warning_msg = None

        def find_nearest_paved_node(coord: Tuple[float, float]) -> int:
            paved_edge_indices = np.where(self.road_types == ROAD_TYPE_TO_ID[PAVED_ROADS])[0]
            if len(paved_edge_indices) == 0:
                raise ValueError("No paved roads found in graph.")
            paved_nodes_arr = np.unique(self.edges[paved_edge_indices])
            
            # Filter paved nodes to only those in the giant component
            if self.vertex_in_giant is not None:
                paved_nodes_arr = paved_nodes_arr[self.vertex_in_giant[paved_nodes_arr]]
                if len(paved_nodes_arr) == 0:
                    raise ValueError("No paved roads found in the giant component of the graph.")
            
            lon, lat = coord
            all_dists = (self.vertices[:, 0] - lon) ** 2 + (self.vertices[:, 1] - lat) ** 2
            paved_dists = all_dists[paved_nodes_arr]
            best_idx = np.argmin(paved_dists)
            return int(paved_nodes_arr[best_idx])

        try:
            # Vectorized weights array
            weights = self._get_vectorized_weights(unorthodoxy_score)
            
            # Solve using igraph (returns node path)
            vpath = []
            try:
                paths = self.graph.get_shortest_paths(
                    start_node,
                    to=end_node,
                    weights=weights,
                    output="vpath"
                )
                vpath = paths[0]
            except Exception:
                # Direct route failed (raised exception, e.g. unreachable)
                pass

            if not vpath:
                # Direct path failed, try fallbacks
                try:
                    fallback_start_node = find_nearest_paved_node(start)
                    fallback_end_node = find_nearest_paved_node(end)
                except Exception as fe:
                    return {
                        "status": "error",
                        "message": f"Route calculation failed and fallback snapping failed: {fe}"
                    }

                # Try 1: Snap Destination (start_node -> fallback_end_node)
                try:
                    paths = self.graph.get_shortest_paths(
                        start_node,
                        to=fallback_end_node,
                        weights=weights,
                        output="vpath"
                    )
                    vpath = paths[0]
                    if vpath:
                        warning_msg = "Route snapped to nearest accessible roadway due to isolated start/end location."
                except Exception:
                    pass

                # Try 2: Snap Start (fallback_start_node -> end_node)
                if not vpath:
                    try:
                        paths = self.graph.get_shortest_paths(
                            fallback_start_node,
                            to=end_node,
                            weights=weights,
                            output="vpath"
                        )
                        vpath = paths[0]
                        if vpath:
                            warning_msg = "Route snapped to nearest accessible roadway due to isolated start/end location."
                    except Exception:
                        pass

                # Try 3: Snap Both (fallback_start_node -> fallback_end_node)
                if not vpath:
                    try:
                        paths = self.graph.get_shortest_paths(
                            fallback_start_node,
                            to=fallback_end_node,
                            weights=weights,
                            output="vpath"
                        )
                        vpath = paths[0]
                        if vpath:
                            warning_msg = "Route snapped to nearest accessible roadway due to isolated start/end location."
                    except Exception:
                        pass

            if not vpath:
                return {
                    "status": "error",
                    "message": "No routing path could be found between specified coordinates."
                }

            # Reconstruct edge path (epath) from vertex path (vpath)
            epath = self.graph.get_eids(pairs=list(zip(vpath[:-1], vpath[1:])))

            # Write coordinates directly into pre-allocated coordinate buffer to prevent heap fragmentation
            num_nodes = len(vpath)
            if self._coord_buffer is None or len(self._coord_buffer) < num_nodes:
                self._coord_buffer = np.zeros((max(num_nodes * 2, len(self.vertices) if self.vertices is not None else 100000), 2), dtype=np.float32)
            
            # Slice/copy coordinates from self.vertices to the coordinate buffer
            self._coord_buffer[:num_nodes] = self.vertices[vpath]
            
            # Extract coordinates as native Python float tuples from the buffer to ensure JSON serializability
            route_geometry = [(float(coord[0]), float(coord[1])) for coord in self._coord_buffer[:num_nodes]]
            
            # Calculate road type statistics from NumPy arrays directly
            total_distance = 0.0
            road_type_breakdown = {}
            for edge_idx in epath:
                dist = float(self.lengths[edge_idx])
                r_type_id = self.road_types[edge_idx]
                r_type = ID_TO_ROAD_TYPE[r_type_id]
                
                total_distance += dist
                road_type_breakdown[r_type] = road_type_breakdown.get(r_type, 0.0) + dist

            # Resolve segment street names and feature IDs from SQLite
            resolved_segments = self.resolve_edge_attributes(epath)

            response = {
                "status": "success",
                "unorthodoxy_score": unorthodoxy_score,
                "total_distance_meters": total_distance,
                "road_type_breakdown_meters": road_type_breakdown,
                "coordinates": route_geometry,
                "segments": resolved_segments
            }
            if warning_msg:
                response["warning"] = warning_msg

            return response

        except Exception as e:
            return {
                "status": "error",
                "message": f"Route calculation failed: {e}"
            }

    def bail_out(self, current_coord: Tuple[float, float]) -> Dict[str, Any]:
        """
        Bail Out Logic: Find the absolute physically shortest path to the nearest paved road.
        Uses physical distance ('length') with no off-road multipliers.
        Uses a high-speed NumPy geometric bounding pass to identify the single closest paved node
        before solving, keeping execution time in milliseconds.
        """
        if not self.is_loaded:
            return {"status": "error", "message": "Graph data is not loaded."}

        start_node = self.find_nearest_node(current_coord)
        
        # Find all nodes that touch a paved road
        paved_edge_indices = np.where(self.road_types == ROAD_TYPE_TO_ID[PAVED_ROADS])[0]
        if len(paved_edge_indices) == 0:
            return {
                "status": "error",
                "message": "No paved roads found in graph to bail out to."
            }

        paved_nodes_arr = np.unique(self.edges[paved_edge_indices])
        
        # Filter paved nodes to only those in the giant component
        if self.vertex_in_giant is not None:
            paved_nodes_arr = paved_nodes_arr[self.vertex_in_giant[paved_nodes_arr]]
            if len(paved_nodes_arr) == 0:
                return {
                    "status": "error",
                    "message": "No paved roads found in the giant component to bail out to."
                }

        if start_node in paved_nodes_arr:
            start_pt = self.vertices[start_node]
            return {
                "status": "success",
                "total_distance_meters": 0.0,
                "coordinates": [(float(start_pt[0]), float(start_pt[1]))],
                "segments": []
            }

        try:
            lon, lat = current_coord
            
            # 1. Compute distance to ALL vertices in the master graph simultaneously (In-Place, No Slicing)
            all_dists = (self.vertices[:, 0] - lon) ** 2 + (self.vertices[:, 1] - lat) ** 2
            
            # 2. Extract only the distances for nodes that touch a paved road using the index mask
            paved_dists = all_dists[paved_nodes_arr]
            
            # 3. Find the minimum index relative to the paved subset, and map it back instantly
            best_idx = np.argmin(paved_dists)
            target_paved_node = int(paved_nodes_arr[best_idx])

            # 2. Targeted single-pair SSSP using igraph
            paths = self.graph.get_shortest_paths(
                start_node,
                to=target_paved_node,
                weights=self.lengths,
                output="vpath"
            )
            vpath = paths[0]
            
            if not vpath:
                return {
                    "status": "error",
                    "message": "Failed to calculate a bail out route to nearest highway."
                }

            epath = self.graph.get_eids(pairs=list(zip(vpath[:-1], vpath[1:])))
            min_dist = float(np.sum(self.lengths[epath]))

            # Write coordinates directly into pre-allocated coordinate buffer to prevent heap fragmentation
            num_nodes = len(vpath)
            if self._coord_buffer is None or len(self._coord_buffer) < num_nodes:
                self._coord_buffer = np.zeros((max(num_nodes * 2, len(self.vertices) if self.vertices is not None else 100000), 2), dtype=np.float32)
            
            self._coord_buffer[:num_nodes] = self.vertices[vpath]
            
            # Extract coordinates as native Python float tuples from the buffer to ensure JSON serializability
            route_geometry = [(float(coord[0]), float(coord[1])) for coord in self._coord_buffer[:num_nodes]]
            resolved_segments = self.resolve_edge_attributes(epath)

            return {
                "status": "success",
                "total_distance_meters": min_dist,
                "coordinates": route_geometry,
                "segments": resolved_segments
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to calculate a bail out route to nearest highway: {e}"
            }
        finally:
            # Ensure C-allocation cleanup is safely executed
            try:
                self.graph.__invalidate_cache()
            except Exception:
                pass

    def cleanup(self) -> None:
        """
        Explicitly invalidates internal C-caches and releases memory allocated
        by the igraph C core during routing calculations.
        
        Note: If a custom C extension lacks exposed python APIs, standard ctypes
        can be used to bind to C free() or custom destroy handlers. Example:
        
        # import ctypes
        # libc = ctypes.CDLL(None) or ctypes.cdll.msvcrt
        # libc.free(pointer)
        """
        if self.graph is not None:
            try:
                # Invalidate internal igraph C caches to free lazy incidence/adjacency lists
                self.graph.__invalidate_cache()
            except Exception:
                pass
