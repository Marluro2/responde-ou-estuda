"""Ponto de entrada da VERSÃO ONLINE (site) do Responde ou Estuda.

``flet build web`` procura este arquivo. No site, o Python roda dentro do
navegador do aluno (sys.platform == "emscripten"); no computador, este arquivo
apenas repassa para ``responda_ou_estuda.iniciar()``, o mesmo usado pelo
INICIAR_JOGO.bat.
"""

from __future__ import annotations

import sys

import flet as ft

from estado_jogo import ARQUIVO_ESTADO, EstadoJogo
from responda_ou_estuda import PASTA_ASSETS, iniciar, main

# Chave do estado do jogo (jogadores, saldos, preferências) no navegador.
CHAVE_NAVEGADOR = "responde_ou_estuda.estado"


def rodando_no_navegador() -> bool:
    """True no jogo publicado como site."""
    return sys.platform == "emscripten"


async def main_site(page: ft.Page) -> None:
    """No site, o arquivo de estado existe só na memória da página.

    Antes de abrir o jogo, restaura o estado guardado no navegador do aluno
    (localStorage); depois, a cada salvamento, envia a nova versão para lá.
    Nada sai do computador do aluno.
    """
    preferencias = ft.SharedPreferences()
    try:
        salvo = await preferencias.get(CHAVE_NAVEGADOR)
    except Exception:
        salvo = None
    if isinstance(salvo, str) and salvo.strip():
        try:
            ARQUIVO_ESTADO.parent.mkdir(parents=True, exist_ok=True)
            ARQUIVO_ESTADO.write_text(salvo, encoding="utf-8")
        except OSError:
            pass
    EstadoJogo.ao_salvar = lambda texto: page.run_task(
        preferencias.set, CHAVE_NAVEGADOR, texto
    )
    main(page)


# No site este arquivo pode ser carregado como módulo, e não como programa
# principal; por isso o jogo também inicia quando está no navegador.
if rodando_no_navegador():
    ft.run(main_site, assets_dir=str(PASTA_ASSETS))
elif __name__ == "__main__":
    iniciar()
