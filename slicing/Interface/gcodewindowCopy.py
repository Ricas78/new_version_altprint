import tkinter as tk  # biblioteca padrão de GUI do Python
# widgets mais modernos (botões, frames, etc.)
from tkinter import ttk, messagebox, filedialog
# renderização gráfica (GPU), área de desenho 3D
from vispy.scene import visuals, SceneCanvas
from vispy.scene.visuals import Plane
from vispy.scene.cameras import TurntableCamera
from vispy.visuals.transforms import MatrixTransform
from vispy.app import use_app  # integra VisPy com Tkinter
import os  # manipulação de arquivos
import re  # regex (parse do G-code)
import numpy as np  # arrays eficientes
import matplotlib.cm as cm  # mapas de cores


X_MAX_DEFAULT = 220
Y_MAX_DEFAULT = 220
Z_MAX_DEFAULT = 220


class GcodeWindow:
    def __init__(self, mWindow: ttk.Notebook, window: tk.Tk):
        self.gcodewindow = ttk.Frame(mWindow)
        self.mainwindow = window

        # atributos pros metodos
        self.xMaxSv = tk.StringVar(value=str(X_MAX_DEFAULT))
        self.yMaxSv = tk.StringVar(value=str(Y_MAX_DEFAULT))
        self.zMaxSv = tk.StringVar(value=str(Z_MAX_DEFAULT))
        self.mapaDeCores = cm.coolwarm
        self.layerSliderVar = tk.DoubleVar()
        self.layerSliderVarH = tk.DoubleVar()
        self.currentLayer = 1
        self.nLayers = None

        # tela-container para: botao de abrir gcode, label do status gcode
        self.control_frame = ttk.Frame(self.gcodewindow, padding="10")
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

        # tela-container para: label layers, label de valor do slider e scala do slider (vertical)
        self.vert_frame = ttk.Frame(self.gcodewindow, padding="10")
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

        # tela-container para: label de n of layers, label de valor do slider e scala do slider (Horizontal)
        self.sim_frame = ttk.Frame(self.gcodewindow, padding="10")
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

        ##

        # tela-container para: visualização do gcode
        self.plot_frame = ttk.Frame(self.gcodewindow)
        self.plot_frame.pack(side='bottom', fill='both',
                             expand=True, padx=5, pady=5)

        # integra VisPy com Tkinter
        use_app('tkinter')

        # visualização da animação do gcode (cria canvas 3D)
        self.vispyCanvas = SceneCanvas(
            keys='interactive', bgcolor='white', parent=self.plot_frame)
        self.vispyCanvas.native.pack(side=tk.TOP, fill=tk.BOTH, expand=1)

        # controle de camera da visualização
        self.vispy_view = self.vispyCanvas.central_widget.add_view()

        self.vispy_view.camera = TurntableCamera(
            fov=45,
            distance=600,
            center=(X_MAX_DEFAULT/2, Y_MAX_DEFAULT/2, Z_MAX_DEFAULT/2),
            up='+z',
            translate_speed=25
        )

        # objeto que desenha as linhas do gcode
        self.vispy_linha_visual = visuals.Line(parent=self.vispy_view.scene)

# Aplicando a bed (Transformar isso em uma classe para usar tanto na aba gcode viewer como na aba stl viewer)
        # criando a bed como um plano
        bed = Plane(width=X_MAX_DEFAULT,
                    height=Y_MAX_DEFAULT,
                    direction='+z',
                    color=(0.6, 0.6, 0.6, 1),  # cinza claro
                    parent=self.vispy_view.scene)

        # centralizando a bed
        bed.transform = MatrixTransform()
        bed.transform.translate((X_MAX_DEFAULT/2, Y_MAX_DEFAULT/2, 0))

        # criando as grades da bed
        grid_points = []
        step = 10

        # grade base da mesa
        for x in range(0, X_MAX_DEFAULT + 1, step):
            grid_points.append([x, 0, 0])
            grid_points.append([x, Y_MAX_DEFAULT, 0])

        for y in range(0, Y_MAX_DEFAULT + 1, step):
            grid_points.append([0, y, 0])
            grid_points.append([X_MAX_DEFAULT, y, 0])

        # grade altura da mesa
        for x in range(0, X_MAX_DEFAULT + 1, X_MAX_DEFAULT):
            grid_points.append([x, 0, Z_MAX_DEFAULT])
            grid_points.append([x, Y_MAX_DEFAULT, Z_MAX_DEFAULT])
            grid_points.append([x, 0, 0])
            grid_points.append([x, 0, Z_MAX_DEFAULT])
            grid_points.append([x, Y_MAX_DEFAULT, 0])
            grid_points.append([x, Y_MAX_DEFAULT, Z_MAX_DEFAULT])

        for y in range(0, Y_MAX_DEFAULT + 1, Y_MAX_DEFAULT):
            grid_points.append([0, y, Z_MAX_DEFAULT])
            grid_points.append([X_MAX_DEFAULT, y, Z_MAX_DEFAULT])
            grid_points.append([0, y, 0])
            grid_points.append([0, y, Z_MAX_DEFAULT])
            grid_points.append([X_MAX_DEFAULT, y, 0])
            grid_points.append([X_MAX_DEFAULT, y, Z_MAX_DEFAULT])

        # convertendo em np array para visualização
        grid_points = np.array(grid_points, dtype=np.float32)
        bed_grid = visuals.Line(pos=grid_points,
                                color=(0.7, 0.7, 0.7, 1),
                                connect='segments',
                                parent=self.vispy_view.scene)

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
        colors = []
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

                                # se o par de pontos for de extrusão e houver mudança na coordenada Z, atualiza o contador de camadas
                                elif novaPos[2] != zAnterior:
                                    layersM.append(posicoesAUX)
                                    layersC.append(colorsAUX)
                                    posicoesAUX = []
                                    colorsAUX = []

                                    zAnterior = novaPos[2]
                                    nLayers += 1

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

                layersM.append(posicoesAUX)
                layersC.append(colorsAUX)
                self.nLayers = nLayers

                # print(nLayers)
                # # print(posicoes)
                # # print(layersM)
                # for i in range(0, 2, 1):
                #     print(layersM[i])
                # print(layersC[i])
            # Converte as listas de coordenadas e cores de segmentos em arrays np (mais eficiente pra trabalhar com vispy)
            self.gCodePosData = np.array(posicoes, dtype=np.float32)
            self.gCodeCorData = np.array(colors, dtype=np.float32)

            self.gCodeLayers = []
            self.gCodeColorLayers = []

            # mesma coisa que o debaixo, só é mais eficiente
            # for move, moveColor in zip(layersM[:nLayers], layersC[:nLayers]):
            #     self.gCodeLayers.append(np.array(move, dtype=np.float32))
            #     self.gCodeColorLayers.append(np.array(moveColor, dtype=np.float32))

            # bloco mais simples
            for i in range(0, nLayers, 1):
                self.gCodeLayers.append(np.array(layersM[i], dtype=np.float32))
                self.gCodeColorLayers.append(
                    np.array(layersC[i], dtype=np.float32))

            # Envia os dados pro Vispy, relacionando cada par de coordenadas de movimento com o respectivo par de cor
            self.vispy_linha_visual.set_data(
                pos=self.gCodePosData,
                color=self.gCodeCorData,
                connect='segments'
            )

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
################################
            # slider de camadas
            # pega o numero N de linhas gcode
            # totalVertices = len(self.gCodePosData)

            # # configura o slider pra ir de 0 a N
            # # self.layerSliderV.config(from_=nLayers, to=0)
            # self.layerSlider.config(to=totalVertices)

            # # incializa o slider no máximo da escala já
            # self.layerSliderVar.set(totalVertices)

            # # muda o texto desta variavel
            # # self.layerSliderValorV.config(text=f"100%")
            # self.layerSliderValor.config(text=f"100%")

            # # label do slider
            # self.gcodeLabelStatusSv.set(
            #     f"{os.path.basename(path)} | {len(posicoes)//2} movimentos | Altura: {zMax:.2f}mm")

            # # ativa slider
            # # self.layerSliderV.config(state='normal')
            # self.layerSlider.config(state='normal')

            self.layerSlider.config(state='normal')
            self.simularGcodeVispy(
                str(len(self.gCodeLayers[self.currentLayer-1])))

            self.layerSliderV.config(from_=self.nLayers, to=1)
            self.layerSliderVar.set(self.nLayers)
            # self.layerSliderValorV.config(text=str(self.nLayers))

            self.layerSliderV.config(state='normal')
            self.simularLayerV(str(nLayers))
################################

        # tratamento de erro
        except Exception as e:
            messagebox.showerror("Erro ao Ler G-Code",
                                 f"Não foi possível analisar o arquivo: {e}")
            self.gcodeLabelStatusSv.set("Erro ao carregar arquivo.")
            # self.layerSliderV.config(state='disabled')
            self.layerSlider.config(state='disabled')

    def simularLayerV(self, sliderValStr):

        self.currentLayer = int(float(sliderValStr))

        self.layerSliderValorV.config(text=f"{self.currentLayer} layer")

        # 2. Se o slider estiver no zero, não há o que concatenar
        if self.currentLayer <= 0:
            self.gCodeAcumulado = np.empty(
                (0, 3), dtype=np.float32)  # Cria um array vazio 0x3
            # Adicionado para limpar as cores também
            self.gCodeAcumuladoCor = np.empty((0, 3), dtype=np.float32)

            # Atualiza o VisPy com arrays vazios para sumir com o desenho da tela
            self.vispy_linha_visual.set_data(
                pos=self.gCodeAcumulado, color=self.gCodeAcumuladoCor)
            return

        # 3. Pega todas as camadas do início até a camada atual de uma vez só
        # O fatiamento [:self.currentLayer] vai do índice 0 até o índice desejado
        camadas_para_unir = self.gCodeLayers[:self.currentLayer]
        cor_camadas = self.gCodeColorLayers[:self.currentLayer]

        # 4. Concatena todas elas de uma só vez no eixo das linhas (axis=0)
        self.gCodeAcumulado = np.concatenate(camadas_para_unir, axis=0)
        self.gCodeAcumuladoCor = np.concatenate(cor_camadas, axis=0)

        # Agora self.gCodeAcumulado é um único array NumPyzão com formato (Total_De_Linhas, 3)

        self.simularGcodeVispy(str(len(self.gCodeLayers[self.currentLayer-1])))
        # renderizando gcode atual
        self.vispy_linha_visual.visible = True

        self.vispy_linha_visual.set_data(
            pos=self.gCodeAcumulado,
            color=self.gCodeAcumuladoCor,
            connect='segments'
        )

    def simularGcodeVispy(self, sliderValStr):

        # # verifica se gcodePosData existe
        # if self.gCodePosData is None:
        #     return

        try:
            # converte o valor do slider que vem inicialmente com String
            current_vertices = int(float(sliderValStr))
        except ValueError:
            current_vertices = 0

        if current_vertices <= 0:
            # <--- Solução: Esconde em vez de mandar array vazio
            self.vispy_linha_visual.visible = False

            percent = 0.0

            # self.layerSliderValorV.config(text=f"{percent:.1f} %")
            self.layerSliderValor.config(text=f"{percent:.1f} %")
            return
        try:

            self.layerSlider.config(from_=0,
                                    to=len(self.gCodeLayers[self.currentLayer-1]))
            totalVertices = self.layerSlider.cget("to")

            self.layerSliderVarH.set(current_vertices)

            # porcentagem das linhas gcode lidas
            if totalVertices > 0:
                percent = (current_vertices / totalVertices) * 100.0
            else:
                percent = 0.0

            # self.layerSliderValorV.config(text=f"{percent:.1f} %")
            self.layerSliderValor.config(text=f"{percent:.1f} %")

        except Exception as e:
            print(f"Erro ao atualizar label do slider: {e}")
            pass

        # condições de visualização:
        num_vertices = current_vertices
        # se n tiver vértices, renderiza nada
        if num_vertices <= 0:
            self.vispy_linha_visual.visible = False
            return

        # se tiver um número impar de coordenadas, remova uma para haver segmentos completos (pares de coordenadas)
        if num_vertices % 2 != 0:
            num_vertices -= 1

        gCodeCurrent = self.gCodeLayers[self.currentLayer-1]
        gCodeColorCurrent = self.gCodeColorLayers[self.currentLayer-1]

        # SE POR ALGUM MOTIVO O ARRAY DA CAMADA VIER VAZIO DE FATO, EVITA O CRASH
        if len(gCodeCurrent[:num_vertices]) == 0:
            self.vispy_linha_visual.visible = False
            return

        # renderizando gcode atual
        self.vispy_linha_visual.visible = True

        self.vispy_linha_visual.set_data(
            pos=gCodeCurrent[:num_vertices],
            color=gCodeColorCurrent[:num_vertices],
            connect='segments'
        )
