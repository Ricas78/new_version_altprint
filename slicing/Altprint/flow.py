# este código é responsável por construir toda a lógica de como funcionará o fluxo do filamento do bico para mesa
# formado por duas funções

import numpy as np


def calculate(w=0.48, h=0.2, df=1.75, adjust=1.14):  # 1.14
    # quanto de filamento é necessário extrudar pra fazer a área de um raster
    """
    Calculates the flow multiplier factor, using the rounded rectangle model.

    ARGS:
    w: raster width (default 0.48mm) (float)
    h: raster height (default 0.2mm) (float)
    df: filament diameter (default 1.75mm) (float)
    adjust: adjust factor (default 100%) (float)

    RETURNS:
    Flow multiplier factor
    """
    a = 4 * w * h + \
        (np.pi - 4) * h**2  # área de um retângulo arredondado que é a seção transversal do caminho que o bico da impressora 3D vai seguir (o raster)
    b = np.pi * df**2  # área da seção transversal do filamento (cilindrico)
    flow = adjust * a / b  # fator de fluxo é então calculado como a razão dessas duas áreas, ajustada por um fator de ajuste. Isso dá uma medida de quanto filamento precisa ser extrudido para preencher a área do raster
    return flow


def extrude(x, y, flow):
    """
    Generates the extrusion coordinate array.

    ARGS:
    x: x array (array)
    y: y array (array)
    flow: flow multiplier (float)
    RETURNS:
    Extrusion coordinate array (array)
    """
    extrusion = np.zeros(len(
        x))  # usando a função zeros da biblioteca NumPy para criar um array de zeros. O tamanho do array é determinado pelo comprimento do array x, que é o que len(x) retorna.
    for i in range(1, len(x)):  # itera o laço for a quantidade vezes equivalente a quantiade de coordenadas armazenadas na array de coordenadas X
        # distancia entre a coordenada x atual e a anterior
        dx = abs(x[i] - x[i - 1])
        # distancia entre a coordenada y atual e a anterior
        dy = abs(y[i] - y[i - 1])
        # array que armazena o valor da quantidade de filamento utilizada para cada "conjunto" de coordenadas XY que compõem a trajetória até o ponto atual
        extrusion[i] = np.sqrt((dx**2) + (dy**2)) * flow + extrusion[i-1]
    return extrusion
