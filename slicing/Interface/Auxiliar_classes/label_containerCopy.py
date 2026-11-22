import tkinter as tk
from tkinter import ttk
from typing import Callable, Optional, Dict, List


class Label_Container:
    """Gerencia a criação e o layout modular de grupos de Label, Entry e Button.

    Attributes:
        labelframe (ttk.Labelframe): Container pai onde os sub-frames serão inseridos.
        n_frames (int): Quantidade inicial de linhas/sub-containers.
        frames (List[ttk.Frame]): Lista de sub-containers individuais para controle de grid.
        entry (Dict[int, ttk.Entry]): Dicionário mapeando o índice do frame ao seu respectivo Entry.
        din_entry (List[List[ttk.Entry]]): Lista de listas contendo os Entrys criados dinamicamente.
    """

    def __init__(self, labelframe: ttk.Labelframe, n_frames: int) -> None:
        """Inicializa o container modular e cria os sub-containers estruturais.

        Args:
            labelframe: O widget Labelframe/container_pai que abrigará os frames/sub-containers que abrigaram os parâmetros.
            n_frames: Quantidade de sub-containers empilhados a serem criados.
        """
        self.labelframe: ttk.Labelframe = labelframe
        self.n_frames: int = n_frames
        self.frames: List[ttk.Frame] = []
        self.entry: Dict[int, ttk.Entry] = {}
        self.din_entry: List[List[ttk.Entry]] = []

        # Constrói os sub-containers base para permitir dimensionamento independente de colunas
        for i in range(self.n_frames):
            frame = ttk.Frame(self.labelframe)
            frame.grid(row=i, column=0, columnspan=3,
                       padx=5, pady=5, sticky="ew")
            self.frames.append(frame)

    def inserir_parametro(
        self,
        line: int,
        frame_ref: int,
        text_label: str,
        width_entry: int,
        text_entry: str,
        flag_button: bool,
        text_button: Optional[str],
        command_function: Optional[Callable]
    ) -> ttk.Entry:
        """Cria e posiciona uma linha composta por Label, Entry e Button (opcional).

        Args:
            line: Linha do grid dentro do sub-frame alvo.
            frame_ref: Índice do sub-frame na lista `self.frames`.
            text_label: Texto exibido na Label descritiva.
            width_entry: Largura em caracteres do campo Entry.
            text_entry: Valor inicial (placeholder/default) do Entry.
            flag_button: Define se um botão de ação deve ser criado à direita do Entry.
            text_button: Rótulo do botão (caso `flag_button` seja True).
            command_function: Callback executado ao clicar no botão.

        Returns:
            ttk.Entry: A instância do campo de entrada recém-criado.
        """
        ttk.Label(self.frames[frame_ref], text=text_label).grid(
            row=line, column=0, padx=5, pady=5, sticky="w"
        )

        entry_widget = ttk.Entry(self.frames[frame_ref], width=width_entry)
        entry_widget.insert(0, text_entry)
        entry_widget.grid(row=line, column=1, padx=5, pady=5, sticky="w")
        self.entry[frame_ref] = entry_widget

        if flag_button and command_function is not None:
            ttk.Button(
                self.frames[frame_ref],
                text=text_button or "Select",
                command=command_function
            ).grid(row=line, column=2, padx=5, pady=5, sticky="w")

        return entry_widget

    def inserir_parametros_dinamicos(
        self,
        dict_frame_ref_entry: Dict[int, ttk.Entry],
        frame_ref_entry: int,
        frame_ref_inser: int,
        text_label: str,
        width_entry: int,
        text_entry: str,
        flag_button: bool,
        text_button: Optional[str],
        command_function: Optional[Callable]
    ) -> None:
        """Reconstrói dinamicamente múltiplos campos com base no valor numérico de outro Entry.

        Args:
            dict_frame_ref_entry: Dicionário onde reside o Entry controlador.
            frame_ref_entry: Chave do Entry controlador que define a quantidade de repetições.
            frame_ref_inser: Índice do sub-frame onde os novos widgets serão renderizados.
            text_label: Prefixo do texto das Labels dinâmicas.
            width_entry: Largura dos campos Entry dinâmicos.
            text_entry: Texto padrão dos campos Entry dinâmicos.
            flag_button: Define se cada linha dinâmica terá um botão.
            text_button: Texto do botão dinâmico.
            command_function: Função callback que receberá o índice `i` da linha clicada.
        """
        if self.frames[frame_ref_inser] is not None:
            self.frames[frame_ref_inser].destroy()

        # Limpa registros anteriores se estiver reconstruindo o mesmo frame dinâmico
        self.din_entry.clear()
        aux_entry: List[ttk.Entry] = []

        try:
            n_parameter = int(dict_frame_ref_entry[frame_ref_entry].get())
        except ValueError:
            n_parameter = 0

        self.frames[frame_ref_inser] = ttk.Frame(self.labelframe)
        self.frames[frame_ref_inser].grid(
            row=frame_ref_inser, column=0, columnspan=3, padx=5, pady=5, sticky="ew"
        )

        for i in range(n_parameter):
            # Captura o índice `i` por valor (idx=i) para evitar late-binding closure em loops
            callback_indexado = (
                (lambda idx=i: command_function(idx))
                if command_function is not None
                else None
            )

            entry_criado = self.inserir_parametro(
                line=i,
                frame_ref=frame_ref_inser,
                text_label=f"{text_label} {i + 1}:",
                width_entry=width_entry,
                text_entry=text_entry,
                flag_button=flag_button,
                text_button=text_button,
                command_function=callback_indexado
            )
            aux_entry.append(entry_criado)

        self.din_entry.append(aux_entry)

    def atualizar_texto_entry(
        self,
        frame_ref: int,
        novo_texto: str,
        dinamico_idx: Optional[int] = None
    ) -> None:
        """Substitui o conteúdo de um campo Entry estático ou dinâmico de forma segura.

        Args:
            frame_ref: Índice do sub-frame onde o Entry está localizado.
            novo_texto: Novo texto (ex: caminho de arquivo) a ser inserido no campo.
            dinamico_idx: Índice da linha caso o alvo seja um Entry dinâmico. Default é None.
        """
        if dinamico_idx is not None and self.din_entry:
            target_entry = self.din_entry[0][dinamico_idx]
        else:
            # precisa pegar o ttk.Entry no dicionário correspondente a chave frame_ref
            target_entry = self.entry.get(frame_ref)

            # OBS: diferente do que aconteceria se colocasse self.entry[frame_ref].get(), essa função iria retornar o texto do que no ttk.Entry do dicionario para a chave frame_ref, nao serve de nada pq nao podemos manipular/alterar o texto direto no entry só copiar o texto que já está lá

        if target_entry is not None:
            # Apaga todo o texto atual da caixinha na tela, desde o primeiro caractere (índice 0) até o último (tk.END). Sem esse passo, o novo texto seria apenas concatenado ao texto antigo.
            target_entry.delete(0, tk.END)
            # Insere a nova string (novo_texto, como o caminho de um arquivo selecionado) a partir da posição inicial (0) do campo agora vazio.
            target_entry.insert(0, novo_texto)
