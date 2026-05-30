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


class ParametersWindow:
    def __init__(self, mWindow: ttk.Notebook, window: tk.Tk):
        self.parameterwindow = ttk.Frame(mWindow)
        self.mainwindow = window

        # atributos pros metodos
        self.flex_regions_L = []
        self.flex_regions_entry_stl = []
        self.flex_regions_button = []
        # Atributo que guardará o sub-frame das regiões dinâmicas
        self.container_dianamico_flex_regions = None

        # criando Canvas (container dinamico com scroll) que conterá o container dos parametros
        self.canvas_scroll = tk.Canvas(
            self.parameterwindow, highlightthickness=0)

        # criando a scrollbar
        self.scrollbar = ttk.Scrollbar(
            self.parameterwindow, orient="vertical", command=self.canvas_scroll.yview)

        # Vincula o Canvas à Barra de Rolagem
        self.canvas_scroll.configure(yscrollcommand=self.scrollbar.set)

        # Primeiro posicionamos a scrollbar na extrema esquerda
        self.scrollbar.pack(side='left', fill='y', padx=5, pady=5)
        # Depois o canvas ocupa o lado esquerdo (direita da scrollbar)
        self.canvas_scroll.pack(side='left', fill='both', expand=True)

        # criando container que ditará o tamanho do scroll dinamicamente para abrigar todas as labels dos parametros
        self.container_parameters = ttk.Frame(self.canvas_scroll)

        # Inserimos o Frame dentro do Canvas como uma janela interna na origem (0,0) a north-west (canto superior esquerdo e nao no meio)
        self.canvas_window = self.canvas_scroll.create_window(
            (0, 0), window=self.container_parameters, anchor="nw"
        )

        # Atualizações dinâmicas de tamanho ao redimensionar a tela
        self.container_parameters.bind("<Configure>", self.atualizar_scroll)


######## -Criação das LabelsFrames para todos os parametros/arquivos de input do fatiador-##################

        ### STL files LabelFrame ###
        # criação do LabelFrame/Containerzao que abrigará os containers base para todos os parametros/arquivos relacionados aos STL files
        self.stl_files = ttk.Labelframe(
            self.container_parameters, text=" STL Files ")
        self.stl_files.pack(fill="x", padx=10, pady=10)

        # container base para abrigar a tela-matriz que representa os dados de inserção do stl model file
        self.container_stl_model_file = ttk.Frame(self.stl_files)
        self.container_stl_model_file.grid(
            row=0, column=0, columnspan=3, padx=5, pady=5, sticky="ew")

        # add arquivo STL do model file padrão (Label, campo de entrada do usuário e botão para selecionar arquivo)
        ttk.Label(self.container_stl_model_file, text="STL model file:").grid(
            row=0, column=0, padx=5, pady=5, sticky="w")
        self.entry_stl = ttk.Entry(self.container_stl_model_file, width=40)
        self.entry_stl.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        ttk.Button(self.container_stl_model_file, text="search", command=self.select_stl).grid(
            row=0, column=2, padx=5, pady=5, sticky="w")

        # container base para abrigar a tela-matriz que representa os dados de inserção do num de flex regions
        self.container_num_flex_regions = ttk.Frame(self.stl_files)
        self.container_num_flex_regions.grid(
            row=1, column=0, columnspan=3, padx=5, pady=5, sticky="ew")

        # add número de regiões flexíveis na peça (Label, campo de entrada do usuário e botão para atualizar a quantidade de campos de para seleção dos STLs das regioes flex)
        ttk.Label(self.container_num_flex_regions, text="number of flex regions:").grid(
            row=0, column=0, padx=5, pady=5, sticky="w")
        self.entry_n_f_regions = ttk.Entry(
            self.container_num_flex_regions, width=4)
        self.entry_n_f_regions.insert(0, "1")
        self.entry_n_f_regions.grid(
            row=0, column=1, padx=5, pady=5, sticky="w")
        ttk.Button(self.container_num_flex_regions, text="confirm", command=self.add_num_flex_regions).grid(
            row=0, column=2, padx=5, pady=5, sticky="w")

    def select_stl(self):
        return

    def add_num_flex_regions(self):
        # Se a sub-tela(container) que contém os campos para inserção dos STLs das flex_regions já existir, limpa ele completamente
        if self.container_dianamico_flex_regions is not None:
            self.container_dianamico_flex_regions.destroy()

        # Reinicializa as listas
        self.flex_regions_L = []
        self.flex_regions_entry_stl = []
        self.flex_regions_button = []

        try:
            n_regioes = int(self.entry_n_f_regions.get())
        except ValueError:
            n_regioes = 1  # valor padrão caso o campo esteja vazio ou inválido

        # criação da subtela/container base que contém a tela-matriz para inserção dos STLs das flex_regions
        self.container_dianamico_flex_regions = ttk.Frame(self.stl_files)
        # Como o stl_files usa grid, posicionamos o frame na linha 2, cobrindo as 3 colunas
        self.container_dianamico_flex_regions.grid(
            row=2, column=0, columnspan=3, padx=5, pady=5, sticky="ew")

        for i in range(n_regioes):

            # Criando e guardando a Label
            lbl = ttk.Label(self.container_dianamico_flex_regions,
                            text=f"STL flex region model file {i + 1}: ")
            lbl.grid(row=i, column=0, padx=5, pady=5, sticky="w")
            self.flex_regions_L.append(lbl)

            # Criando e guardando a Entry
            ent = ttk.Entry(self.container_dianamico_flex_regions, width=40)
            ent.grid(row=i, column=1, padx=5, pady=5, sticky="w")
            self.flex_regions_entry_stl.append(ent)

            # Criando e guardando o Botão
            btn = ttk.Button(self.container_dianamico_flex_regions,
                             text="search", command=self.select_stl)
            btn.grid(row=i, column=2, padx=5, pady=5, sticky="w")
            self.flex_regions_button.append(btn)

    # Evento essencial: Atualiza a área de rolagem toda vez que o tamanho do frame mudar
    def atualizar_scroll(self, event):
        self.canvas_scroll.configure(
            scrollregion=self.canvas_scroll.bbox("all"))
