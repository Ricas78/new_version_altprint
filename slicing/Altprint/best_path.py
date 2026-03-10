from itertools import permutations
# from shapely import wkt
from shapely.geometry import LineString, Point
# from shapely.ops import nearest_points  # Correção na importação
# from itertools import permutations, product

import shapely as sp

# faz a dist ponto a ponto do point com a rawlist_points (coord mais prox da lista do point)


def closestPoint(point, RawList_points):
    # Search for the closest point of Point from the RawList
    # agg_info: agregated info, such as angle for each RawPoint

    min_distance = 999  # Initilize as a number bigger enough to fit the next 'if' statement

    for i in range(len(RawList_points)):

        perimeterCoord = RawList_points[i]

        # Cast to 'Point' Object
        perimeterCoord = sp.Point(perimeterCoord)

        # Calculate the distance
        dist = perimeterCoord.distance(sp.Point(point))

        # Storage only the min. distance
        if dist <= min_distance:
            min_distance = dist
            closestCoord = perimeterCoord

    return closestCoord


def RawList_Points(linestring, makeTuple=False):
    # Only if the list is a list of linestrings
    # converti o objeto linestring em uma lista de tuplas (coordenadas da linestring)
    listRaw_Points = []

    for linestr in linestring.coords:
        list_linestr = list(linestr)
        if makeTuple == True:
            listRaw_Points.append(linestr)

        if makeTuple == False:
            for coord in list_linestr:
                listRaw_Points.append(coord)

    return listRaw_Points


def RawList_MultiPoints(multilinestring, makeTuple=False):
    # Only if the list is a multilinestring objects
    # converti o objeto multilinestring em uma lista(listas de linestrings) de lista de tuplas (coordenadas da linestring)
    listRaw_MultiPoints = []

    buffer = [k for k in multilinestring.geoms]

    multiLinestr_lenght = len(buffer)

    for i in range(multiLinestr_lenght):
        listRaw_MultiPoints.append(RawList_Points(
            multilinestring.geoms[i], makeTuple=makeTuple))

    return listRaw_MultiPoints


def perimeterPath_byPoint(startPoint, rawList_perimeterPoints, clockwise=True):

    # rearranja o caminho do perímetro baseado no ponto incial dele definido no ponto mais proximo do perimetro da proxima camada para o final do infill da atual

    # startPoint is a POINT object

    # Get the perimeter path by using the starting point, orientation and perimeter RawList_Points

    # Set index of start point and slice the rawList untill the end of process(firstHalf). Then get the coord. of the end, to search the
    # initial point(SecondHalf) and continue untill reach the startPoint of firstHalf.

    bestPath = []

    if clockwise == True:

        # It needs to be that type of slice because of the existence of the 'skirt' in front of the 'perimeter' coords list.

        startIndex1 = rawList_perimeterPoints.index(list(startPoint.coords)[0])
        firstHalf = rawList_perimeterPoints[startIndex1:]

        # startIndex2 = rawList_perimeterPoints.index(firstHalf[-1])
        # secondHalf = rawList_perimeterPoints[startIndex2+1:startIndex1+1]

        # aqui nao seira melhor só:
        secondHalf = rawList_perimeterPoints[:startIndex1+1]

        # o intuito dessa segunda lista é pegar do começo da lista original até o indice que contém a coordenada mais próxima (definida na primeira lista)

        bestPath = firstHalf + secondHalf

    return bestPath


def bestPath_Infill2Perimeter(list_nextPerimeters, list_infill):

    # coloca dentro da lista do caminho do proximo perimetro com o ponto mais proximo do infill da camada atual
    # Function that returns the best starting point in Perimeter Path, after finish the infill

    # Extracting the last point
    last_pointInfill = sp.Point(list_infill[-1])

    bestPath_listPerimeters = []

    for perimeter in list_nextPerimeters:

        # Algorith to calculate all distances(reference by last infill point) and storage the minimun distance, and the points related.

        closestCoord = closestPoint(last_pointInfill, perimeter)

        bestPath_perimeter = perimeterPath_byPoint(closestCoord, perimeter)

        bestPath_listPerimeters.append(bestPath_perimeter)

    return bestPath_listPerimeters


def split_PerimeterPath(PathList, numPerimeters):
    # n utiliza mais

    # Split a Path list into a list of lists (each path, e.g perimeter 0, perimeter 1, etc.) (Input: list of tuples (coords.))
    perimeter_byNumber = []
    temp_list = []

    count_2 = 1

    firstCoord = PathList[0]

    for n in range(len(PathList)):
        temp_list.append(PathList[n])
        count_2 += 1

        if (firstCoord == PathList[n]) and (n != 0) and (count_2 > 2):

            perimeter_byNumber.append(temp_list.copy())
            temp_list = []

            count_2 = 1

            if n != (len(PathList)-1):  # Não esta no final
                firstCoord = PathList[n+1]

    if numPerimeters != len(perimeter_byNumber):
        print("Error, numPerimeters != len(perimeter_byNumber) ")
        print("numPerimeters: ", numPerimeters)
        print("lenPathlist: ", len(perimeter_byNumber))
        return -1

    else:
        return perimeter_byNumber


def bestPath_Perimeter2Infill(listPerimeter, listInfill):
    # N USA MAIS
    # Search the best startPoint to initiate the Infill.
    # Calculate the distance from the lastPointPerimeter and the pointAlfa_Infill and pointBeta_Infill

    # Then the closestPoint get the priority to start the list of the infill path

    pointAlfa_Infill = sp.Point(listInfill[0])
    pointBeta_Infill = sp.Point(listInfill[-1])

    lastPoint_perimeter = sp.Point(listPerimeter[-1])

    distAlfa = lastPoint_perimeter.distance(pointAlfa_Infill)
    distBeta = lastPoint_perimeter.distance(pointBeta_Infill)

    if distAlfa <= distBeta:
        return listInfill

    else:
        return listInfill[::-1]  # Reversed


def bestPath_skirt(list_linestrings):

    bestpath_skirt = []

    # Pick the First Linestring (and pop it from the list)
    first_linestring = list_linestrings.pop(0)

    # Insert the First Linestring (because it's the skirt)
    bestpath_skirt.append(first_linestring)

    last_point = sp.Point(first_linestring.coords[-1])

    # Basically for each linestring we define two points (A- the first coord. and B-the last coord.) and calculate which one is closer, than perform a revese if it's necessary

    for linestring in list_linestrings:
        point_A = sp.Point(linestring.coords[0])
        point_B = sp.Point(linestring.coords[-1])

        dist_to_A = sp.distance(point_A, last_point)
        dist_to_B = sp.distance(point_B, last_point)

        if dist_to_B < dist_to_A:
            bestpath_skirt.append(linestring.revese())
        else:
            bestpath_skirt.append(linestring)

    return bestpath_skirt


def conc_LoopLinestrings(listLinestrings):
    """
    Recebe uma lista de linestrings quebradas (splited_by_regions) e concatena elas até fazer um loop, e assim por diante.
    No final temos listas de linestrings, cada lista representa o conjunto de linestrings que completam um loop.
    """
    conc_linestrings = []
    buffer_list = []

    Flag_first_point = True

    for linestring in listLinestrings:
        raw_linestring = RawList_Points(linestring, makeTuple=True)

        # print("raw_linestring", raw_linestring)
        for point in raw_linestring:

            if Flag_first_point:  # Save first point of the loop
                first_point = point

                buffer_list.append(point)
                Flag_first_point = False

            else:  # If it is not the first point..

                buffer_list.append(point)

                if point == first_point:
                    # Tratando algumas repetições na buffer_list
                    last_pt = buffer_list.pop()

                    seen = set()
                    seen_add = seen.add
                    buffer_list = [point for point in buffer_list if not (
                        point in seen or seen_add(point))]

                    buffer_list.append(last_pt)

                    conc_linestrings.append(sp.LineString(buffer_list.copy()))

                    buffer_list = []
                    Flag_first_point = True

    return conc_linestrings


def searchAndSplit(raw_lists, raw_point):
    # ->function that split list by the closest 'reference point', them create 2 lists(main list splitted)

    RefPoint = sp.Point(raw_point)
    min_dist = 9999999
    closest_point = 0
    mainList = []
    Index_counter = 0
    Index_list = 0

    for raw_list in raw_lists:  # Find the closest point in a list of lists
        for pt in raw_list:

            pt = sp.Point(pt)

            if pt.distance(RefPoint) <= min_dist:
                min_dist = pt.distance(RefPoint)
                closest_point = pt
                mainList = raw_list
                Index_list = Index_counter

        Index_counter += 1

    closest_point = list(closest_point.coords)[0]

    list1 = mainList[:mainList.index(closest_point)]
    list2 = mainList[mainList.index(closest_point):]

    raw_lists.pop(Index_list)  # Delete the old list that was splitted

    if len(list1) == 1:
        list2.append(list1.pop())

    if len(list2) == 1:
        list1.append(list2.pop())

    if list1 != []:
        # Add the splitted vesions in the beggining of the array
        raw_lists.insert(0, list1)

    if list2 != []:
        raw_lists.insert(0, list2)

    return raw_lists, closest_point


def searchAndSplit_alt(raw_lists, raw_point):
    # ->function that split list by the closest 'reference point', them create 2 lists(main list splitted)

    RefPoint = sp.Point(raw_point)
    min_dist = 9999999
    closest_point = 0
    mainList = []
    Index_counter = 0
    Index_list = 0

    for raw_list in raw_lists:  # Find the closest point in a list of lists
        for pt in raw_list:

            pt = sp.Point(pt)

            if pt.distance(RefPoint) <= min_dist:
                min_dist = pt.distance(RefPoint)
                closest_point = pt
                mainList = raw_list
                Index_list = Index_counter

        Index_counter += 1

    closest_point = list(closest_point.coords)[0]

    # Check if the 'list1' and 'list2' have *at least* lenght = 2

    list1 = mainList[:mainList.index(closest_point)]
    list2 = mainList[mainList.index(closest_point)-1:]

    if (len(list1) <= 1) or (len(list2) <= 1):
        list1 = mainList[:mainList.index(closest_point)+1]
        list2 = mainList[mainList.index(closest_point):]

        if (len(list1) <= 1) or (len(list2) <= 1):
            list1 = mainList[:mainList.index(closest_point)-1]
            list2 = mainList[mainList.index(closest_point)-2:]

    raw_lists.pop(Index_list)  # Delete the old list that was splitted

    if len(list1) == 1:
        list2.append(list1.pop())

    if len(list2) == 1:
        list1.append(list2.pop())

    if list1 != []:
        # Add the splitted vesions in the beggining of the array
        raw_lists.insert(0, list1)

    if list2 != []:
        raw_lists.insert(0, list2)

    return raw_lists, closest_point


def order_list(multilinestrings, best_path, best_directions):
    # ele ordena as linestrings da multinestring e decide qual a direção/sentido de cada linestring para a continuidade

    # Recebe os parâmetros e a lista para oderná-la
    best_path_list = []

    list_of_linestrings = [k for k in multilinestrings.geoms]

    # best_diretions and best_path are already parsed

    # Sort in best_path order
    for j in range(len(multilinestrings.geoms)):
        index = best_path[j]

        if best_directions[j] == -1:
            best_path_list.append(list_of_linestrings[index].reverse())
        else:
            best_path_list.append(list_of_linestrings[index])

    # # Apply best_directions (revese if necessary)
    # for i, linestring in enumerate([k for k in best_path_multilinestring.geoms]):

    #     if best_directions[i] == -1:
    #         print("linestring atual: ", list_of_linestrings[i])
    #         list_of_linestrings[i] = linestring.reverse()
    #         print("linestring depois: ", list_of_linestrings[i])

    return sp.MultiLineString(best_path_list)

# Função para calcular o custo total de um caminho


def path_cost(start_point, lines, path, directions):

    # calcula o custo de uma combinação de linestrings
    total_cost = 0
    current_point = start_point

    for i, line_index in enumerate(path):
        line_coords = lines[line_index]

        # Se a linha estiver invertida, inverte as coordenadas
        if directions[i] == -1:
            line_coords = line_coords[::-1]

        line = LineString(line_coords)

        # Adiciona a distância até o ponto mais próximo
        # Distância ao primeiro ponto da linha
        total_cost += current_point.distance(Point(line.coords[0]))

        # Atualiza o ponto atual para o final da linha (respeitando a inversão)
        current_point = Point(line.coords[1])

    return total_cost


def bruteForce_perm(Angle_n_lists, start_point):
    # itera sobre os custos e ver qual o menor e retorná-lo

    total_best_path = None
    total_best_directions = None
    total_best_angle = None

    final_cost = float('inf')

    # Para cada multilinestring de listas do infill geradas por angulo
    for i in range(len(Angle_n_lists)):
        # Define as linhas
        lines = Angle_n_lists[i]

        # Gera todas as permutações possíveis de linhas
        line_permutations = list(permutations(range(len(lines))))

        # Gera todas as combinações de direções (1 = normal, -1 = invertida)
        directions = list(product([1, -1], repeat=len(lines)))

        # Inicializa a melhor solução
        best_path = None
        best_directions = None
        min_cost = float('inf')

        # Testa cada permutação e cada combinação de direções
        for perm in line_permutations:
            for dir_comb in directions:
                current_cost = path_cost(start_point, lines, perm, dir_comb)
                if current_cost < min_cost:
                    min_cost = current_cost
                    best_path = perm
                    best_directions = dir_comb

        if min_cost < final_cost:
            final_cost = min_cost

            total_best_path = best_path
            total_best_directions = best_directions
            total_best_angle = i

    return total_best_path, total_best_directions, total_best_angle


def searchParameters_Perimeter2Infill_rotateFlex(listPerimeter, Angle_n_listsInfill):
    """
    n_listInfill é uma lista de listas primordialmente.
    [[infill_path_angulo0], [infill_path_angulo1], [...]]

    entretanto, estes "infill_path_angulo{} podem ser lista ou nao
    caso sejam, é necessario permutar por força bruta e decidir qual ordenação é mais favoravel,
    porém, precisa avaliar também de cada ângulo
    """
    # encontra os melhores parametros de organizaçao das linesrting, se elas invertidas ou n (BA ou AB) e o angulo da direção de impressão
    lastPoint_perimeter = sp.Point(listPerimeter[-1])

    # Se algum angulo produzir um infill com mais de 1 caminho -> permutar combinações
    if max([len(Angle_n_listsInfill[k]) for k in range(len(Angle_n_listsInfill))]) > 1:

        # best_path, best_directions, best_angle = bruteForce_perm(Angle_n_listsInfill, lastPoint_perimeter)

        # Emergency search_and_split
        # Pick the first (and only) angle infill
        n_listInfill = Angle_n_listsInfill[0]

        # iter into a infills, search the closest first point of infill list
        closest_dist = 999999999

        best_path = list(range(len(n_listInfill)))
        buf_bestpath = -1

        best_directions = [1 for n in range(len(n_listInfill)-1)]
        buf_directions = 0

        best_angle = 0
        for index, infill in enumerate(n_listInfill):

            pointAlpha = sp.Point(infill[0])
            pointBeta = sp.Point(infill[-1])

            distAlpha = lastPoint_perimeter.distance(pointAlpha)
            distBeta = lastPoint_perimeter.distance(pointBeta)

            if distAlpha < closest_dist:
                closest_dist = distAlpha
                buf_directions = 1
                buf_bestpath = index

            if distBeta < closest_dist:
                closest_dist = distBeta
                buf_directions = -1
                buf_bestpath = index

        best_path.insert(0, best_path.pop(buf_bestpath))
        best_directions.insert(0, buf_directions)

    else:
        best_angle = 0
        closest_dist = 999999999

        for index, listInfill in enumerate(Angle_n_listsInfill):
            listInfill = listInfill[0]

            pointAlpha = sp.Point(listInfill[0])
            pointBeta = sp.Point(listInfill[-1])

            distAlpha = lastPoint_perimeter.distance(pointAlpha)
            distBeta = lastPoint_perimeter.distance(pointBeta)

            if distAlpha < closest_dist:
                closest_dist = distAlpha
                best_directions = 1
                best_angle = index

            if distBeta < closest_dist:
                closest_dist = distBeta
                best_directions = -1
                best_angle = index

        best_path = tuple([0])
        best_directions = tuple([best_directions])

    return best_path, best_directions, best_angle
