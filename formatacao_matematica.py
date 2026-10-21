"""Componentes compartilhados para matemática formal no Flet 0.86.3.

Todo conteúdo matemático visível deve chegar a :func:`markdown_matematico`
com delimitadores LaTeX (``$...$`` ou ``$$...$$``). Assim, frações são
renderizadas com ``\\frac`` e nunca como uma divisão textual com barra.
"""

from __future__ import annotations

import re
from typing import Any

import flet as ft


# ----------------------------------------------------------------------
# Delimitadores de fórmulas no Markdown do Flet 0.86.3
# ----------------------------------------------------------------------
# O cliente do Flet só reconhece o FIM de uma fórmula em linha quando o
# delimitador de fechamento é seguido por espaço, pela pontuação abaixo ou
# pelo fim do texto. Em "$C=2.300$; taxa: $i=0{,}018$" o ";" impede o
# fechamento: a fórmula "engole" o texto seguinte e a tela mostra
# "Parser Error: Can't use function '$' in math mode".
_APOS_FORMULA = " \t\n\r\f\v?!.,:？！。，："
# Espaço finíssimo (hair space) inserido depois do "$" quando necessário.
_SEPARADOR_FORMULA = " "

# Mesmos 8 pares de delimitadores configurados no cliente do Flet.
_DELIMITADORES_FLET = (
    ("$$", "$$"),
    ("$", "$"),
    (r"\pu{", "}"),
    (r"\ce{", "}"),
    (r"\(", r"\)"),
    ("( ", " )"),
    (r"\[", r"\]"),
    ("[ ", " ]"),
)
_REGEX_FLET = re.compile(
    "("
    + "|".join(
        re.escape(esq)
        + r"((?:\\.|[^\\\n])*?(?:\\.|[^\\\n]|(?!"
        + re.escape(dir_)
        + r")))"
        + re.escape(dir_)
        for esq, dir_ in _DELIMITADORES_FLET
    )
    + r")(?=[\s?!.,:？！。，：]|$)",
    re.MULTILINE | re.IGNORECASE,
)


# ----------------------------------------------------------------------
# Celular
# ----------------------------------------------------------------------
# O LaTeX não quebra linha: numa tela estreita, uma fórmula larga sai cortada
# na borda do cartão. Enquanto a tela for de celular (recursos_jogo avisa por
# definir_tela_estreita), as fórmulas ficam um pouco menores e cada
# "A \qquad B" de uma fórmula em destaque ($$...$$) vira duas linhas.
ESCALA_LATEX_CELULAR = 0.82
# Cadeias (a = b = c) e somas (a + ⋯ + b) só quebram quando o LaTeX da
# fórmula passa deste número de caracteres; as curtas já cabem no celular.
CARACTERES_SEM_QUEBRA = 40
_tela_estreita = False


def definir_tela_estreita(estreita: bool) -> None:
    global _tela_estreita
    _tela_estreita = bool(estreita)


def _fora_das_chaves(formula: str, alvo: str) -> list[int]:
    """Posições de ``alvo`` fora de chaves (fora de \\frac{...}, expoentes...)."""
    posicoes: list[int] = []
    profundidade, indice = 0, 0
    while indice < len(formula):
        if formula.startswith(alvo, indice) and profundidade == 0:
            posicoes.append(indice)
        caractere = formula[indice]
        if caractere == "\\":
            # Pula o nome do comando (\frac, \cdot...) ou o caractere escapado.
            fim = indice + 1
            while fim < len(formula) and formula[fim].isalpha():
                fim += 1
            indice = max(fim, indice + 2)
            continue
        if caractere == "{":
            profundidade += 1
        elif caractere == "}":
            profundidade -= 1
        indice += 1
    return posicoes


def _cortar(formula: str, posicoes: list[int]) -> list[str]:
    limites = [0, *posicoes, len(formula)]
    return [formula[a:b].strip() for a, b in zip(limites, limites[1:]) if formula[a:b].strip()]


def _uma_formula_por_linha(texto: str) -> str:
    """No celular, quebra em linhas as fórmulas em destaque ($$...$$) largas.

    Quebra em cada \\qquad, antes do 2º "=" de uma cadeia (a = b = c) e antes
    de "+\\cdots" numa soma longa. As linhas ficam num ambiente "aligned",
    alinhadas pelo "=" (o Flet 0.86.3 não conhece "gathered"; \\cr separa
    as linhas).
    """

    def empilhar(achado: re.Match[str]) -> str:
        linhas: list[str] = []
        for parte in re.split(r"\s*\\qquad\s*", achado.group(1)):
            iguais = _fora_das_chaves(parte, "=")
            if len(parte) <= CARACTERES_SEM_QUEBRA:
                # Curta: cabe na tela do celular sem quebrar.
                linhas.append(parte.strip())
            elif len(iguais) >= 2:
                linhas.extend(_cortar(parte, iguais[1:]))
            elif (reticencias := _fora_das_chaves(parte, r"+\cdots")):
                linhas.extend(_cortar(parte, reticencias[:1]))
            else:
                linhas.append(parte.strip())
        if len(linhas) == 1:
            return achado.group(0)
        alinhadas = []
        for linha in linhas:
            if linha.startswith("="):
                alinhadas.append("&" + linha)
            elif linha.startswith("+"):
                alinhadas.append(r"&\quad " + linha)
            else:
                # Alinha pela primeira relação (=, ≈, →, <, >, ≤, ≥) da linha.
                relacoes = [
                    posicao
                    for simbolo in ("=", r"\approx", r"\to", "<", ">", r"\le", r"\ge")
                    for posicao in _fora_das_chaves(linha, simbolo)
                    # "\le" não pode ser o começo de "\left", nem "\to" de "\top".
                    if not linha[posicao + len(simbolo):][:1].isalpha()
                    or not simbolo.startswith("\\")
                ]
                corte = min(relacoes) if relacoes else 0
                alinhadas.append(linha[:corte] + "&" + linha[corte:])
        return "$$\\begin{aligned}" + r"\cr ".join(alinhadas) + "\\end{aligned}$$"

    return re.sub(r"\$\$(.+?)\$\$", empilhar, texto, flags=re.DOTALL)


def formulas_pretendidas(texto: str) -> list[str]:
    """Fórmulas escritas pelo autor: trechos entre "$" ou "$$" sem escape."""
    formulas: list[str] = []
    indice, tamanho = 0, len(texto)
    abertura: str | None = None
    inicio = 0
    while indice < tamanho:
        caractere = texto[indice]
        if caractere == "\\" and indice + 1 < tamanho:
            indice += 2
            continue
        if caractere == "$":
            delimitador = "$$" if texto.startswith("$$", indice) else "$"
            if abertura is None:
                abertura, inicio = delimitador, indice + len(delimitador)
            elif texto.startswith(abertura, indice):
                formulas.append(texto[inicio:indice])
                indice += len(abertura)
                abertura = None
                continue
            indice += len(delimitador)
            continue
        indice += 1
    return formulas


def proteger_formulas(texto: str) -> str:
    """Garante que cada fórmula termine onde o autor fechou o "$".

    Quando o "$" de fechamento é seguido por um caractere que o Flet não
    aceita (";", ")", letras etc.), insere um espaço finíssimo logo depois.
    """
    texto = str(texto)
    partes: list[str] = []
    indice, tamanho = 0, len(texto)
    abertura: str | None = None
    while indice < tamanho:
        caractere = texto[indice]
        if caractere == "\\" and indice + 1 < tamanho:
            partes.append(texto[indice:indice + 2])
            indice += 2
            continue
        if caractere == "$":
            delimitador = "$$" if texto.startswith("$$", indice) else "$"
            if abertura is None:
                abertura = delimitador
            elif texto.startswith(abertura, indice):
                delimitador = abertura
                abertura = None
                partes.append(delimitador)
                indice += len(delimitador)
                if indice < tamanho and texto[indice] not in _APOS_FORMULA:
                    partes.append(_SEPARADOR_FORMULA)
                continue
            partes.append(delimitador)
            indice += len(delimitador)
            continue
        partes.append(caractere)
        indice += 1
    return "".join(partes)


def formulas_como_o_flet_le(texto: str) -> list[str]:
    """Reproduz como o cliente do Flet separa texto e fórmulas em linha."""
    formulas: list[str] = []
    indice, tamanho = 0, len(texto)
    while indice < tamanho:
        encontrado = _REGEX_FLET.match(texto, indice)
        if encontrado:
            conteudo = next(
                grupo for grupo in encontrado.groups()[1:] if grupo is not None
            )
            formulas.append(conteudo)
            indice = encontrado.end()
            continue
        if texto[indice] == "\\" and indice + 1 < tamanho:
            indice += 2
            continue
        indice += 1
    return formulas


def problemas_de_formula(texto: str) -> list[str]:
    """Descreve diferenças entre as fórmulas escritas e as que o Flet exibirá."""
    exibido = proteger_formulas(texto)
    esperadas = formulas_pretendidas(exibido)
    lidas = formulas_como_o_flet_le(exibido)
    if esperadas == lidas:
        return []
    return [
        "fórmulas lidas pelo Flet diferem das escritas: "
        f"esperado {esperadas!r}, lido {lidas!r}"
    ]


def markdown_matematico(
    texto: str,
    *,
    cor: str,
    tamanho: float = 14,
    peso: Any = None,
    alinhamento: ft.MainAxisAlignment = ft.MainAxisAlignment.SPACE_BETWEEN,
    expandir: bool = False,
    escala_latex: float = 1.05,
    selecionavel: bool = False,
    col: Any = None,
) -> ft.Markdown:
    """Cria Markdown com LaTeX e padronização profissional dos parágrafos.

    No Flet 0.86.3, o alinhamento do texto de ``MarkdownStyleSheet`` usa
    ``MainAxisAlignment``. ``SPACE_BETWEEN``, combinado com
    ``fit_content=False``, ocupa toda a largura disponível e apresenta os
    parágrafos com alinhamento visual nas duas margens. Fórmulas e destaques
    que precisam permanecer centralizados continuam informando explicitamente
    ``MainAxisAlignment.CENTER`` nas telas dos módulos.
    """

    if _tela_estreita:
        texto = _uma_formula_por_linha(str(texto))
        escala_latex *= ESCALA_LATEX_CELULAR

    # Em frases com fórmulas, o alinhamento justificado (SPACE_BETWEEN)
    # afasta texto e fórmulas para as bordas ("eleva      P      porque").
    # Nesses casos o parágrafo fica alinhado à esquerda.
    if (
        alinhamento == ft.MainAxisAlignment.SPACE_BETWEEN
        and formulas_pretendidas(str(texto))
    ):
        alinhamento = ft.MainAxisAlignment.START

    estilo = ft.TextStyle(
        color=cor,
        size=tamanho,
        weight=peso,
    )
    argumentos: dict[str, Any] = {
        # proteger_formulas evita o erro "Can't use function '$' in math mode".
        "value": proteger_formulas(texto),
        "selectable": selecionavel,
        "extension_set": ft.MarkdownExtensionSet.GITHUB_FLAVORED,
        "shrink_wrap": True,
        # Textos corridos precisam ocupar toda a largura do cartão para que o
        # alinhamento visual nas duas margens seja percebido. Componentes com
        # alinhamento explícito (por exemplo, fórmulas centralizadas) mantêm o
        # comportamento compacto já existente.
        "fit_content": alinhamento != ft.MainAxisAlignment.SPACE_BETWEEN,
        "soft_line_break": True,
        "md_style_sheet": ft.MarkdownStyleSheet(
            p_text_style=estilo,
            p_padding=0,
            block_spacing=0,
            text_alignment=alinhamento,
            strong_text_style=ft.TextStyle(
                color=cor,
                size=tamanho,
                weight=ft.FontWeight.BOLD,
            ),
        ),
        "latex_style": estilo,
        "latex_scale_factor": escala_latex,
        "expand": expandir or None,
    }
    if col is not None:
        argumentos["col"] = col
    return ft.Markdown(**argumentos)


def _extrair_argumento_balanceado(
    texto: str,
    inicio: int,
) -> tuple[str, int] | None:
    """Extrai um argumento LaTeX entre chaves, respeitando aninhamento."""

    if inicio >= len(texto) or texto[inicio] != "{":
        return None
    profundidade = 0
    for indice in range(inicio, len(texto)):
        caractere = texto[indice]
        if caractere == "{":
            profundidade += 1
        elif caractere == "}":
            profundidade -= 1
            if profundidade == 0:
                return texto[inicio + 1 : indice], indice + 1
    return None


def _fracoes_para_fala(texto: str) -> str:
    """Transforma ``\\frac{a}{b}`` em uma expressão adequada à narração."""

    while r"\frac" in texto:
        inicio = texto.rfind(r"\frac")
        cursor = inicio + len(r"\frac")
        numerador = _extrair_argumento_balanceado(texto, cursor)
        if numerador is None:
            texto = texto[:inicio] + " fração " + texto[cursor:]
            continue
        denominador = _extrair_argumento_balanceado(texto, numerador[1])
        if denominador is None:
            texto = texto[:inicio] + " fração " + texto[numerador[1] :]
            continue
        substituto = (
            f" ({numerador[0]}) dividido por ({denominador[0]}) "
        )
        texto = texto[:inicio] + substituto + texto[denominador[1] :]
    return texto


def texto_para_narracao(texto: str) -> str:
    """Remove marcação Markdown/LaTeX sem perder o sentido matemático."""

    fala = _fracoes_para_fala(str(texto))
    fala = fala.replace(r"R\$", " reais ")
    substituicoes = {
        r"\cdot": " vezes ",
        r"\times": " vezes ",
        r"\div": " dividido por ",
        r"\approx": " aproximadamente ",
        r"\neq": " diferente de ",
        r"\leq": " menor ou igual a ",
        r"\geq": " maior ou igual a ",
        r"\to": " tende a ",
        r"\infty": " infinito ",
        r"\delta": " delta ",
        r"\sum": " somatório ",
        r"\lim": " limite ",
        r"\qquad": ". ",
        r"\quad": " ",
        r"\,": " ",
        r"\;": " ",
        r"\left": "",
        r"\right": "",
        r"\$": "$",
    }
    for origem, destino in substituicoes.items():
        fala = fala.replace(origem, destino)

    for comando in ("text", "mathrm", "mathbf", "operatorname"):
        padrao = re.compile(rf"\\{comando}\{{([^{{}}]*)\}}")
        while padrao.search(fala):
            fala = padrao.sub(r"\1", fala)

    fala = re.sub(r"\^\{([^{}]+)\}", r" elevado a \1 ", fala)
    fala = re.sub(r"\^\(([^()]+)\)", r" elevado a \1 ", fala)
    fala = re.sub(r"\^([A-Za-z0-9+-]+)", r" elevado a \1 ", fala)
    fala = re.sub(r"_\{([^{}]+)\}", r" índice \1 ", fala)
    fala = re.sub(r"_\(([^()]+)\)", r" índice \1 ", fala)
    fala = re.sub(r"_([A-Za-z0-9]+)", r" índice \1 ", fala)
    fala = fala.replace("$$", " ").replace("$", " ")
    fala = fala.replace("[", " ").replace("]", " ")
    fala = fala.replace("{", " ").replace("}", " ")
    fala = fala.replace("\\", " ")
    fala = re.sub(r"[*#`]", " ", fala)
    fala = re.sub(r"\s+([,.;:!?])", r"\1", fala)
    fala = re.sub(r"\s+", " ", fala)
    return fala.strip()
