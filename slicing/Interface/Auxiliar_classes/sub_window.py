import tkinter as tk  # biblioteca padrão de GUI do Python
# widgets mais modernos (botões, frames, etc.)
from tkinter import ttk
# renderização gráfica (GPU), área de desenho 3D
from vispy.scene import visuals, SceneCanvas
from vispy.scene.visuals import Plane
from vispy.scene.cameras import TurntableCamera
from vispy.visuals.transforms import MatrixTransform
from vispy.app import use_app  # integra VisPy com Tkinter
import numpy as np  # arrays eficientes


class SubWindow:
    def __init__(self, notebook: ttk.Notebook, mainwindow: tk.Tk):
        self.subwindow = ttk.Frame(notebook)
        self.mainwindow = mainwindow
        self.vispyCanvas = None
        self.vispy_view = None

    def generate_build_volume(self, side_frame: str, X_MAX_DEFAULT, Y_MAX_DEFAULT, Z_MAX_DEFAULT):
        """metodo p/ construir a visualização do build_volume/stl/gcode
        "side_frame" -> posição em que o frame que vai armazenar o buildvolume vai ficar na subwindow\n
        "X", "Y" e "Z" maximos do build volume """
        # tela-container para: visualização do build_volume/stl/gcode
        plot_frame = ttk.Frame(self.subwindow)
        plot_frame.pack(side=side_frame, fill='both',
                        expand=True, padx=5, pady=5)

        # integra VisPy com Tkinter
        use_app('tkinter')

        # visualização da animação do gcode (cria canvas 3D)
        self.vispyCanvas = SceneCanvas(
            keys='interactive', bgcolor='white', parent=plot_frame)
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

        # Gerando a visualização da BED/build volume
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
