"""Ponto de entrada da VERSÃO ONLINE (site) do Responda ou Estuda.

``flet build web`` procura este arquivo. No site, o Python roda dentro do
navegador do aluno (sys.platform == "emscripten"); no computador, este arquivo
apenas repassa para ``responda_ou_estuda.iniciar()``, o mesmo usado pelo
INICIAR_JOGO.bat.
"""

from __future__ import annotations

import sys

import flet as ft

from responda_ou_estuda import PASTA_ASSETS, iniciar, main


def rodando_no_navegador() -> bool:
    """True no jogo publicado como site."""
    return sys.platform == "emscripten"


# No site este arquivo pode ser carregado como módulo, e não como programa
# principal; por isso o jogo também inicia quando está no navegador.
if rodando_no_navegador():
    ft.run(main, assets_dir=str(PASTA_ASSETS))
elif __name__ == "__main__":
    iniciar()
