from Altprint.base import BasePrint
from Altprint.slicer import STLSlicer
from Altprint.layer import Layer, Raster
from Altprint.height_method import StandartHeightMethod
from Altprint.rectilinear_infill import RectilinearInfill
from Altprint.gcode import GcodeExporter
from Altprint.lineutil import split_by_regions, retract
from Altprint.settingsparser import SettingsParser

from Altprint.best_path import *


class FlexProcess():  # definição da classe responsável por controlar os parâmetros de impressão
    # método construtor da classe, aceita um número arbitrário de argumentos de palavra-chave
    def __init__(self, **kwargs):
        # dicionário criado que contém os valores padrão para vários parâmetros que serão usadas no processo de impressão
        prop_defaults = {
            "model_file": "",
            "flex_model_file": "",
            "slicer": STLSlicer(StandartHeightMethod()),
            "infill_method": RectilinearInfill,
            "infill_angle": 0,
            "offset": (0, 0, 0),
            "external_adjust": 0.5,
            "perimeter_num": 1,
            "perimeter_gap": 0.5,
            "raster_gap": 0.5,
            "overlap": 0.0,
            "skirt_distance": 10,
            "skirt_num": 3,
            "skirt_gap": 0.5,
            "travel_speed": 12000,
            "retraction": -0.5,
            "first_layer_flow": 2,
            "flow": 1.2,
            "speed": 2400,
            "flex_flow": 0,
            "flex_speed": 2000,
            "retract_flow": 2,
            "retract_speed": 1200,
            "retract_ratio": 0.9,
            "gcode_exporter": GcodeExporter,
            "start_script": "",
            "end_script": "",
            "vertical_gap_flex_infill": False,
            "horizontal_gap_flex_infill": False,
            "horizontal_num_gap": 1,
            "horizontal_perc_gap": 0.5,
            "orientation_gap": False,
            "best_path": True,
            "verbose": True,
        }
        # loop que percorre todos os itens do dicionário "prop_defaults". Para cada item, ele usa a função "setattr" para definir um atributo na instância atual com o nome "prop" e o valor correspondente de kwargs se ele existir, caso contrário, ele usa o valor padrão default.
        for (prop, default) in prop_defaults.items():
            setattr(self, prop, kwargs.get(prop, default))
        # Se "kwargs" contém uma chave "settings_file", um objeto "SettingsParser" é criado e usado para carregar as configurações de um arquivo yml, esse objeto tem a função de transformar as configurações de um arquivo yml em um dicionário em python. Em seguida, essas configurações são usadas para definir atributos adicionais na instância atual.
        if 'settings_file' in kwargs.keys():
            settings = SettingsParser().load_from_file(kwargs['settings_file'])
            for (setting, value) in settings.items():
                setattr(self, setting, value)


class FlexPrint(BasePrint):  # definição da classe responsável por implementar o fatiamento, geração de camadas e exportação do gcode de um arquivo de uma peça CAD em stl para ser enviado a impreesora 3D
    """The common print. Nothing special"""

    _height = float  # variável float que armazena altura da camada
    # dicionário que contém a altura de cada camada
    _layers_dict = dict[_height, Layer]

    # método construtor da classe, recebe um parâmetro "process" que é uma instância da classe "FlexProcess". O construtor inicializa três atributos de instância
    def __init__(self, process: FlexProcess):
        # atributo que recebe as configurações dos parâmetros de impressão fornecidado pela classe "FlexProcess"
        self.process = process
        # dicionário vazio que armazena as alturas referente a cada camada
        self.layers: _layers_dict = {}
        # lista vazia que armazena os valores das alturas como float
        self.heights: list[float] = []

    def slice(self):  # método que fatia modelo 3D e calcula as alturas das camadas
        if self.process.verbose is True:
            print("slicing {} ...".format(self.process.model_file))
        # atribui as configurações dos parâmetros de impressão como um objeto da classe STLSlicer
        slicer = self.process.slicer
        # método dentro da Classe STLSlicer que lê o arquivo do objeto 3D referente a região normal (em stl) determinado no arquivo yml
        slicer.load_model(self.process.model_file)
        # método dentro da Classe STLSlicer que translada o objeto no plano 3D para um offset determinado no arquivo yml
        slicer.translate_model(self.process.offset)
        # método dentro da Classe STLSlicer que fatia o objeto 3D em uma quantidade de planos igual ao numero de camadas
        self.sliced_planes = slicer.slice_model()
        # método da classe StandartHeightMethod, calcula e retorna uma lista com as alturas de cada camada
        self.heights = self.sliced_planes.get_heights()

        # método dentro da Classe STLSlicer que lê o arquivo do objeto 3D referente a região flexível (em stl) determinado no arquivo yml
        slicer.load_model(self.process.flex_model_file)
        # método dentro da Classe STLSlicer que translada o objeto no plano 3D para um offset determinado no arquivo yml
        slicer.translate_model(self.process.offset)
        # método dentro da Classe STLSlicer que fatia o objeto 3D em uma quantidade de planos igual ao numero de camadas (que é obtido através do tamanho do vetor que armazena as alturas de cada camada)
        self.flex_planes = slicer.slice_model(self.heights)

    def make_layers(self):  # método que gera as trajetórias das camadas, desde a saia inicial, e o perímetro/contorno e o preenchimento de cada camada
        if self.process.verbose is True:  # linha de verificação fornecida dentro das configurações do próprio arquivo yml
            # mensagem quando executa essa função do programa
            print("generating layers ...")
        # atribui as configurações dos parâmetros de impressão como um objeto da classe RectilinearInfill
        infill_method = self.process.infill_method()

        # lógica de construção da saia em volta da primeira camada da peça
        # cria uma instância "skirt" da classe "Layer" que recebe os parâmetros da saia fornecidos pelo arquivo yml
        skirt = Layer(self.sliced_planes.planes[self.heights[0]],
                      self.process.skirt_num,
                      self.process.skirt_gap,
                      - self.process.skirt_distance - self.process.skirt_gap * self.process.skirt_num,  # noqa: E501
                      self.process.overlap)
        # utiliza o método da classe "Layer" para criação do perímetro formado pela saia
        skirt.make_perimeter()

        last_InfillPaths = []  # Just initialzie

        # loop que percorre todas as alturas na lista "heights". A função enumerate é usada para obter tanto o índice (i) quanto o valor (height) de cada altura.
        for i, height in enumerate(self.heights):
            # para cada altura, é criado um novo objeto "Layer", que recebe os parãmetros referentes ao perímetro fornecidos pelo arquivo yml, e atribuído a "layer" que é referente a cada camada
            layer = Layer(self.sliced_planes.planes[height],
                          self.process.perimeter_num,
                          self.process.perimeter_gap,
                          self.process.external_adjust,
                          self.process.overlap)
            # Se o atributo shape do objeto layer for uma lista vazia, o objeto layer é adicionado ao dicionário "layers" com a chave "height" e o loop continua para a próxima iteração.
            if layer.shape == []:
                self.layers[height] = layer
                continue
            # utiliza o método da classe "Layer" para criação do perímetro da camada atual
            layer.make_perimeter()
            # utiliza o método da classe "Layer" para criação dos limites do preenchimento da camada atual
            layer.make_infill_border()

            # define a região flexível na camada atual baseado nos planos que compêm cada camada desta região já definida na função "slice"
            flex_regions = self.flex_planes.planes[height]

            # em caso de "True" define a região flexível com gaps
            if self.process.horizontal_gap_flex_infill:
                flex_regions_gapped = create_gaps(flex_regions,
                                                  self.process.horizontal_num_gap,
                                                  self.process.horizontal_perc_gap,
                                                  self.process.orientation_gap)

            # em caso de "False", não existe gap, apenas as regiões flexíveis
            else:
                flex_regions_gapped = flex_regions

            # Se "flex_regions" não for uma lista, ele é convertido em uma lista
            if not type(flex_regions) == list:  # noqa: E721
                flex_regions = list(flex_regions.geoms)

            # define se a impressão da região flexível alterna entre: imprimir e não imprimir
            alternate_layers = self.process.vertical_gap_flex_infill

            # Se esta for a primeira iteração do loop (ou seja, se estamos na primeira camada), os caminhos do perímetro da saia são adicionados ao perímetro da camada
            Lists_skirt = []

            if i == 0:  # skirt
                for path in skirt.perimeter_paths.geoms:
                    # com raster, faz a saia com os parâmetros fornecidos do arquivo yml
                    layer.perimeter.append(
                        Raster(path, self.process.first_layer_flow, self.process.speed))
                    Lists_skirt.append(RawList_Points(path, makeTuple=True))

                lastLoop_skirt = Lists_skirt[-1]  # Already "Raw" type list

            # ------ COMEÇO DO PRE-PROCESSAMENTO DO PERIMETER_PATH -------
            if self.process.best_path:  # Caso best_path esteja abilitado no .yml
                Raw_ListPerimeter = RawList_MultiPoints(sp.MultiLineString(
                    [k for k in layer.perimeter_paths.geoms]), makeTuple=True)

                if i == 0:
                    print(Raw_ListPerimeter)
                    Raw_bestPerimeterPath = bestPath_Infill2Perimeter(
                        Raw_ListPerimeter, lastLoop_skirt)
                    layer.perimeter_paths = sp.MultiLineString(
                        [sp.LineString(k) for k in Raw_bestPerimeterPath])

                else:

                    # Select the last linestring (of the Multilinestring obj) and transform to "Raw" type (Casting)
                    Raw_lastInfillPath = RawList_Points(
                        last_InfillPaths.geoms[-1], makeTuple=True)

                    Raw_bestPerimeterPath = bestPath_Infill2Perimeter(
                        Raw_ListPerimeter, Raw_lastInfillPath)

                    # Casting back (Raw -> Linestring -> Multilinestring)
                    layer.perimeter_paths = sp.MultiLineString(
                        [sp.LineString(k) for k in Raw_bestPerimeterPath])

            # ------ FIM DO PRE-PROCESSAMENTO DO PERIMETER_PATH -------
            for path in split_by_regions(layer.perimeter_paths, flex_regions).geoms:
                flex_path = False

                for region in flex_regions:  # para a região flexível
                    if path.within(region.buffer(0.01, join_style=2)):
                        flex_path, retract_path = retract(path, self.process.retract_ratio)  # noqa: E501
                        layer.perimeter.append(Raster(flex_path, self.process.flex_flow, self.process.flex_speed))  # noqa: E501
                        layer.perimeter.append(Raster(retract_path, self.process.retract_flow, self.process.retract_speed))  # noqa: E501
                        flex_path = True
                        break

                if not flex_path:  # para a região normal
                    if i == 0:  # para a primeira camada
                        # adiciona ao perímetro da primeira camada como deve ser o fluxo e a velocidade do raster
                        layer.perimeter.append(
                            Raster(path, self.process.first_layer_flow, self.process.speed))

                    else:  # para as demais camadas
                        # adiciona ao perímetro da camada como deve ser o fluxo e a velocidade do raster
                        layer.perimeter.append(
                            Raster(path, self.process.flow, self.process.speed))

            # ------ COMEÇO DO PRE-PROCESSAMENTO DO INFILL_PATH -------
            if self.process.best_path:  # Caso best_path esteja abilitado no .yml
                # Calcula o melhor caminho do preenchimento (perímetro para o preenchimento)
                infill_paths = self.BestPath_Perimeter2Infill(
                    layer, infill_method)

                # Salva o último caminho do preenchimento (para calcular o caminho do perímetro da próxima camada)
                last_InfillPaths = infill_paths

            else:
                infill_paths = infill_method.generate_infill(layer,
                                                             self.process.raster_gap,
                                                             self.process.infill_angle[0])

            infill_paths = split_by_regions(infill_paths, flex_regions)
            # ------ FIM DO PRE-PROCESSAMENTO DO INFILL_PATH -------
            for path in infill_paths.geoms:
                flex_path = False

                # Não imprime o padrão(com ou sem gap vertical) da região flexível
                if (i % 2 != 0) and alternate_layers:

                    for region in flex_regions:  # para a região flexível
                        if path.within(region.buffer(0.01, join_style=2)):
                            flex_path = True
                            break

                    if not flex_path:  # para a região normal
                        if i == 0:  # para a primeira camada
                            # adiciona ao preenchimento da primeira camada como deve ser o fluxo e a velocidade do raster
                            layer.infill.append(
                                Raster(path, self.process.first_layer_flow, self.process.speed))
                        else:
                            # adiciona ao preenchimento da camada como deve ser o fluxo e a velocidade do raster
                            layer.infill.append(
                                Raster(path, self.process.flow, self.process.speed))

                else:  # imprime o padrão(com ou sem gap vertical) da região fléxivel

                    for region in flex_regions_gapped.geoms:  # para a região flexível

                        # se o caminho estiver na região flexivel
                        if path.within(region.buffer(0.01, join_style=2)):
                            flex_path, retract_path = retract(path, self.process.retract_ratio)  # noqa: E501
                            layer.infill.append(Raster(flex_path, self.process.flex_flow, self.process.flex_speed))  # noqa: E501
                            layer.infill.append(Raster(retract_path, self.process.retract_flow, self.process.retract_speed))  # noqa: E501
                            flex_path = True
                            break

                        else:  # its gap
                            for flex in flex_regions:
                                if path.within(flex.buffer(0.02, join_style=2)):
                                    flex_path = True

                    if not flex_path:  # para a região normal
                        if i == 0:  # para a primeira camada
                            # adiciona ao preenchimento da primeira camada como deve ser o fluxo e a velocidade do raster
                            layer.infill.append(
                                Raster(path, self.process.first_layer_flow, self.process.speed))
                        else:
                            # adiciona ao preenchimento da camada como deve ser o fluxo e a velocidade do raster
                            layer.infill.append(
                                Raster(path, self.process.flow, self.process.speed))

            # a camada atual é adicionada ao dicionário "layers" com a chave "height" referente a altura desta camada
            self.layers[height] = layer

    def BestPath_Perimeter2Infill(self, layer: Layer, infill_method):
        """
        A lógica do código consistem em:
        * Gera diferente preenchimentos variando a rotação
        * itera pelos preenchimentos(gerados em cada angulo) e joga para a função "searchParameters"
        * A função calcula as distâncias percorridas (custo) em relação ao ultimo ponto do perímetro
        * A função escolhe e retorna os melhores parâmetros para criar o infill em que o custo é minimizado
        * É gerado o infill com o ângulo emq ue o custo é minimizado (best_angle)
        * a função "order_list" recebe o caminho do preenchimento e ordena ele corretamente
        * OBS: ordena, pois o preenchimento é composto de varios "pedaços" (Linestrings) estes pedaços podem ser permutados para mudar de ordem
        assim como podem ser invertidos.
        """

        list_angles = self.process.infill_angle
        buffer_InfillPaths_byAngle = []
        temp_list = []

        InfillPaths_byAngle = [infill_method.generate_infill(
            layer, self.process.raster_gap, angle) for angle in list_angles]

        for j in range(len(list_angles)):

            for k in InfillPaths_byAngle[j].geoms:

                temp_list.append(RawList_Points(k, makeTuple=True))

            buffer_InfillPaths_byAngle.append(temp_list.copy())
            temp_list = []

        perimeterBuffer = RawList_Points(
            [k for k in layer.perimeter_paths.geoms][-1], makeTuple=True)

        best_path, best_directions, best_angle = searchParameters_Perimeter2Infill_rotateFlex(
            perimeterBuffer, buffer_InfillPaths_byAngle)

        infill_paths = infill_method.generate_infill(layer,
                                                     self.process.raster_gap,
                                                     list_angles[best_angle])

        infill_paths = order_list(infill_paths, best_path, best_directions)

        return infill_paths

    def export_gcode(self, filename):
        if self.process.verbose is True:  # linha de verificação fornecida dentro das configurações do próprio arquivo yml
            # mensagem quando executa essa função do programa
            print("exporting gcode to {}".format(filename))

        # cria uma instância "gcode_exporter" da classe "GcodeExporter" que recebe os parãmetros referentes ao script cabeçalho inicial e final do modelo da impressora utilizada fornecido pelo arquivo yml
        gcode_exporter = self.process.gcode_exporter(self.process.travel_speed, self.process.retraction, start_script=self.process.start_script,
                                                     end_script=self.process.end_script)
        # utiliza o método "make_gcode" da classe "GcodeExporter" para gerar o gcode de todas as camadas da peça 3D
        gcode_exporter.make_gcode(self)
        # utiliza o método "export_gcode" da classe "GcodeExporter" para salvar todas as linhas do gcode gerado, fornecidas por uma lista, em um arquivo com o nome fornecido pelo usuário
        gcode_exporter.export_gcode(filename)
