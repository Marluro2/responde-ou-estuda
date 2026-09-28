"""Modo administrador do "Responda ou Estuda".

Serve para o professor conferir questões, imagens, alternativas, gabarito,
telas de estudo e resoluções sem precisar jogar cada rodada.

Como abrir:
    Clique duas vezes em INICIAR_ADMIN.bat.
    (O arquivo define RESPONDA_ADMIN=1 antes de iniciar o jogo.)

O que muda no modo administrador:
    • aparece uma barra amarela "MODO ADMINISTRADOR" nos módulos;
    • é possível escolher qualquer questão, avançar e voltar;
    • botões levam direto à situação, às alternativas, ao estudo ou à
      resolução da questão;
    • o gabarito da questão aparece na barra;
    • o cronômetro fica desligado;
    • as questões aparecem na ordem do banco, sem sorteio;
    • os saldos são gravados em dados/estado_admin.json, e não alteram
      dados/estado_jogo.json nem dados/ranking.xlsx dos jogadores reais.

Os módulos usam este arquivo por meio de:
    ADMIN_ATIVO          -> True quando o jogo foi aberto pelo INICIAR_ADMIN.bat
    criar_estado_admin() -> estado separado usado no modo administrador
    barra_admin(jogo)    -> barra de navegação exibida acima das telas
"""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any
from urllib.parse import urlencode

import flet as ft

from estado_jogo import DADOS_DIR, EstadoJogo
from formatacao_matematica import texto_para_narracao


ADMIN_ATIVO = os.environ.get("RESPONDA_ADMIN", "").strip() == "1"

ARQUIVO_ESTADO_ADMIN = DADOS_DIR / "estado_admin.json"

# Nomes usados automaticamente para que os módulos não parem no cadastro.
NOMES_ADMIN = ("Admin A", "Admin B")

# Ordem dos níveis do módulo PRICE na lista de questões do administrador.
ORDEM_NIVEIS = ("Super fácil", "Fácil", "Médio", "Difícil")

# Telas das rodadas. Nelas a barra mostra os atalhos da questão atual.
TELAS_DA_QUESTAO = {"jogada", "pergunta", "estudo", "feedback"}

LETRAS = "ABCDEFGHIJ"


def criar_estado_admin() -> EstadoJogo:
    """Cria o estado separado do administrador, já com jogadores válidos."""
    estado = EstadoJogo(ARQUIVO_ESTADO_ADMIN, gerar_ranking=False)
    validos, _mensagem = estado.nomes_validos()
    if not validos:
        estado.definir_quantidade(len(NOMES_ADMIN))
        for indice, nome in enumerate(NOMES_ADMIN):
            estado.definir_nome(indice, nome)
    return estado


def lista_admin(jogo: Any) -> list[dict[str, Any]]:
    """Todas as questões do módulo, na ordem do banco (PRICE por nível)."""
    questoes = list(jogo.questoes_originais)
    if any("nivel" in questao for questao in questoes):
        questoes.sort(
            key=lambda questao: (
                ORDEM_NIVEIS.index(questao["nivel"])
                if questao.get("nivel") in ORDEM_NIVEIS
                else len(ORDEM_NIVEIS)
            )
        )
    return questoes


def _posicao_atual(jogo: Any, questoes: list[dict[str, Any]]) -> int:
    """Localiza a questão atual do jogo dentro da lista do administrador."""
    if not jogo.questoes or jogo.indice_questao >= len(jogo.questoes):
        return 0
    identificador = jogo.questoes[jogo.indice_questao].get("id")
    for posicao, questao in enumerate(questoes):
        if questao.get("id") == identificador:
            return posicao
    return 0


def ir_para(jogo: Any, posicao: int, tela: str = "jogada") -> None:
    """Abre diretamente uma questão em uma das telas da rodada."""
    questoes = lista_admin(jogo)
    if not questoes:
        return
    posicao = max(0, min(posicao, len(questoes) - 1))
    questao = questoes[posicao]

    jogo._parar_cronometro()
    jogo._parar_narracao()
    jogo._ultima_questao_narrada = None
    if not jogo.jogadores:
        jogo.jogadores = jogo.estado.jogadores_ativos()

    jogo.questoes = questoes
    jogo.indice_questao = posicao
    jogo._questao_cronometro = None
    jogo._rodada_finalizada = tela in {"estudo", "feedback"}
    jogo.ultimo_resultado = None
    if tela == "feedback":
        # Mostra a resolução como se a alternativa correta tivesse sido
        # escolhida. Nenhum saldo é alterado por este atalho.
        jogo.ultimo_resultado = {
            "acertou": True,
            "resposta": int(questao["correta"]),
            "variacao": 0.0,
            "tempo_esgotado": False,
        }

    # Atributos que existem somente em alguns módulos.
    if hasattr(jogo, "nivel_selecionado") and questao.get("nivel"):
        jogo.nivel_selecionado = questao["nivel"]
    if hasattr(jogo, "pagina_estudo"):
        jogo.pagina_estudo = 0
    if hasattr(jogo, "_estudo_em_andamento"):
        # No PRICE, "Concluir estudo" só passa a vez quando isto é True.
        jogo._estudo_em_andamento = tela == "estudo"
    if hasattr(jogo, "_historico_telas"):
        jogo._historico_telas.clear()

    jogo.tela_atual = tela
    jogo._renderizar()


# ----------------------------------------------------------------------
# TESTE LIBRAS (experimental) - veja TESTE_LIBRAS.txt
# ----------------------------------------------------------------------
PAGINA_TESTE_LIBRAS = "teste_libras/teste_libras.html"


def _texto_para_libras(texto: str) -> str:
    """Converte fórmulas em palavras (como na narração) para o VLibras ler."""
    legivel = texto_para_narracao(str(texto))
    legivel = re.sub(r"\breais\s+(\d[\d.,]*\d|\d)", r"R$ \1", legivel)
    legivel = re.sub(r"(\d),\s+(\d)", r"\1,\2", legivel)
    return re.sub(r"\s+", " ", legivel).strip()


def abrir_teste_libras(jogo: Any, questao: dict[str, Any]) -> None:
    """Abre a página de teste do VLibras com o enunciado e a resolução."""
    parametros = urlencode(
        {
            "id": str(questao.get("id", "")),
            "enunciado": _texto_para_libras(questao.get("enunciado", "")),
            "resolucao": _texto_para_libras(questao.get("explicacao", "")),
        }
    )
    # A página é aberta direto do arquivo (file://), sem depender do servidor
    # do jogo: continua funcionando mesmo depois de fechar a janela do jogo.
    arquivo = Path(__file__).resolve().parent / "assets" / PAGINA_TESTE_LIBRAS
    url = f"{arquivo.as_uri()}#{parametros}"
    # Registro do último envio, útil para conferir o teste.
    try:
        (DADOS_DIR / "teste_libras_ultimo_envio.txt").write_text(
            f"page.url = {getattr(jogo.page, 'url', None)!r}\n"
            f"endereço = {url}\n",
            encoding="utf-8",
        )
    except OSError:
        pass
    # Abre no Edge/Chrome (o mesmo navegador usado pelo jogo), passando o
    # endereço completo como argumento para não perder o texto após o "#".
    try:
        import subprocess

        from iniciar_janela_app import _localizar_navegador

        subprocess.Popen(
            [str(_localizar_navegador()), "--new-window", url],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return
    except Exception:
        pass
    import webbrowser

    webbrowser.open(url, new=1)


def _texto_opcao(numero: int, questao: dict[str, Any]) -> str:
    titulo = str(questao.get("titulo") or questao.get("produto") or "")
    if len(titulo) > 46:
        titulo = titulo[:45] + "…"
    nivel = f"[{questao['nivel']}] " if questao.get("nivel") else ""
    return f"{numero:02d} · {questao.get('id', '')} · {nivel}{titulo}"


def barra_admin(jogo: Any) -> ft.Control:
    """Barra de navegação do administrador exibida acima das telas."""
    tema = jogo.tema
    questoes = lista_admin(jogo)
    total = len(questoes)
    posicao = _posicao_atual(jogo, questoes)
    em_questao = jogo.tela_atual in TELAS_DA_QUESTAO and bool(jogo.questoes)

    def abrir(tela: str):
        return lambda _evento: ir_para(jogo, posicao, tela)

    def ao_escolher(evento: ft.ControlEvent) -> None:
        ir_para(jogo, int(evento.control.value), "jogada")

    seletor = ft.Dropdown(
        value=str(posicao),
        options=[
            ft.DropdownOption(key=str(indice), text=_texto_opcao(indice + 1, q))
            for indice, q in enumerate(questoes)
        ],
        label=f"Questão ({total} no banco)",
        bgcolor=tema["cartao"],
        color=tema["texto"],
        border_color=tema["destaque"],
        focused_border_color=tema["primaria"],
        border_radius=10,
        dense=True,
        text_size=12,
        width=330,
        menu_height=420,
        on_select=ao_escolher,
    )

    def botao_tela(texto: str, icone: str, tela: str) -> ft.Control:
        ativo = em_questao and jogo.tela_atual == tela
        return ft.Button(
            content=texto,
            icon=icone,
            color=tema["fundo_1"] if ativo else tema["texto"],
            bgcolor=tema["destaque"] if ativo else tema["cartao_2"],
            height=32,
            style=ft.ButtonStyle(padding=ft.Padding.symmetric(horizontal=10)),
            on_click=abrir(tela),
        )

    # GABARITO RESUMIDO: uma linha com reticências; o texto completo aparece
    # ao passar o mouse (tooltip).
    gabarito: list[ft.Control] = []
    if em_questao and total:
        questao = questoes[posicao]
        correta = int(questao["correta"])
        letra = LETRAS[correta] if correta < len(LETRAS) else str(correta + 1)
        alternativa = _texto_para_libras(str(questao["alternativas"][correta]))
        gabarito = [
            ft.Container(
                content=ft.Text(
                    f"🔑 {letra}) {alternativa}",
                    color=tema["positivo"],
                    size=12,
                    weight=ft.FontWeight.BOLD,
                    max_lines=1,
                    overflow=ft.TextOverflow.ELLIPSIS,
                ),
                tooltip=f"Gabarito da questão {posicao + 1} de {total}: {letra}) {alternativa}",
                expand=True,
            )
        ]

    # BARRA EM UMA LINHA: ocupa pouco espaço para as telas caberem sem rolar.
    linha = ft.Row(
        controls=[
            ft.Container(
                content=ft.Text(
                    "ADMIN",
                    color=tema["fundo_1"],
                    size=11,
                    weight=ft.FontWeight.BOLD,
                ),
                bgcolor=tema["destaque"],
                padding=ft.Padding.symmetric(horizontal=8, vertical=4),
                border_radius=6,
                tooltip="Modo administrador: cronômetro desligado e saldos de teste",
            ),
            ft.IconButton(
                icon=ft.Icons.CHEVRON_LEFT,
                icon_color=tema["texto"],
                tooltip="Questão anterior",
                disabled=posicao <= 0 and em_questao,
                on_click=lambda _e: ir_para(
                    jogo, posicao - 1 if em_questao else 0
                ),
            ),
            seletor,
            ft.IconButton(
                icon=ft.Icons.CHEVRON_RIGHT,
                icon_color=tema["texto"],
                tooltip="Próxima questão",
                disabled=posicao >= total - 1 and em_questao,
                on_click=lambda _e: ir_para(
                    jogo, posicao + 1 if em_questao else 0
                ),
            ),
            botao_tela("SITUAÇÃO", ft.Icons.IMAGE_OUTLINED, "jogada"),
            botao_tela("ALTERNATIVAS", ft.Icons.RULE, "pergunta"),
            botao_tela("ESTUDO", ft.Icons.MENU_BOOK, "estudo"),
            botao_tela("RESOLUÇÃO", ft.Icons.FACT_CHECK, "feedback"),
            # TESTE LIBRAS: envia a questão atual à página do VLibras.
            ft.IconButton(
                icon=ft.Icons.SIGN_LANGUAGE,
                icon_color=tema["primaria"],
                tooltip="LIBRAS (TESTE): abrir esta questão no VLibras",
                disabled=not total,
                on_click=lambda _e: abrir_teste_libras(
                    jogo, questoes[posicao]
                ),
            ),
            *gabarito,
        ],
        spacing=6,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
    )

    return ft.Container(
        content=linha,
        padding=ft.Padding.symmetric(horizontal=10, vertical=4),
        margin=ft.Margin.symmetric(horizontal=16),
        bgcolor=tema["cartao"],
        border=ft.Border.all(2, tema["destaque"]),
        border_radius=ft.BorderRadius.all(12),
    )
