import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from vispy.scene import visuals, SceneCanvas
from vispy.app import use_app
import os
import matplotlib.pyplot as plt
import re
import numpy as np
import matplotlib.cm as cm


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
        self.comandosGcodeParaEnviar = []
        self.totalMovimentos = 0
        self.movimentosConfirmados = 0

        self.gcodeLabelStatusSv = tk.StringVar(
            value="Nenhum arquivo carregado.")

        # tela-container para o botao de abrir gcode
        control_frame = ttk.Frame(self.gcodewindow, padding="10")
        control_frame.pack(side='top', fill='x')

        btnLer = ttk.Button(control_frame, text="Abrir G-Code",
                            command=self.carregarGcodeVispy)
        btnLer.pack(side='left', padx=5)

        labelStatus = ttk.Label(
            control_frame, textvariable=self.gcodeLabelStatusSv)
        labelStatus.pack(side='left', padx=10, expand=True, fill='x')

        self.sim_frame = ttk.Frame(self.gcodewindow, padding="10")
        self.sim_frame.pack(side='top', fill='x')

        ttk.Label(self.sim_frame, text="Number of layers: ").pack(side='left')

        self.layerSliderValor = ttk.Label(self.sim_frame, width=6)
        self.layerSliderValor.pack(side='right', padx=5)

        self.layerSlider = ttk.Scale(self.sim_frame, from_=0, to=100, orient='horizontal',
                                     state='disabled', variable=self.layerSliderVar, command=self.simularGcodeVispy)
        self.layerSlider.pack(side='left', fill='x', expand=True)

        print_frame = ttk.Frame(self.gcodewindow, padding="10")
        print_frame.pack(side='top', fill='x')

        # self.btn_imprimir = ttk.Button(
        #     print_frame, text="Imprimir G-Code", command=self.iniciarImpressao)
        # self.btn_imprimir.pack(side='left', padx=5)

        # self.btn_cancelar = ttk.Button(
        #     print_frame, text="Cancelar", command=self.cancelarImpressao, state='disabled')
        # self.btn_cancelar.pack(side='left', padx=5)

        # self.print_progress_var = tk.DoubleVar()
        # self.print_progress_bar = ttk.Progressbar(
        #     print_frame, variable=self.print_progress_var, maximum=100)
        # self.print_progress_bar.pack(
        #     side='left', fill='x', expand=True, padx=5)

        self.plot_frame = ttk.Frame(self.gcodewindow)
        self.plot_frame.pack(side='bottom', fill='both',
                             expand=True, padx=5, pady=5)

        use_app('tkinter')

        self.vispyCanvas = SceneCanvas(
            keys='interactive', bgcolor='black', parent=self.plot_frame)
        self.vispyCanvas.native.pack(side=tk.TOP, fill=tk.BOTH, expand=1)

        self.vispy_view = self.vispyCanvas.central_widget.add_view()

        self.vispy_linha_visual = visuals.Line(parent=self.vispy_view.scene)

        self.vispy_view.camera = 'turntable'
        self.vispy_view.camera.fov = 45
        self.vispy_view.camera.distance = 100

    def carregarGcodeVispy(self):
        path = filedialog.askopenfilename(
            title="Selecionar arquivo G-Code",
            # , ("Todos os arquivos", "*.*")]
            filetypes=[("G-Code", "*.gcode")]
        )
        if not path:
            return

        self.gcodeArqPath = path

        self.gcodeLabelStatusSv.set(f"Lendo: {os.path.basename(path)}...")
        self.mainwindow.update_idletasks()

        posicoes = []
        colors = []

        self.comandosGcodeParaEnviar = []

        posAtual = [0.0, 0.0, 0.0]
        tempAtual = 20.0
        tempMin, tempMax = 20.0, 20.0
        zMax = 0.0

        flagComeco = True

        self.tempNormalizada = plt.Normalize(vmin=20, vmax=250)

        try:
            with open(path, 'r', encoding='utf-8') as f:
                avisado = False
                for linha in f:
                    linhaStrip = linha.split(';')[0].strip().upper()

                    comandos = linhaStrip.split()
                    if not comandos:
                        continue

                    if "M104" in comandos or "M109" in comandos:
                        sEncontrado = re.search(
                            r"S(\d+(?:\.\d+)?)", linhaStrip)  # (\d+\.?\d*)
                        if sEncontrado:
                            tempAtual = float(sEncontrado.group(1))
                            if tempAtual > tempMax:
                                tempMax = tempAtual
                            if tempAtual > 20 and (tempAtual < tempMin or tempMin == 20.0):
                                tempMin = tempAtual
                        pass

                    movimentoFlag = False
                    if "G0" in comandos or "G1" in comandos:
                        movimentoFlag = True
                        xEncontrado = re.search(r"X(\-?\d+\.?\d*)", linhaStrip)
                        yEncontrado = re.search(r"Y(\-?\d+\.?\d*)", linhaStrip)
                        zEncontrado = re.search(r"Z(\-?\d+\.?\d*)", linhaStrip)
                        eEncontrado = re.search(r"E(\-?\d+\.?\d*)", linhaStrip)

                        novaPos = list(posAtual)

                        if xEncontrado:
                            novaPos[0] = float(xEncontrado.group(1))
                        if yEncontrado:
                            novaPos[1] = float(yEncontrado.group(1))
                        if zEncontrado:
                            novaPos[2] = float(zEncontrado.group(1))

                        if (novaPos[0] > abs(float(self.xMaxSv.get())) or novaPos[1] > abs(float(self.yMaxSv.get())) or novaPos[2] > abs(float(self.zMaxSv.get()))):
                            if not avisado:
                                messagebox.showerror(
                                    "Aviso", "O G-Code carregado ultrapassa os limites da impressora")
                                avisado = True

                        movExtruCheck = eEncontrado and float(
                            eEncontrado.group(1)) > 0 and "G1" in comandos

                        if novaPos == posAtual and not eEncontrado:
                            continue

                        if flagComeco:
                            flagComeco = False
                        else:
                            posicoes.append(posAtual)
                            posicoes.append(novaPos)

                            if movExtruCheck:
                                color = self.mapaDeCores(
                                    self.tempNormalizada(tempAtual))
                                colors.append(color)
                                colors.append(color)
                            else:
                                travel_color = (0.5, 0.5, 1.0, 0.3)
                                colors.append(travel_color)
                                colors.append(travel_color)

                        posAtual = novaPos
                        if novaPos[2] > zMax:
                            zMax = novaPos[2]
                    self.comandosGcodeParaEnviar.append(linhaStrip)
                    self.totalMovimentos += 1

            if tempMin >= tempMax:
                self.tempNormalizada = plt.Normalize(vmin=20, vmax=250)
            else:
                self.tempNormalizada = plt.Normalize(
                    vmin=tempMin, vmax=tempMax)

            self.gCodePosData = np.array(posicoes, dtype=np.float32)
            self.gCodeCorData = np.array(colors, dtype=np.float32)

            self.vispy_linha_visual.set_data(
                pos=self.gCodePosData,
                color=self.gCodeCorData,
                connect='segments'
            )

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
