# widgets mais modernos (botões, frames, etc.)
from tkinter import ttk


class Label_Container:

    """Classe que permite construir todas as labels/entrys/bottons relacionadas aos arquivos/parametros que devem estar contidos em um Labelframe/container"""

    def __init__(self, labelframe: ttk.Labelframe, n_frames: int):
        """ recebe como inputs o Labelframe que ira abrigar todo o container e a quantidade de frames/sub-containers que irão abrigar parametros/arquivos diferentes
         cria-se 1 sub-container pra cada um pq só assim cada um pode dimensionar os própris tamanhos das céluas de suas matrizes """

        # atributos/variaveis globais da classe:
        # guarda a ref do LabelFrame para construção de cada um dos n frames dentro
        self.labelframe = labelframe
        self.n_frames = n_frames
        # lista p/ armazenar os frames, dicionario p/ armazenar os textos digitados nos entrys, lista p/ armazenar todos os entrys dinamicos juntos
        self.frames = []
        self.entry = {}
        self.din_entry = []

        # Construção e armazenamento dos containers base para abrigar cada tela-matriz que recebe os dados de inserção (label, entry e button) seja parametro/arquivo
        for i in range(self.n_frames):
            self.frames.append(ttk.Frame(self.labelframe))
            # posiciona cada frame/container base um embaixo do outro (empilhando por meio do "row"), com uma matriz com 3 colunas ("columnspan") tomando de oeste a leste/direita p/ esquerda ("sticky")
            self.frames[i].grid(
                row=i, column=0, columnspan=3, padx=5, pady=5, sticky="ew")

    def inserir_parametro(self, line: int, frame_ref: int, text_label: str, width_entry: int, text_entry: str, flag_button: bool, text_button: str, command_function):
        """ criação e inserção (no frame desejado) de cada Label, Entry (campo de entrada do usuário) e botão para selecionar arquivo/ confirmar valor de parâmetro)\n
        "line" -> informa em qual linha da matriz do frame devem ser posicionados (Label, Entry e Button),\n
        "frame_ref" -> informa qual deve ser o frame (por meio do indice da lista que armazena todos os frames) em que serão criados a Label, Entry e Bottom,\n 
        "text_label" -> texto da Label,\n
        "width_entry" -> numero de caracteres do Entry,\n
        "text_entry" -> texto default do entry,\n
        "flag_button" -> flag pra ativar ou desativar a criação do botão
        "text_button" -> texto do botão,\n
        "command_function" -> função de ação do botão (*OBS: passar ela sempre com a função lambda antes para o python resolver a função mais antiga primeiro e dps ela) """

        # criação da Label e posicionamento
        ttk.Label(self.frames[frame_ref], text=text_label).grid(
            row=line, column=0, padx=5, pady=5, sticky="w")

        # criação da Entry, armazenamento no dict e posicionamento
        self.entry[frame_ref] = ttk.Entry(
            self.frames[frame_ref], width=width_entry)
        self.entry[frame_ref].insert(0, text_entry)
        self.entry[frame_ref].grid(
            row=line, column=1, padx=5, pady=5, sticky="w")

        if (flag_button):
            # criação da Button e posicionamento
            ttk.Button(self.frames[frame_ref], text=text_button, command=command_function).grid(
                row=line, column=2, padx=5, pady=5, sticky="w")

        # else:
        #     ttk.Label(self.frames[frame_ref], text=text_label_units).grid(
        #     row=line, column=2, padx=5, pady=5, sticky="w")

    def inserir_parametros_dinamicos(self, dict_frame_ref_entry: dict, frame_ref_entry: int, frame_ref_inser: int, text_label: str, width_entry: int, text_entry: str, flag_button: bool, text_button: str, command_function):
        """ Criação e inserção dinamica (no frame desejado) de Labels, Entrys e Buttons
        "dict_frame_ref_entry" -> dicionario desejado
        "frame_ref_entry" -> indice do Entry desejado no dicionário de armazenamento dos campos do usuário\n
        "frame_ref_inser" -> indice do frame desejado na lista de frames armazenados 
        "text_label" -> texto da Label,\n
        "width_entry" -> numero de caracteres do Entry,\n
        "text_entry" -> texto default do entry,\n
        "flag_button" -> flag pra ativar ou desativar a criação do botão
        "text_button" -> texto do botão,\n
        "command_function" -> função de ação do botão (*OBS: passar ela sempre com a função lambda antes para o python resolver a função mais antiga primeiro e dps ela) """

        # Se a sub-tela(container)/frame desejado já existir, limpa ele completamente
        if self.frames[frame_ref_inser] is not None:
            self.frames[frame_ref_inser].destroy()

        # Reinicializa as lista auxiliar para os entry do frame/container dinamico
        aux_entry = []

        # Acessa o valor digitado no entry desejado contido no dicionario
        n_parameter = int(dict_frame_ref_entry[frame_ref_entry].get())

        # reconstrução da subtela/container dianamico base que contém a tela-matriz para inserção dos Labels, Entrys e Buttons dinamicos
        self.frames[frame_ref_inser] = ttk.Frame(self.labelframe)
        # posicionamento do frame
        self.frames[frame_ref_inser].grid(
            row=frame_ref_inser, column=0, columnspan=3, padx=5, pady=5, sticky="ew")

        # Laço que criará e inserirá os Labels, Entrys e Buttons dos parametros/arquivos no frame dianmico criado
        for i in range(n_parameter):

            self.inserir_parametro(
                i, frame_ref_inser, f"{text_label} {i+1}", width_entry, text_entry, flag_button, text_button, command_function)

            # lista auxiliar para armazenar os entry do frame/container dinamico
            aux_entry.append(self.entry[frame_ref_inser])

        # salva a lista auxiliar na lista global da classe para ter acesso aos entrys do frame dinamico
        self.din_entry.append(aux_entry)
