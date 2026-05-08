import tkinter as tk  # biblioteca padrão de GUI do Python
# widgets mais modernos (botões, frames, etc.)
from tkinter import ttk, messagebox, filedialog
# renderização gráfica (GPU), área de desenho 3D
from vispy.scene import visuals, SceneCanvas
from vispy.scene.visuals import Box
from vispy.visuals.transforms import STTransform, MatrixTransform
from vispy.app import use_app  # integra VisPy com Tkinter
import os  # manipulação de arquivos
import re  # regex (parse do G-code)
import numpy as np  # arrays eficientes
import matplotlib.cm as cm  # mapas de cores


X_MAX_DEFAULT = 200
Y_MAX_DEFAULT = 200
Z_MAX_DEFAULT = 200


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

        # tela-container para: label de n of layers, label de valor do slider e scala do slider
        self.sim_frame = ttk.Frame(self.gcodewindow, padding="10")
        self.sim_frame.pack(side='top', fill='x')

        # label de n of layers
        self.layersRef = ttk.Label(self.sim_frame, text="Number of layers: ")
        self.layersRef.pack(side='left')

        # label de valor do slider
        self.layerSliderValor = ttk.Label(self.sim_frame, width=6)
        self.layerSliderValor.pack(side='right', padx=5)

        # scala do slider
        self.layerSlider = ttk.Scale(self.sim_frame, from_=0, to=100, orient='horizontal',
                                     state='disabled', variable=self.layerSliderVar, command=self.simularGcodeVispy)
        self.layerSlider.pack(side='left', fill='x', expand=True)

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
        self.vispy_view.camera = 'turntable'
        self.vispy_view.camera.up = 'z'
        self.vispy_view.camera.azimuth = 45
        self.vispy_view.camera.elevation = 30
        self.vispy_view.camera.fov = 45
        self.vispy_view.camera.distance = 100

        # objeto que desenha as linhas do gcode
        self.vispy_linha_visual = visuals.Line(parent=self.vispy_view.scene)

# Aplicando a bed
        # bed = Box(
        #     width=200,
        #     height=200,
        #     depth=1,
        #     color=(0.2, 0.2, 0.2, 1),  # cinza escuro
        #     parent=self.vispy_view.scene
        # )

        # bed.transform = STTransform(
        #     translate=(100, 100, -0.5)
        # )

        # trans = MatrixTransform()
        # trans.rotate(90, (1, 0, 0))  # 90° em torno do eixo X

        # bed.transform = trans

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
        posicoes = []
        colors = []
        posAtual = [0.0, 0.0, 0.0]
        zMax = 0.0
        flagComeco = True

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

                        # verifica se a alguma coordenada de gcode fora dos limites da área de impressão
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
                            # adiciona o par de pontos de cada segmento
                            posicoes.append(posAtual)
                            posicoes.append(novaPos)

                            # se o par de pontos for de extrusão, adicona as cores desse segmento
                            if movExtruCheck:
                                color = self.mapaDeCores(1.0)
                                colors.append(color)
                                colors.append(color)

                            # se o par de pontos for de travel, adicona as cores desse segmento
                            else:
                                travel_color = self.mapaDeCores(0.0)
                                colors.append(travel_color)
                                colors.append(travel_color)

                        # atualiza a posAtual
                        posAtual = novaPos

                        # atualiza a altura
                        if novaPos[2] > zMax:
                            zMax = novaPos[2]

            self.gCodePosData = np.array(posicoes, dtype=np.float32)
            self.gCodeCorData = np.array(colors, dtype=np.float32)

            self.vispy_linha_visual.set_data(
                pos=self.gCodePosData,
                color=self.gCodeCorData,
                connect='segments'
            )

            # Ajuste de camera
            x_min, y_min, z_min = np.min(self.gCodePosData, axis=0)
            x_max, y_max, z_max = np.max(self.gCodePosData, axis=0)

            centro_peca = [
                (x_min + x_max) / 2,
                (y_min + y_max) / 2,
                (z_min + z_max) / 2
            ]

            tamanho_peca = max(x_max - x_min, y_max - y_min, z_max - z_min)

            self.vispy_view.camera.center = centro_peca
            self.vispy_view.camera.distance = tamanho_peca * 2

            # slider de camadas
            totalVertices = len(self.gCodePosData)
            self.layerSlider.config(to=totalVertices)
            self.layerSliderVar.set(totalVertices)

            self.layerSliderValor.config(text=f"100%")

            self.gcodeLabelStatusSv.set(
                f"{os.path.basename(path)} | {len(posicoes)//2} movimentos | Altura: {zMax:.2f}mm")
            self.layerSlider.config(state='normal')

        except Exception as e:
            messagebox.showerror("Erro ao Ler G-Code",
                                 f"Não foi possível analisar o arquivo: {e}")
            self.gcodeLabelStatusSv.set("Erro ao carregar arquivo.")
            self.layerSlider.config(state='disabled')

    def simularGcodeVispy(self, sliderValStr):
        if self.gCodePosData is None:
            return

        try:
            current_vertices = int(float(sliderValStr))
        except ValueError:
            current_vertices = 0

        try:
            totalVertices = self.layerSlider.cget("to")

            if totalVertices > 0:
                percent = (current_vertices / totalVertices) * 100.0
            else:
                percent = 0.0

            self.layerSliderValor.config(text=f"{percent:.1f} %")

        except Exception as e:
            print(f"Erro ao atualizar label do slider: {e}")
            pass

        num_vertices = current_vertices
        if num_vertices % 2 != 0:
            num_vertices -= 1

        if num_vertices <= 0:
            self.vispy_linha_visual.visible = False
            return

        self.vispy_linha_visual.visible = True

        self.vispy_linha_visual.set_data(
            pos=self.gCodePosData[:num_vertices],
            color=self.gCodeCorData[:num_vertices],
            connect='segments'
        )
