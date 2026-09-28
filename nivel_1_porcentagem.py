"""Jogo de porcentagem "Responda ou Estuda" em Flet 0.86.3.

Integração:
    from nivel_1_porcentagem import criar_tela_porcentagem
    controle = criar_tela_porcentagem(page, funcao_para_voltar)

Questões:
    dados/questoes_porcentagem.json

Imagens:
    assets/imagens/produtos/

Sons:
    assets/sons/
"""

from __future__ import annotations

import asyncio
import base64
import json
import random
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Callable

import flet as ft
from flet_audio import Audio, ReleaseMode
from estado_jogo import EstadoJogo
from formatacao_matematica import markdown_matematico, texto_para_narracao
from modo_admin import ADMIN_ATIVO, barra_admin
import recursos_jogo as rj

try:
    import winsound
except ImportError:  # Android, iOS, macOS e Linux usam o áudio do Flet.
    winsound = None


BASE_DIR = Path(__file__).resolve().parent
ASSETS_DIR = BASE_DIR / "assets"
ARQUIVO_QUESTOES = BASE_DIR / "dados" / "questoes_porcentagem.json"

PREMIO_ACERTO = 100.0
PENALIDADE_ERRO = 200.0
PREMIO_ESTUDO = 50.0

# CRONÔMETRO: altere 60 para definir quantos segundos o jogador terá em cada
# questão. O tempo começa quando a situação-problema é apresentada.
TEMPO_POR_QUESTAO = 60

# Nome do módulo nos relatórios de pesquisa (dados/respostas.csv).
MODULO_PESQUISA = "Porcentagem"

# ROLAGEM DAS TELAS: espaço livre, em pixels, no fim de cada tela do módulo.
ESPACO_FINAL_ROLAGEM = 48

# VELOCIDADES DA NARRAÇÃO: o primeiro número é o valor usado internamente
# pela voz. O segundo texto é o que aparece no menu da interface.
# Para acrescentar outra opção, repita o mesmo formato. Exemplo:
# 1.25: "Moderado 1,25x",
VELOCIDADES_NARRACAO = {
    0.75: "Lento 0,75x",
    1.0: "Normal 1,0x",
    1.5: "Rápido 1,5x",
    2.0: "Muito rápido 2,0x",
}

# MASCOTE DO MÓDULO: para substituir a imagem futuramente, coloque o novo
# arquivo dentro da pasta "assets" e altere somente o caminho entre aspas.
CAMINHO_MASCOTE = "mascote_financeiro.webp"

TRILHAS = {
    "Aventura": "sons/01_aventura.wav",
    "Arcade": "sons/02_arcade.wav",
    "Conquista": "sons/03_conquista.wav",
    "Suspense": "sons/04_suspense.wav",
    "Quiz": "sons/05_quiz.wav",
    "Futurista": "sons/06_futurista.wav",
    "8 bits": "sons/07_8_bits.wav",
    "Jornada": "sons/08_jornada.wav",
    "Neon": "sons/09_neon.wav",
    "Desafio": "sons/10_desafio.wav",
}

TEMAS = {
    "Financeiro": {
        "fundo_1": "#06143C",
        "fundo_2": "#073B7A",
        "cartao": "#092B66",
        "cartao_2": "#0B4B94",
        "primaria": "#59F4FF",
        "destaque": "#FFD34E",
        "positivo": "#45E59A",
        "negativo": "#FF6E86",
        "texto": "#FFFFFF",
        "suave": "#C7F3FF",
    },
    "Neon roxo": {
        "fundo_1": "#160B35",
        "fundo_2": "#4B167E",
        "cartao": "#2B1459",
        "cartao_2": "#64239A",
        "primaria": "#70F6FF",
        "destaque": "#FFDF5D",
        "positivo": "#6EF7AD",
        "negativo": "#FF74B8",
        "texto": "#FFFFFF",
        "suave": "#E9D9FF",
    },
    "Esmeralda": {
        "fundo_1": "#052D2B",
        "fundo_2": "#087563",
        "cartao": "#075247",
        "cartao_2": "#0B8F78",
        "primaria": "#77FFE0",
        "destaque": "#FFE179",
        "positivo": "#A6FF8C",
        "negativo": "#FF8A8A",
        "texto": "#FFFFFF",
        "suave": "#D3FFF5",
    },
    "Pôr do sol": {
        "fundo_1": "#3A1032",
        "fundo_2": "#A33A35",
        "cartao": "#68253B",
        "cartao_2": "#C45137",
        "primaria": "#FFD08A",
        "destaque": "#FFF06A",
        "positivo": "#9DFFB1",
        "negativo": "#FF9EB2",
        "texto": "#FFFFFF",
        "suave": "#FFE1D9",
    },
    "Claro": {
        "fundo_1": "#EAF7FF",
        "fundo_2": "#A7D8F5",
        "cartao": "#FFFFFF",
        "cartao_2": "#D6EEFF",
        "primaria": "#006F9B",
        "destaque": "#A34B00",
        "positivo": "#087A4F",
        "negativo": "#B4233B",
        "texto": "#09254A",
        "suave": "#244E6C",
    },
}


def _borda(cor: str, largura: float = 1.0) -> ft.Border:
    return ft.Border.all(width=largura, color=cor)


def _lado(cor: str, largura: float = 1.0) -> ft.BorderSide:
    return ft.BorderSide(width=largura, color=cor)


def _raio(valor: float) -> ft.BorderRadius:
    return ft.BorderRadius.all(valor)


def _sombra(cor: str, desfoque: float = 18, y: float = 6) -> ft.BoxShadow:
    return ft.BoxShadow(
        color=cor,
        blur_radius=desfoque,
        spread_radius=0,
        offset=(0, y),
    )


def formatar_reais(valor: float) -> str:
    """Formata um número no padrão monetário brasileiro."""
    return (
        f"R$ {valor:,.2f}"
        .replace(",", "X")
        .replace(".", ",")
        .replace("X", ".")
    )


def carregar_questoes(caminho: Path = ARQUIVO_QUESTOES) -> list[dict[str, Any]]:
    """Carrega e valida o banco externo de questões."""
    with caminho.open("r", encoding="utf-8") as arquivo:
        dados = json.load(arquivo)

    questoes = dados.get("questoes")
    if not isinstance(questoes, list) or len(questoes) < 20:
        raise ValueError("O banco deve conter pelo menos 20 questões.")

    campos = {
        "id",
        "titulo",
        "produto",
        "imagem",
        "enunciado",
        "alternativas",
        "correta",
        "explicacao",
        "estudo",
        "fonte",
    }
    identificadores: set[str] = set()
    for numero, questao in enumerate(questoes, start=1):
        ausentes = campos.difference(questao)
        if ausentes:
            raise ValueError(
                f"Questão {numero}: campos ausentes: {sorted(ausentes)}"
            )
        identificador = str(questao["id"])
        if identificador in identificadores:
            raise ValueError(f"ID repetido: {identificador}")
        identificadores.add(identificador)

        alternativas = questao["alternativas"]
        correta = questao["correta"]
        if not isinstance(alternativas, list) or len(alternativas) < 2:
            raise ValueError(
                f"Questão {identificador}: inclua ao menos duas alternativas."
            )
        if not isinstance(correta, int) or not 0 <= correta < len(alternativas):
            raise ValueError(
                f"Questão {identificador}: índice da resposta inválido."
            )

        imagem_informada = str(questao["imagem"])
        if imagem_informada.startswith(("http://", "https://")):
            raise ValueError(
                f"Questão {identificador}: imagens remotas não são permitidas."
            )
        imagem = ASSETS_DIR / imagem_informada
        if not imagem.exists():
            raise FileNotFoundError(
                f"Questão {identificador}: imagem não encontrada: {imagem}"
            )

    return questoes


class JogoPorcentagem:
    """Controla cadastro, rodadas, placar, temas, trilhas e resultado."""

    def __init__(
        self,
        page: ft.Page,
        ao_voltar: Callable[..., Any],
        estado: EstadoJogo | None = None,
    ) -> None:
        self.page = page
        self.ao_voltar = ao_voltar
        self.estado = estado or EstadoJogo()
        self.trilhas = self.estado.trilhas_disponiveis()
        self.questoes_originais = carregar_questoes()
        self.questoes: list[dict[str, Any]] = []
        self.jogadores: list[dict[str, Any]] = []
        self.indice_jogador = 0
        self.indice_questao = 0
        self.tela_atual = "cadastro"
        self.tema_nome = self.estado.tema
        self.trilha_nome = self.estado.trilha
        self.som_ativo = False
        self.ultimo_resultado: dict[str, Any] | None = None
        self.tempo_restante = TEMPO_POR_QUESTAO
        self._token_cronometro = 0
        self._questao_cronometro: str | None = None
        self._cronometro_rodando = False
        self._rodada_finalizada = False
        self.texto_cronometro: ft.Text | None = None
        self.barra_cronometro: ft.ProgressBar | None = None
        self.icone_cronometro: ft.Icon | None = None
        self.narracao_ativa = False
        self._ultima_questao_narrada: str | None = None
        self._processo_narracao: subprocess.Popen[Any] | None = None
        self.velocidade_narracao = 1.0
        # VELOCIDADE INICIAL: troque 1.0 por 0.75, 1.5 ou 2.0 para mudar
        # a velocidade selecionada quando o módulo de Porcentagem for aberto.

        self.quantidade_jogadores = self.estado.quantidade_jogadores
        self.campos_nomes = [
            ft.TextField(
                label=f"Nome do jogador {indice}",
                hint_text="Digite o nome",
                value=str(self.estado.jogadores[indice - 1]["nome"]),
                prefix_icon=ft.Icons.PERSON,
                border_radius=14,
                filled=True,
                col={"xs": 12, "sm": 6},
                visible=indice <= self.quantidade_jogadores,
            )
            for indice in range(1, 5)
        ]

        self.audio = Audio(
            src=self.trilhas[self.trilha_nome],
            autoplay=False,
            volume=0.80,
            release_mode=ReleaseMode.LOOP,
        )
        self.page.services.append(self.audio)

        self.raiz = ft.Container(expand=True)
        validos, _mensagem = self.estado.nomes_validos()
        if validos:
            self._preparar_nova_partida()
        self._renderizar()
        rj.ativar_teclado(self)

    @property
    def tema(self) -> dict[str, str]:
        return TEMAS[self.tema_nome]

    @property
    def jogador_atual(self) -> dict[str, Any]:
        return self.jogadores[self.indice_jogador]

    @property
    def questao_atual(self) -> dict[str, Any]:
        return self.questoes[self.indice_questao]

    def _preparar_nova_partida(self) -> None:
        """Inicia as rodadas sem zerar o saldo acumulado dos jogadores."""
        rj.nova_sessao(self, MODULO_PESQUISA)
        self.jogadores = self.estado.jogadores_ativos()
        self.questoes = random.sample(
            self.questoes_originais,
            k=len(self.questoes_originais),
        )
        if ADMIN_ATIVO:
            # Modo administrador: mantém a ordem do banco de questões.
            self.questoes = list(self.questoes_originais)
        self.indice_jogador = 0
        self.indice_questao = 0
        self.ultimo_resultado = None
        self._questao_cronometro = None
        self._rodada_finalizada = False
        self._parar_cronometro()
        self._parar_narracao()
        self.tela_atual = "jogada"

    # ------------------------------------------------------------------
    # Renderização geral
    # ------------------------------------------------------------------

    def _controles_admin(self) -> list[ft.Control]:
        """Barra do modo administrador (vazia no jogo normal)."""
        if not ADMIN_ATIVO or self.tela_atual in {"cadastro", "erro"}:
            return []
        return [barra_admin(self)]

    def _renderizar(self) -> None:
        telas = {
            "cadastro": self._tela_cadastro,
            "jogada": self._tela_jogada,
            "pergunta": self._tela_pergunta,
            "estudo": self._tela_estudo,
            "feedback": self._tela_feedback,
            "resultado": self._tela_resultado,
            "erro": self._tela_erro,
        }
        construtor = telas.get(self.tela_atual, self._tela_cadastro)
        self.raiz.gradient = ft.LinearGradient(
            begin=ft.Alignment.TOP_CENTER,
            end=ft.Alignment.BOTTOM_CENTER,
            colors=[self.tema["fundo_1"], self.tema["fundo_2"]],
        )
        self.raiz.content = ft.SafeArea(
            content=ft.Column(
                controls=[
                    self._cabecalho(),
                    *self._controles_admin(),
                    ft.Container(
                        content=rj.com_transicao(self, construtor()),
                        padding=ft.Padding.symmetric(
                            horizontal=16,
                            # AJUSTE DE POSIÇÃO GERAL: diminua "vertical" para
                            # subir todo o conteúdo; aumente para criar mais
                            # espaço acima e abaixo das telas do módulo.
                            vertical=6,
                        ),
                    ),
                    # MARGEM FINAL: garante que a parte de baixo de cada tela
                    # (bordas, botões e últimos cartões) possa ser vista ao
                    # rolar até o fim. Aumente se algo ainda ficar cortado.
                    ft.Container(height=ESPACO_FINAL_ROLAGEM),
                ],
                # AJUSTE DE ESPAÇO: este valor separa o cabeçalho do conteúdo.
                # Diminua para subir o jogo; aumente para afastar os blocos.
                spacing=2,
                # ALWAYS deixa a barra de rolagem sempre visível, indicando
                # que existe conteúdo abaixo quando a tela não cabe inteira.
                scroll=ft.ScrollMode.ALWAYS,
                expand=True,
            ),
            minimum_padding=ft.Padding.all(6),
        )
        try:
            self.raiz.update()
        except RuntimeError:
            # Na primeira construção a raiz ainda não foi adicionada à página.
            pass
        self._sincronizar_recursos_da_rodada()

    def _cabecalho(self) -> ft.Control:
        tema = self.tema
        seletor_tema = ft.Dropdown(
            value=self.tema_nome,
            options=[
                ft.DropdownOption(key=nome, text=nome)
                for nome in TEMAS
            ],
            label="Tema",
            leading_icon=ft.Icons.PALETTE,
            bgcolor=tema["cartao"],
            color=tema["texto"],
            border_color=tema["primaria"],
            focused_border_color=tema["destaque"],
            border_radius=14,
            dense=True,
            width=170,
            on_select=self._trocar_tema,
        )
        seletor_trilha = ft.Dropdown(
            value=self.trilha_nome,
            options=[
                ft.DropdownOption(key=nome, text=nome)
                for nome in self.trilhas
            ],
            label="Trilha",
            leading_icon=ft.Icons.MUSIC_NOTE,
            bgcolor=tema["cartao"],
            color=tema["texto"],
            border_color=tema["primaria"],
            focused_border_color=tema["destaque"],
            border_radius=14,
            dense=True,
            width=170,
            on_select=self._trocar_trilha,
        )
        botao_som = ft.Button(
            content="MUTE" if self.som_ativo else "ATIVAR SOM",
            icon=(
                ft.Icons.VOLUME_UP
                if self.som_ativo
                else ft.Icons.VOLUME_OFF
            ),
            color=tema["texto"],
            bgcolor=tema["cartao_2"],
            on_click=self._alternar_som,
        )
        botao_voltar = ft.OutlinedButton(
            content="VOLTAR",
            icon=ft.Icons.ARROW_BACK,
            style=ft.ButtonStyle(
                color=tema["texto"],
                side=_lado(tema["primaria"], 1.5),
            ),
            on_click=self._voltar_ao_inicio,
        )

        titulo = ft.Column(
            controls=[
                ft.Text(
                    "RESPONDA OU ESTUDA",
                    color=tema["destaque"],
                    size=24,
                    weight=ft.FontWeight.BOLD,
                ),
                ft.Text(
                    "DESAFIO DE PORCENTAGEM",
                    color=tema["primaria"],
                    size=12,
                    weight=ft.FontWeight.BOLD,
                ),
            ],
            spacing=1,
            col={"xs": 12, "md": 4},
        )

        controles = ft.Container(
            content=ft.Row(
                controls=[
                    seletor_tema,
                    seletor_trilha,
                    botao_som,
                    botao_voltar,
                ],
                spacing=10,
                wrap=True,
                alignment=ft.MainAxisAlignment.END,
            ),
            col={"xs": 12, "md": 8},
        )

        return ft.Container(
            content=ft.ResponsiveRow(
                controls=[titulo, controles],
                columns=12,
                run_spacing=10,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=ft.Padding.symmetric(
                horizontal=20,
                # ALTURA DO CABEÇALHO: aumente ou diminua este valor para
                # deixar a faixa superior mais alta ou mais compacta.
                vertical=8,
            ),
            bgcolor=tema["cartao"],
            border=_borda(tema["primaria"], 1.5),
            border_radius=_raio(18),
            shadow=_sombra("#44000000", 16, 4),
        )

    # ------------------------------------------------------------------
    # Cadastro
    # ------------------------------------------------------------------

    def _tela_cadastro(self) -> ft.Control:
        tema = self.tema
        seletor_quantidade = ft.Dropdown(
            value=str(self.quantidade_jogadores),
            options=[
                ft.DropdownOption(key=str(numero), text=f"{numero} jogadores")
                for numero in range(2, 5)
            ],
            label="Quantidade de jogadores",
            leading_icon=ft.Icons.GROUPS,
            bgcolor=tema["cartao_2"],
            color=tema["texto"],
            border_color=tema["primaria"],
            focused_border_color=tema["destaque"],
            border_radius=14,
            width=250,
            on_select=self._alterar_quantidade,
        )

        for campo in self.campos_nomes:
            campo.bgcolor = tema["cartao_2"]
            campo.color = tema["texto"]
            campo.border_color = tema["primaria"]
            campo.focused_border_color = tema["destaque"]

        regras = [
            ("+ R$ 100,00", "Resposta correta", tema["positivo"]),
            ("− R$ 200,00", "Resposta incorreta", tema["negativo"]),
            ("R$ 50,00", "Estudar e passar a vez", tema["primaria"]),
        ]
        cartoes_regras = [
            ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Text(
                            valor,
                            color=cor,
                            size=23,
                            weight=ft.FontWeight.BOLD,
                        ),
                        ft.Text(
                            descricao,
                            color=tema["texto"],
                            size=12,
                            text_align=ft.TextAlign.CENTER,
                        ),
                    ],
                    spacing=4,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                padding=14,
                bgcolor=tema["cartao_2"],
                border=_borda(cor, 1.5),
                border_radius=_raio(16),
                col={"xs": 12, "sm": 4},
            )
            for valor, descricao, cor in regras
        ]

        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Icon(
                        ft.Icons.PERCENT,
                        size=72,
                        color=tema["destaque"],
                    ),
                    ft.Text(
                        "QUEM VAI JOGAR?",
                        size=32,
                        color=tema["texto"],
                        weight=ft.FontWeight.BOLD,
                        text_align=ft.TextAlign.CENTER,
                    ),
                    ft.Text(
                        (
                            "Cadastre de 2 a 4 participantes. A vez alterna "
                            "depois de acerto, erro ou estudo."
                        ),
                        size=15,
                        color=tema["suave"],
                        text_align=ft.TextAlign.CENTER,
                    ),
                    seletor_quantidade,
                    ft.ResponsiveRow(
                        controls=self.campos_nomes,
                        columns=12,
                        spacing=12,
                        run_spacing=12,
                    ),
                    ft.ResponsiveRow(
                        controls=cartoes_regras,
                        columns=12,
                        spacing=12,
                        run_spacing=12,
                    ),
                    ft.Text(
                        (
                            "O saldo pode ficar negativo. Serão apresentadas "
                            f"{len(self.questoes_originais)} situações reais."
                        ),
                        color=tema["suave"],
                        size=12,
                        text_align=ft.TextAlign.CENTER,
                    ),
                    ft.Button(
                        content="COMEÇAR O JOGO",
                        icon=ft.Icons.ROCKET_LAUNCH,
                        color=tema["fundo_1"],
                        bgcolor=tema["destaque"],
                        height=52,
                        on_click=self._iniciar_jogo,
                    ),
                ],
                spacing=16,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            width=920,
            padding=ft.Padding.all(24),
            bgcolor=tema["cartao"],
            border=_borda(tema["primaria"], 2),
            border_radius=_raio(24),
            shadow=_sombra("#55000000", 24, 8),
            alignment=ft.Alignment.CENTER,
            margin=ft.Margin.symmetric(vertical=18),
        )

    def _alterar_quantidade(self, evento: ft.ControlEvent) -> None:
        self.quantidade_jogadores = int(evento.control.value)
        self.estado.definir_quantidade(self.quantidade_jogadores)
        for indice, campo in enumerate(self.campos_nomes):
            campo.visible = indice < self.quantidade_jogadores
        self.page.update()

    def _iniciar_jogo(self, _evento: ft.ControlEvent) -> None:
        nomes = [
            (campo.value or "").strip()
            for campo in self.campos_nomes[: self.quantidade_jogadores]
        ]
        if any(not nome for nome in nomes):
            self._avisar("Digite o nome de todos os jogadores.")
            return
        if len({nome.casefold() for nome in nomes}) != len(nomes):
            self._avisar("Use nomes diferentes para identificar os jogadores.")
            return

        self.estado.definir_quantidade(self.quantidade_jogadores)
        for indice, nome in enumerate(nomes):
            self.estado.definir_nome(indice, nome)
        self._preparar_nova_partida()
        self._renderizar()

    # ------------------------------------------------------------------
    # Elementos compartilhados durante as rodadas
    # ------------------------------------------------------------------

    def _placar(self) -> ft.Control:
        tema = self.tema
        cartoes = []
        for indice, jogador in enumerate(self.jogadores):
            ativo = indice == self.indice_jogador and self.tela_atual != "resultado"
            saldo = float(jogador["saldo"])
            cor_saldo = tema["positivo"] if saldo >= 0 else tema["negativo"]
            imagem = str(jogador.get("imagem", ""))
            avatar: ft.Control
            if imagem:
                avatar = ft.Image(
                    src=imagem,
                    width=28,
                    height=28,
                    fit=ft.BoxFit.COVER,
                    border_radius=_raio(14),
                    error_content=ft.Icon(
                        ft.Icons.PERSON,
                        size=18,
                        color=tema["suave"],
                    ),
                )
            else:
                avatar = ft.Icon(
                    ft.Icons.PERSON,
                    size=18,
                    color=tema["destaque"] if ativo else tema["suave"],
                )
            cartoes.append(
                ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Row(
                                controls=[
                                    avatar,
                                    ft.Text(
                                        jogador["nome"],
                                        color=tema["texto"],
                                        size=13,
                                        weight=ft.FontWeight.BOLD,
                                    ),
                                ],
                                spacing=6,
                            ),
                            rj.texto_saldo(
                                self,
                                jogador,
                                formatar_reais,
                                cor_positiva=tema["positivo"],
                                cor_negativa=tema["negativo"],
                                tamanho=20,
                            ),
                        ],
                        spacing=4,
                    ),
                    padding=12,
                    bgcolor=tema["cartao_2"],
                    border=_borda(
                        tema["destaque"] if ativo else tema["primaria"],
                        2 if ativo else 1,
                    ),
                    border_radius=_raio(14),
                    col={"xs": 6, "sm": 3},
                )
            )
        return ft.ResponsiveRow(
            controls=cartoes,
            columns=12,
            spacing=10,
            run_spacing=10,
        )

    def _progresso(self) -> ft.Control:
        tema = self.tema
        total = len(self.questoes)
        atual = min(self.indice_questao + 1, total)
        return ft.Column(
            controls=[
                ft.Row(
                    controls=[
                        ft.Text(
                            f"RODADA {atual} DE {total}",
                            color=tema["primaria"],
                            size=12,
                            weight=ft.FontWeight.BOLD,
                        ),
                        ft.Text(
                            f"VEZ DE {self.jogador_atual['nome'].upper()}",
                            color=tema["destaque"],
                            size=12,
                            weight=ft.FontWeight.BOLD,
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    wrap=True,
                ),
                ft.ProgressBar(
                    value=atual / total,
                    bar_height=8,
                    color=tema["destaque"],
                    bgcolor=tema["cartao_2"],
                    border_radius=4,
                ),
            ],
            spacing=7,
        )

    # ------------------------------------------------------------------
    # Cronômetro regressivo e narração da questão
    # ------------------------------------------------------------------

    def _sincronizar_recursos_da_rodada(self) -> None:
        """Inicia ou encerra timer e narração conforme a tela atual."""
        telas_com_tempo = {"jogada", "pergunta"}
        telas_com_narracao = {"jogada", "pergunta", "estudo"}

        if self.tela_atual in telas_com_tempo and self.questoes:
            identificador = str(self.questao_atual["id"])
            if identificador != self._questao_cronometro:
                self._iniciar_cronometro(identificador)
        else:
            self._parar_cronometro()

        if self.tela_atual in telas_com_narracao and self.questoes:
            chave_narracao = self._chave_da_narracao()
            if (
                self.narracao_ativa
                and chave_narracao != self._ultima_questao_narrada
            ):
                # A chave muda conforme a tela: "questao", "alternativas" ou
                # "resolucao". Assim, ao abrir as respostas, a voz reinicia e
                # lê o enunciado com todas as alternativas; ao entrar em
                # "Estudar", passa a ler somente a explicação correspondente.
                self._narrar_questao()
        else:
            self._parar_narracao()

    def _iniciar_cronometro(self, identificador: str) -> None:
        """Cria um novo ciclo de 60 segundos para a questão atual."""
        self._parar_cronometro()
        self._questao_cronometro = identificador
        self.tempo_restante = TEMPO_POR_QUESTAO
        self._cronometro_rodando = True
        self._rodada_finalizada = False
        if ADMIN_ATIVO:
            # Modo administrador: o cronômetro fica desligado.
            self._cronometro_rodando = False
            return
        token = self._token_cronometro
        self.page.run_task(self._executar_cronometro, token)

    def _parar_cronometro(self) -> None:
        """Invalida com segurança qualquer tarefa anterior do cronômetro."""
        self._token_cronometro += 1
        self._cronometro_rodando = False

    async def _executar_cronometro(self, token: int) -> None:
        """Atualiza a contagem sem bloquear cliques ou a interface do Flet."""
        while (
            self._cronometro_rodando
            and token == self._token_cronometro
            and self.tempo_restante > 0
        ):
            await asyncio.sleep(1)
            if (
                not self._cronometro_rodando
                or token != self._token_cronometro
                or self._rodada_finalizada
            ):
                return
            self.tempo_restante -= 1
            self._atualizar_cronometro_visual()

        if (
            token == self._token_cronometro
            and self.tempo_restante <= 0
            and not self._rodada_finalizada
        ):
            self._tempo_esgotado()

    def _atualizar_cronometro_visual(self) -> None:
        """Atualiza somente os controles do timer, evitando redesenhar a tela."""
        cor = (
            self.tema["negativo"]
            if self.tempo_restante <= 10
            else self.tema["destaque"]
        )
        try:
            if self.texto_cronometro is not None:
                self.texto_cronometro.value = f"{self.tempo_restante:02d}s"
                self.texto_cronometro.color = cor
                rj.pulsar_cronometro(self)
                self.texto_cronometro.update()
            if self.barra_cronometro is not None:
                self.barra_cronometro.value = (
                    self.tempo_restante / TEMPO_POR_QUESTAO
                )
                self.barra_cronometro.color = cor
                self.barra_cronometro.semantics_value = self.tempo_restante
                self.barra_cronometro.update()
            if self.icone_cronometro is not None:
                self.icone_cronometro.color = cor
                self.icone_cronometro.update()
        except RuntimeError:
            # O controle pode estar sendo substituído exatamente neste instante.
            pass

    def _tempo_esgotado(self) -> None:
        """Registra automaticamente um erro quando a contagem chega a zero."""
        if self._rodada_finalizada or self.tela_atual not in {
            "jogada",
            "pergunta",
        }:
            return
        self._rodada_finalizada = True
        self._cronometro_rodando = False
        self.estado.registrar_resultado(
            str(self.jogador_atual["id"]),
            "erro",
        )
        rj.registrar_resposta(
            self,
            MODULO_PESQUISA,
            "tempo_esgotado",
            tempo_total=TEMPO_POR_QUESTAO,
        )
        rj.efeitos(self).tocar(self, "erro")
        self.ultimo_resultado = {
            "acertou": False,
            "resposta": None,
            "variacao": -PENALIDADE_ERRO,
            "tempo_esgotado": True,
        }
        self.tela_atual = "feedback"
        self._renderizar()

    def _controle_cronometro(self) -> ft.Control:
        """Monta o indicador visual de tempo exibido ao lado da questão."""
        tema = self.tema
        cor = (
            tema["negativo"]
            if self.tempo_restante <= 10
            else tema["destaque"]
        )
        self.icone_cronometro = ft.Icon(
            ft.Icons.TIMER_OUTLINED,
            color=cor,
            size=24,
        )
        self.texto_cronometro = ft.Text(
            f"{self.tempo_restante:02d}s",
            color=cor,
            size=24,
            weight=ft.FontWeight.BOLD,
            semantics_label=(
                f"{self.tempo_restante} segundos restantes para responder"
            ),
        )
        self.barra_cronometro = ft.ProgressBar(
            value=self.tempo_restante / TEMPO_POR_QUESTAO,
            bar_height=9,
            color=cor,
            bgcolor=tema["fundo_1"],
            border_radius=5,
            semantics_label="Tempo restante da questão",
            semantics_value=self.tempo_restante,
        )
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            self.icone_cronometro,
                            ft.Text(
                                "TEMPO",
                                color=tema["suave"],
                                size=12,
                                weight=ft.FontWeight.BOLD,
                                expand=True,
                            ),
                            self.texto_cronometro,
                        ],
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    self.barra_cronometro,
                    ft.Text(
                        "Nos últimos 10 segundos o indicador ficará vermelho.",
                        color=tema["suave"],
                        size=9,
                        text_align=ft.TextAlign.CENTER,
                    ),
                ],
                spacing=6,
            ),
            padding=10,
            bgcolor=tema["cartao_2"],
            border=_borda(cor, 1.5),
            border_radius=_raio(14),
        )

    def _texto_da_narracao(self) -> str:
        """Retorna somente o texto correspondente à tela que está visível."""
        questao = self.questao_atual
        if self.tela_atual == "estudo":
            estudo = questao["estudo"]
            resposta_correta = questao["alternativas"][questao["correta"]]
            # ALVO DA LEITURA NA TELA ESTUDAR: mantenha este bloco separado
            # do enunciado. Assim a voz lê exclusivamente a explicação e a
            # resolução que o jogador está visualizando no painel de estudo.
            return (
                f"Momento de estudo. {estudo['titulo']}. "
                f"Explicação. {estudo['texto']}. "
                f"Fórmula. {estudo['formula']}. "
                f"Exemplo de aplicação. {estudo['exemplo']}. "
                "Resolução passo a passo. "
                f"Primeiro, escolha a estratégia. {estudo['texto']}. "
                f"Segundo, organize a fórmula. {estudo['formula']}. "
                f"Terceiro, substitua os valores e calcule. "
                f"{questao['explicacao']}. "
                f"Resultado. A alternativa correta é {resposta_correta}."
            )

        texto_questao = (
            f"Questão de porcentagem. {questao['titulo']}. "
            f"{questao['enunciado']}"
        )

        if self.tela_atual == "pergunta":
            # NARRAÇÃO DAS ALTERNATIVAS: este bloco é executado quando os
            # botões A, B, C e D estão visíveis. Para mudar o modo de leitura,
            # altere os textos "Alternativa" e "Escolha uma alternativa".
            # Não remova o enumerate, pois ele relaciona cada opção à sua letra.
            letras = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
            texto_alternativas = " ".join(
                f"Alternativa {letras[indice]}. {alternativa}."
                for indice, alternativa in enumerate(questao["alternativas"])
            )
            return (
                f"{texto_questao}. "
                f"{texto_alternativas} "
                "Escolha uma alternativa."
            )

        # Na primeira tela da rodada, antes de o jogador escolher Responder,
        # são lidos somente o título e o enunciado.
        return texto_questao

    def _chave_da_narracao(self) -> str:
        """Diferencia enunciado, alternativas e resolução na leitura."""
        if self.tela_atual == "estudo":
            alvo = "resolucao"
        elif self.tela_atual == "pergunta":
            alvo = "alternativas"
        else:
            alvo = "questao"
        return f"{self.questao_atual['id']}:{alvo}"

    def _parar_narracao(self) -> None:
        """Interrompe a voz atual sem mudar a preferência do jogador."""
        processo = self._processo_narracao
        self._processo_narracao = None
        if processo is None or processo.poll() is not None:
            return
        try:
            processo.terminate()
        except OSError:
            pass

    def _narrar_questao(self, forcar: bool = False) -> bool:
        """Usa a voz nativa do sistema operacional, sem serviço de internet."""
        if not self.questoes:
            return False
        identificador = self._chave_da_narracao()
        if not forcar and identificador == self._ultima_questao_narrada:
            return True

        texto = texto_para_narracao(self._texto_da_narracao())
        taxa = self.velocidade_narracao
        self._parar_narracao()
        comando: list[str] | None = None
        opcoes: dict[str, Any] = {}

        if sys.platform.startswith("win"):
            executavel = shutil.which("powershell") or shutil.which("pwsh")
            if executavel:
                texto_base64 = base64.b64encode(
                    texto.encode("utf-8")
                ).decode("ascii")
                # A voz do Windows aceita valores inteiros de -10 a 10.
                # Esta conversão aproxima 0,75x, 1x, 1,5x e 2x da interface.
                taxa_windows = max(-10, min(10, round((taxa - 1.0) * 6)))
                script = (
                    "$texto=[System.Text.Encoding]::UTF8.GetString("
                    "[System.Convert]::FromBase64String('"
                    f"{texto_base64}'));"
                    "Add-Type -AssemblyName System.Speech;"
                    "$voz=New-Object "
                    "System.Speech.Synthesis.SpeechSynthesizer;"
                    f"$voz.Rate={taxa_windows};$voz.Volume=100;"
                    "$voz.Speak($texto);$voz.Dispose()"
                )
                comando = [
                    executavel,
                    "-NoProfile",
                    "-NonInteractive",
                    "-Command",
                    script,
                ]
                opcoes["creationflags"] = getattr(
                    subprocess,
                    "CREATE_NO_WINDOW",
                    0,
                )
        elif sys.platform == "darwin":
            executavel = shutil.which("say")
            if executavel:
                # O comando "say" recebe a velocidade em palavras por minuto.
                palavras_por_minuto = round(180 * taxa)
                comando = [
                    executavel,
                    "-r",
                    str(palavras_por_minuto),
                    texto,
                ]
        else:
            executavel = (
                shutil.which("spd-say")
                or shutil.which("espeak-ng")
                or shutil.which("espeak")
            )
            if executavel:
                nome_executavel = Path(executavel).name.lower()
                if nome_executavel == "spd-say":
                    # spd-say usa uma escala de -100 a 100.
                    taxa_spd = max(-100, min(100, round((taxa - 1.0) * 100)))
                    comando = [executavel, "-r", str(taxa_spd), texto]
                else:
                    # eSpeak usa palavras por minuto.
                    palavras_por_minuto = round(175 * taxa)
                    comando = [
                        executavel,
                        "-s",
                        str(palavras_por_minuto),
                        texto,
                    ]

        if comando is None:
            return False
        try:
            self._processo_narracao = subprocess.Popen(
                comando,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                **opcoes,
            )
        except OSError:
            self._processo_narracao = None
            return False

        self._ultima_questao_narrada = identificador
        return True

    def _alterar_velocidade_narracao(
        self,
        evento: ft.ControlEvent,
    ) -> None:
        """Aplica a velocidade escolhida e reinicia a fala que estiver ativa."""
        try:
            velocidade = float(evento.control.value)
        except (TypeError, ValueError):
            return
        if velocidade not in VELOCIDADES_NARRACAO:
            return
        self.velocidade_narracao = velocidade
        self._ultima_questao_narrada = None
        if self.narracao_ativa and not self._narrar_questao(forcar=True):
            self.narracao_ativa = False
            self._avisar(
                "A narração nativa não está disponível neste sistema."
            )

    def _alternar_narracao(self, _evento: ft.ControlEvent) -> None:
        """Liga ou desliga a leitura, sempre por escolha do usuário."""
        self.narracao_ativa = not self.narracao_ativa
        if self.narracao_ativa:
            if not self._narrar_questao(forcar=True):
                self.narracao_ativa = False
                self._avisar(
                    "A narração nativa não está disponível neste sistema."
                )
        else:
            self._parar_narracao()
        self._renderizar()

    def _botao_narracao(self) -> ft.Control:
        tema = self.tema
        if self.tela_atual == "estudo":
            alvo = "RESOLUÇÃO"
        elif self.tela_atual == "pergunta":
            alvo = "ALTERNATIVAS"
        else:
            alvo = "QUESTÃO"
        return ft.Button(
            content=(
                "DESATIVAR ÁUDIO"
                if self.narracao_ativa
                else f"OUVIR {alvo}"
            ),
            icon=(
                ft.Icons.VOLUME_OFF
                if self.narracao_ativa
                else ft.Icons.RECORD_VOICE_OVER
            ),
            color=tema["fundo_1"],
            bgcolor=(
                tema["negativo"]
                if self.narracao_ativa
                else tema["primaria"]
            ),
            height=42,
            on_click=self._alternar_narracao,
            tooltip=(
                "A leitura em voz alta só funciona quando você ativá-la."
            ),
        )

    def _controles_narracao(self) -> ft.Control:
        """Agrupa o botão de voz e o seletor visual de velocidade."""
        tema = self.tema
        seletor_velocidade = ft.Dropdown(
            value=str(self.velocidade_narracao),
            options=[
                ft.DropdownOption(key=str(valor), text=rotulo)
                for valor, rotulo in VELOCIDADES_NARRACAO.items()
            ],
            label="Velocidade da voz",
            leading_icon=ft.Icons.SPEED,
            bgcolor=tema["cartao_2"],
            color=tema["texto"],
            border_color=tema["primaria"],
            focused_border_color=tema["destaque"],
            border_radius=12,
            dense=True,
            on_select=self._alterar_velocidade_narracao,
            tooltip=(
                "Escolha 0,75x, 1,0x, 1,5x ou 2,0x. "
                "A mudança reinicia a leitura atual."
            ),
        )
        return ft.Column(
            controls=[
                self._botao_narracao(),
                seletor_velocidade,
            ],
            # AJUSTE DO CONTROLE DE ÁUDIO: diminua este valor para aproximar
            # botão e seletor; aumente para criar mais espaço entre eles.
            spacing=6,
            horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
        )

    def _imagem_mascote(self, altura: float = 150) -> ft.Control:
        """Espaço reservado para trocar somente o arquivo do mascote."""
        tema = self.tema
        return ft.Container(
            content=ft.Image(
                src=CAMINHO_MASCOTE,
                height=altura,
                fit=ft.BoxFit.CONTAIN,
                semantics_label="Mascote financeiro do jogo",
                error_content=ft.Column(
                    controls=[
                        ft.Icon(
                            ft.Icons.ADD_PHOTO_ALTERNATE_OUTLINED,
                            color=tema["destaque"],
                            size=48,
                        ),
                        ft.Text(
                            "ESPAÇO PARA O MASCOTE FINANCEIRO",
                            color=tema["suave"],
                            size=11,
                            weight=ft.FontWeight.BOLD,
                            text_align=ft.TextAlign.CENTER,
                        ),
                    ],
                    spacing=8,
                    alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                ),
            ),
            height=altura + 18,
            alignment=ft.Alignment.CENTER,
            bgcolor=tema["fundo_1"],
            border=_borda(tema["primaria"], 1.5),
            border_radius=_raio(16),
            padding=8,
        )

    def _painel_interacao(self) -> ft.Control:
        """Preenche a lateral com mascote, timer e acessibilidade."""
        tema = self.tema
        return ft.Container(
            content=ft.Column(
                controls=[
                    self._imagem_mascote(105),
                    # ALTURA DO MASCOTE NESTA TELA: altere 105 para aumentar
                    # ou diminuir a imagem. Valores maiores ocupam mais altura.
                    ft.Text(
                        "MASCOTE FINANCEIRO",
                        color=tema["primaria"],
                        size=13,
                        weight=ft.FontWeight.BOLD,
                        text_align=ft.TextAlign.CENTER,
                    ),
                    self._controle_cronometro(),
                    self._controles_narracao(),
                    ft.Text(
                        "A narração é opcional e pode ser interrompida a qualquer momento.",
                        color=tema["suave"],
                        size=10,
                        text_align=ft.TextAlign.CENTER,
                    ),
                ],
                # ESPAÇO VERTICAL DO PAINEL: diminua para aproximar mascote,
                # timer, áudio e texto; aumente para afastá-los.
                spacing=7,
                horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
            ),
            # TAMANHO INTERNO DO PAINEL: diminua para deixá-lo mais compacto.
            padding=10,
            bgcolor=tema["cartao"],
            border=_borda(tema["primaria"], 2),
            border_radius=_raio(18),
            col={"xs": 12, "lg": 3},
        )

    def _area_questao(self, mostrar_alternativas: bool) -> ft.Control:
        """Organiza a questão e o novo painel lateral na mesma faixa."""
        return ft.ResponsiveRow(
            controls=[
                ft.Container(
                    content=self._cartao_questao(mostrar_alternativas),
                    col={"xs": 12, "lg": 9},
                ),
                self._painel_interacao(),
            ],
            columns=12,
            spacing=14,
            run_spacing=14,
            vertical_alignment=ft.CrossAxisAlignment.START,
        )

    def _cartao_questao(self, mostrar_alternativas: bool) -> ft.Control:
        tema = self.tema
        questao = self.questao_atual
        imagem = ft.Container(
            content=ft.Image(
                src=questao["imagem"],
                fit=ft.BoxFit.CONTAIN,
                # CONTAIN mostra a imagem inteira dentro do retângulo, sem cortes.
                border_radius=_raio(12),
                semantics_label=f"Imagem ilustrativa de {questao['produto']}",
                error_content=ft.Icon(
                    ft.Icons.BROKEN_IMAGE,
                    color=tema["negativo"],
                    size=60,
                ),
            ),
            height=270,
            # ALTURA DO CARTÃO DA IMAGEM: altere 270 para aumentar ou
            # diminuir a altura da questão. Um valor menor sobe os botões
            # "Responder" e "Estudar" na tela.
            padding=8,
            alignment=ft.Alignment.CENTER,
            bgcolor=tema["fundo_1"],
            border=_borda(tema["primaria"], 2),
            border_radius=_raio(18),
            clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
            col={"xs": 12, "md": 5},
        )

        conteudo = [
            ft.Text(
                questao["titulo"].upper(),
                color=tema["destaque"],
                size=13,
                weight=ft.FontWeight.BOLD,
            ),
            ft.Text(
                questao["produto"],
                color=tema["primaria"],
                size=18,
                weight=ft.FontWeight.BOLD,
            ),
            markdown_matematico(
                questao["enunciado"],
                cor=tema["texto"],
                tamanho=20,
                peso=ft.FontWeight.W_600,
            ),
        ]

        if mostrar_alternativas:
            botoes = []
            letras = "ABCD"
            for indice, alternativa in enumerate(questao["alternativas"]):
                destaque = rj.cores_alternativa(self, indice, tema) or (
                    tema["cartao_2"], tema["primaria"], 1.5
                )
                botoes.append(
                    ft.OutlinedButton(
                        content=markdown_matematico(
                            f"**{letras[indice]}.** {alternativa}",
                            cor=tema["texto"],
                            # FONTE DAS ALTERNATIVAS: tamanho padronizado para
                            # leitura confortável em todos os módulos.
                            tamanho=16,
                            escala_latex=1.0,
                        ),
                        style=ft.ButtonStyle(
                            color=tema["texto"],
                            side=_lado(destaque[1], destaque[2]),
                            bgcolor=destaque[0],
                        ),
                        height=60,
                        on_click=lambda evento, resposta=indice: self._responder(
                            resposta,
                            evento,
                        ),
                        col={"xs": 12, "sm": 6},
                    )
                )
            conteudo.append(
                ft.ResponsiveRow(
                    controls=botoes,
                    columns=12,
                    spacing=10,
                    run_spacing=10,
                )
            )

        texto = ft.Container(
            content=ft.Column(
                controls=conteudo,
                spacing=12,
                alignment=ft.MainAxisAlignment.CENTER,
            ),
            padding=ft.Padding.all(18),
            bgcolor=tema["cartao"],
            border=_borda(tema["primaria"], 2),
            border_radius=_raio(18),
            col={"xs": 12, "md": 7},
        )
        return ft.ResponsiveRow(
            controls=[imagem, texto],
            columns=12,
            spacing=14,
            run_spacing=14,
            # ResponsiveRow usa quebra automática de linha. O alinhamento
            # STRETCH não é suportado nesse modo pelo Flutter e fazia todo o
            # cartão desaparecer após o cadastro dos jogadores. START mantém
            # a imagem e o enunciado visíveis no computador e no celular.
            vertical_alignment=ft.CrossAxisAlignment.START,
        )

    # ------------------------------------------------------------------
    # Jogada, resposta, estudo e feedback
    # ------------------------------------------------------------------

    def _tela_jogada(self) -> ft.Control:
        tema = self.tema
        return ft.Column(
            controls=[
                self._placar(),
                self._progresso(),
                self._area_questao(mostrar_alternativas=False),
                ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Text(
                                f"{self.jogador_atual['nome']}, qual é sua escolha?",
                                color=tema["texto"],
                                size=18,
                                weight=ft.FontWeight.BOLD,
                                text_align=ft.TextAlign.CENTER,
                            ),
                            ft.ResponsiveRow(
                                controls=[
                                    ft.Button(
                                        content="RESPONDER",
                                        icon=ft.Icons.PSYCHOLOGY,
                                        color=tema["fundo_1"],
                                        bgcolor=tema["destaque"],
                                        height=46,
                                        # ALTURA DO BOTÃO RESPONDER: altere
                                        # 46 para aumentar ou diminuir.
                                        on_click=self._escolher_responder,
                                        col={"xs": 12, "sm": 6},
                                    ),
                                    ft.Button(
                                        content="ESTUDAR",
                                        icon=ft.Icons.MENU_BOOK,
                                        color=tema["fundo_1"],
                                        bgcolor=tema["primaria"],
                                        height=46,
                                        # ALTURA DO BOTÃO ESTUDAR: altere
                                        # 46 para aumentar ou diminuir.
                                        on_click=self._escolher_estudar,
                                        col={"xs": 12, "sm": 6},
                                    ),
                                ],
                                columns=12,
                                spacing=10,
                                run_spacing=8,
                            ),
                            ft.Text(
                                (
                                    "Acertou: +R$ 100,00  •  Errou: −R$ 200,00  "
                                    "•  Estudou: +R$ 50,00\n"
                                    + rj.ATALHOS_TEXTO
                                ),
                                color=tema["suave"],
                                size=12,
                                text_align=ft.TextAlign.CENTER,
                            ),
                        ],
                        # ESPAÇO ENTRE TÍTULO, BOTÕES E REGRA FINANCEIRA:
                        # diminua para reduzir a altura do último container.
                        spacing=7,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    padding=ft.Padding.symmetric(
                        horizontal=14,
                        # AJUSTE DO TAMANHO DO ÚLTIMO CONTAINER: diminua
                        # "vertical" para reduzir sua altura; aumente para
                        # deixar mais espaço interno acima e abaixo.
                        vertical=9,
                    ),
                    margin=ft.Margin.symmetric(
                        # AJUSTE DA LARGURA: aumente "horizontal" para deixar
                        # o container mais estreito; diminua para alargá-lo.
                        horizontal=36,
                        vertical=0,
                    ),
                    offset=ft.Offset(0, -0.035),
                    # AJUSTE DE POSIÇÃO: o 1º valor move na horizontal
                    # (negativo=esquerda; positivo=direita). O 2º move na
                    # vertical (negativo=para cima; positivo=para baixo).
                    # Ex.: ft.Offset(0, -0.06) sobe mais o container.
                    bgcolor=tema["cartao"],
                    border=_borda(tema["destaque"], 1.5),
                    border_radius=_raio(18),
                ),
            ],
            # ESPAÇO ENTRE PLACAR, PROGRESSO, QUESTÃO E ESCOLHA: diminua para
            # subir "Responder/Estudar"; aumente para separar mais os blocos.
            spacing=8,
        )

    def _escolher_responder(self, _evento: ft.ControlEvent) -> None:
        if self._rodada_finalizada:
            return
        self.tela_atual = "pergunta"
        self._renderizar()

    def _escolher_estudar(self, _evento: ft.ControlEvent) -> None:
        if self._rodada_finalizada:
            return
        self._rodada_finalizada = True
        self.estado.registrar_resultado(
            str(self.jogador_atual["id"]),
            "estudo",
        )
        rj.registrar_resposta(
            self,
            MODULO_PESQUISA,
            "estudo",
            tempo_total=TEMPO_POR_QUESTAO,
        )
        self.tela_atual = "estudo"
        self._renderizar()

    def _tela_pergunta(self) -> ft.Control:
        return ft.Column(
            controls=[
                self._placar(),
                self._progresso(),
                self._area_questao(mostrar_alternativas=True),
            ],
            spacing=14,
        )

    def _responder(
        self,
        indice_resposta: int,
        _evento: ft.ControlEvent,
    ) -> None:
        if self._rodada_finalizada:
            return
        self._rodada_finalizada = True
        questao = self.questao_atual
        acertou = indice_resposta == int(questao["correta"])
        if acertou:
            self.estado.registrar_resultado(
                str(self.jogador_atual["id"]),
                "acerto",
            )
            variacao = PREMIO_ACERTO
        else:
            self.estado.registrar_resultado(
                str(self.jogador_atual["id"]),
                "erro",
            )
            variacao = -PENALIDADE_ERRO

        self.ultimo_resultado = {
            "acertou": acertou,
            "resposta": indice_resposta,
            "variacao": variacao,
            "tempo_esgotado": False,
        }
        rj.registrar_resposta(
            self,
            MODULO_PESQUISA,
            "acerto" if acertou else "erro",
            escolhida=indice_resposta,
            tempo_total=TEMPO_POR_QUESTAO,
        )
        self._parar_cronometro()
        # DESTAQUE: a alternativa escolhida fica verde/vermelha por alguns
        # instantes (recursos_jogo.ESPERA_DESTAQUE) antes da resolução.
        indice_questao = self.indice_questao

        def abrir_resolucao() -> None:
            if self.tela_atual == "pergunta" and self.indice_questao == indice_questao:
                self.tela_atual = "feedback"
                self._renderizar()
        rj.iniciar_destaque(self, indice_resposta, int(questao["correta"]), abrir_resolucao)
        self._renderizar()

    def _cartao_exemplo_estudo(
        self,
        titulo: str,
        texto: str,
    ) -> ft.Control:
        tema = self.tema
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text(
                        titulo,
                        color=tema["primaria"],
                        size=11,
                        weight=ft.FontWeight.BOLD,
                    ),
                    markdown_matematico(
                        texto,
                        cor=tema["texto"],
                        tamanho=13,
                    ),
                ],
                spacing=4,
            ),
            padding=12,
            bgcolor=tema["cartao_2"],
            border=_borda(tema["primaria"]),
            border_radius=_raio(12),
        )

    def _passo_resolucao(
        self,
        numero: int,
        titulo: str,
        texto: str,
    ) -> ft.Control:
        tema = self.tema
        return ft.Row(
            controls=[
                ft.Container(
                    content=ft.Text(
                        str(numero),
                        color=tema["fundo_1"],
                        size=13,
                        weight=ft.FontWeight.BOLD,
                    ),
                    width=30,
                    height=30,
                    alignment=ft.Alignment.CENTER,
                    bgcolor=tema["destaque"],
                    border_radius=_raio(15),
                ),
                ft.Column(
                    controls=[
                        ft.Text(
                            titulo,
                            color=tema["primaria"],
                            size=12,
                            weight=ft.FontWeight.BOLD,
                        ),
                        markdown_matematico(
                            texto,
                            cor=tema["texto"],
                            tamanho=13,
                            expandir=True,
                        ),
                    ],
                    spacing=2,
                    expand=True,
                ),
            ],
            spacing=10,
            vertical_alignment=ft.CrossAxisAlignment.START,
        )

    def _painel_estudo_detalhado(self) -> ft.Control:
        """Ocupa a lateral com exemplos e a resolução da questão atual."""
        tema = self.tema
        questao = self.questao_atual
        estudo = questao["estudo"]
        resposta_correta = questao["alternativas"][questao["correta"]]
        return ft.Container(
            content=ft.Column(
                controls=[
                    self._imagem_mascote(125),
                    self._controles_narracao(),
                    ft.Divider(height=1, color=tema["primaria"]),
                    ft.Text(
                        "EXEMPLOS EXTRAS DE PORCENTAGEM",
                        color=tema["destaque"],
                        size=15,
                        weight=ft.FontWeight.BOLD,
                        text_align=ft.TextAlign.CENTER,
                    ),
                    self._cartao_exemplo_estudo(
                        "EXEMPLO RELACIONADO",
                        estudo["exemplo"],
                    ),
                    self._cartao_exemplo_estudo(
                        "COMPRAS NO SUPERMERCADO",
                        (
                            r"Um produto de R\$ 80,00 com 25% de desconto "
                            r"fica por R\$ 60,00, pois $80\cdot0{,}75=60$."
                        ),
                    ),
                    self._cartao_exemplo_estudo(
                        "REAJUSTE NO ORÇAMENTO",
                        (
                            r"Uma despesa de R\$ 150,00 com aumento de 12% "
                            r"passa para R\$ 168,00, pois $150\cdot1{,}12=168$."
                        ),
                    ),
                    ft.Divider(height=1, color=tema["primaria"]),
                    ft.Text(
                        "RESOLUÇÃO PASSO A PASSO",
                        color=tema["destaque"],
                        size=15,
                        weight=ft.FontWeight.BOLD,
                        text_align=ft.TextAlign.CENTER,
                    ),
                    self._passo_resolucao(
                        1,
                        "IDENTIFIQUE O OBJETIVO",
                        questao["enunciado"],
                    ),
                    self._passo_resolucao(
                        2,
                        "ESCOLHA A ESTRATÉGIA",
                        estudo["texto"],
                    ),
                    self._passo_resolucao(
                        3,
                        "ORGANIZE A FÓRMULA",
                        estudo["formula"],
                    ),
                    self._passo_resolucao(
                        4,
                        "SUBSTITUA E CALCULE",
                        questao["explicacao"],
                    ),
                    self._passo_resolucao(
                        5,
                        "CONFIRA O RESULTADO",
                        f"A alternativa correta é {resposta_correta}.",
                    ),
                ],
                spacing=12,
                horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
            ),
            padding=18,
            bgcolor=tema["cartao"],
            border=_borda(tema["destaque"], 2),
            border_radius=_raio(20),
            shadow=_sombra("#55000000", 22, 7),
            col={"xs": 12, "lg": 5},
        )

    def _tela_estudo(self) -> ft.Control:
        tema = self.tema
        estudo = self.questao_atual["estudo"]
        fonte = self.questao_atual["fonte"]
        painel_conceito = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Icon(
                        ft.Icons.AUTO_STORIES,
                        color=tema["destaque"],
                        size=58,
                    ),
                    ft.Text(
                        "MOMENTO DE ESTUDO",
                        color=tema["destaque"],
                        size=28,
                        weight=ft.FontWeight.BOLD,
                        text_align=ft.TextAlign.CENTER,
                    ),
                    ft.Text(
                        estudo["titulo"],
                        color=tema["primaria"],
                        size=22,
                        weight=ft.FontWeight.BOLD,
                        text_align=ft.TextAlign.CENTER,
                    ),
                    markdown_matematico(
                        estudo["texto"],
                        cor=tema["texto"],
                        tamanho=17,
                    ),
                    ft.Container(
                        content=markdown_matematico(
                            estudo["formula"],
                            cor=tema["fundo_1"],
                            tamanho=18,
                            peso=ft.FontWeight.BOLD,
                            alinhamento=ft.MainAxisAlignment.CENTER,
                            escala_latex=1.18,
                        ),
                        padding=16,
                        bgcolor=tema["destaque"],
                        border_radius=_raio(14),
                    ),
                    ft.Text(
                        (
                            f"Preço de referência consultado em "
                            f"{fonte['loja']} em {fonte['consulta']}."
                        ),
                        color=tema["suave"],
                        size=11,
                        text_align=ft.TextAlign.CENTER,
                    ),
                    ft.Container(
                        content=ft.Text(
                            (
                                f"{self.jogador_atual['nome']} recebeu "
                                f"{formatar_reais(PREMIO_ESTUDO)} por estudar. "
                                "A próxima vez será de outro jogador."
                            ),
                            color=tema["positivo"],
                            size=14,
                            weight=ft.FontWeight.BOLD,
                            text_align=ft.TextAlign.CENTER,
                        ),
                        padding=14,
                        bgcolor=tema["cartao_2"],
                        border=_borda(tema["positivo"]),
                        border_radius=_raio(13),
                    ),
                    ft.Button(
                        content="CONCLUIR ESTUDO E PASSAR A VEZ",
                        icon=ft.Icons.SWAP_HORIZ,
                        color=tema["fundo_1"],
                        bgcolor=tema["destaque"],
                        height=52,
                        on_click=self._proxima_rodada,
                    ),
                ],
                spacing=16,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=ft.Padding.all(26),
            bgcolor=tema["cartao"],
            border=_borda(tema["primaria"], 2),
            border_radius=_raio(22),
            shadow=_sombra("#55000000", 22, 7),
            col={"xs": 12, "lg": 7},
        )
        return ft.Column(
            controls=[
                self._placar(),
                self._progresso(),
                ft.ResponsiveRow(
                    controls=[
                        painel_conceito,
                        self._painel_estudo_detalhado(),
                    ],
                    columns=12,
                    spacing=14,
                    run_spacing=14,
                    vertical_alignment=ft.CrossAxisAlignment.START,
                ),
            ],
            spacing=14,
        )

    def _tela_feedback(self) -> ft.Control:
        tema = self.tema
        if self.ultimo_resultado is None:
            self.tela_atual = "jogada"
            return self._tela_jogada()

        acertou = bool(self.ultimo_resultado["acertou"])
        tempo_esgotado = bool(
            self.ultimo_resultado.get("tempo_esgotado", False)
        )
        cor = tema["positivo"] if acertou else tema["negativo"]
        if tempo_esgotado:
            icone = ft.Icons.TIMER_OFF
            titulo = "TEMPO ESGOTADO!"
        else:
            icone = (
                ft.Icons.EMOJI_EVENTS
                if acertou
                else ft.Icons.HEART_BROKEN
            )
            titulo = (
                "RESPOSTA CORRETA!"
                if acertou
                else "RESPOSTA INCORRETA"
            )
        valor = "+ R$ 100,00" if acertou else "− R$ 200,00"
        resposta_correta = self.questao_atual["alternativas"][
            self.questao_atual["correta"]
        ]

        return ft.Column(
            controls=[
                self._placar(),
                self._progresso(),
                *(
                    [faixa]
                    if (faixa := rj.faixa_sequencia(self, tema))
                    else []
                ),
                ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Icon(icone, color=cor, size=72),
                            ft.Text(
                                titulo,
                                color=cor,
                                size=30,
                                weight=ft.FontWeight.BOLD,
                                text_align=ft.TextAlign.CENTER,
                            ),
                            ft.Text(
                                (
                                    "A questão foi registrada automaticamente "
                                    "como erro."
                                    if tempo_esgotado
                                    else (
                                        "Confira abaixo a resolução desta "
                                        "situação-problema."
                                    )
                                ),
                                color=tema["suave"],
                                size=13,
                                text_align=ft.TextAlign.CENTER,
                            ),
                            ft.Text(
                                valor,
                                color=cor,
                                size=34,
                                weight=ft.FontWeight.BOLD,
                            ),
                            markdown_matematico(
                                f"**Resposta correta:** {resposta_correta}",
                                cor=tema["destaque"],
                                tamanho=17,
                                peso=ft.FontWeight.BOLD,
                                alinhamento=ft.MainAxisAlignment.CENTER,
                            ),
                            ft.Container(
                                content=markdown_matematico(
                                    self.questao_atual["explicacao"],
                                    cor=tema["texto"],
                                    tamanho=17,
                                ),
                                padding=18,
                                bgcolor=tema["cartao_2"],
                                border=_borda(tema["primaria"]),
                                border_radius=_raio(16),
                            ),
                            ft.Text(
                                (
                                    f"Saldo de {self.jogador_atual['nome']}: "
                                    f"{formatar_reais(self.jogador_atual['saldo'])}"
                                ),
                                color=tema["texto"],
                                size=20,
                                weight=ft.FontWeight.BOLD,
                            ),
                            ft.Text(
                                (
                                    "A vez será alternada mesmo após uma "
                                    "resposta correta."
                                ),
                                color=tema["suave"],
                                size=13,
                                text_align=ft.TextAlign.CENTER,
                            ),
                            ft.Button(
                                content="PASSAR A VEZ",
                                icon=ft.Icons.SWAP_HORIZ,
                                color=tema["fundo_1"],
                                bgcolor=tema["destaque"],
                                height=52,
                                on_click=self._proxima_rodada,
                            ),
                        ],
                        spacing=15,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    width=860,
                    padding=ft.Padding.all(28),
                    bgcolor=tema["cartao"],
                    border=_borda(cor, 2),
                    border_radius=_raio(24),
                    shadow=_sombra("#55000000", 24, 8),
                    alignment=ft.Alignment.CENTER,
                ),
            ],
            spacing=14,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )

    def _proxima_rodada(self, _evento: ft.ControlEvent) -> None:
        self.indice_questao += 1
        if self.indice_questao >= len(self.questoes):
            self.tela_atual = "resultado"
            self._renderizar()
            return

        self.indice_jogador = (self.indice_jogador + 1) % len(self.jogadores)
        self.ultimo_resultado = None
        self.tela_atual = "jogada"
        self._renderizar()

    # ------------------------------------------------------------------
    # Resultado
    # ------------------------------------------------------------------

    def _tela_resultado(self) -> ft.Control:
        tema = self.tema
        classificacao = sorted(
            self.jogadores,
            key=lambda item: (
                item["saldo"],
                item["acertos"],
                -item["erros"],
            ),
            reverse=True,
        )
        melhor_saldo = classificacao[0]["saldo"]
        vencedores = [
            jogador["nome"]
            for jogador in classificacao
            if jogador["saldo"] == melhor_saldo
        ]
        if len(vencedores) == 1:
            mensagem = f"{vencedores[0]} venceu o desafio!"
        else:
            mensagem = "Empate entre " + " e ".join(vencedores) + "!"

        linhas = []
        for posicao, jogador in enumerate(classificacao, start=1):
            saldo = float(jogador["saldo"])
            linhas.append(
                ft.Container(
                    content=ft.ResponsiveRow(
                        controls=[
                            ft.Text(
                                f"{posicao}º",
                                color=tema["destaque"],
                                size=24,
                                weight=ft.FontWeight.BOLD,
                                col={"xs": 2, "sm": 1},
                            ),
                            ft.Text(
                                jogador["nome"],
                                color=tema["texto"],
                                size=18,
                                weight=ft.FontWeight.BOLD,
                                col={"xs": 10, "sm": 3},
                            ),
                            ft.Text(
                                formatar_reais(saldo),
                                color=(
                                    tema["positivo"]
                                    if saldo >= 0
                                    else tema["negativo"]
                                ),
                                size=18,
                                weight=ft.FontWeight.BOLD,
                                col={"xs": 6, "sm": 3},
                            ),
                            ft.Text(
                                (
                                    f"✓ {jogador['acertos']}  "
                                    f"✗ {jogador['erros']}  "
                                    f"📖 {jogador['estudos']}"
                                ),
                                color=tema["suave"],
                                size=13,
                                col={"xs": 6, "sm": 5},
                            ),
                        ],
                        columns=12,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    padding=14,
                    bgcolor=tema["cartao_2"],
                    border=_borda(
                        tema["destaque"] if posicao == 1 else tema["primaria"],
                        2 if posicao == 1 else 1,
                    ),
                    border_radius=_raio(14),
                )
            )

        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Icon(
                        ft.Icons.EMOJI_EVENTS,
                        color=tema["destaque"],
                        size=82,
                    ),
                    ft.Text(
                        "FIM DO JOGO",
                        color=tema["destaque"],
                        size=36,
                        weight=ft.FontWeight.BOLD,
                        text_align=ft.TextAlign.CENTER,
                    ),
                    ft.Text(
                        mensagem,
                        color=tema["texto"],
                        size=22,
                        weight=ft.FontWeight.BOLD,
                        text_align=ft.TextAlign.CENTER,
                    ),
                    ft.Text(
                        (
                            "✓ acertos  •  ✗ erros  •  📖 escolhas de estudo"
                        ),
                        color=tema["suave"],
                        size=12,
                    ),
                    rj.podio(self, self.jogadores, tema, formatar_reais),
                    *linhas,
                    ft.ResponsiveRow(
                        controls=[
                            ft.Button(
                                content="JOGAR NOVAMENTE",
                                icon=ft.Icons.REFRESH,
                                color=tema["fundo_1"],
                                bgcolor=tema["destaque"],
                                height=50,
                                on_click=self._jogar_novamente,
                                col={"xs": 12, "sm": 6},
                            ),
                            ft.OutlinedButton(
                                content="VOLTAR À TELA INICIAL",
                                icon=ft.Icons.HOME,
                                style=ft.ButtonStyle(
                                    color=tema["texto"],
                                    side=_lado(tema["primaria"], 1.5),
                                ),
                                height=50,
                                on_click=self._voltar_ao_inicio,
                                col={"xs": 12, "sm": 6},
                            ),
                        ],
                        columns=12,
                        spacing=12,
                        run_spacing=12,
                    ),
                ],
                spacing=14,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            width=900,
            padding=ft.Padding.all(28),
            bgcolor=tema["cartao"],
            border=_borda(tema["destaque"], 2),
            border_radius=_raio(24),
            shadow=_sombra("#55000000", 24, 8),
            alignment=ft.Alignment.CENTER,
            margin=ft.Margin.symmetric(vertical=16),
        )

    def _jogar_novamente(self, _evento: ft.ControlEvent) -> None:
        self._preparar_nova_partida()
        self._renderizar()

    def _voltar_cadastro(self, _evento: ft.ControlEvent) -> None:
        """Mantido para testes isolados; na integração o cadastro é inicial."""
        self._parar_cronometro()
        self._parar_narracao()
        self.tela_atual = "cadastro"
        self.questoes = []
        self.ultimo_resultado = None
        self._questao_cronometro = None
        self._renderizar()

    # ------------------------------------------------------------------
    # Tema, som, navegação e erros
    # ------------------------------------------------------------------

    def _trocar_tema(self, evento: ft.ControlEvent) -> None:
        nome = str(evento.control.value)
        if nome in TEMAS:
            self.tema_nome = nome
            self.estado.definir_tema(nome)
            self._renderizar()

    def _trilha_atual(self) -> tuple[str, Path]:
        relativo = self.trilhas[self.trilha_nome]
        return relativo, ASSETS_DIR / relativo

    async def _iniciar_audio_atual(self) -> None:
        relativo, caminho = self._trilha_atual()
        if not caminho.exists():
            raise FileNotFoundError(f"Arquivo de áudio não encontrado: {caminho}")
        if winsound is not None and caminho.suffix.lower() == ".wav":
            winsound.PlaySound(
                str(caminho),
                winsound.SND_FILENAME
                | winsound.SND_ASYNC
                | winsound.SND_LOOP
                | winsound.SND_NODEFAULT,
            )
        else:
            self.audio.src = relativo
            self.audio.update()
            await self.audio.play()
        self.som_ativo = True

    async def _parar_audio_atual(self) -> None:
        _relativo, caminho = self._trilha_atual()
        if winsound is not None and caminho.suffix.lower() == ".wav":
            winsound.PlaySound(None, 0)
        else:
            await self.audio.pause()
        self.som_ativo = False

    async def _trocar_trilha(self, evento: ft.ControlEvent) -> None:
        nome = str(evento.control.value)
        if nome not in self.trilhas:
            return
        estava_ativa = self.som_ativo
        try:
            if estava_ativa:
                await self._parar_audio_atual()
            self.trilha_nome = nome
            self.estado.definir_trilha(nome)
            self.audio.src = self.trilhas[nome]
            self.audio.update()
            if estava_ativa:
                await self._iniciar_audio_atual()
        except Exception as erro:
            print(f"Erro ao trocar a trilha: {erro}")
            self.som_ativo = False
            self._avisar("Não foi possível trocar a trilha.")
        self._renderizar()

    async def _alternar_som(self, _evento: ft.ControlEvent) -> None:
        try:
            if self.som_ativo:
                await self._parar_audio_atual()
            else:
                await self._iniciar_audio_atual()
        except Exception as erro:
            print(f"Erro ao controlar o áudio: {erro}")
            self.som_ativo = False
            self._avisar("Não foi possível iniciar o som.")
        self._renderizar()

    async def _voltar_ao_inicio(self, _evento: ft.ControlEvent) -> None:
        self._parar_cronometro()
        self._parar_narracao()
        try:
            if self.som_ativo:
                await self._parar_audio_atual()
        except Exception:
            pass
        self.som_ativo = False
        self.estado.salvar()
        retorno = self.ao_voltar()
        if hasattr(retorno, "__await__"):
            await retorno

    def _avisar(self, texto: str) -> None:
        aviso = ft.SnackBar(
            content=ft.Text(
                texto,
                color="#FFFFFF",
                weight=ft.FontWeight.BOLD,
            ),
            bgcolor="#9A2844",
            show_close_icon=True,
            duration=3200,
            margin=ft.Margin.all(18),
        )
        self.page.show_dialog(aviso)

    def _tela_erro(self) -> ft.Control:
        tema = self.tema
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Icon(
                        ft.Icons.ERROR_OUTLINE,
                        color=tema["negativo"],
                        size=70,
                    ),
                    ft.Text(
                        "NÃO FOI POSSÍVEL CARREGAR O JOGO",
                        color=tema["negativo"],
                        size=24,
                        weight=ft.FontWeight.BOLD,
                        text_align=ft.TextAlign.CENTER,
                    ),
                    ft.Text(
                        (
                            "Confira o arquivo dados/questoes_porcentagem.json "
                            "e as imagens da pasta assets/imagens/produtos."
                        ),
                        color=tema["texto"],
                        text_align=ft.TextAlign.CENTER,
                    ),
                ],
                spacing=14,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=30,
            bgcolor=tema["cartao"],
            border=_borda(tema["negativo"], 2),
            border_radius=_raio(22),
        )


def criar_tela_porcentagem(
    page: ft.Page,
    ao_voltar: Callable[..., Any],
    estado: EstadoJogo | None = None,
) -> ft.Control:
    """Fábrica exigida pelo arquivo principal."""
    try:
        jogo = JogoPorcentagem(page, ao_voltar, estado)
        return jogo.raiz
    except Exception as erro:
        print(f"Erro ao criar o jogo de porcentagem: {erro}")
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Icon(
                        ft.Icons.ERROR_OUTLINE,
                        color="#FF6E86",
                        size=72,
                    ),
                    ft.Text(
                        "ERRO AO CARREGAR O JOGO DE PORCENTAGEM",
                        color="#FF6E86",
                        size=24,
                        weight=ft.FontWeight.BOLD,
                        text_align=ft.TextAlign.CENTER,
                    ),
                    ft.Text(
                        str(erro),
                        color="#FFFFFF",
                        text_align=ft.TextAlign.CENTER,
                    ),
                    ft.Button(
                        content="VOLTAR",
                        icon=ft.Icons.ARROW_BACK,
                        on_click=lambda _evento: ao_voltar(),
                    ),
                ],
                spacing=14,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            expand=True,
            alignment=ft.Alignment.CENTER,
            bgcolor="#06143C",
            padding=30,
        )


def main(page: ft.Page) -> None:
    """Permite testar este módulo sem abrir o menu principal."""
    page.title = "Responda ou Estuda - Porcentagem"
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 0
    page.window.width = 1280
    page.window.height = 820
    page.window.min_width = 360
    page.window.min_height = 640

    host = ft.Container(expand=True)
    estado = EstadoJogo()

    def reiniciar() -> None:
        host.content = criar_tela_porcentagem(page, reiniciar, estado)
        host.update()

    host.content = criar_tela_porcentagem(page, reiniciar, estado)
    page.add(host)


if __name__ == "__main__":
    ft.run(
        main,
        name="responde_ou_estuda_porcentagem",
        assets_dir=str(ASSETS_DIR),
    )
