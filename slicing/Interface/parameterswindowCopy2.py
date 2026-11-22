import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from typing import Optional, List
import meshio
import numpy as np
from vispy.scene.visuals import Mesh, Line
from vispy.visuals.transforms import MatrixTransform

from Auxiliar_classes.label_containerCopy import Label_Container
from Auxiliar_classes.sub_window import SubWindow

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

    def __init__(self, notebook: ttk.Notebook, mainwindow: tk.Tk) -> None:
        """Inicializa a aba de parâmetros, área de rolagem, formulários e canvas 3D.

        Args:
            notebook: O widget Notebook pai onde a aba será adicionada.
            mainwindow: A janela principal Tk da aplicação.
        """
        super().__init__(notebook, mainwindow)

        self.labelContainers: List[Label_Container] = []

        # Configuração do Canvas rolável para os parâmetros
        self.canvas_scroll = tk.Canvas(
            self.subwindow, highlightthickness=0, width=565
        )
        self.scrollbar = ttk.Scrollbar(
            self.subwindow, orient="vertical", command=self.canvas_scroll.yview
        )
        self.canvas_scroll.configure(yscrollcommand=self.scrollbar.set)

        self.scrollbar.pack(side='left', fill='y', padx=10, pady=5)
        self.canvas_scroll.pack(side='left', fill='y')

        self.container_parameters = ttk.Frame(self.canvas_scroll)
        self.canvas_window = self.canvas_scroll.create_window(
            (0, 0), window=self.container_parameters, anchor="nw"
        )
        self.container_parameters.bind("<Configure>", self.atualizar_scroll)

        # Atributos de estado visual 3D
        self.modelo_stl_visual: Optional[Mesh] = None
        self.regioes_flexiveis_visuais: Optional[List[Line]] = None
        self.offset_x: float = 0.0
        self.offset_y: float = 0.0
        self.offset_z: float = 0.0

        self._construir_formularios()

        # Gera a visualização da mesa de impressão (Build Volume)
        self.generate_build_volume(
            "left", X_MAX_DEFAULT, Y_MAX_DEFAULT, Z_MAX_DEFAULT
        )

    def _construir_formularios(self) -> None:
        """Instancia e organiza todos os LabelFrames e parâmetros da interface."""
        # 1. STL Files LabelFrame
        self.stl_files = ttk.Labelframe(
            self.container_parameters, text=" STL Files "
        )
        self.stl_files.pack(fill="x", padx=10, pady=10)

        self.labelContainers.append(Label_Container(self.stl_files, 3))

        # Linha 0: Modelo STL principal
        self.labelContainers[0].inserir_parametro(
            line=0,
            frame_ref=0,
            text_label="STL model file:",
            width_entry=40,
            text_entry="selecione o arquivo STL",
            flag_button=True,
            text_button="search",
            command_function=lambda: self.select_stl(is_flex_region=False)
        )

        # Linha 1: Quantidade de regiões flexíveis e gatilho dinâmico
        self.labelContainers[0].inserir_parametro(
            line=0,
            frame_ref=1,
            text_label="number of flex regions:",
            width_entry=3,
            text_entry="5",
            flag_button=True,
            text_button="confirm",
            command_function=lambda: [
                self.labelContainers[0].inserir_parametros_dinamicos(
                    self.labelContainers[0].entry, 1, 2,
                    "STL flex region model file ", 40, "selecione o arquivo STL",
                    True, "search",
                    lambda idx: self.select_stl(
                        is_flex_region=True, flex_index=idx)
                ),
                self.labelContainers[4].inserir_parametros_dinamicos(
                    self.labelContainers[0].entry, 1, 3,
                    "Horizontal number gap ", 5, "1", False, None, None
                ),
                self.labelContainers[4].inserir_parametros_dinamicos(
                    self.labelContainers[0].entry, 1, 4,
                    "Horizontal perc gap (%) ", 5, "20", False, None, None
                )
            ]
        )

        # 2. Printer Setup LabelFrame
        self.printer_setup = ttk.Labelframe(
            self.container_parameters, text=" Printer Setup "
        )
        self.printer_setup.pack(fill="x", padx=10, pady=10)

        self.labelContainers.append(Label_Container(self.printer_setup, 5))
        self.labelContainers[1].inserir_parametro(
            0, 0, "Start header file:", 40, "selecione o arquivo gcode", True, "search", self.select_file
        )
        self.labelContainers[1].inserir_parametro(
            0, 1, "End header file:", 40, "selecione o arquivo gcode", True, "search", self.select_file
        )
        self.labelContainers[1].inserir_parametro(
            0, 2, "X max Build volume (mm):", 5, "220", False, None, None
        )
        self.labelContainers[1].inserir_parametro(
            0, 3, "Y max Build volume (mm):", 5, "220", False, None, None
        )
        self.labelContainers[1].inserir_parametro(
            0, 4, "Z max Build volume (mm):", 5, "220", False, None, None
        )

        # 3. Common Printing Parameters LabelFrame
        self.common_print_parameters = ttk.Labelframe(
            self.container_parameters, text=" Common Printing Parameters "
        )
        self.common_print_parameters.pack(fill="x", padx=10, pady=10)

        self.labelContainers.append(
            Label_Container(self.common_print_parameters, 18)
        )
        parametros_comuns = [
            ("Infill angle (°):", "180"),
            ("Infill gap (mm):", "0.5"),
            ("X offset (mm):", "0"),
            ("Y offset (mm):", "0"),
            ("Z offset (mm):", "0"),
            ("External adjust (mm):", "0.5"),
            ("Raster gap (mm):", "0.5"),
            ("Perimeter number:", "2"),
            ("Perimeter to perimeter gap (mm):", "0.5"),
            ("Perimeter to infill gap (mm):", "0.35"),
            ("Skirt distance (mm):", "8"),
            ("Skirt number:", "2"),
            ("Skirt gap (mm):", "0.6"),
            ("Overlap (mm):", "0.0"),
            ("Layer height (mm):", "0.2"),
            ("Travel speed (mm/min):", "12000"),
            ("Retraction (mm):", "0.2"),
            ("Best path:", "True"),
        ]
        # Uso funcional de enumerate para evitar repetição de chamadas manuais
        for idx, (nome, padrao) in enumerate(parametros_comuns):
            self.labelContainers[2].inserir_parametro(
                0, idx, nome, 5, padrao, False, None, None
            )

        # 4. Non-flexible Region Parameters LabelFrame
        self.non_flex_region_parameters = ttk.Labelframe(
            self.container_parameters, text=" Non-flexible Region Parameters "
        )
        self.non_flex_region_parameters.pack(fill="x", padx=10, pady=10)

        self.labelContainers.append(
            Label_Container(self.non_flex_region_parameters, 3)
        )
        self.labelContainers[3].inserir_parametro(
            0, 0, "First layer flow (g/min):", 5, "0.9", False, None, None
        )
        self.labelContainers[3].inserir_parametro(
            0, 1, "Flow (g/min):", 5, "0.9", False, None, None
        )
        self.labelContainers[3].inserir_parametro(
            0, 2, "Speed (mm/min):", 5, "3600", False, None, None
        )

        # 5. Flexible Region Parameters LabelFrame
        self.flex_region_parameters = ttk.Labelframe(
            self.container_parameters, text=" Flexible Region Parameters "
        )
        self.flex_region_parameters.pack(fill="x", padx=10, pady=10)

        self.labelContainers.append(
            Label_Container(self.flex_region_parameters, 6)
        )
        self.labelContainers[4].inserir_parametro(
            0, 0, "Flow (g/min):", 5, "0.6", False, None, None
        )
        self.labelContainers[4].inserir_parametro(
            0, 1, "Speed (mm/min):", 5, "3600", False, None, None
        )
        self.labelContainers[4].inserir_parametro(
            0, 2, "Horizontal gap:", 5, "True", False, None, None
        )
        self.labelContainers[4].inserir_parametro(
            0, 5, "Orientation gap:", 5, "True", False, None, None
        )

    def select_stl(self, is_flex_region: bool, flex_index: Optional[int] = None) -> None:
        """Abre o seletor de arquivos STL, renderiza o modelo 3D e preenche o campo de texto.

        Args:
            is_flex_region: Indica se o arquivo pertence a uma região flexível (wireframe)
                ou à peça principal (sólida).
            flex_index: Índice da região flexível dinâmica selecionada, se aplicável.
        """
        path = filedialog.askopenfilename(
            title="Selecionar modelo STL",
            filetypes=[("Modelos STL", "*.stl")]
        )

        if not path:
            return

        # Trava de segurança antes de ler o arquivo caso falte a peça principal
        if is_flex_region and self.modelo_stl_visual is None:
            messagebox.showwarning(
                "Aviso", "Carregue a peça principal primeiro para alinhar corretamente."
            )
            return

        try:
            mesh = meshio.read(path)
            vertices = mesh.points
            faces = mesh.cells_dict["triangle"]

            if not is_flex_region:
                if self.modelo_stl_visual is not None:
                    self.modelo_stl_visual.parent = None
                    self.modelo_stl_visual = None

                stl_visual = Mesh(
                    vertices=vertices,
                    faces=faces,
                    color=(0.2, 0.6, 1.0, 0.6),
                    shading='flat',
                    parent=self.vispy_view.scene
                )
                self.modelo_stl_visual = stl_visual

                # Cálculo de centralização na mesa
                x_min, x_max = np.min(vertices[:, 0]), np.max(vertices[:, 0])
                y_min, y_max = np.min(vertices[:, 1]), np.max(vertices[:, 1])
                z_min = np.min(vertices[:, 2])

                centro_x = (x_min + x_max) / 2
                centro_y = (y_min + y_max) / 2

                self.offset_x = (X_MAX_DEFAULT / 2) - centro_x
                self.offset_y = (Y_MAX_DEFAULT / 2) - centro_y
                self.offset_z = 0.0 - z_min

                if self.regioes_flexiveis_visuais is None:
                    self.regioes_flexiveis_visuais = []
                else:
                    for regiao in self.regioes_flexiveis_visuais:
                        regiao.parent = None
                    self.regioes_flexiveis_visuais.clear()

                # Atualiza o campo de texto (Entry) da peça principal com o caminho completo
                self.labelContainers[0].atualizar_texto_entry(
                    frame_ref=0, novo_texto=path
                )

            else:
                # Extração de arestas únicas para renderização em Wireframe
                arestas = np.empty((faces.shape[0], 3, 2), dtype=np.int32)
                arestas[:, 0, 0] = faces[:, 0]
                arestas[:, 0, 1] = faces[:, 1]
                arestas[:, 1, 0] = faces[:, 1]
                arestas[:, 1, 1] = faces[:, 2]
                arestas[:, 2, 0] = faces[:, 2]
                arestas[:, 2, 1] = faces[:, 0]

                arestas_unicas = np.unique(
                    np.sort(arestas.reshape(-1, 2), axis=1), axis=0
                )
                linhas_coords = vertices[arestas_unicas]

                stl_visual = Line(
                    pos=linhas_coords,
                    color=(1.0, 0.1, 0.1, 0.8),
                    connect='segments',
                    width=1.5,
                    parent=self.vispy_view.scene
                )
                if self.regioes_flexiveis_visuais is not None:
                    self.regioes_flexiveis_visuais.append(stl_visual)

                # Atualiza o campo de texto (Entry) da região flexível correspondente
                self.labelContainers[0].atualizar_texto_entry(
                    frame_ref=2, novo_texto=path, dinamico_idx=flex_index
                )

            # Aplica o alinhamento calculado da mesa e atualiza o canvas 3D
            stl_visual.transform = MatrixTransform()
            stl_visual.transform.translate(
                (self.offset_x, self.offset_y, self.offset_z)
            )
            self.vispyCanvas.update()

        except Exception as e:
            messagebox.showerror(
                "Erro ao carregar STL",
                f"Não foi possível ler o arquivo STL:\n{e}"
            )

    def select_file(self) -> None:
        """Placeholder para seleção de arquivos G-Code de cabeçalho (Start/End)."""
        pass

    def atualizar_scroll(self, event: tk.Event) -> None:
        """Recalcula a região de rolagem do Canvas sempre que o conteúdo interno muda."""
        self.canvas_scroll.configure(
            scrollregion=self.canvas_scroll.bbox("all")
        )
