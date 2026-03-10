from abc import ABC, abstractmethod
import numpy as np


# definição da classe base HeightMethod. A classe HeightMethod herda de ABC, o que a torna uma classe abstrata.
class HeightMethod(ABC):
    """Generates the height values on which the object will be sliced in"""

    @abstractmethod
    # método abstrato, como é decorado com @abstractmethod, qualquer classe concreta que herde de HeightMethod deve fornecer uma implementação para este método
    def get_heights(self, bounds) -> list[float]:
        pass


# definição da classe StandartHeightMethod, que herda de HeightMethod
class StandartHeightMethod(HeightMethod):
    """Evenly spaced layers"""

    # método construtor da classe, ele aceita um parâmetro layer_height com um valor padrão de 0.2
    def __init__(self, layer_height: float):
        self.layer_height = layer_height

    # método que calcula as alturas das camadas com base nos limites fornecidos e na altura da camada definida no construtor, recebe um parâmetro bounds e retorna uma lista de números de ponto flutuante
    def get_heights(self, bounds) -> list[float]:
        # zi é definido como a coordenada Z do primeiro elemento de bounds (ou seja, o limite inferior no eixo z) mais a altura da camada
        zi = bounds[0][2] + self.layer_height
        # zf é definido como a coordenada Z do segundo elemento de bounds (ou seja, o limite superior no eixo z)
        zf = bounds[1][2]
        h = zf - zi  # h é definido como a diferença entre zf e zi, que é a altura total da peça
        # lista de alturas de camada. A função np.linspace é usada para gerar um número de valores igualmente espaçados entre zi e zf. O número de valores é determinado pela altura total h dividida pela altura da camada, arredondada para o número inteiro mais próximo, mais 1 (para incluir a camada que foi subtraída no cáclulo de h)
        heights = list(np.linspace(zi, zf, round(h/self.layer_height)+1))
        # pequeno valor é subtraído da última altura na lista heights. Isso é feito para garantir que a última camada seja incluída na fatia
        heights[-1] = heights[-1]-0.001
        # valores em heights são arredondados para três casas decimais usando a função np.around
        heights = list(np.around(heights, decimals=3))
        return heights  # retorna a lista com as alturas de cada camada
