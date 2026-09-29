"""Monta as telas matemáticas dos quatro módulos com Flet 0.86.3.

O teste não abre navegador nem inicia cronômetros. Ele verifica se todas as 100
questões conseguem construir enunciado, alternativas, painel Estudar e feedback
com componentes ``ft.Markdown``. Também monta cada página teórica de Juros,
PRICE e SAC, incluindo a fórmula da prestação com fração LaTeX empilhada.
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path
from typing import Any, Iterable

import flet as ft


BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import estado_jogo as modulo_estado  # noqa: E402
from estado_jogo import EstadoJogo  # noqa: E402
from formatacao_matematica import texto_para_narracao  # noqa: E402
from nivel_1_porcentagem import JogoPorcentagem  # noqa: E402
from nivel_2_juros import JogoJuros, PAGINAS_TEORIA as TEORIA_JUROS  # noqa: E402
from nivel_3_price import JogoPrice, PAGINAS_TEORIA as TEORIA_PRICE  # noqa: E402
from nivel_4_sac import JogoSac, PAGINAS_TEORIA as TEORIA_SAC  # noqa: E402


class PaginaDeTeste:
    """Superfície mínima usada pelos módulos durante a montagem dos controles."""

    def __init__(self) -> None:
        self.services: list[Any] = []

    def run_task(self, *_args: Any, **_kwargs: Any) -> None:
        """Ignora tarefas assíncronas para não iniciar o cronômetro no teste."""

    def show_dialog(self, *_args: Any, **_kwargs: Any) -> None:
        """Ignora avisos, que não fazem parte da validação estrutural."""


def _valores_aninhados(valor: Any) -> Iterable[Any]:
    if isinstance(valor, dict):
        yield from valor.values()
    elif isinstance(valor, (list, tuple, set)):
        yield from valor


def _markdowns(controle: ft.Control) -> list[ft.Markdown]:
    """Localiza Markdown em uma árvore Flet sem depender de APIs internas."""

    encontrados: list[ft.Markdown] = []
    pendentes: list[Any] = [controle]
    visitados: set[int] = set()
    while pendentes:
        atual = pendentes.pop()
        identidade = id(atual)
        if identidade in visitados:
            continue
        visitados.add(identidade)
        if isinstance(atual, ft.Markdown):
            encontrados.append(atual)
        if isinstance(atual, ft.Control):
            for valor in vars(atual).values():
                if isinstance(valor, ft.Control):
                    pendentes.append(valor)
                else:
                    pendentes.extend(_valores_aninhados(valor))
    return encontrados


def _testar_questoes(
    nome: str,
    classe: type[JogoPorcentagem | JogoJuros | JogoPrice | JogoSac],
    estado: EstadoJogo,
) -> tuple[int, int]:
    jogo = classe(PaginaDeTeste(), lambda *_args: None, estado)
    jogo._parar_cronometro()
    jogo.jogadores = estado.jogadores_ativos()
    questoes = list(jogo.questoes_originais)
    markdowns_montados = 0

    for questao in questoes:
        jogo.questoes = [questao]
        jogo.indice_questao = 0
        jogo.indice_jogador = 0
        jogo.tela_atual = "pergunta"
        cartao = jogo._cartao_questao(mostrar_alternativas=True)
        quantidade_cartao = len(_markdowns(cartao))
        minimo_cartao = 1 + len(questao["alternativas"])
        if quantidade_cartao < minimo_cartao:
            raise AssertionError(
                f"{questao['id']}: questão não usa Markdown em todo o conteúdo."
            )

        jogo.tela_atual = "estudo"
        painel = jogo._painel_estudo_detalhado()
        quantidade_painel = len(_markdowns(painel))
        if quantidade_painel < 5:
            raise AssertionError(
                f"{questao['id']}: painel Estudar incompleto em Markdown."
            )

        jogo.ultimo_resultado = {"acertou": True, "tempo_esgotado": False}
        feedback = jogo._tela_feedback()
        quantidade_feedback = len(_markdowns(feedback))
        if quantidade_feedback < 2:
            raise AssertionError(
                f"{questao['id']}: feedback matemático incompleto em Markdown."
            )

        for tela_narrada in ("pergunta", "estudo"):
            jogo.tela_atual = tela_narrada
            fala = texto_para_narracao(jogo._texto_da_narracao())
            if not fala or "\\frac" in fala or "$" in fala or "\\" in fala:
                raise AssertionError(
                    f"{questao['id']}: narração contém marcação matemática."
                )
        markdowns_montados += (
            quantidade_cartao + quantidade_painel + quantidade_feedback
        )

    jogo._parar_cronometro()
    print(
        f"- {nome}: {len(questoes)} questões e "
        f"{markdowns_montados} componentes Markdown montados"
    )
    return len(questoes), markdowns_montados


def _testar_teoria(
    nome: str,
    classe: type[JogoJuros | JogoPrice | JogoSac],
    paginas: list[dict[str, Any]],
    estado: EstadoJogo,
) -> int:
    jogo = classe(PaginaDeTeste(), lambda *_args: None, estado)
    total = 0
    for indice in range(len(paginas)):
        jogo.etapa_teoria = indice
        jogo.tela_atual = "teoria"
        controle = jogo._tela_teoria()
        quantidade = len(_markdowns(controle))
        if quantidade < 4:
            raise AssertionError(
                f"{nome}, teoria {indice + 1}: conteúdo Markdown incompleto."
            )
        total += quantidade
    print(
        f"- Teoria {nome}: {len(paginas)} páginas e "
        f"{total} componentes Markdown montados"
    )
    return total


def main() -> int:
    # EstadoJogo atualiza o ranking ao ser criado. O teste redireciona os dois
    # arquivos persistentes para uma pasta temporária, preservando os dados reais.
    with tempfile.TemporaryDirectory(prefix="responda_teste_") as pasta:
        temporaria = Path(pasta)
        caminho_estado = temporaria / "estado_jogo.json"
        caminho_estado.write_bytes(
            (BASE_DIR / "dados" / "estado_jogo.json").read_bytes()
        )
        modulo_estado.ARQUIVO_RANKING = temporaria / "ranking.xlsx"
        estado = EstadoJogo(caminho_estado)
        if not estado.nomes_validos()[0]:
            raise AssertionError(
                "O estado de teste precisa ter jogadores válidos."
            )

        totais = [
            _testar_questoes("Porcentagem", JogoPorcentagem, estado),
            _testar_questoes("Juros", JogoJuros, estado),
            _testar_questoes("PRICE", JogoPrice, estado),
            _testar_questoes("SAC", JogoSac, estado),
        ]
        _testar_teoria("Juros", JogoJuros, TEORIA_JUROS, estado)
        total_teoria_price = _testar_teoria(
            "PRICE", JogoPrice, TEORIA_PRICE, estado
        )
        total_teoria_price += _testar_teoria("SAC", JogoSac, TEORIA_SAC, estado)

    formulas_price = " ".join(str(pagina.get("formula", "")) for pagina in TEORIA_PRICE)
    formula_exigida = r"\frac{i\cdot(1+i)^n}{(1+i)^n-1}"
    if formula_exigida not in formulas_price:
        raise AssertionError("A fórmula formal de PMT não está na teoria PRICE.")

    total_questoes = sum(item[0] for item in totais)
    total_markdowns = sum(item[1] for item in totais) + total_teoria_price
    print(
        f"TESTE DE TELAS APROVADO: {total_questoes} questões; "
        f"mais de {total_markdowns} componentes Markdown validados."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
