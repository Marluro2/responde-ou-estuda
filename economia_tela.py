"""Telas do MODO ECONOMIA (usadas pela tela inicial e pelos quatro módulos).

    linha_economia(jogo, jogador, tema)  -> "Carteira | Cofrinho" + botão do cofrinho
    abrir_cofrinho(jogo, jogador, tema)  -> janela para aplicar e resgatar
    iniciar_relogio(page, estado, ...)   -> 1 minuto de jogo aberto = 1 "mês"

``tema`` é um dicionário com as cores: texto, primaria, destaque, positivo,
negativo, cartao, cartao_2, fundo_1 e suave (o mesmo formato dos módulos).
As regras e as contas ficam em economia.py.
"""

from __future__ import annotations

import asyncio
import time
from typing import Any, Callable

import flet as ft

import economia as eco


def reais(valor: float) -> str:
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


# ----------------------------------------------------------- textos ao vivo
# Cada texto de carteira/cofrinho na tela fica registrado aqui; o relógio os
# atualiza a cada "mês" sem redesenhar a tela inteira.
_VIVOS: list[tuple[ft.Text, dict[str, Any], str, dict[str, str]]] = []


def _valor(jogador: dict[str, Any], tipo: str) -> float:
    return eco.carteira(jogador) if tipo == "carteira" else float(jogador.get("cofrinho", 0.0))


def _cor(valor: float, tema: dict[str, str], tipo: str) -> str:
    if tipo == "cofrinho":
        return tema["destaque"]
    return tema["positivo"] if valor >= 0 else tema["negativo"]


# Janelas do cofrinho abertas: são redesenhadas a cada "mês".
_JANELAS_ABERTAS: list[Callable[[], None]] = []


def atualizar_textos(_tema: dict[str, str] | None = None) -> None:
    for redesenhar in list(_JANELAS_ABERTAS):
        try:
            redesenhar()
        except Exception:
            _JANELAS_ABERTAS.remove(redesenhar)
    vivos = []
    for texto, jogador, tipo, tema in _VIVOS:
        valor = _valor(jogador, tipo)
        texto.value = reais(valor)
        texto.color = _cor(valor, tema, tipo)
        try:
            texto.update()
            vivos.append((texto, jogador, tipo, tema))
        except Exception:
            pass  # controle que já saiu da tela
    _VIVOS[:] = vivos[-80:]


def _texto_vivo(jogador: dict[str, Any], tipo: str, tema: dict[str, str], tamanho: float) -> ft.Text:
    valor = _valor(jogador, tipo)
    texto = ft.Text(reais(valor), color=_cor(valor, tema, tipo), size=tamanho, weight=ft.FontWeight.BOLD)
    _VIVOS.append((texto, jogador, tipo, tema))
    return texto


def linha_economia(jogo: Any, jogador: dict[str, Any], tema: dict[str, str], *, tamanho: float = 12) -> list[ft.Control]:
    """Linha "CARTEIRA ... COFRINHO ..." com o botão do cofrinho (vazia se desligado)."""
    if not eco.ativo(jogo.estado):
        return []
    return [
        ft.Row(
            controls=[
                ft.Column(
                    controls=[
                        ft.Text("CARTEIRA", color=tema["suave"], size=max(8, tamanho - 3), weight=ft.FontWeight.BOLD),
                        _texto_vivo(jogador, "carteira", tema, tamanho),
                    ],
                    spacing=0,
                ),
                ft.Column(
                    controls=[
                        ft.Text("COFRINHO", color=tema["suave"], size=max(8, tamanho - 3), weight=ft.FontWeight.BOLD),
                        _texto_vivo(jogador, "cofrinho", tema, tamanho),
                    ],
                    spacing=0,
                ),
                ft.IconButton(
                    icon=ft.Icons.SAVINGS,
                    icon_color=tema["destaque"],
                    icon_size=tamanho + 10,
                    tooltip="Cofrinho: aplicar ou resgatar (rende 1% por minuto de jogo)",
                    on_click=lambda _e: abrir_cofrinho(jogo, jogador, tema),
                ),
            ],
            spacing=10,
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )
    ]


def aplicar_no_placar(jogo: Any, cartoes: list[ft.Control], jogadores: list[dict[str, Any]], tema: dict[str, str]) -> None:
    """Acrescenta carteira/cofrinho AO LADO do saldo em cada cartão do placar.

    Não aumenta a altura do placar. Com até 2 jogadores os cartões ficam mais
    largos e mostram os valores; com 3 ou 4, aparece só o botão do cofrinho.
    """
    if not eco.ativo(jogo.estado):
        return
    completo = len(cartoes) <= 2
    for cartao, jogador in zip(cartoes, jogadores):
        extras: list[ft.Control] = []
        if completo:
            extras += [
                ft.Column(
                    [ft.Text("CARTEIRA", color=tema["suave"], size=9, weight=ft.FontWeight.BOLD),
                     _texto_vivo(jogador, "carteira", tema, 14)],
                    spacing=0,
                ),
                ft.Column(
                    [ft.Text("COFRINHO", color=tema["suave"], size=9, weight=ft.FontWeight.BOLD),
                     _texto_vivo(jogador, "cofrinho", tema, 14)],
                    spacing=0,
                ),
            ]
        extras.append(
            ft.IconButton(
                icon=ft.Icons.SAVINGS,
                icon_color=tema["destaque"],
                icon_size=24,
                tooltip="Cofrinho: aplicar ou resgatar (rende 1% por minuto de jogo)",
                on_click=lambda _e, j=jogador: abrir_cofrinho(jogo, j, tema),
            )
        )
        cartao.content = ft.Row(
            [ft.Container(content=cartao.content, expand=True), *extras],
            spacing=12,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )
        if completo:
            cartao.col = {"xs": 12, "sm": 6}


# ----------------------------------------------------------- janela do cofrinho
def abrir_cofrinho(jogo: Any, jogador: dict[str, Any], tema: dict[str, str]) -> None:
    estado = jogo.estado
    page = jogo.page
    campo = ft.TextField(
        label="Valor para aplicar (R$)",
        keyboard_type=ft.KeyboardType.NUMBER,
        width=220,
        dense=True,
        border_color=tema["primaria"],
        color=tema["texto"],
        text_size=16,
    )
    mensagem = ft.Text("", size=14, weight=ft.FontWeight.BOLD)
    corpo = ft.Column(spacing=10, tight=True, width=640)

    def cartao(titulo: str, controle: ft.Control) -> ft.Control:
        return ft.Container(
            content=ft.Column([ft.Text(titulo, size=11, color=tema["suave"], weight=ft.FontWeight.BOLD), controle], spacing=2),
            padding=10,
            bgcolor=tema["cartao_2"],
            border=ft.Border.all(1, tema["primaria"]),
            border_radius=ft.BorderRadius.all(12),
            expand=True,
        )

    def montar() -> None:
        valor = float(jogador["cofrinho"])
        rendimento = round(valor - float(jogador["cofrinho_aplicado"]), 2)
        faltam = eco.meses_para_resgate(estado, jogador)
        historico = [float(v) for v in jogador.get("cofrinho_historico", [])]
        if len(historico) > 6:
            historico = historico[:1] + historico[-4:]
            reticencias = True
        else:
            reticencias = False
        faixa: list[ft.Control] = []
        for posicao, termo in enumerate(historico):
            if posicao:
                faixa.append(ft.Text("→", color=tema["destaque"], size=14, weight=ft.FontWeight.BOLD))
            if reticencias and posicao == 1:
                faixa.extend([ft.Text("…", color=tema["texto"], size=14), ft.Text("→", color=tema["destaque"], size=14)])
            faixa.append(
                ft.Container(
                    content=ft.Text(f"{termo:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
                                    color=tema["texto"], size=13, weight=ft.FontWeight.BOLD),
                    padding=ft.Padding.symmetric(horizontal=8, vertical=4),
                    bgcolor=tema["fundo_1"],
                    border=ft.Border.all(1, tema["primaria"]),
                    border_radius=ft.BorderRadius.all(9),
                )
            )
        corpo.controls = [
            ft.Row(
                [
                    cartao("CARTEIRA (DISPONÍVEL)", _texto_vivo(jogador, "carteira", tema, 20)),
                    cartao("NO COFRINHO", _texto_vivo(jogador, "cofrinho", tema, 20)),
                    cartao("RENDIMENTO", ft.Text(reais(rendimento), size=20, weight=ft.FontWeight.BOLD, color=tema["positivo"])),
                ],
                spacing=8,
            ),
            ft.Text(
                "Rende 1% a cada minuto de jogo aberto (1 minuto = 1 mês), em juros compostos: "
                "M = C · 1,01ᵗ. Os valores mês a mês formam uma PG de razão 1,01.",
                size=14, color=tema["texto"],
            ),
            *(
                [ft.Row(faixa, spacing=5, wrap=True, alignment=ft.MainAxisAlignment.CENTER)]
                if historico else []
            ),
            ft.Text(
                ("Resgate liberado." if valor > 0 and not faltam
                 else f"Resgate liberado em {faltam} min (carência de {eco.CARENCIA_MESES} min após a última aplicação)."
                 if valor > 0 else "Cofrinho vazio: aplique um valor da carteira."),
                size=13,
                color=tema["positivo"] if (valor > 0 and not faltam) else tema["suave"],
            ),
            ft.Row(
                [
                    campo,
                    *[
                        ft.OutlinedButton(content=f"R$ {v}", on_click=lambda _e, v=v: (setattr(campo, "value", str(v)), campo.update()))
                        for v in (50, 100, 200)
                    ],
                ],
                spacing=8,
                wrap=True,
            ),
            ft.Row(
                [
                    ft.Button(content="APLICAR", icon=ft.Icons.SAVINGS, bgcolor=tema["destaque"], color=tema["fundo_1"],
                              on_click=aplicar, height=44),
                    ft.OutlinedButton(content="RESGATAR TUDO", icon=ft.Icons.PAYMENTS, on_click=resgatar, height=44,
                                      disabled=valor <= 0 or bool(faltam)),
                ],
                spacing=10,
            ),
            mensagem,
        ]

    def mostrar(ok: bool, texto: str) -> None:
        mensagem.value = texto
        mensagem.color = tema["positivo"] if ok else tema["negativo"]
        atualizar_textos(tema)

    def aplicar(_e: Any) -> None:
        try:
            valor = float(str(campo.value or "0").replace("R$", "").replace(".", "").replace(",", ".").strip())
        except ValueError:
            mostrar(False, "Digite um número, por exemplo 100 ou 50,00.")
            return
        ok, texto = eco.aplicar(estado, jogador, valor)
        if ok:
            campo.value = ""
        mostrar(ok, texto)

    def resgatar(_e: Any) -> None:
        mostrar(*eco.resgatar(estado, jogador))

    def redesenhar() -> None:
        montar()
        corpo.update()

    _JANELAS_ABERTAS.append(redesenhar)
    jogo._janela_cofrinho = redesenhar
    montar()
    page.show_dialog(
        ft.AlertDialog(
            modal=True,
            title=ft.Row([ft.Icon(ft.Icons.SAVINGS, color=tema["destaque"]),
                          ft.Text(f"Cofrinho de {jogador.get('nome', '')}")], spacing=10),
            content=corpo,
            actions=[ft.TextButton(content="FECHAR", on_click=lambda _e: _fechar(jogo))],
        )
    )


def _fechar(jogo: Any) -> None:
    redesenhar = getattr(jogo, "_janela_cofrinho", None)
    if redesenhar in _JANELAS_ABERTAS:
        _JANELAS_ABERTAS.remove(redesenhar)
    jogo.page.pop_dialog()
    atualizar_textos()
    ao_fechar = getattr(jogo, "_ao_fechar_cofrinho", None)
    if callable(ao_fechar):
        ao_fechar()


# ----------------------------------------------------------- relógio da economia
# Um relógio por janela (página); uma nova conexão ganha o seu próprio.
_PAGINAS_COM_RELOGIO: set[int] = set()


def iniciar_relogio(page: ft.Page, obter_estado: Callable[[], Any], ao_passar_mes: Callable[[list[str]], None] | None = None) -> None:
    """Conta o tempo de jogo aberto; a cada SEGUNDOS_POR_MES chama passar_mes().

    Chamado uma vez pela tela inicial. Só conta com o Modo economia ligado e
    enquanto o programa está aberto.
    """
    if id(page) in _PAGINAS_COM_RELOGIO:
        return
    _PAGINAS_COM_RELOGIO.add(id(page))

    # Sem conexão, o relógio pausa (o jogo não está aberto); com a janela
    # fechada, ele termina. Isso evita dois relógios cobrando em dobro.
    situacao = {"conectado": True, "fechado": False}

    def encadear(nome: str, acao: Callable[[], None]) -> None:
        anterior = getattr(page, nome, None)

        def manipulador(evento: Any = None) -> Any:
            acao()
            if callable(anterior):
                return anterior(evento)
            return None

        setattr(page, nome, manipulador)

    encadear("on_disconnect", lambda: situacao.update(conectado=False))
    encadear("on_connect", lambda: situacao.update(conectado=True))
    encadear("on_close", lambda: situacao.update(fechado=True, conectado=False))

    async def laco() -> None:
        acumulado = 0.0
        anterior = time.monotonic()
        while not situacao["fechado"]:
            await asyncio.sleep(1)
            agora = time.monotonic()
            passo = min(5.0, agora - anterior)  # ignora pausas longas (suspensão)
            anterior = agora
            if not situacao["conectado"]:
                continue
            estado = obter_estado()
            if estado is None or not eco.ativo(estado):
                continue
            acumulado += passo
            if acumulado >= eco.SEGUNDOS_POR_MES:
                acumulado -= eco.SEGUNDOS_POR_MES
                try:
                    avisos = eco.passar_mes(estado)
                    atualizar_textos()
                    if ao_passar_mes:
                        ao_passar_mes(avisos)
                except Exception as erro:
                    print(f"Economia: erro ao passar o mês: {erro}")
        _PAGINAS_COM_RELOGIO.discard(id(page))

    page.run_task(laco)
