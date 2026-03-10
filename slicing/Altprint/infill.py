from abc import ABC, abstractmethod
from shapely.geometry import MultiLineString
# The Layer class likely contains information about layer shapes, perimeters, and other relevant details
from Altprint.layer import Layer


class InfillMethod(ABC):  # a base class for infill methods

    @abstractmethod
    # takes a "Layer" object as an argument, the method should return a MultiLineString representing the infill paths for that layer
    def generate_infill(self, layer: Layer) -> MultiLineString:
        pass

    @abstractmethod
    # takes a "Layer" object as an argument, the method should return a MultiLineString representing the infill paths for that layer
    def generate_continuous_infill(self, layer: Layer) -> MultiLineString:
        pass
