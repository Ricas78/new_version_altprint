from typing import Optional
from abc import ABC, abstractmethod
import trimesh
from shapely.geometry import MultiPolygon
from Altprint.height_method import HeightMethod


# este arquivo tem como funcionalidade, ler um arquivo em stl, movimentar a peça e depois fatiar ela em planos associados a cada camada (STLslicer), isso é armazenado em um objeto que recebe essas informações e armazena a altura de cada camada, a geometria de cada camada e os limites superior e inferior da peça (SlicedPlanes)


class SlicedPlanes:
    """Represents the section plans obtained from the slicing of an object"""

    _height = float  # A float which represent the height of the section plan
    # A dictionary with heights as keys and MultiPolygon geometries as values
    _planes_dict = dict[_height, MultiPolygon]
    # A tuple of three floats, represent 3D coordinates
    _coord = tuple[float, float, float]
    # A tuple of 2 coords which these coords are upper and lower bounds
    _bounds_coords = tuple[_coord, _coord]

    # constructor method which initializes the "planes" and "bounds" attributes based on the provided parameters
    def __init__(self, planes: _planes_dict, bounds: _bounds_coords):

        self.planes = planes
        self.bounds = bounds

    def get_heights(self):  # method which return the heights layers from dict
        return list(self.planes.keys())


class Slicer(ABC):  # Abstract class
    """Slicer base object"""

    @abstractmethod
    def load_model(self, model_file: str):  # To load a 3D model from a file
        pass

    @abstractmethod
    # To apply a translation to the loaded model
    def translate_model(self, translation):
        pass

    @abstractmethod
    def slice_model(self) -> SlicedPlanes:  # To slice the model and return section planes
        pass


# Concrete implementation of class slicer, specifically for slicing .stl CAD files
class STLSlicer(Slicer):
    """Slice .stl cad files"""

    # Constructor method with argument an instance of HeightMethod (abstract class)
    def __init__(self, height_method: HeightMethod):
        self.height_method = height_method
        self.model: Optional[trimesh.Trimesh] = None

    # Loads an STL mesh from the specified file. It uses the trimesh.load_mesh() function from the trimesh library to read the mesh data from the file
    def load_model(self, model_file: str):
        self.model = trimesh.load_mesh(model_file)

    # The "translation" argument specifies the amount by which the model should be moved in 3D space
    def translate_model(self, translation):
        # The apply_translation() method of the mesh object modifies the coordinates of all vertices by the specified translation vector
        self.model.apply_translation(translation)

    # esse método fatia o modelo carregado em planos de seção (paralelos ao plano XY) em alturas especificadas
    def slice_model(self, heights=None) -> SlicedPlanes:
        if not heights:  # If heights is not provided, it calculates the heights
            heights = self.height_method.get_heights(self.model.bounds)
        # It uses the section_multiplane() function from the trimesh library to obtain the sections
        sections = self.model.section_multiplane([0, 0, 0], [0, 0, 1], heights)
        planes = {}  # empty list to storage the plans
        for i, section in enumerate(sections):  # For each section
            if section:  # If the section is not empty, converts the section polygons to a MultiPolygon and associates it with the corresponding height
                planes[heights[i]] = MultiPolygon(
                    list(section.polygons_full))  # Essa fç vem de <path.py>
            # If the section is empty (no geometry), associates an empty list with the corresponding height
            else:
                # Mesma coisa que planes[heights[i]] = [], só que evita bugs de atributte error
                planes[heights[i]] = MultiPolygon()

        # returns a object containing the plans and the model bounds
        return SlicedPlanes(planes, self.model.bounds)


# In summary, the STLSlicer class loads an STL model, allows translation, and slices it into section planes. The resulting section planes are stored along with their heights and the model bounds in a SlicedPlanes object
