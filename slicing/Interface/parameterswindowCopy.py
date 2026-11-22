import tkinter as tk  # biblioteca padrão de GUI do Python
# widgets mais modernos (botões, frames, etc.)
from tkinter import ttk, messagebox, filedialog
from typing import Optional, List
from Auxiliar_classes.label_container import Label_Container
from Auxiliar_classes.sub_window import SubWindow
import meshio
from vispy.scene.visuals import Mesh, Line  # Para criar o objeto 3D na tela
from vispy.visuals.transforms import MatrixTransform
import numpy as np  # arrays eficientes
from typing import Optional, List, Dict
# import sys


X_MAX_DEFAULT = 220
Y_MAX_DEFAULT = 220
Z_MAX_DEFAULT = 220


class ParametersWindow(SubWindow):
    """Aba responsável pela configuração dos parâmetros de fatiamento e visualização 3D de STLs.

    Attributes:
        labelContainers (List[Label_Container]): Lista dos blocos de formulários da aba.
        modelo_stl_visual (Optional[Mesh]): Malha 3D principal renderizada na cena VisPy.
        regioes_flexiveis_visuais (Optional[List[Line]]): Lista de wireframes 3D das regiões flexíveis.
    """

    def __init__(self, notebook: ttk.Notebook, mainwindow: tk.Tk):
        """Inicializa a aba de parâmetros, área de rolagem, formulários e canvas 3D.

        Args:
            notebook: O widget Notebook pai onde a aba será adicionada.
            mainwindow: A janela principal Tk da aplicação.
        """

        super().__init__(notebook, mainwindow)

        self.labelContainers: List[Label_Container] = []

        # criando Canvas (container dinamico com scroll) que conterá o container dos parametros
        self.canvas_scroll = tk.Canvas(
            self.subwindow, highlightthickness=0, width=565)

        # criando a scrollbar
        self.scrollbar = ttk.Scrollbar(
            self.subwindow, orient="vertical", command=self.canvas_scroll.yview)

        # Vincula o Canvas à Barra de Rolagem
        self.canvas_scroll.configure(yscrollcommand=self.scrollbar.set)

        # Primeiro posicionamos a scrollbar na extrema esquerda
        self.scrollbar.pack(side='left', fill='y', padx=10, pady=5)
        # Depois o canvas ocupa o lado esquerdo (direita da scrollbar) e expande dinamicamente conforme os frames contidos nele crescem
        self.canvas_scroll.pack(side='left', fill='y')

        # criando container que ditará o tamanho do scroll dinamicamente para abrigar todas as labels dos parametros
        self.container_parameters = ttk.Frame(self.canvas_scroll)

        # Inserimos o Frame dentro do Canvas como uma janela interna na origem (0,0) a northwest (canto superior esquerdo e nao no meio)
        self.canvas_window = self.canvas_scroll.create_window(
            (0, 0), window=self.container_parameters, anchor="nw"
        )

        # Atualizações dinâmicas de tamanho ao redimensionar a tela
        self.container_parameters.bind("<Configure>", self.atualizar_scroll)

        # atributos de estado visual 3D p/ métodos
        self.modelo_stl_visual: Optional[Mesh] = None
        self.regioes_flexiveis_visuais: Dict[int, Line] = {}
        self.offset_x: float = 0.0
        self.offset_y: float = 0.0
        self.offset_z: float = 0.0

        # Criação e preenchimento das LabelsFrames para todos os parametros/arquivos de input do fatiador
        self.build_parameters_forms()

        # Gerando a visualização da BED/build volume
        self.generate_build_volume(
            "left", X_MAX_DEFAULT, Y_MAX_DEFAULT, Z_MAX_DEFAULT)

    def build_parameters_forms(self) -> None:
        ### STL files LabelFrame ###
        # criação do LabelFrame/Containerzao que abrigará os containers base para todos os parametros/arquivos relacionados aos STL files
        self.stl_files = ttk.Labelframe(
            self.container_parameters, text=" STL Files ")
        self.stl_files.pack(fill="x", padx=10, pady=10)

        # criando e armazenando toda a estrutura que será inserida dentro da Labelframe dos STL files
        self.labelContainers.append(Label_Container(self.stl_files, 3))

        # criando o parametro que estará dentro do frame 0 da Labelframe "STL Files"
        self.labelContainers[0].inserir_parametro(
            frame_ref=0,
            text_label="STL model file:",
            width_entry=40,
            text_entry="selecione o arquivo STL",
            flag_button=True,
            text_button="search",
            command_function=lambda: self.select_stl(is_flex_region=False)
        )

        # criando o parametro que estará dentro do frame 1 da Labelframe "STL Files"
        # além disso, ao botão desse parametro ser acionado, ele lê o valor n que está no entry desse parâmetro e cria os n parametros que estarão dentro do frame 2 da Labelframe "STL Files", cada parametro ocupa um linha do frame 2
        self.labelContainers[0].inserir_parametro(
            frame_ref=1,
            text_label="number of flex regions:",
            width_entry=3,
            text_entry="0",
            flag_button=True,
            text_button="confirm",
            command_function=lambda: [self.clean_flex_regions(),

                                      self.labelContainers[0].inserir_parametros_dinamicos(
                dict_frame_ref_entry=self.labelContainers[0].entry,
                frame_ref_entry=1,
                frame_ref_inser=2,
                text_label="STL flex region model file ",
                width_entry=40,
                text_entry="selecione o arquivo STL",
                flag_button=True,
                text_button="search",
                command_function=lambda idx: self.select_stl(
                    is_flex_region=True, flex_index=idx)
            ),
                self.labelContainers[4].inserir_parametros_dinamicos(
                    dict_frame_ref_entry=self.labelContainers[0].entry,
                    frame_ref_entry=1,
                    frame_ref_inser=3,
                    text_label="Horizontal number gap ",
                    width_entry=5,
                    text_entry="1",
                    flag_button=False,
                    text_button=None,
                    command_function=None
            ),
                self.labelContainers[4].inserir_parametros_dinamicos(
                    dict_frame_ref_entry=self.labelContainers[0].entry,
                    frame_ref_entry=1,
                    frame_ref_inser=4,
                    text_label="Horizontal perc gap (%) ",
                    width_entry=5,
                    text_entry="20",
                    flag_button=False,
                    text_button=None,
                    command_function=None
            )
            ]
        )

        ### Printer setup LabelFrame ###

        # criação do LabelFrame/Containerzao que abrigará os containers base para todos os parametros/arquivos relacionados ao Printer Setup
        self.printer_setup = ttk.Labelframe(
            self.container_parameters, text=" Printer Setup ")
        self.printer_setup.pack(fill="x", padx=10, pady=10)

        # criando e armazenando toda a estrutura que será inserida dentro da Labelframe dos Printer Setup
        self.labelContainers.append(Label_Container(self.printer_setup, 5))

        # criando o parametro que estará dentro do frame 0 da Labelframe "Printer Setup"
        self.labelContainers[1].inserir_parametro(
            frame_ref=0,
            text_label="Start header file:",
            width_entry=40,
            text_entry="selecione o arquivo gcode",
            flag_button=True,
            text_button="search",
            command_function=lambda: self.select_file(
                typefile="gcode", label_container_ref=1, frame_ref=0)
        )

        # criando o parametro que estará dentro do frame 1 da Labelframe "Printer Setup"
        self.labelContainers[1].inserir_parametro(
            frame_ref=1,
            text_label="End header file:",
            width_entry=40,
            text_entry="selecione o arquivo gcode",
            flag_button=True,
            text_button="search",
            command_function=lambda: self.select_file(
                typefile="gcode", label_container_ref=1, frame_ref=1)
        )

        # criando o parametro que estará dentro do frame 2 da Labelframe "Printer Setup"
        self.labelContainers[1].inserir_parametro(
            frame_ref=2,
            text_label="X max Build volume (mm):",
            width_entry=5,
            text_entry="220",
            flag_button=False,
            text_button=None,
            command_function=None
        )

        # criando o parametro que estará dentro do frame 3 da Labelframe "Printer Setup"
        self.labelContainers[1].inserir_parametro(
            frame_ref=3,
            text_label="Y max Build volume (mm):",
            width_entry=5,
            text_entry="220",
            flag_button=False,
            text_button=None,
            command_function=None
        )

        # criando o parametro que estará dentro do frame 4 da Labelframe "Printer Setup"
        self.labelContainers[1].inserir_parametro(
            frame_ref=4,
            text_label="Z max Build volume (mm):",
            width_entry=5,
            text_entry="220",
            flag_button=False,
            text_button=None,
            command_function=None
        )

        ### Common printing parameters LabelFrame ###

        # criação do LabelFrame/Containerzao que abrigará os containers base para todos os parametros/arquivos relacionados ao Common Printing Parameters
        self.common_print_parameters = ttk.Labelframe(
            self.container_parameters, text=" Common Printing Parameters ")
        self.common_print_parameters.pack(fill="x", padx=10, pady=10)

        # criando e armazenando toda a estrutura que será inserida dentro da Labelframe dos Common Printing Parameters
        self.labelContainers.append(
            Label_Container(self.common_print_parameters, 18))

        # criando o parametro que estará dentro do frame 0 da Labelframe "Common Printing Parameters"
        self.labelContainers[2].inserir_parametro(
            frame_ref=0,
            text_label="Infill angle (°):",
            width_entry=5,
            text_entry="180",
            flag_button=False,
            text_button=None,
            command_function=None
        )

        # criando o parametro que estará dentro do frame 1 da Labelframe "Common Printing Parameters"
        self.labelContainers[2].inserir_parametro(
            frame_ref=1,
            text_label="Infill gap (mm):",
            width_entry=5,
            text_entry="0.5",
            flag_button=False,
            text_button=None,
            command_function=None
        )

        # criando o parametro que estará dentro do frame 2 da Labelframe "Common Printing Parameters"
        self.labelContainers[2].inserir_parametro(
            frame_ref=2,
            text_label="X offset (mm):",
            width_entry=5,
            text_entry="0",
            flag_button=False,
            text_button=None,
            command_function=None
        )

        # criando o parametro que estará dentro do frame 3 da Labelframe "Common Printing Parameters"
        self.labelContainers[2].inserir_parametro(
            frame_ref=3,
            text_label="Y offset (mm):",
            width_entry=5,
            text_entry="0",
            flag_button=False,
            text_button=None,
            command_function=None
        )

        # criando o parametro que estará dentro do frame 4 da Labelframe "Common Printing Parameters"
        self.labelContainers[2].inserir_parametro(
            frame_ref=4,
            text_label="Z offset (mm):",
            width_entry=5,
            text_entry="0",
            flag_button=False,
            text_button=None,
            command_function=None
        )

        # criando o parametro que estará dentro do frame 5 da Labelframe "Common Printing Parameters"
        self.labelContainers[2].inserir_parametro(
            frame_ref=5,
            text_label="External adjust (mm):",
            width_entry=5,
            text_entry="0.5",
            flag_button=False,
            text_button=None,
            command_function=None
        )

        # criando o parametro que estará dentro do frame 6 da Labelframe "Common Printing Parameters"
        self.labelContainers[2].inserir_parametro(
            frame_ref=6,
            text_label="Raster gap (mm):",
            width_entry=5,
            text_entry="0.5",
            flag_button=False,
            text_button=None,
            command_function=None
        )

        # criando o parametro que estará dentro do frame 7 da Labelframe "Common Printing Parameters"
        self.labelContainers[2].inserir_parametro(
            frame_ref=7,
            text_label="Perimeter number:",
            width_entry=5,
            text_entry="2",
            flag_button=False,
            text_button=None,
            command_function=None
        )

        # criando o parametro que estará dentro do frame 8 da Labelframe "Common Printing Parameters"
        self.labelContainers[2].inserir_parametro(
            frame_ref=8,
            text_label="Perimeter to perimeter gap (mm):",
            width_entry=5,
            text_entry="0.5",
            flag_button=False,
            text_button=None,
            command_function=None
        )

        # criando o parametro que estará dentro do frame 9 da Labelframe "Common Printing Parameters"
        self.labelContainers[2].inserir_parametro(
            frame_ref=9,
            text_label="Perimeter to infill gap (mm):",
            width_entry=5,
            text_entry="0.35",
            flag_button=False,
            text_button=None,
            command_function=None
        )

        # criando o parametro que estará dentro do frame 10 da Labelframe "Common Printing Parameters"
        self.labelContainers[2].inserir_parametro(
            frame_ref=10,
            text_label="Skirt distance (mm):",
            width_entry=5,
            text_entry="8",
            flag_button=False,
            text_button=None,
            command_function=None
        )

        # criando o parametro que estará dentro do frame 11 da Labelframe "Common Printing Parameters"
        self.labelContainers[2].inserir_parametro(
            frame_ref=11,
            text_label="Skirt number:",
            width_entry=5,
            text_entry="2",
            flag_button=False,
            text_button=None,
            command_function=None
        )

        # criando o parametro que estará dentro do frame 12 da Labelframe "Common Printing Parameters"
        self.labelContainers[2].inserir_parametro(
            frame_ref=12,
            text_label="Skirt gap (mm):",
            width_entry=5,
            text_entry="0.6",
            flag_button=False,
            text_button=None,
            command_function=None
        )

        # criando o parametro que estará dentro do frame 13 da Labelframe "Common Printing Parameters"
        self.labelContainers[2].inserir_parametro(
            frame_ref=13,
            text_label="Overlap (mm):",
            width_entry=5,
            text_entry="0.0",
            flag_button=False,
            text_button=None,
            command_function=None
        )

        # criando o parametro que estará dentro do frame 14 da Labelframe "Common Printing Parameters"
        self.labelContainers[2].inserir_parametro(
            frame_ref=14,
            text_label="Layer height (mm):",
            width_entry=5,
            text_entry="0.2",
            flag_button=False,
            text_button=None,
            command_function=None
        )

        # criando o parametro que estará dentro do frame 15 da Labelframe "Common Printing Parameters"
        self.labelContainers[2].inserir_parametro(
            frame_ref=15,
            text_label="Travel speed (mm/min):",
            width_entry=5,
            text_entry="12000",
            flag_button=False,
            text_button=None,
            command_function=None
        )

        # criando o parametro que estará dentro do frame 16 da Labelframe "Common Printing Parameters"
        self.labelContainers[2].inserir_parametro(
            frame_ref=16,
            text_label="Retraction (mm):",
            width_entry=5,
            text_entry="0.2",
            flag_button=False,
            text_button=None,
            command_function=None
        )

        # criando o parametro que estará dentro do frame 17 da Labelframe "Common Printing Parameters"
        self.labelContainers[2].inserir_parametro(
            frame_ref=17,
            text_label="Best path:",
            width_entry=5,
            text_entry="True",
            flag_button=False,
            text_button=None,
            command_function=None
        )

        ### Non-flexible region parameters LabelFrame ###

        # criação do LabelFrame/Containerzao que abrigará os containers base para todos os parametros/arquivos relacionados ao "Non-flexible region parameters"
        self.non_flex_region_parameters = ttk.Labelframe(
            self.container_parameters, text=" Non-flexible Region Parameters ")
        self.non_flex_region_parameters.pack(fill="x", padx=10, pady=10)

        # criando e armazenando toda a estrutura que será inserida dentro da Labelframe dos "Non-flexible region parameters"
        self.labelContainers.append(Label_Container(
            self.non_flex_region_parameters, 3))

        # criando o parametro que estará dentro do frame 0 da Labelframe "Non-flexible region parameters"
        self.labelContainers[3].inserir_parametro(
            frame_ref=0,
            text_label="First layer flow (g/min):",
            width_entry=5,
            text_entry="0.9",
            flag_button=False,
            text_button=None,
            command_function=None
        )

        # criando o parametro que estará dentro do frame 1 da Labelframe "Non-flexible region parameters"
        self.labelContainers[3].inserir_parametro(
            frame_ref=1,
            text_label="Flow (g/min):",
            width_entry=5,
            text_entry="0.9",
            flag_button=False,
            text_button=None,
            command_function=None
        )

        # criando o parametro que estará dentro do frame 2 da Labelframe "Non-flexible region parameters"
        self.labelContainers[3].inserir_parametro(
            frame_ref=2,
            text_label="Speed (mm/min):",
            width_entry=5,
            text_entry="3600",
            flag_button=False,
            text_button=None,
            command_function=None
        )

        ### Flexible region parameters LabelFrame ###

        # criação do LabelFrame/Containerzao que abrigará os containers base para todos os parametros/arquivos relacionados ao "Flexible region parameters"
        self.flex_region_parameters = ttk.Labelframe(
            self.container_parameters, text=" Flexible Region Parameters ")
        self.flex_region_parameters.pack(fill="x", padx=10, pady=10)

        # criando e armazenando toda a estrutura que será inserida dentro da Labelframe dos "Flexible region parameters"
        self.labelContainers.append(
            Label_Container(self.flex_region_parameters, 6))

        # criando o parametro que estará dentro do frame 0 da Labelframe "Flexible region parameters"
        self.labelContainers[4].inserir_parametro(
            frame_ref=0,
            text_label="Flow (g/min):",
            width_entry=5,
            text_entry="0.6",
            flag_button=False,
            text_button=None,
            command_function=None
        )

        # criando o parametro que estará dentro do frame 1 da Labelframe "Flexible region parameters"
        self.labelContainers[4].inserir_parametro(
            frame_ref=1,
            text_label="Speed (mm/min):",
            width_entry=5,
            text_entry="3600",
            flag_button=False,
            text_button=None,
            command_function=None
        )

        # criando o parametro que estará dentro do frame 2 da Labelframe "Flexible region parameters"
        self.labelContainers[4].inserir_parametro(
            frame_ref=2,
            text_label="Horizontal gap:",
            width_entry=5,
            text_entry="True",
            flag_button=False,
            text_button=None,
            command_function=None
        )

        # OBS: os parametros dos frames 3 e 4 desta Labelframe foram inseridos na fç lambda do numero de flex regions definido na Labelframe Stl files

        # criando o parametro que estará dentro do frame 5 da Labelframe "Flexible region parameters"
        self.labelContainers[4].inserir_parametro(
            frame_ref=5,
            text_label="Orientation gap:",
            width_entry=5,
            text_entry="True",
            flag_button=False,
            text_button=None,
            command_function=None
        )

    def select_stl(self, is_flex_region: bool, flex_index: int = None):

        if (not is_flex_region):

            path = self.select_file(
                typefile="stl", label_container_ref=0, frame_ref=0)

            if not path:
                return  # Usuário cancelou a seleção do arquivo

            # Usamos o meshio para ler o arquivo de forma segura e moderna!
            # O meshio não sofre com o problema do NumPy.
            mesh = meshio.read(path)

            # Extraímos os vértices e as faces da estrutura do meshio
            vertices = mesh.points  # Coordenadas X, Y, Z dos pontos

            # O meshio guarda as faces dentro de um objeto de células.
            # Pegamos o primeiro grupo de células geométricas (que serão os triângulos do STL)
            faces = mesh.cells_dict["triangle"]

            # Limpeza de segurança: Se já existia um STL carregado antes, remove da cena
            if self.modelo_stl_visual is not None:
                self.modelo_stl_visual.parent = None
                self.modelo_stl_visual = None
            # Cria o objeto visual 3D (Mesh) dentro da cena da sua mesa
            stl_visual = Mesh(
                vertices=vertices,
                faces=faces,
                # Azul translúcido (com 80% de opacidade)
                color=(0.2, 0.6, 1.0, 0.6),
                shading='flat',              # Ativa sombras nas facetas para dar relevo 3D
                parent=self.vispy_view.scene  # <--- ENTRA NA MESMA CENA DA MESA!
            )

            self.modelo_stl_visual = stl_visual

            # MATEMÁTICA DE CENTRALIZAÇÃO (Continua exatamente igual)
            x_min, x_max = np.min(vertices[:, 0]), np.max(vertices[:, 0])
            y_min, y_max = np.min(vertices[:, 1]), np.max(vertices[:, 1])
            z_min, z_max = np.min(vertices[:, 2]), np.max(vertices[:, 2])

            centro_x = (x_min + x_max) / 2
            centro_y = (y_min + y_max) / 2

            self.offset_x = (X_MAX_DEFAULT / 2) - centro_x
            self.offset_y = (Y_MAX_DEFAULT / 2) - centro_y
            self.offset_z = 0.0 - z_min

            # Se re-carregar a peça principal, limpa as flexíveis antigas da tela e atualiza o texto dos respectivos entries de cada região flex
            if self.regioes_flexiveis_visuais:

                for i in self.regioes_flexiveis_visuais.keys():
                    self.labelContainers[0].atualizar_texto_entry(
                        frame_ref=2, new_text="selecione o arquivo STL", line=i)

                self.clean_flex_regions()

        else:

            # SE o usuário tentar carregar a flexível antes da principal, evita o erro:
            if self.modelo_stl_visual is None:
                messagebox.showwarning(
                    "Aviso", "Carregue a peça principal primeiro para alinhar corretamente.")
                return

            if flex_index is None:
                raise ValueError(
                    "O parâmetro 'flex_index' é obrigatório para regiões flexíveis.")

            path = self.select_file(
                typefile="stl", label_container_ref=0, frame_ref=2, line_ref=flex_index)

            if not path:
                return  # Usuário cancelou a seleção do arquivo

            # Usamos o meshio para ler o arquivo de forma segura e moderna!
            # O meshio não sofre com o problema do NumPy.
            mesh = meshio.read(path)

            # Extraímos os vértices e as faces da estrutura do meshio
            vertices = mesh.points  # Coordenadas X, Y, Z dos pontos

            # O meshio guarda as faces dentro de um objeto de células.
            # Pegamos o primeiro grupo de células geométricas (que serão os triângulos do STL)
            faces = mesh.cells_dict["triangle"]

            # VISUALIZAÇÂO DE SOLIDO PARA ARESTA####################################
            # MATEMÁTICA DE ARESTAS: Transforma os triângulos em pares de linhas (Wireframe)
            # Pegamos os índices dos vértices que formam as faces
            # Para cada triângulo com vértices (A, B, C), criamos as linhas A->B, B->C, C->A
            arestas = np.empty((faces.shape[0], 3, 2), dtype=np.int32)
            arestas[:, 0, 0] = faces[:, 0]
            arestas[:, 0, 1] = faces[:, 1]
            arestas[:, 1, 0] = faces[:, 1]
            arestas[:, 1, 1] = faces[:, 2]
            arestas[:, 2, 0] = faces[:, 2]
            arestas[:, 2, 1] = faces[:, 0]

            # Achamos apenas os caminhos de índices únicos para não desenhar a mesma linha duas vezes
            arestas_unicas = np.unique(
                np.sort(arestas.reshape(-1, 2), axis=1), axis=0)

            # Mapeia os índices de volta para as coordenadas X, Y, Z reais dos vértices (mapeia "arestas_unicas" que sao bidimensionais nos "vértices" que sao 3D)
            linhas_coords = vertices[arestas_unicas]

            # Se já existir um wireframe vinculado a este `flex_index`, remove da cena antes de criar o novo, em outras palavras, se já tiver sido colocado um stl para flex region flex_index, ele apaga a visualização deste stl anterior
            visual_anterior = self.regioes_flexiveis_visuais.get(flex_index)
            if visual_anterior is not None:
                visual_anterior.parent = None

            # Cria o objeto visual de LINHAS (Wireframe) em vez de uma malha sólida
            stl_visual = Line(
                pos=linhas_coords,
                color=(1.0, 0.1, 0.1, 0.8),  # Vermelho bem vivo e visível
                connect='segments',          # Diz ao VisPy para conectar em pares isolados
                # Espessura da linha da grade (pode ajustar)
                width=1.5,
                parent=self.vispy_view.scene
            )

            ####################################

            # Armazena/sobrescreve exatamente na chave correspondente a esta região flexível
            self.regioes_flexiveis_visuais[flex_index] = stl_visual

        # Aplica EXATAMENTE o mesmo vetor de transformação em ambas
        stl_visual.transform = MatrixTransform()
        stl_visual.transform.translate(
            (self.offset_x, self.offset_y, self.offset_z))

        # Atualiza a tela
        self.vispyCanvas.update()
        # except Exception as e:
        #     messagebox.showerror("Erro ao carregar STL",
        #                          f"Não foi possível ler o arquivo STL:\n{e}")

    def select_file(self, typefile: str, label_container_ref: int, frame_ref: int, line_ref: int = 0):

        # 1. Validação de Tipo (evita falha silenciosa caso passem None ou número)
        if not isinstance(typefile, str):
            raise TypeError(
                f"O parâmetro 'typefile' deve ser uma string, mas recebeu {type(typefile).__name__}."
            )

        # higienização de string, removendo todos os espaços em branco invisíveis que possam existir antes do primeiro caractere e depois do último caractere do texto
        clean_typefile = typefile.strip()

        # 2. Normalização: o Tkinter exige '*.' antes da extensão (ex: '*.stl')
        typefile_format = f"*.{clean_typefile}"
        label_type = f"Arquivos .{clean_typefile}"

        # 3. Abre a caixa de diálogo para selecionar APENAS arquivos STL
        path = filedialog.askopenfilename(
            title=f"Selecione um arquivo {clean_typefile}",
            filetypes=[(label_type, typefile_format)]
        )

        # Se o usuário fechar a janela ou cancelar, interrompe o processo
        if not path:
            return

        # 4. Atualiza o campo de texto (Entry) da peça principal com o caminho completo
        self.labelContainers[label_container_ref].atualizar_texto_entry(
            frame_ref=frame_ref, new_text=path, line=line_ref
        )

        return path

    def clean_flex_regions(self) -> None:
        """Remove todos os wireframes das regiões flexíveis da cena 3D.
         Ou seja, remove todos os objetos 3D das regiões flexiveis visualizados """

        for regiao_visual in self.regioes_flexiveis_visuais.values():
            regiao_visual.parent = None

        self.regioes_flexiveis_visuais.clear()

    # Evento essencial: Atualiza a área de rolagem toda vez que o tamanho do frame mudar
    def atualizar_scroll(self, event):
        self.canvas_scroll.configure(
            scrollregion=self.canvas_scroll.bbox("all"))
