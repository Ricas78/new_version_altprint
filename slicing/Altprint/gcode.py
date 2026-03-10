# importando classe que criará objetos que representam o lugar geométrico de uma linha (unidimensional)
from shapely.geometry import LineString
# classe abstrata que quero utilizar para criar outra classe que seja subclasse dela para criar objetos
from Altprint.base import BasePrint
import numpy as np  # abreviação da lib numpy para usar seus recursos de forma simplificada


class GcodeExporter:  # criando a classe que contém as funções para criação do código gcode da peça

    # método/função de construção da classe, que recebe como argumento os arquivos cabeçalhos inicial e final da impressora
    # add o atributo "travel_speed_value" para poder passar como parametro no YML a velocidade de deslocamento do bico
    def __init__(self, travel_speed: float, travel_retraction: float, start_script='', end_script=''):
        # lista que armazenará os comandos gcode gerado como strings
        self.gcode_content: list[str] = []
        self.head_x: float = 0.0  # posição atual do cabeçote da máquina no eixo X
        self.head_y: float = 0.0  # posição atual do cabeçote da máquina no eixo Y
        self.min_jump: float = 1  # movimentação mínima de uma coordenada para a outra
        # atributo que indica que é o nome de um arquivo cabeçalho inicial
        self.start_script_fname = start_script
        # atributo que indica que é o nome de um arquivo cabeçalho final
        self.end_script_fname = end_script
        self.travel_speed_value: float = travel_speed
        self.travel_retraction_value: float = travel_retraction
    # método que recebe 5 parâmetros, coordenadas X, Y e Z, quanto de filamento em mm sera puxado e a velocidade de movimento nos eixos, ele retorna uma string

    def segment(self, x, y, z, e, v) -> str:
        segment = []  # lista que armazena as linhas de gcode somente quando este método é chamado
        # string de comentário é adicionada à lista segment. Em G-code, qualquer texto após um ponto e vírgula (;) é considerado um comentário e é ignorado pela máquina CNC
        segment.append('; segment\n')
        # comando G92 é adicionado à lista. O comando G92 é usado para definir a posição atual do extrusor para um valor especificado, neste caso, 0.
        segment.append('G92 E0.0000\n')
        # comando G1 é adicionado à lista. O comando G1 é usado para movimentos lineares. O parâmetro F define a taxa de alimentação para o movimento. Neste caso, a taxa de alimentação é definida para o primeiro valor na lista v
        segment.append('G1 F{0:.3f}\n'.format(v[0]))
        if z is not None:
            # Se z não for None, um comando G1 é adicionado à lista para mover o extrusor para a posição z
            segment.append('G1 Z{0:.3f}\n'.format(z))
        # comando G1 é adicionado à lista para mover o extrusor para a posição (x[0], y[0])
        segment.append('G1 X{0:.3f} Y{1:.3f}\n'.format(x[0], y[0]))

        # A variável actual_speed é definida como o primeiro valor na lista v
        actual_speed = v[0]
        # Um loop é iniciado que percorre todos os elementos nas listas x e y, exceto o último.
        for i in range(len(x)-1):
            if actual_speed != v[i+1]:
                # Se a velocidade atual for diferente da próxima velocidade na lista v, um comando G1 é adicionado à lista para mover o extrusor para a próxima posição (x[i+1], y[i+1]) com a taxa de extrusão e[i+1] e a taxa de alimentação v[i+1]
                segment.append('G1 X{0:.3f} Y{1:.3f} E{2:.4f} F{1:.3f} \n'.format(x[i+1], y[i+1], e[i+1], ))  # noqa: E501
                # A velocidade atual é então atualizada para v[i+1]
                actual_speed = v[i+1]
            else:
                # Se a velocidade atual for igual à próxima velocidade na lista v, um comando G1 é adicionado à lista para mover o extrusor para a próxima posição (x[i+1], y[i+1]) com a taxa de extrusão e[i+1]
                segment.append('G1 X{0:.3f} Y{1:.3f} E{2:.4f} \n'.format(x[i+1], y[i+1], e[i+1]))  # noqa: E501
        # comando G92 é adicionado à lista para redefinir a posição do extrusor para 0
        segment.append('G92 E0.0000\n')
        # a lista segment é convertida em uma única string
        segment = "".join(segment)
        return segment  # o método retorna a string "segment"
# mudança

    def jump(self, x, y, v, e) -> str:  # método responsável por gerar um rápido movimento de um ponto ao outro (salto) sem realizar extrusão de material em gcode, recebe os parâmetros X, Y e V que são as coordenadas e velocidade para o salto, ele retorna uma string
        # removi o valor fixo de v (que antes era de 12000), agora pelo YML é possível alterá-lo em "travel_speed"
        jump = []  # lista que armazena as linhas de gcode somente quando este método é chamado
        # string de comentário é adicionada à lista jump
        jump.append('; jumping\n')
        # comando G92 é adicionado à lista para redefinir a posição do extrusor para 3
        jump.append('G92 E0.0000\n')  # mudei de 3.0 p/ 0.0
        # comando G1 é adicionado à lista. O extrusor é movido para a posição 0 a uma taxa de alimentação de 2400
        jump.append('G1 E{:.1f} F2400\n'.format(e))
        # comando G1 é adicionado à lista para mover o extrusor para a posição (x, y) a uma taxa de alimentação v
        jump.append('G1 X{0:.3f} Y{1:.3f} F{2:.3f}\n'.format(x, y, v))
        # comando G1 é adicionado à lista. O extrusor é movido para a posição 3 a uma taxa de alimentação de 2400
        jump.append('G1 E0 F2400\n')  # mudei de 3 p/ 0
        # comando G92 é adicionado à lista para redefinir a posição do extrusor para 0
        jump.append('G92 E0.0000\n')
        jump = "".join(jump)  # a lista jump é convertida em uma única string
        return jump  # o método retorna a string "jump"

    # método responsável pela leitura de arquivo, recebe como parâmetro o nome do arquivo que deseja ser lido
    def read_script(self, fname):
        script = ""  # string vazia criada. Esta string será usada para armazenar o conteúdo do arquivo
        with open(fname, 'r') as f:  # O arquivo com o nome fname é aberto para leitura ('r'). O arquivo aberto é referenciado pela variável f
            script = f.readlines()  # O método "readlines" é chamado no objeto do arquivo para ler todas as linhas do arquivo. O resultado é uma lista de strings, onde cada string é uma linha do arquivo. Esta lista é atribuída à variável "script"
            # A lista de strings é convertida em uma única string.
            script = ''.join(script)
        return script  # o método retorna a string "script"

    # Método que gera o gcode para todas as camadas da peça. Este método aceita um parâmetro printable que é uma instância da classe BasePrint
    def make_gcode(self, printable: BasePrint):

        self.gcode_content = []  # o atributo gcode_content da instância é inicializado como uma lista vazia que armazenará o gcode gerado dentro desse método
        # Os scripts de início e fim são lidos dos arquivos cujos nomes são armazenados nos atributos start_script_fname e end_script_fname, respectivamente. O método read_script é usado para ler o conteúdo desses arquivos.
        start_script = self.read_script(self.start_script_fname)
        end_script = self.read_script(self.end_script_fname)
        # adiciona o script de início na lista gcode_content
        self.gcode_content.append(start_script)

        # Um loop é iniciado que percorre todos os itens no dicionário layers do objeto printable. Cada item no dicionário é um par de chave-valor, onde a chave é a coordenada z da camada e o valor é a camada em si.
        for z, layer in printable.layers.items():
            for raster in layer.perimeter:  # Um loop interno é iniciado que percorre todos os rasters no perímetro da camada
                x, y = raster.path.xy  # raster.path.xy está acessando o atributo "xy" do objeto "path" do objeto "raster". O atributo "xy" é uma tupla que contém duas listas: a primeira lista contém as coordenadas x de todos os pontos no caminho, e a segunda lista contém as coordenadas y correspondentes. Essas duas listas são então atribuídas às variáveis x e y, respectivamente
                # as listas x e y são convertidas em arrays numpy para facilitar operações matemáticas com as coordenadas armazenadas
                x, y = np.array(x), np.array(y)
                # Se a distância entre a posição atual do bico da impressora e a primeira posição do raster for maior que min_jump, um comando de salto é adicionado à lista gcode_content. O comando de salto move o bico da impressora para a primeira posição do raster sem extrudir material
                if LineString([(self.head_x, self.head_y), (x[0], y[0])]).length > self.min_jump:
                    # noqa: E501
                    self.gcode_content.append(
                        self.jump(x[0], y[0], self.travel_speed_value, self.travel_retraction_value))  # MEXI AQUI PRA TRAVEL_SPEED NO YML****
                # A posição atual do bico da impressora é atualizada para a última posição do raster
                self.head_x, self.head_y = x[-1], y[-1]
                # comando segment é adicionado à lista gcode_content. O comando segment move o bico da impressora ao longo do caminho do raster enquanto extruda material
                self.gcode_content.append(self.segment(
                    x, y, z, raster.extrusion, raster.speed))
                # noqa: E501

            for raster in layer.infill:  # mesmo processo é repetido para os rasters no preenchimento da camada
                x, y = raster.path.xy
                x, y = np.array(x), np.array(y)
                if LineString([(self.head_x, self.head_y), (x[0], y[0])]).length > self.min_jump:  # noqa: E501
                    self.gcode_content.append(
                        self.jump(x[0], y[0], self.travel_speed_value, self.travel_retraction_value))
                self.head_x, self.head_y = x[-1], y[-1]
                self.gcode_content.append(self.segment(x, y, z, raster.extrusion, raster.speed))  # noqa: E501

        # script cabeçalho final da impressor é adicionado à lista gcode_content
        self.gcode_content.append(end_script)

    # esse método é o mesmo que o anterior só que para gerar o gcode de uma única camada da peça
    def make_layer_gcode(self, layer):
        layer_gcode = []
        for raster in layer.perimeter:
            x, y = raster.path.xy
            x, y = np.array(x), np.array(y)
            if LineString([(self.head_x, self.head_y), (x[0], y[0])]).length > self.min_jump:  # noqa: E501
                # Exemplo de Lazy, se tirar o "self.travel...", o arquivo compila se n usar a fç "make_layer_gcode"
                layer_gcode.append(
                    self.jump(x[0], y[0], self.travel_speed_value, self.travel_retraction_value))
            self.head_x, self.head_y = x[-1], y[-1]
            layer_gcode.append(self.segment(
                x, y, None, raster.extrusion, raster.speed))

        for raster in layer.infill:
            x, y = raster.path.xy
            x, y = np.array(x), np.array(y)
            if LineString([(self.head_x, self.head_y), (x[0], y[0])]).length > self.min_jump:  # noqa: E501
                layer_gcode.append(
                    self.jump(x[0], y[0], self.travel_speed_value, self.travel_retraction_value))
            self.head_x, self.head_y = x[-1], y[-1]
            layer_gcode.append(self.segment(
                x, y, None, raster.extrusion, raster.speed))

        return layer_gcode

    # método que escreve todas as linhas de gcode armazenados na lista "gcode_content" em um arquivo cujo nome é fornecido pelo usuário
    def export_gcode(self, filename):
        with open(filename, 'w') as f:  # arquivo com o nome filename é aberto para escrita ('w'). O arquivo aberto é referenciado pela variável f. O uso da declaração "with" garante que o arquivo será fechado corretamente após o término do bloco de código indentado abaixo dele
            for gcode_block in self.gcode_content:  # loop que percorre todas as linhas gcode na lista "gcode_content"
                # cada linha de gcode é escrita no arquivo
                f.write(gcode_block)
