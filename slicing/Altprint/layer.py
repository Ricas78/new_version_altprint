from shapely.geometry import Polygon, MultiPolygon, LineString, MultiLineString
from Altprint.best_path import *
import numpy as np
from Altprint.flow import calculate

# from itertools import permutations
# from shapely.geometry import LineString, Point
# from shapely.ops import nearest_points  # Correção na importação
# from itertools import permutations, product

# import shapely as sp


# Define como será feito o percurso do raster (trajetória extrudindo) e como será lógica da construção de camadas que é dividida em perimetro e prenchimento


class Raster:  # Esta classe representa um caminho raster na impressão

    # método que inicializa o raster com os seguintes parâmetros: path: Um LineString representando o caminho do bico da impressora, flow: O fator multiplicador de fluxo (calculado usando a função de cálculo), speed: A velocidade de impressão (valor escalar)
    def __init__(self, path: LineString, flow, speed):

        self.path = path  # "path" é armazenado como uma variável de instância

        # "speed" é usada para criar uma matriz de velocidades (uma para cada ponto coordenado no caminho)
        self.speed = np.ones(len(path.coords)) * speed
        # A matriz de extrusão é inicializada com zeros (para acumular valores de extrusão)
        self.extrusion = np.zeros(len(path.coords))
        x, y = path.xy  # Extrai as coordenadas X e Y de "path"
        # itera o laço a quantidade de vezes equivalente a quantiade de coordenadas armazenadas na array "path"
        for i in range(1, len(path.coords)):
            # distância entre a coordenada x atual e a anterior
            dx = abs(x[i] - x[i - 1])
            # distância entre a coordenada y atual e a anterior
            dy = abs(y[i] - y[i - 1])
            # array que armazena o valor da quantidade de filamento utilizada para cada "conjunto" de coordenadas XY que compõe a traetória do raster até o ponto atual
            self.extrusion[i] = np.sqrt(
                (dx**2) + (dy**2)) * flow * calculate() + self.extrusion[i-1]


class Layer:  # class represents a layer in a 3D printing process
    """Layer Object that stores layer internal and external shapes, also perimeters and infill path"""  # noqa: E501

    def __init__(self, shape: MultiPolygon, perimeter_num, perimeter_to_perimeter_gap, perimeter_to_infill_gap, external_adjust, overlap):  # method that initializes the layer # noqa: E501
        # A MultiPolygon representing the layer’s shape (both internal and external)
        self.shape = shape
        self.perimeter_num = perimeter_num  # The number of perimeters for this layer
        # A parameter related to the spacing between perimeters
        self.perimeter_to_perimeter_gap = perimeter_to_perimeter_gap

        self.perimeter_to_infill_gap = perimeter_to_infill_gap
        # An adjustment factor specific to external shapes
        self.external_adjust = external_adjust
        # A value indicating how much overlap there is between adjacent perimeters
        self.overlap = overlap
        self.perimeter_paths: List = []  # noqa: F821 #A list (initialized as empty) to store the paths of individual perimeters
        self.perimeter: List = []  # noqa: F821 #list (initialized as empty) for additional perimeter-related information
        self.infill: List = []  # noqa: F821 #list to store information related to infill paths
        # A MultiPolygon (initialized as an empty MultiPolygon) representing the border of the infill area
        self.infill_border: MultiPolygon = MultiPolygon()

    def make_perimeter(self):  # Este método constrói os caminhos de perímetro para uma camada erodindo a forma da camada e extraindo os segmentos de limite (externo) e furo (interno). Esses segmentos são armazenados no atributo perimeter_paths
        """Generates the perimeter based on the layer process"""

        # empty list "perimeter_paths" to store the individual segments of the perimeter
        perimeter_paths = []
        # the loop iterates through each section (geometry) within the layer’s shape (which is a MultiPolygon)
        for section in self.shape.geoms:
            for i in range(self.perimeter_num):  # the loop iterates number of perimeters
                eroded_shape = section.buffer(- self.perimeter_to_perimeter_gap*(i)
                                              - self.external_adjust/2, join_style=2)  # Calculates an “eroded shape” by buffering the section with a negative distance
                # The negative distance is determined by subtracting the product of self.perimeter_gap * i and self.external_adjust / 2. The join_style=2 argument specifies how the buffer should handle intersections

                # If the eroded shape is empty (has no geometry), the loop breaks
                if eroded_shape.is_empty:
                    break
                # If the eroded shape is a single Polygon, it creates a list containing that polygon
                if type(eroded_shape) == Polygon:
                    polygons = [eroded_shape]
                # If the eroded shape is a MultiPolygon, it extracts the individual polygons from it
                elif type(eroded_shape) == MultiPolygon:
                    polygons = list(eroded_shape.geoms)

                # For each polygon (both exterior and interior)
                for poly in polygons:
                    for hole in poly.interiors:
                        # Adds the interior rings (holes) as individual LineString segments to perimeter_paths
                        perimeter_paths.append(LineString(hole))
                for poly in polygons:
                    # Adds the exterior ring (boundary) as a LineString segment to perimeter_paths
                    perimeter_paths.append(LineString(poly.exterior))
        # assigns the entire perimeter_paths list (composed of all the segments) to the self.perimeter_paths attribute (which is a MultiLineString)
        self.perimeter_paths = MultiLineString(perimeter_paths)

    def make_infill_border(self):  # method constructs the infill border for a layer by eroding the layer’s shape and extracting the individual polygons that form the border. These polygons are stored in the infill_border attribute
        """Generates the infill border based on the layer process"""

        # empty list called infill_border_geoms to store the individual geometries (polygons) of the infill border
        infill_border_geoms = []
        # the loop iterates through each section (geometry) within the layer’s shape (which is a MultiPolygon)
        for section in self.shape.geoms:
            eroded_shape = section.buffer(- self.perimeter_to_infill_gap
                                          * self.perimeter_num
                                          - self.external_adjust/2
                                          + self.overlap, join_style=2)  # Calculates an “eroded shape” by buffering the section with a negative distance
            if not eroded_shape.is_empty:  # If the eroded shape is not empty
                # If the eroded shape is a single Polygon, it appends it to the infill_border_geoms list
                if type(eroded_shape) == Polygon:
                    infill_border_geoms.append(eroded_shape)
                else:
                    # If the eroded shape is a MultiPolygon, it extends the list with the individual polygons extracted from it
                    infill_border_geoms.extend(eroded_shape.geoms)

        # the entire infill_border_geoms list (composed of all the individual geometries) to the self.infill_border attribute (which is a MultiPolygon)
        self.infill_border = MultiPolygon(infill_border_geoms)


class ContinuousLayer(Layer):
    """Enhanced Layer class generating continuous paths for perimeter and infill"""

    def __init__(self, shape: MultiPolygon, perimeter_num, perimeter_to_perimeter_gap, perimeter_to_infill_gap, external_adjust, overlap, flex_print_instance):

        super().__init__(shape, perimeter_num, perimeter_to_perimeter_gap,
                         perimeter_to_infill_gap, external_adjust, overlap)
        self.continuous_perimeter_paths: List[LineString] = []
        self.continuous_infill_paths: List[LineString] = []
        self.flex_print_ref = flex_print_instance

    def make_perimeter(self):
        """Generates the perimeter based on the layer process"""

        perimeter_paths = []

        for section in self.shape.geoms:
            for i in range(self.perimeter_num):
                eroded_shape = section.buffer(- self.perimeter_to_perimeter_gap*(i)
                                              - self.external_adjust/2, join_style=2)

                if eroded_shape.is_empty:
                    break

                if type(eroded_shape) == Polygon:
                    polygons = [eroded_shape]

                elif type(eroded_shape) == MultiPolygon:
                    polygons = list(eroded_shape.geoms)

                for poly in polygons:
                    for hole in poly.interiors:

                        perimeter_paths.append(LineString(hole))
                for poly in polygons:

                    perimeter_paths.append(LineString(poly.exterior))

        # Rearrange for Continuous Path

        if (self.flex_print_ref.last_loop == []):  # skirt condition

            perimeter_paths = bestPath_skirt(perimeter_paths)

        else:  # perimeter condition

            last_loop = self.flex_print_ref.last_loop

            Raw_perimeter_paths = [RawList_Points(
                k, makeTuple=True) for k in perimeter_paths]
            Raw_last_loop = RawList_Points(last_loop, makeTuple=True)

            perimeter_paths = bestPath_Infill2Perimeter(
                Raw_perimeter_paths, Raw_last_loop)

        perimeter_paths = MultiLineString(perimeter_paths)

        self.flex_print_ref.last_loop = perimeter_paths.geoms[-1]
        self.perimeter_paths = perimeter_paths

    def make_infill_border(self):
        """Generates the infill border based on the layer process"""

        # empty list called infill_border_geoms to store the individual geometries (polygons) of the infill border
        infill_border_geoms = []
        # the loop iterates through each section (geometry) within the layer’s shape (which is a MultiPolygon)
        for section in self.shape.geoms:
            eroded_shape = section.buffer(- self.perimeter_to_infill_gap
                                          * self.perimeter_num
                                          - self.external_adjust/2
                                          + self.overlap, join_style=2)  # Calculates an “eroded shape” by buffering the section with a negative distance
            if not eroded_shape.is_empty:  # If the eroded shape is not empty
                # If the eroded shape is a single Polygon, it appends it to the infill_border_geoms list
                if type(eroded_shape) == Polygon:
                    infill_border_geoms.append(eroded_shape)
                else:
                    # If the eroded shape is a MultiPolygon, it extends the list with the individual polygons extracted from it
                    infill_border_geoms.extend(eroded_shape.geoms)

        # the entire infill_border_geoms list (composed of all the individual geometries) to the self.infill_border attribute (which is a MultiPolygon)
        self.infill_border = MultiPolygon(infill_border_geoms)


# import matplotlib.pyplot as plt
# from shapely.geometry import Polygon, MultiPolygon, LineString, MultiLineString
# import numpy as np

# def visualize_make_perimeter():
#     # Create a test shape with a hole
#     exterior = Polygon([(0, 0), (10, 0), (10, 8), (0, 8)])
#     hole = Polygon([(3, 3), (7, 3), (7, 5), (3, 5)])
#     shape_with_hole = exterior.difference(hole)

#     # Create layer parameters
#     perimeter_num = 3
#     perimeter_gap = 0.8
#     external_adjust = 0.2
#     overlap = 0.1

#     # Create the layer
#     layer = type('Layer', (), {})()  # Simple object to mimic Layer
#     layer.shape = MultiPolygon([shape_with_hole])
#     layer.perimeter_num = perimeter_num
#     layer.perimeter_gap = perimeter_gap
#     layer.external_adjust = external_adjust
#     layer.overlap = overlap

#     # Modified make_perimeter for visualization
#     def make_perimeter_visual(layer):
#         perimeter_paths = []
#         all_eroded_shapes = []  # Store all eroded shapes for visualization
#         all_polygons = []  # Store individual polygons at each step

#         print("=== Perimeter Generation Process ===")

#         for section_idx, section in enumerate(layer.shape.geoms):
#             print(f"\nProcessing section {section_idx + 1}")

#             for i in range(layer.perimeter_num):
#                 print(f"  Creating perimeter {i + 1}")

#                 # Calculate erosion distance
#                 erosion_distance = -layer.perimeter_gap * i - layer.external_adjust / 2
#                 print(f"    Erosion distance: {erosion_distance:.3f}")

#                 # Erode the shape
#                 eroded_shape = section.buffer(erosion_distance, join_style=2)
#                 all_eroded_shapes.append((i, eroded_shape))

#                 if eroded_shape.is_empty:
#                     print("    Shape is empty - stopping")
#                     break

#                 # Handle polygon types
#                 if type(eroded_shape) == Polygon:
#                     polygons = [eroded_shape]
#                     print(f"    Single polygon created")
#                 elif type(eroded_shape) == MultiPolygon:
#                     polygons = list(eroded_shape.geoms)
#                     print(f"    MultiPolygon with {len(polygons)} polygons")

#                 all_polygons.extend(polygons)

#                 # Extract paths
#                 for poly in polygons:
#                     # Interior paths (holes)
#                     for hole_idx, hole in enumerate(poly.interiors):
#                         path = LineString(hole)
#                         perimeter_paths.append(path)
#                         print(f"    Added interior path {hole_idx + 1} (length: {path.length:.3f})")

#                     # Exterior path
#                     exterior_path = LineString(poly.exterior)
#                     perimeter_paths.append(exterior_path)
#                     print(f"    Added exterior path (length: {exterior_path.length:.3f})")

#         layer.perimeter_paths = MultiLineString(perimeter_paths)
#         return all_eroded_shapes, all_polygons, perimeter_paths

#     # Generate and visualize
#     eroded_shapes, all_polygons, paths = make_perimeter_visual(layer)

#     # Create visualization
#     fig, axes = plt.subplots(2, 2, figsize=(15, 12))
#     axes = axes.flatten()

#     # Plot 1: Original shape and eroded shapes
#     ax1 = axes[0]
#     ax1.set_title('1. Original Shape and Eroded Layers')

#     # Plot original shape
#     x, y = shape_with_hole.exterior.xy
#     ax1.plot(x, y, 'k-', linewidth=3, label='Original Shape')

#     # Plot holes
#     for interior in shape_with_hole.interiors:
#         x, y = interior.xy
#         ax1.plot(x, y, 'k-', linewidth=3)

#     # Plot eroded shapes with different colors
#     colors = ['red', 'blue', 'green', 'orange', 'purple']
#     for i, (perim_num, eroded_shape) in enumerate(eroded_shapes):
#         if not eroded_shape.is_empty:
#             if type(eroded_shape) == Polygon:
#                 x, y = eroded_shape.exterior.xy
#                 ax1.plot(x, y, color=colors[i], linewidth=2,
#                         label=f'Perimeter {perim_num + 1}')
#                 for interior in eroded_shape.interiors:
#                     x, y = interior.xy
#                     ax1.plot(x, y, color=colors[i], linewidth=2)
#             else:
#                 for poly in eroded_shape.geoms:
#                     x, y = poly.exterior.xy
#                     ax1.plot(x, y, color=colors[i], linewidth=2,
#                             label=f'Perimeter {perim_num + 1}' if i == 0 else "")
#                     for interior in poly.interiors:
#                         x, y = interior.xy
#                         ax1.plot(x, y, color=colors[i], linewidth=2)

#     ax1.legend()
#     ax1.set_aspect('equal')
#     ax1.grid(True, alpha=0.3)

#     # Plot 2: Individual polygons after erosion
#     ax2 = axes[1]
#     ax2.set_title('2. Individual Polygons After Processing')

#     for i, poly in enumerate(all_polygons):
#         x, y = poly.exterior.xy
#         ax2.plot(x, y, color=colors[i % len(colors)], linewidth=2,
#                 label=f'Polygon {i + 1}' if i < 5 else "")

#         for interior in poly.interiors:
#             x, y = interior.xy
#             ax2.plot(x, y, color=colors[i % len(colors)], linewidth=2)

#     ax2.legend()
#     ax2.set_aspect('equal')
#     ax2.grid(True, alpha=0.3)

#     # Plot 3: Final perimeter paths (disconnected)
#     ax3 = axes[2]
#     ax3.set_title('3. Final Perimeter Paths (Disconnected)')

#     for i, path in enumerate(paths):
#         x, y = path.xy
#         ax3.plot(x, y, color=colors[i % len(colors)], linewidth=2,
#                 label=f'Path {i + 1}' if i < 5 else "")

#         # Mark start and end points
#         ax3.plot(x[0], y[0], 'go', markersize=8, label='Start' if i == 0 else "")
#         ax3.plot(x[-1], y[-1], 'ro', markersize=8, label='End' if i == 0 else "")

#     ax3.legend()
#     ax3.set_aspect('equal')
#     ax3.grid(True, alpha=0.3)

#     # Plot 4: Comparison with continuous paths
#     ax4 = axes[3]
#     ax4.set_title('4. Comparison: Regular vs Continuous Paths')

#     # Plot regular paths (disconnected)
#     for i, path in enumerate(paths):
#         x, y = path.xy
#         ax4.plot(x, y, 'b-', linewidth=1, alpha=0.5, label='Regular' if i == 0 else "")
#         ax4.plot(x[0], y[0], 'go', markersize=6)
#         ax4.plot(x[-1], y[-1], 'ro', markersize=6)

#     # Simulate what continuous paths would look like (simplified)
#     # In reality, you'd use the ContinuousLayer class
#     if len(paths) >= 2:
#         # Connect first two paths for demonstration
#         last_point = paths[0].coords[-1]
#         first_point = paths[1].coords[0]
#         connection = LineString([last_point, first_point])
#         x, y = connection.xy
#         ax4.plot(x, y, 'm--', linewidth=2, label='Travel Move')

#     ax4.legend()
#     ax4.set_aspect('equal')
#     ax4.grid(True, alpha=0.3)

#     plt.tight_layout()
#     plt.show()

#     # Print statistics
#     print(f"\n=== Statistics ===")
#     print(f"Total perimeter paths generated: {len(paths)}")
#     print(f"Total perimeter length: {sum(path.length for path in paths):.2f}")
#     print(f"Number of travel moves needed: {len(paths) - 1}")
#     print(f"Erosion distances used: {[-layer.perimeter_gap*i - layer.external_adjust/2 for i in range(layer.perimeter_num)]}")

# # Run the visualization
# visualize_make_perimeter()
