# widgets mais modernos (botões, frames, etc.)
import tkinter as tk
from tkinter import ttk
from typing import Callable, Optional, Dict, List, Tuple


class Label_Container:

    """ Gerencia a criação de Frames dentro de um Labelframe, cada frame é uma matriz individual sendo preenchida com Label, Entry e Button para cada respectivo parâmetro ou arquivo.

    Attributes:
        labelframe (ttk.Labelframe): Frame-pai/container-pai onde os sub-frames/sub-containers serão inseridos.
        n_frames (int): Quantidade inicial de sub-containers.
        frames (List[ttk.Frame]): Lista de sub-containers individuais para controle de grid.
        entry (Dict[int, ttk.Entry]): Dicionário mapeando o índice do frame ao seu respectivo Entry.
    """

    def __init__(self, labelframe: ttk.Labelframe, n_frames: int):
        """Inicializa o container modular e cria os sub-containers estruturais.

        Args:
            labelframe: O widget Labelframe/container_pai que abrigará os frames/sub-containers que abrigaram os parâmetros.
            n_frames: Quantidade de sub-containers empilhados a serem criados.
        """
        # atributos/variaveis globais da classe:
        # guarda a ref do LabelFrame para construção de cada um dos n frames dentro
        self.labelframe: ttk.Labelframe = labelframe
        self.n_frames: int = n_frames
        # lista p/ armazenar os frames, dicionario p/ armazenar os textos digitados nos entrys, lista p/ armazenar todos os entrys dinamicos juntos
        self.frames: List[ttk.Frame] = []
        # Chave composta (frame_ref, line) unifica campos estáticos e dinâmicos
        self.entry: Dict[Tuple[int, int], ttk.Entry] = {}
        # self.din_entry = []

        # Constrói os sub-containers base para permitir dimensionamento independente de colunas
        for i in range(self.n_frames):
            frame = ttk.Frame(self.labelframe)
            # posiciona cada frame/sub_container base um embaixo do outro (por meio do "row"), com uma matriz com 3 colunas ("columnspan") tomando de oeste a leste/direita p/ esquerda ("sticky")
            frame.grid(row=i, column=0, columnspan=3,
                       padx=5, pady=5, sticky="ew")
            self.frames.append(frame)

    def inserir_parametro(
        self,
        frame_ref: int,
        text_label: str,
        width_entry: int,
        text_entry: str,
        flag_button: bool,
        text_button: str,
        command_function: Optional[Callable],
        # Callable só indica que será passada uma função generica (com qualquer entrada e qualquer saida)
        line: int = 0
    ) -> None:
        """ criação e inserção (no frame desejado) de cada Label, Entry (campo de entrada do usuário) e botão para selecionar arquivo/ confirmar valor de parâmetro).

        Args:
            line: Linha do grid dentro do sub-frame alvo.
            frame_ref: Índice do sub-frame na lista `self.frames`.
            text_label: Texto exibido na Label descritiva.
            width_entry: Largura em caracteres do campo Entry.
            text_entry: Valor inicial (placeholder/default) do Entry.
            flag_button: Define se um botão de ação deve ser criado à direita do Entry.
            text_button: Rótulo do botão (caso `flag_button` seja True).
            command_function: função (Callback) de ação do botão (*OBS: passar ela sempre com a função lambda antes para o python resolver a função mais antiga primeiro e dps ela) """

        # criação da Label e posicionamento
        ttk.Label(self.frames[frame_ref], text=text_label).grid(
            row=line, column=0, padx=5, pady=5, sticky="w")

        # criação da Entry e armazenamento no dict, inserção de texto default e posicionamento no frame do parametro
        entry_widget = ttk.Entry(self.frames[frame_ref], width=width_entry)
        entry_widget.insert(0, text_entry)
        entry_widget.grid(row=line, column=1, padx=5, pady=5, sticky="w")
        self.entry[frame_ref, line] = entry_widget

        if (flag_button):
            # criação da Button e posicionamento
            ttk.Button(self.frames[frame_ref], text=text_button, command=command_function).grid(
                row=line, column=2, padx=5, pady=5, sticky="w")

    def inserir_parametros_dinamicos(
            self,
            dict_frame_ref_entry: Dict[Tuple[int, int], ttk.Entry],
            frame_ref_entry: int,
            frame_ref_inser: int,
            text_label: str,
            width_entry: int,
            text_entry: str,
            flag_button: bool,
            text_button: str,
            command_function: Optional[Callable[[int], None]]
            # Callable só indica que será passada uma função que deve ter pelo menos um parametro de entrada como int e retorna None
    ) -> None:
        """ Criação e inserção dinamica (no frame desejado) de Labels, Entrys e Buttons (widgets), com base no valor numérico de outro Entry.

        Args:
            dict_frame_ref_entry: Dicionário onde reside o Entry controlador.
            frame_ref_entry: Chave do Entry controlador que define a quantidade de repetições.
            frame_ref_inser: Índice do sub-frame onde os novos widgets serão renderizados.
            text_label: Prefixo do texto das Labels dinâmicas.
            width_entry: Largura dos campos Entry dinâmicos.
            text_entry: Texto padrão dos campos Entry dinâmicos.
            flag_button: Define se cada linha dinâmica terá um botão.
            text_button: Texto do botão dinâmico.
            command_function: função de ação (callback) do botão (*OBS: passar ela sempre com a função lambda antes para o python resolver a função mais antiga primeiro e dps ela)
            que receberá o índice `i` da linha clicada.
        """

        # Se a sub-tela(container)/frame desejado já existir, limpa ele completamente
        if self.frames[frame_ref_inser] is not None:
            self.frames[frame_ref_inser].destroy()

        # Recria o dict entry da classe, removendo de forma funcional apenas os Entries antigos pertencentes ao frame reconstruído
        # utiliza dict comprehension, recurso de prog func, semehante a usar filter
        self.entry = {
            # chave é a tupla (frame_ref,linha_do_frame) e o valor é o widget (ttk.entry) correspondente
            chave: widget
            for chave, widget in self.entry.items()
            # Condição para manter apenas os entries que não estão sendo atualizados pela função inserir_parametros_dinamicos()
            # chave[0] pega o primeiro item da tupla (frame_ref,linha_do_frame), portanto, pega frame_ref
            if chave[0] != frame_ref_inser
        }

        # Acessa o valor digitado no entry desejado contido no dicionario
        try:
            n_parameter = int(
                dict_frame_ref_entry[(frame_ref_entry, 0)].get())
        except (ValueError, KeyError):
            n_parameter = 0

        # reconstrução do frame/sub-container dinamico base que contém matriz/grid para inserção dos Labels, Entrys e Buttons dinamicos
        self.frames[frame_ref_inser] = ttk.Frame(self.labelframe)
        # posicionamento do frame
        self.frames[frame_ref_inser].grid(
            row=frame_ref_inser, column=0, columnspan=3, padx=5, pady=5, sticky="ew")

        # Laço que criará e inserirá os Labels, Entrys e Buttons dos parametros/arquivos no frame dianamico criado
        for i in range(n_parameter):
            # Captura o índice `i` por valor (idx=i) para evitar late-binding closure em loops
            callback_indexado = (
                (lambda idx=i: command_function(idx))
                if command_function is not None
                else None
            )
            self.inserir_parametro(
                line=i,
                frame_ref=frame_ref_inser,
                text_label=f"{text_label} {i+1}:",
                width_entry=width_entry,
                text_entry=text_entry,
                flag_button=flag_button,
                text_button=text_button,
                command_function=callback_indexado
            )

    def atualizar_texto_entry(
        self,
        frame_ref: int,
        new_text: str,
        line: int = 0
    ) -> None:
        """Substitui o conteúdo de qualquer campo Entry (estático ou dinâmico).

        Args:
            frame_ref: Índice do sub-frame onde o Entry está localizado.
            new_text: Novo texto a ser inserido no campo.
            line: Linha do Entry dentro do sub-frame. Default é 0 (para campos estáticos).
        """
        # precisa pegar o ttk.Entry no dicionário correspondente a chave (frame_ref, line)
        target_entry = self.entry.get((frame_ref, line))

        # OBS: diferente do que aconteceria se colocasse self.entry[(frame_ref, line)s].get(), essa função iria retornar o texto do que no ttk.Entry do dicionario para a chave frame_ref, nao serve de nada pq nao podemos manipular/alterar o texto direto no entry só copiar o texto que já está lá

        if target_entry is not None:
            # Apaga todo o texto atual da caixinha na tela, desde o primeiro caractere (índice 0) até o último (tk.END). Sem esse passo, o novo texto seria apenas concatenado ao texto antigo.
            target_entry.delete(0, tk.END)
            # Insere a nova string (novo_texto, como o caminho de um arquivo selecionado) a partir da posição inicial (0) do campo agora vazio.
            target_entry.insert(0, new_text)
