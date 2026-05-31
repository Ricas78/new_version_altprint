import tkinter as tk  # biblioteca padrão de GUI do Python
# widgets mais modernos (botões, frames, etc.)
from tkinter import ttk, messagebox, filedialog
# renderização gráfica (GPU), área de desenho 3D
from vispy.scene import visuals
import os  # manipulação de arquivos
import re  # regex (parse do G-code)
import numpy as np  # arrays eficientes
import matplotlib.cm as cm  # mapas de cores
from Auxiliar_classes.sub_window import SubWindow


X_MAX_DEFAULT = 220
Y_MAX_DEFAULT = 220
Z_MAX_DEFAULT = 220


class GcodeWindow(SubWindow):
    def __init__(self, notebook: ttk.Notebook, mainwindow: tk.Tk):
        super().__init__(notebook, mainwindow)

        # atributos pros metodos
        self.xMaxSv = tk.StringVar(value=str(X_MAX_DEFAULT))
        self.yMaxSv = tk.StringVar(value=str(Y_MAX_DEFAULT))
        self.zMaxSv = tk.StringVar(value=str(Z_MAX_DEFAULT))
        # verificar se é necessário isso aqui, talvez por numpy da pra modificar direto, eliminando a necessidade de mais um import
        self.mapaDeCores = cm.coolwarm
        self.layerSliderVar = tk.DoubleVar()
        self.layerSliderVarH = tk.DoubleVar()
        self.currentLayer = 1
        self.nLayers = None
        self.gCodeLayers = []
        self.gCodeColorLayers = []
        self.gCodePosData = None

############################################################################################
        # tela-container para: botao de abrir gcode, label do status gcode
        self.control_frame = ttk.Frame(self.subwindow, padding="10")
        self.control_frame.pack(side='top', fill='x')

        # botão abrir gcode
        self.btnLer = ttk.Button(self.control_frame, text="Abrir G-Code",
                                 command=self.carregarGcodeVispy)
        self.btnLer.pack(side='left', padx=5)

        # label do status gcode
        self.gcodeLabelStatusSv = tk.StringVar(
            value="Nenhum arquivo carregado.")

        self.labelStatus = ttk.Label(
            self.control_frame, textvariable=self.gcodeLabelStatusSv)
        self.labelStatus.pack(side='left', padx=10, expand=True, fill='x')
############################################################################################
        # tela-container para: label layers, label de valor do slider e escala do slider (vertical)
        self.vert_frame = ttk.Frame(self.subwindow, padding="10")
        self.vert_frame.pack(side='right', fill='y')

        # label de n of layers
        self.layersRefV = ttk.Label(self.vert_frame, text="layers: ")
        self.layersRefV.pack(side='bottom')

        # label de valor do slider
        self.layerSliderValorV = ttk.Label(self.vert_frame, width=6)
        self.layerSliderValorV.pack(side='top', padx=5)

        # scala do slider
        self.layerSliderV = ttk.Scale(self.vert_frame, from_=self.nLayers, to=1, orient='vertical',
                                      state='disabled', variable=self.layerSliderVar, command=self.simularLayerV)
        self.layerSliderV.pack(side='bottom', fill='y', expand=True)
############################################################################################
        # tela-container para: label de n of layers, label de valor do slider e scala do slider (Horizontal)
        self.sim_frame = ttk.Frame(self.subwindow, padding="10")
        self.sim_frame.pack(side='top', fill='x')

        # label de n of layers
        self.layersRef = ttk.Label(self.sim_frame, text="Number of moves: ")
        self.layersRef.pack(side='left')

        # label de valor do slider
        self.layerSliderValor = ttk.Label(self.sim_frame, width=6)
        self.layerSliderValor.pack(side='right', padx=5)

        # scala do slider
        self.layerSlider = ttk.Scale(self.sim_frame, from_=0, to=100, orient='horizontal',
                                     state='disabled', variable=self.layerSliderVarH, command=self.simularGcodeVispy)
        self.layerSlider.pack(side='left', fill='x', expand=True)
############################################################################################

        # Gerando a visualização da BED/build volume
        self.generate_build_volume(
            "bottom", X_MAX_DEFAULT, Y_MAX_DEFAULT, Z_MAX_DEFAULT)

        # objetos que desenham as linhas do gcode
        self.vispy_linha_visual = visuals.Line(parent=self.vispy_view.scene)

        self.vispy_linha_visual2 = visuals.Line(parent=self.vispy_view.scene)

    def carregarGcodeVispy(self):

        # abrir selecionador de arquivos e selecionar apenas arquivos gcode
        path = filedialog.askopenfilename(
            title="Selecionar arquivo G-Code",
            # , ("Todos os arquivos", "*.*")]
            filetypes=[("G-Code", "*.gcode")]
        )
        if not path:
            return

        # atualiza o texto da label de status de leitura do gcode
        self.gcodeLabelStatusSv.set(f"Lendo: {os.path.basename(path)}...")
        self.mainwindow.update_idletasks()

        # inicializando variaveis locais
        layersM = []
        layersC = []
        posicoes = []
        posicoesAUX = []
        colors = []  # possivelmente essa var pode ser eliminada
        colorsAUX = []
        posAtual = [0.0, 0.0, 0.0]
        zMax = 0.0
        flagComeco = True
        zAnterior = None
        nLayers = 0

        try:
            # inicio da leitura do arquivo gcode
            with open(path, 'r', encoding='utf-8') as f:
                avisado = False
                for linha in f:

                    # remove comentários
                    linhaStrip = linha.split(';')[0].strip().upper()

                    # separa linha a linha dos comandos gcode
                    comandos = linhaStrip.split()

                    # se comandos tiver vazio, vai para proxima iteração do laço
                    if not comandos:
                        continue

                    # filtra pra pegar apenas comandos de travel (G0) e extrusão (G1)
                    if "G0" in comandos or "G1" in comandos:

                        # extrai as coordenadas do comando (seja negativo ou decimal)
                        xEncontrado = re.search(r"X(\-?\d+\.?\d*)", linhaStrip)
                        yEncontrado = re.search(r"Y(\-?\d+\.?\d*)", linhaStrip)
                        zEncontrado = re.search(r"Z(\-?\d+\.?\d*)", linhaStrip)
                        eEncontrado = re.search(r"E(\-?\d+\.?\d*)", linhaStrip)

                        # copia da pos atual
                        novaPos = list(posAtual)

                        # extrai somente o valor numérico das coords e reescreve no array novaPos
                        if xEncontrado:
                            novaPos[0] = float(xEncontrado.group(1))
                        if yEncontrado:
                            novaPos[1] = float(yEncontrado.group(1))
                        if zEncontrado:
                            novaPos[2] = float(zEncontrado.group(1))

                        # verifica se há alguma coordenada de gcode fora dos limites da área de impressão
                        if (novaPos[0] > abs(float(self.xMaxSv.get())) or novaPos[1] > abs(float(self.yMaxSv.get())) or novaPos[2] > abs(float(self.zMaxSv.get()))):
                            if not avisado:
                                messagebox.showerror(
                                    "Aviso", "O G-Code carregado ultrapassa os limites da impressora")
                                avisado = True

                        # verifica se é um movimento de extrusão
                        movExtruCheck = eEncontrado and float(
                            eEncontrado.group(1)) > 0 and "G1" in comandos

                        # ignora movimentos que são iguais ao anterior e n apresentam extrusão (volta pro começo do loop)
                        if novaPos == posAtual and not eEncontrado:
                            continue

                        # ignora o primeiro ponto pq ainda n existe segmento anterior (descarta o ponto 0,0,0 colocado pra iniciar a var)
                        if flagComeco:
                            flagComeco = False

                        else:
                            # se o par de pontos for de extrusão, adicona as cores desse segmento
                            if movExtruCheck:

                                # se o par de pontos for de extrusão e houver mudança na coordenada Z, atualiza o contador de camadas
                                if zAnterior is None:
                                    zAnterior = novaPos[2]
                                    nLayers += 1

                                # se o par de pontos for de extrusão e houver mudança na coordenada Z, add todos os movs/cores da camada anterior como elemento da lista de camdas, limpa as var AUX buffers e atualiza o contador de camadas
                                elif novaPos[2] != zAnterior:
                                    layersM.append(posicoesAUX)
                                    layersC.append(colorsAUX)
                                    posicoesAUX = []
                                    colorsAUX = []

                                    zAnterior = novaPos[2]
                                    nLayers += 1

                                # enchendo os buffers dnv com os movs/cores da camada atual
                                color = self.mapaDeCores(1.0)
                                colors.append(color)
                                colors.append(color)
                                colorsAUX.append(color)
                                colorsAUX.append(color)

                            # se o par de pontos for de travel, adicona as cores desse segmento
                            else:
                                travel_color = self.mapaDeCores(0.0)
                                colors.append(travel_color)
                                colors.append(travel_color)
                                colorsAUX.append(travel_color)
                                colorsAUX.append(travel_color)

                            # adiciona o par de pontos de cada segmento
                            posicoes.append(posAtual)
                            posicoes.append(novaPos)
                            posicoesAUX.append(posAtual)
                            posicoesAUX.append(novaPos)

                        # atualiza a posAtual
                        posAtual = novaPos

                        # atualiza a altura
                        if novaPos[2] > zMax:
                            zMax = novaPos[2]

                # dps que sai do laço, preciso add o que tava no buffer por ultimo pq é referente a ultima camada que só termina quando sai do laço
                layersM.append(posicoesAUX)
                layersC.append(colorsAUX)

                # passando a var local do metodo pra var global da classe (outros metodos desta classe podem acessá-la assim)
                self.nLayers = nLayers

            # Converte as listas de coordenadas e cores de segmentos em arrays np (mais eficiente pra trabalhar com vispy)
            self.gCodePosData = np.array(posicoes, dtype=np.float32)
            # self.gCodeCorData = np.array(colors, dtype=np.float32)

            # mesma coisa que o debaixo, só é mais eficiente: add a 3ª dimensão dos dados que seria a lista que armazena cada camada como elemento
            for move, moveColor in zip(layersM[:nLayers], layersC[:nLayers]):
                self.gCodeLayers.append(np.array(move, dtype=np.float32))
                self.gCodeColorLayers.append(
                    np.array(moveColor, dtype=np.float32))

            # bloco mais simples
            # for i in range(0, nLayers, 1):
            #     self.gCodeLayers.append(np.array(layersM[i], dtype=np.float32))
            #     self.gCodeColorLayers.append(
            #         np.array(layersC[i], dtype=np.float32))

            # habilitando o slider Horizontal
            self.layerSlider.config(state='normal')

            # habilitando o slider Vertical
            self.layerSliderV.config(from_=self.nLayers, to=1)
            self.layerSliderVar.set(self.nLayers)
            self.layerSliderV.config(state='normal')
            self.simularLayerV(str(nLayers))

            # Ajuste de camera
            # Pega a coordenada mínima que aparece em todos os eixos das coordenadas na lista de gcode
            x_min, y_min, z_min = np.min(self.gCodePosData, axis=0)
            # Pega a coordenada máxima que aparece em todos os eixos das coordenadas na lista de gcode
            x_max, y_max, z_max = np.max(self.gCodePosData, axis=0)

            # calcula ponto médio da peça
            centro_peca = [
                (x_min + x_max) / 2,
                (y_min + y_max) / 2,
                (z_min + z_max) / 2
            ]

            # Pega o valor da coordenada máxima entre os 3 eixos
            tamanho_peca = max(x_max - x_min, y_max - y_min, z_max - z_min)

            # centraliza a camera
            self.vispy_view.camera.center = centro_peca

            # ajuste da distância da camera
            self.vispy_view.camera.distance = tamanho_peca * 1

        # tratamento de erro
        except Exception as e:
            messagebox.showerror("Erro ao Ler G-Code",
                                 f"Não foi possível analisar o arquivo: {e}")
            self.gcodeLabelStatusSv.set("Erro ao carregar arquivo.")
            self.layerSlider.config(state='disabled')
            self.layerSliderV.config(state='disabled')

    def simularLayerV(self, sliderValStr):

        # pega o valor setado no slider vertical e converte pra int
        self.currentLayer = int(float(sliderValStr))

        # atualiza o numero que aparece na label do sliderV pro valor da camda setada atual
        self.layerSliderValorV.config(text=f"{self.currentLayer}")

        # Se o slider estiver no zero, não há o que concatenar
        if self.currentLayer <= 0:
            self.vispy_linha_visual.visible = False
            return

        # Pega todas as camadas do início até a camada atual de uma vez só
        # O fatiamento [:self.currentLayer] vai do índice 0 até o índice desejado -1
        camadas_para_unir = self.gCodeLayers[:self.currentLayer]
        cor_camadas = self.gCodeColorLayers[:self.currentLayer]

        # Concatena todas elas de uma só vez no eixo das linhas (axis=0)
        gCodeAcumulado = np.concatenate(camadas_para_unir, axis=0)
        gCodeAcumuladoCor = np.concatenate(cor_camadas, axis=0)

        # inicializa a camada selecionada com o slider vertical em 100%
        self.simularGcodeVispy(str(len(self.gCodeLayers[self.currentLayer-1])))

        # renderizando gcode das camadas até a camda atual definida pelo o usuário no sliderV
        self.vispy_linha_visual.visible = True

        # Envia os dados pro Vispy, relacionando cada par de coordenadas de movimento com o respectivo par de cor
        self.vispy_linha_visual.set_data(
            pos=gCodeAcumulado,
            color=gCodeAcumuladoCor,
            connect='segments'
        )

        # Se a camada atual n for a primeira, ele habilita a construção da sombra das camadas anteriores
        if self.currentLayer > 1:

            # pegas as camadas até a anterior a atual (pq é a sombra)
            camadas_para_unir_Sup = self.gCodeLayers[:self.currentLayer-1]
            # n fiz uma copia da lista de cores de comandos para cada camada pq como vou usar uma só cor pra sombra, posso usar a mesma lista de cima que me fornecerá o mesmo num de elementos

            # concatena todos os movs das camdas em um unico vetor
            gCodeAcumuladoSup = np.concatenate(camadas_para_unir_Sup, axis=0)

            # Agora self.gCodeAcumuladoSup é um único array NumPyzão com formato (todos os movs/linhas gcode de camdas até a camada atual-1, 3)

            cor_escolhida = np.array([0.0, 0.0, 0.0], dtype=np.float32)

            # Pegamos o número total de linhas acumuladas, como o numero de linhas de comando gcode tem o mesmo numero de linhas das suas respectivas cores de mov, uso a mesma lista (comandos/movs)
            total_linhas = len(gCodeAcumuladoSup)

            # Criamos a matriz de cores repetindo a 'cor_escolhida' para cada linha do G-code
            gCodeAcumuladoCorSup = np.tile(
                cor_escolhida, (total_linhas, 1))

            # Trava de segurança: se o array final por acaso estiver vazio, não renderiza
            if total_linhas == 0:
                self.vispy_linha_visual2.visible = False
                return

            # Desabilita a renderização mas deixa toda a estrutura de visualização construida em segundo plano
            self.vispy_linha_visual2.visible = False
            self.vispy_linha_visual2.set_data(
                pos=gCodeAcumuladoSup,
                color=gCodeAcumuladoCorSup,
                # utilizando strip ao inves de segment pq n preciso que a sombra passe pedaço por pedaço das trajetorias e sim que pode gerar de uma vez direto
                connect='strip'
            )

        else:
            # Deixa desabilitada a renderização estrutura visual da sombra
            self.vispy_linha_visual2.visible = False
            return

    def simularGcodeVispy(self, sliderValStr):

        try:
            # converte o valor do slider que vem inicialmente com String
            current_vertices = int(float(sliderValStr))
        except ValueError:
            print(
                "Tipo de dado incompativel com 'current_vertices', escreva um valor númerico")

        # se n tiver vértices, renderiza nada e retorna
        if current_vertices <= 0:
            # Esconde em vez de mandar array vazio
            self.vispy_linha_visual.visible = False

            percent = 0.0
            self.layerSliderValor.config(text=f"{percent:.1f} %")

            return

        # Define o total de movs/linhas gcode a serem lidas para a camada atual
        self.layerSlider.config(from_=0,
                                to=len(self.gCodeLayers[self.currentLayer-1]))
        totalVertices = self.layerSlider.cget("to")

        # Inicializa/atualiza o sliderH na linha de comando gcode/mov na parte da escala do sliderH em que o usuario selecionou
        self.layerSliderVarH.set(current_vertices)

        # porcentagem das linhas gcode lidas/ parametrização da visualização da escala em formato de %
        if totalVertices > 0:
            percent = (current_vertices / totalVertices) * 100.0
        else:
            percent = 0.0

        self.layerSliderValor.config(text=f"{percent:.1f} %")

        # se tiver um número impar de coordenadas, remova uma para haver segmentos completos (pares de coordenadas)
        if current_vertices % 2 != 0:
            current_vertices -= 1

        # vars locais para pegar só as linhas gcodes da camada atual definida no sliderV
        gCodeCurrent = self.gCodeLayers[self.currentLayer-1]
        gCodeColorCurrent = self.gCodeColorLayers[self.currentLayer-1]

        # SE POR ALGUM MOTIVO O ARRAY DA CAMADA VIER VAZIO DE FATO, EVITA O CRASH
        if len(gCodeCurrent[:current_vertices]) == 0:
            self.vispy_linha_visual.visible = False
            return

        # renderizando gcode atual
        # se a camada atual for > 1, a "sombra" das camadas anteriores renderiza
        if self.currentLayer > 1:
            self.vispy_linha_visual2.visible = True

        # renderiza a camada atual até as linhas de gcode/movs selecionadas pelo usuario no sliderH
        self.vispy_linha_visual.visible = True

        self.vispy_linha_visual.set_data(
            pos=gCodeCurrent[:current_vertices],
            color=gCodeColorCurrent[:current_vertices],
            connect='segments'
        )
