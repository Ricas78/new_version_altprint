from shapely.geometry import Polygon, MultiLineString
from shapely.affinity import translate, rotate
import numpy as np
from Altprint.infill import InfillMethod
from Altprint.layer import Layer

from Altprint.best_path import *

# arquivo define como será feito o tipo/caminho do preenchimento (raster), cada área de cada camada tem suas colunas de preenchimento e de buracos além de definir a estratégia de preenchimento pela rotação e translação de segmentos


def x_from_y(a, b, yc):
    dx = b[0]-a[0]  # distância x do segmento
    dy = b[1]-a[1]  # distância y do segmento
    if dx == 0:  # Se o segmento de linha for vertical
        # Cria um array de valores iguais à coordenada x do ponto a, com o mesmo tamanho que o array yc
        return np.ones(len(yc))*a[0]
    # Caso contrário, ela calcula a coordenada x usando interpolação linear com base na inclinação (dx/dy) entre a e b
    return (yc - a[1])*dx/dy + a[0]


# essa função me diz quais colunas serão de prenchimento e quais de buracos dentro da area de cada camada
def get_column(a, b, gap, height, hole):
    # verifica quem dos pontos (a ou b) possui maior valor na componente y e salva na variável esse valor
    maxy = max(a[1], b[1])
    # verifica quem dos pontos (a ou b) possui menor valor na componente y e salva na variável esse valor
    miny = min(a[1], b[1])
    # determina o limite superior e inferior da faixa de coordenadas y coberta pelo segmento
    # distância y do segmento, representa a inclinação vertical do segmento
    dy = b[1] - a[1]
    # Divide o valor mínimo de y pelo tamanho do espaçamento entre os segmentos de preenchimento (gap) e arredonda para cima
    start = int(np.ceil(miny/gap))
    # Divide o valor máximo de y pelo tamanho do espaçamento entre os segmentos de preenchimento (gap), arredonda para baixo e adiciona 1
    end = int(np.floor(maxy/gap)+1)
    # Cria um array de coordenadas y dentro da faixa especificada (start a end)
    ys = np.arange(start, end)*gap
    xs = x_from_y(a, b, ys)  # Calcula as coordenadas x correspondentes
    # Inicializa um array de máscara com todos os valores iguais a 1, esse array será usado para mascarar as coordenadas x que não estão dentro da faixa de y
    mask = np.ones(height)
    mask[start:end] = 0  # Define os valores da máscara como 0 para os índices dentro da faixa de y, isso indica que essas coordenadas x são válidas e não devem ser mascaradas
    # array mascarado inicializado com zeros, os valores dentro da faixa de y são mantidos, enquanto os valores fora da faixa são mascarados
    col = np.ma.array(np.zeros(height), mask=mask)
    col[start:end] = xs
    if dy > 0:  # se o segmento é no sentido positivo
        if not hole:  # se é preenchimento
            # as colunas estão contidas na faixa y (max/min), portanto mascara 0 e há preenchimento
            fill_col = np.ma.array(np.zeros(height), mask=mask)
        else:
            # as colunas não estão contidas na faixa y, portanto mascara 1 e não há preenchimento
            fill_col = np.ma.array(np.ones(height), mask=mask)
    else:  # se o segmento é no sentido negativo
        if not hole:  # se é preenchimento
            # as colunas não estão contidas na faixa y, portanto mascara 1 e não há preenchimento
            fill_col = np.ma.array(np.ones(height), mask=mask)
        else:
            # as colunas estão contidas na faixa y (max/min), portanto mascara 0 e há preenchimento
            fill_col = np.ma.array(np.zeros(height), mask=mask)
    # Inicializa um array mascarado used_col com zeros, esse array pode ser usado para rastrear quais coordenadas x foram usadas
    used_col = np.ma.array(np.zeros(height), mask=mask)
    # Retorna os arrays como uma tupla, esses arrays representam a coluna de coordenadas x, o preenchimento e o rastreamento de uso para o segmento de linha
    return col, fill_col, used_col


def get_cols(shape, gap, thres, height, hole):
    if not shape.is_ccw:  # Verifica se a forma não está definida no sentido anti-horário
        coords = shape.coords[::-1]  # inverte a ordem das coordenadas
    else:
        # mantém a ordem original das coordenadas, essas coordenadas representam os vértices da forma
        coords = shape.coords
    # Inicializa listas vazias para armazenar os dados das colunas, informações de preenchimento e rastreamento das colunas usadas
    cols = []
    fill = []
    used = []
    # Itera através de pares consecutivos de coordenadas na forma
    for i in range(len(coords)-1):
        # Atribui a coordenada atual (a) e a próxima coordenada (b) às variáveis
        a = coords[i]
        b = coords[i+1]
        # Calcula a diferença entre as coordenadas y de "b" e "a", isso representa a inclinação vertical do segmento
        dy = b[1] - a[1]
        if abs(dy) > thres:  # Verifica se o valor absoluto da inclinação excede um limite (thres)
            # gera os dados da coluna usando a função get_column
            col, fill_col, used_col = get_column(a, b, gap, height, hole)
            # adiciona as respectivas listas
            cols.append(col)
            fill.append(fill_col)
            used.append(used_col)
    # Retorna arrays mascarados para as colunas, preenchimento e colunas usadas como uma tupla
    return np.ma.array(cols), np.ma.array(fill), np.ma.array(used)


def sort_cols(cols, fill, used):
    # r = list(range(cols.shape[1])) + list(range(cols.shape[1]-2, -1, -1))
    # lista r contendo os índices das colunas (colunas de coordenadas x)
    r = list(range(cols.shape[1]))
    for i in r:  # Itera através dos índices das colunas
        # Atribui a coluna de coordenadas x correspondente ao índice i à variável "col"
        col = cols[:, i]
        # Encontra os índices válidos (ou seja, não mascarados) na coluna, os índices são determinados pelos valores não nulos na coluna
        valid_indexes = (col+1).nonzero()[0]
        # Classifica os índices válidos com base nos valores correspondentes na coluna. Isso garante que as colunas sejam reorganizadas corretamente
        sorted_indexes = valid_indexes[col[valid_indexes].argsort()]
        # Atualiza as colunas, informações de preenchimento e rastreamento de uso com os índices reorganizados
        cols[[valid_indexes]] = cols[[sorted_indexes]]
        fill[[valid_indexes]] = fill[[sorted_indexes]]
        used[[valid_indexes]] = used[[sorted_indexes]]


# encontrar a próxima linha (ou coordenada y) para preenchimento
def next_line(cols, fill, i, j, d):
    # Obtém as dimensões da matriz de colunas (número de linhas e colunas)
    m, n = cols.shape
    # Verifica se o valor de preenchimento na posição (i, j) é o oposto de d
    if fill[i][j] == int(not d):
        return None
    if d:  # se "d" for verdadeiro, o intervalo vai de i até m
        r = range(i, m)
    # Caso contrário, o intervalo vai de i até -1 (ou seja, de i até 0, em ordem decrescente)
    else:
        r = range(i, -1, -1)
    for k in r:  # Itera através dos índices no intervalo r
        # Verifica se o valor de preenchimento na posição (k, j) é o oposto de d
        if fill[k][j] == int(not d):
            return k  # Se for verdadeiro, retorna o índice k


# encontrar a próxima coluna (ou coordenada x) para preenchimento contínuo
def next_con(cols, fill, i, j):
    m, n = cols.shape  # Obtém as dimensões da matriz de colunas
    next_con = j+1  # Define o próximo índice de coluna
    if next_con < n:  # Verifica se o próximo índice de coluna está dentro dos limites da matriz
        if not cols.mask.any():  # Verifica se a matriz de colunas não possui nenhum valor mascarado (ou seja, todos os valores são válidos)
            return next_con
        # verifica se o valor na posição (i, next_con) não está mascarado
        elif not cols.mask[i][next_con]:
            return next_con  # retorna o próximo índice
    return None  # retorna vazio se o próximo indice estiver fora dos limites


def find_path(cols, fill, used, i0, j0, d, gap):
    # Inicializa as coordenadas iniciais e o caminho
    i, j = i0, j0
    path = [(cols[i][j], j*gap)]
    used[i][j] = 1  # Marca a coluna como usada
    while True:
        # Encontra a próxima linha para preenchimento
        # Calcula o próximo índice de linha para preenchimento contínuo
        k = next_line(cols, fill, i, j, d)
        if k is not None:  # Verifica se o índice de linha calculado é válido
            if used[k][j] == 0:  # Verifica se a coluna correspondente à linha k ainda não foi usada
                used[k][j] = 1  # Se for verdadeiro, marca a coluna como usada
                i = k  # Atualiza o índice de linha atual para k, isso move o preenchimento para a próxima linha
                # Inverte a direção do preenchimento (de ascendente para descendente ou vice-versa)
                d = not d
                # Adiciona a coordenada atual (calculada a partir das colunas) ao caminho
                path.append((cols[i][j], j*gap))
            else:
                # Retorna o caminho atual (que foi construído até agora). Isso ocorre quando não é possível encontrar uma próxima linha para preenchimento
                return path
        else:
            return path
        # Calcula o próximo índice de coluna para preenchimento contínuo
        l1 = next_con(cols, fill, i, j)
        if l1 is not None:  # Verifica se o índice de coluna calculado é válido
            # Verifica se a coluna correspondente à linha i e coluna l1 ainda não foi usada
            if used[i][l1] == 0:
                used[i][l1] = 1  # Se for verdadeiro, marca a coluna como usada
                j = l1  # Atualiza o índice de coluna atual para l1
                # Adiciona a coordenada atual (calculada a partir das colunas) ao caminho
                path.append((cols[i][j], j*gap))
            else:
                return path
        else:
            return path


# Essa função tem como objetivo gerar caminhos de preenchimento retilenar (ou seja, com ângulos retos) dentro de uma matriz de colunas
def get_rectilinear_path(cols, fill, used, gap):
    m, n = cols.shape  # Obtém as dimensões da matriz de colunas, m representa o número de linhas e n representa o número de colunas
    paths = []  # Inicializa uma lista vazia chamada paths para armazenar os caminhos de preenchimento
    d = True  # direção ascendente
    # Itera através de todos os índices de linha (i) e coluna (j) na matriz de colunas
    for i in range(m):
        for j in range(n):
            # Verifica se a coluna correspondente à linha i e coluna j ainda não foi usada
            if used[i][j] == 0:
                # Chama a função find_path para obter um caminho de preenchimento reticulado
                path = find_path(cols, fill, used, i, j, d, gap)
                if len(path) > 1:  # Verifica se o caminho gerado contém mais de um ponto (ou seja, não é apenas um ponto isolado)
                    # Se verdadeiro, adiciona o caminho à lista de caminhos paths
                    paths.append(path)
    # Retorna os caminhos de preenchimento como um objeto MultiLineString. Esse objeto representa várias linhas conectadas
    return MultiLineString(paths)


def rectilinear_fill(shape, gap, angle=0, thres=0):
    # Gira a forma original (shape) em um ângulo especificado (angle), o ponto de rotação é o ponto (0, 0) no plano
    r_shape = rotate(shape, angle, origin=(0, 0))
    # Translada a forma rotacionada (r_shape) para que seu canto inferior esquerdo esteja na origem (0, 0), isso garante que a forma esteja alinhada corretamente
    tr_shape = translate(r_shape, -r_shape.bounds[0], -r_shape.bounds[1])
    # Calcula a altura total da área onde o preenchimento será gerado, divide a altura da forma rotacionada pelo espaçamento (gap) e arredonda para baixo, adiciona 1 para garantir que a altura seja suficiente para cobrir toda a forma
    height = int(np.floor(tr_shape.bounds[3]/gap)+1)
    # Obtém as colunas de coordenadas x, informações de preenchimento e rastreamento de uso, usa a borda exterior da forma rotacionada como entrada
    cols, fill, used = get_cols(tr_shape.exterior, gap, thres, height, False)
    # Itera através dos buracos (interiores) da forma rotacionada
    for hole in tr_shape.interiors:

        # Para cada buraco, obtém as colunas, informações de preenchimento e rastreamento de uso
        cols2, fill2, used2 = get_cols(hole, gap, thres, height, True)
        cols = np.ma.append(cols, cols2, 0)
        fill = np.ma.append(fill, fill2, 0)
        used = np.ma.append(used, used2, 0)
    # Classifica as colunas para otimizar o preenchimento
    sort_cols(cols, fill, used)
    # Verifica se há buracos (interiores) na forma rotacionada
    if tr_shape.interiors:
        sort_cols(cols, fill, used)  # classifica novamente as colunas
    # obtém os caminhos de preenchimento reticulado com base nas colunas, informações de preenchimento e rastreamento de uso
    paths = get_rectilinear_path(cols, fill, used, gap)
    # Translada os caminhos de volta para a posição original (antes da translação)
    paths = translate(paths, r_shape.bounds[0], r_shape.bounds[1])
    # Gira os caminhos de preenchimento de volta para a orientação original (antes da rotação)
    paths = rotate(paths, -angle, origin=(0, 0))
    return paths  # Retorna os caminhos de preenchimento reticulado como um objeto geométrico


# Essa classe representa um método específico de preenchimento reticulado
class RectilinearInfill(InfillMethod):
    def __init__(self, flex_print_instance):

        self.flex_print_ref = flex_print_instance

    # método que gera preenchimento, retorna um objeto MultiLineString, que representa várias linhas conectadas
    def generate_infill(self, layer: Layer, gap, angle) -> MultiLineString:
        infill = []  # armazenar os caminhos de preenchimento
        for border in layer.infill_border.geoms:  # Itera através das geometrias da borda de preenchimento da camada
            # para cada borda, gera caminhos de preenchimento reticulado usando a função rectilinear_fill
            paths = rectilinear_fill(border, gap, angle)
            # Adiciona os caminhos gerados à lista infill
            infill.extend(paths.geoms)
        # Retorna os caminhos de preenchimento como um objeto MultiLineString

        multilinestring_infill = MultiLineString(infill)

        self.flex_print_ref.last_loop = multilinestring_infill.geoms[-1]

        return multilinestring_infill

    def generate_continuous_infill(self, layer: Layer, gap, angle) -> MultiLineString:
        infill = []  # armazenar os caminhos de preenchimento
        for border in layer.infill_border.geoms:  # Itera através das geometrias da borda de preenchimento da camada
            # para cada borda, gera caminhos de preenchimento reticulado usando a função rectilinear_fill
            paths = rectilinear_fill(border, gap, angle)
            # Adiciona os caminhos gerados à lista infill
            infill.extend(paths.geoms)
        # Retorna os caminhos de preenchimento como um objeto MultiLineString
        multilinestring_infill = MultiLineString(infill)

        # ----- Processing BestPath -----
        perimeterBuffer = RawList_Points(layer.flex_print_ref.last_loop, makeTuple=True)
        
        buffer_InfillPaths = []


        for k in multilinestring_infill.geoms:
            buffer_InfillPaths.append(RawList_Points(k, makeTuple=True))

        best_path, best_directions, _ = searchParameters_Perimeter2Infill_rotateFlex(
            perimeterBuffer, [buffer_InfillPaths])

        multilinestring_bufferInfill = MultiLineString(buffer_InfillPaths)

        infill_paths = order_list(multilinestring_bufferInfill, best_path, best_directions)

        # ----- END OF Processing BestPath -----

        self.flex_print_ref.last_loop = infill_paths.geoms[-1]
        return infill_paths