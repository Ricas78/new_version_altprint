import tkinter as tk  # biblioteca padrão de GUI do Python
# widgets mais modernos (botões, frames, etc.)
from tkinter import ttk, messagebox, filedialog
from Auxiliar_classes.label_container import Label_Container


class ParametersWindow:
    def __init__(self, mWindow: ttk.Notebook, window: tk.Tk):
        self.parameterwindow = ttk.Frame(mWindow)
        self.mainwindow = window

        self.labelContainers = []
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
        # Depois o canvas ocupa o lado esquerdo (direita da scrollbar) e expande dinamicamente conforme os frames contidos nele crescem
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

        # criando e armazenando toda a estrutura que será inserida dentro da Labelframe dos STL files
        self.labelContainers.append(Label_Container(self.stl_files, 3))

        # Inserindo os parâmetros de forma empilhada
        self.labelContainers[0].inserir_parametro(
            0, 0, "STL model file:", 40, "selecione o arquivo STL", True, "search", self.select_file)
        self.labelContainers[0].inserir_parametro(0, 1, "number of flex regions:", 3, "1", True, "confirm", lambda: self.labelContainers[0].inserir_parametros_dinamicos(
            1, 2, "STL flex region model file ", 40, "selecione o arquivo STL", True, "search", self.select_file))

        ### Printer setup LabelFrame ###
        self.printer_setup = ttk.Labelframe(
            self.container_parameters, text=" Printer Setup ")
        self.printer_setup.pack(fill="x", padx=10, pady=10)

        self.labelContainers.append(Label_Container(self.printer_setup, 5))

        self.labelContainers[1].inserir_parametro(
            0, 0, "Start header file:", 40, "selecione o arquivo gcode", True, "search", self.select_file)
        self.labelContainers[1].inserir_parametro(
            0, 1, "End header file:", 40, "selecione o arquivo gcode", True, "search", self.select_file)
        self.labelContainers[1].inserir_parametro(
            0, 2, "X max Build volume (mm):", 5, "220", False, None, None)
        self.labelContainers[1].inserir_parametro(
            0, 3, "Y max Build volume (mm):", 5, "220", False, None, None)
        self.labelContainers[1].inserir_parametro(
            0, 4, "Z max Build volume (mm):", 5, "220", False, None, None)

    def select_file(self):
        return

    # Evento essencial: Atualiza a área de rolagem toda vez que o tamanho do frame mudar
    def atualizar_scroll(self, event):
        self.canvas_scroll.configure(
            scrollregion=self.canvas_scroll.bbox("all"))
