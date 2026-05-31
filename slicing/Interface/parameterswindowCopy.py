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
        self.labelContainers[0].inserir_parametro(0, 1, "number of flex regions:", 3, "5", True, "confirm", lambda: [self.labelContainers[0].inserir_parametros_dinamicos(
            self.labelContainers[0].entry, 1, 2, "STL flex region model file ", 40, "selecione o arquivo STL", True, "search", self.select_file), self.labelContainers[4].inserir_parametros_dinamicos(
            self.labelContainers[0].entry, 1, 3, "Horizontal number gap:", 5, "1", False, None, None), self.labelContainers[4].inserir_parametros_dinamicos(
            self.labelContainers[0].entry, 1, 4, "Horizontal perc gap (%):", 5, "20", False, None, None)])

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

        ### Common printing parameters LabelFrame ###
        self.printer_setup = ttk.Labelframe(
            self.container_parameters, text=" Common Printing Parameters ")
        self.printer_setup.pack(fill="x", padx=10, pady=10)

        self.labelContainers.append(Label_Container(self.printer_setup, 18))

        self.labelContainers[2].inserir_parametro(
            0, 0, "Infill angle (°):", 5, "180", False, None, None)
        self.labelContainers[2].inserir_parametro(
            0, 1, "Infill gap (mm):", 5, "0.5", False, None, None)
        self.labelContainers[2].inserir_parametro(
            0, 2, "X offset (mm):", 5, "0", False, None, None)
        self.labelContainers[2].inserir_parametro(
            0, 3, "Y offset (mm):", 5, "0", False, None, None)
        self.labelContainers[2].inserir_parametro(
            0, 4, "Z offset (mm):", 5, "0", False, None, None)
        self.labelContainers[2].inserir_parametro(
            0, 5, "External adjust (mm):", 5, "0.5", False, None, None)
        self.labelContainers[2].inserir_parametro(
            0, 6, "Raster gap (mm):", 5, "0.5", False, None, None)
        self.labelContainers[2].inserir_parametro(
            0, 7, "Perimeter number:", 5, "2", False, None, None)
        self.labelContainers[2].inserir_parametro(
            0, 8, "Perimeter to perimeter gap (mm):", 5, "0.5", False, None, None)
        self.labelContainers[2].inserir_parametro(
            0, 9, "Perimeter to infill gap (mm):", 5, "0.35", False, None, None)
        self.labelContainers[2].inserir_parametro(
            0, 10, "Skirt distance (mm):", 5, "8", False, None, None)
        self.labelContainers[2].inserir_parametro(
            0, 11, "Skirt number:", 5, "2", False, None, None)
        self.labelContainers[2].inserir_parametro(
            0, 12, "Skirt gap (mm):", 5, "0.6", False, None, None)
        self.labelContainers[2].inserir_parametro(
            0, 13, "Overlap (mm):", 5, "0.0", False, None, None)
        self.labelContainers[2].inserir_parametro(
            0, 14, "Layer height (mm):", 5, "0.2", False, None, None)
        self.labelContainers[2].inserir_parametro(
            0, 15, "Travel speed (mm/min):", 5, "12000", False, None, None)
        self.labelContainers[2].inserir_parametro(
            0, 16, "Retraction (mm):", 5, "0.2", False, None, None)
        self.labelContainers[2].inserir_parametro(
            0, 17, "Best path:", 5, "True", False, None, None)

        ### Non-flexible region parameters LabelFrame ###
        self.printer_setup = ttk.Labelframe(
            self.container_parameters, text=" Non-flexible Region Parameters ")
        self.printer_setup.pack(fill="x", padx=10, pady=10)

        self.labelContainers.append(Label_Container(self.printer_setup, 3))

        self.labelContainers[3].inserir_parametro(
            0, 0, "First layer flow (g/min):", 5, "0.9", False, None, None)
        self.labelContainers[3].inserir_parametro(
            0, 1, "Flow (g/min):", 5, "0.9", False, None, None)
        self.labelContainers[3].inserir_parametro(
            0, 2, "Speed (mm/min):", 5, "3600", False, None, None)

        ### Flexible region parameters LabelFrame ###
        self.printer_setup = ttk.Labelframe(
            self.container_parameters, text=" Flexible Region Parameters ")
        self.printer_setup.pack(fill="x", padx=10, pady=10)

        self.labelContainers.append(Label_Container(self.printer_setup, 6))

        self.labelContainers[4].inserir_parametro(
            0, 0, "Flow (g/min):", 5, "0.6", False, None, None)
        self.labelContainers[4].inserir_parametro(
            0, 1, "Speed (mm/min):", 5, "3600", False, None, None)
        self.labelContainers[4].inserir_parametro(
            0, 2, "Horizontal gap:", 5, "True", False, None, None)
        # os parametro 3 e 4 desta label foram inseridos na fç lambda do numero de flex regions definido na Labelframe Stl files
        self.labelContainers[4].inserir_parametro(
            0, 5, "Orientation gap:", 5, "True", False, None, None)

    def select_file(self):
        return

    # Evento essencial: Atualiza a área de rolagem toda vez que o tamanho do frame mudar
    def atualizar_scroll(self, event):
        self.canvas_scroll.configure(
            scrollregion=self.canvas_scroll.bbox("all"))
