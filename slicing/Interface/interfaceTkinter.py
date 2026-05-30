import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
# from vispy.scene import visuals, SceneCanvas
# from vispy.app import use_app
import os
import sys
# import matplotlib.pyplot as plt
# from matplotlib.animation import FuncAnimation
# from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
# import re
# import numpy as np
# import matplotlib.cm as cm
import sv_ttk
# from gcodewindow import GcodeWindow
from gcodewindowCopy import GcodeWindow
# from parameterswindow import ParametersWindow
from parameterswindowCopy import ParametersWindow

if getattr(sys, 'frozen', False):
    APP_PATH = os.path.dirname(sys.executable)
    ASSET_PATH = sys._MEIPASS
else:
    APP_PATH = os.path.abspath(".")
    ASSET_PATH = APP_PATH


# class ParametersWindow(ttk.Frame):
#     def __init__(self, mWindow):
#         super().__init__(mWindow)


# class StlWindow(ttk.Frame):
#     def __init__(self, mWindow):
#         super().__init__(mWindow)


class MainWindow:

    def __init__(self, window: tk.Tk):
        self.window = window
        self.window.title("AltPrint V2.0")
        self.window.geometry("800x600")
        self.style = ttk.Style(self.window)
        self.tema = "light"

        # aplicar tema
        sv_ttk.set_theme(self.tema)

        # tela-container na mainWindow pra add os botões
        self.conTela = ttk.Frame(self.window, padding="10")
        self.conTela.pack(fill='x', side='top')
        self.conTela.columnconfigure(1, weight=1)
        self.conTela.columnconfigure(3, weight=1)

        # Making a Notebook
        self.notebook = ttk.Notebook(window)
        self.notebook.pack(expand=True, fill='both',
                           side='top', pady=5, padx=10)

        # Making sub-windows
        self.w1 = ParametersWindow(self.notebook, self.window)
        # self.w2 = StlWindow(self.notebook)
        self.w3 = GcodeWindow(self.notebook, self.window)

        # Adicionar abas ao notebook
        self.notebook.add(self.w1.parameterwindow, text="Parameters set")
        # self.notebook.add(self.w2, text="STL viewer")
        self.notebook.add(self.w3.gcodewindow, text="Gcode viewer")

        # botão com recurso de troca de modo claro-escuro
        self.iconeTema = tk.PhotoImage(
            file=os.path.join(ASSET_PATH, "D:\Github\_new_version_altprint\slicing\Interface\mudarTema.png"))

        self.botaoTema = ttk.Button(
            self.conTela, image=self.iconeTema, command=lambda: self.mudarTema(self.w3))
        self.botaoTema.grid(row=0, column=6, padx=5, pady=5)

    def mudarTema(self, gcodewindow: GcodeWindow):
        if self.tema == "dark":
            self.tema = "light"

        else:
            self.tema = "dark"

        # aplicar tema
        sv_ttk.set_theme(self.tema)

        # aplicar tema na animação do gcode
        if gcodewindow.vispyCanvas is None:
            return
        if (self.tema == "dark"):
            bg_color = "#2B2B2B"
        else:
            bg_color = "#F0F0F0"

        gcodewindow.vispyCanvas.bgcolor = bg_color


if __name__ == "__main__":
    janela = tk.Tk()
    inte = MainWindow(janela)
    janela.mainloop()
