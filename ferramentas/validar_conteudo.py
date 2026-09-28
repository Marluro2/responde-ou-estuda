"""Valida Porcentagem, Juros, PRICE e os arquivos usados pelo jogo."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any


BASE_DIR = Path(__file__).resolve().parents[1]
ASSETS_DIR = BASE_DIR / "assets"
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from formatacao_matematica import problemas_de_formula  # noqa: E402
BANCOS = (
    (
        "Porcentagem",
        BASE_DIR / "dados" / "questoes_porcentagem.json",
        {"preco_referencia"},
    ),
    (
        "Juros",
        BASE_DIR / "dados" / "questoes_juros.json",
        set(),
    ),
    (
        "PRICE",
        BASE_DIR / "dados" / "questoes_price.json",
        set(),
    ),
)


def _argumento_latex(texto: str, inicio: int) -> int | None:
    """Retorna a posição após um argumento balanceado entre chaves."""

    if inicio >= len(texto) or texto[inicio] != "{":
        return None
    profundidade = 0
    for indice in range(inicio, len(texto)):
        if texto[indice] == "{":
            profundidade += 1
        elif texto[indice] == "}":
            profundidade -= 1
            if profundidade == 0:
                return indice + 1
    return None


def _validar_latex(identificador: str, texto: str) -> list[str]:
    """Valida delimitadores e todos os pares numerador/denominador de \frac."""

    erros: list[str] = []
    delimitadores = re.findall(r"(?<!\\)\$", texto)
    if len(delimitadores) % 2:
        erros.append(
            f"{identificador}: quantidade ímpar de delimitadores LaTeX '$'."
        )

    cursor = 0
    while True:
        inicio = texto.find(r"\frac", cursor)
        if inicio < 0:
            break
        numerador = _argumento_latex(texto, inicio + len(r"\frac"))
        denominador = (
            _argumento_latex(texto, numerador)
            if numerador is not None
            else None
        )
        if numerador is None or denominador is None:
            erros.append(
                f"{identificador}: comando \\frac sem numerador e denominador "
                "balanceados."
            )
            break
        cursor = denominador

    comandos = (r"\frac", r"\cdot", r"\sum", r"\lim")
    if any(comando in texto for comando in comandos) and not delimitadores:
        erros.append(
            f"{identificador}: expressão matemática sem delimitadores LaTeX."
        )
    # Confere se o Flet vai separar texto e fórmulas exatamente como escrito
    # (evita "Parser Error: Can't use function '$' in math mode" na tela).
    erros.extend(
        f"{identificador}: {problema}"
        for problema in problemas_de_formula(texto)
    )
    return erros


def validar_textos_do_codigo() -> list[str]:
    """Confere as fórmulas escritas diretamente nos arquivos dos módulos."""
    import ast

    erros: list[str] = []
    for nome in (
        "nivel_1_porcentagem.py",
        "nivel_2_juros.py",
        "nivel_3_price.py",
    ):
        arvore = ast.parse((BASE_DIR / nome).read_text(encoding="utf-8"))
        for no in ast.walk(arvore):
            if (
                isinstance(no, ast.Constant)
                and isinstance(no.value, str)
                and "$" in no.value
            ):
                erros.extend(
                    f"{nome}, linha {no.lineno}: {problema}"
                    for problema in problemas_de_formula(no.value)
                )
    return erros


def validar_banco(
    nome: str,
    caminho: Path,
    campos_extras: set[str],
) -> tuple[list[str], int, int]:
    """Valida estrutura, alternativas, imagens, estudo e fontes de um banco."""
    erros: list[str] = []
    try:
        with caminho.open("r", encoding="utf-8") as arquivo:
            dados: dict[str, Any] = json.load(arquivo)
    except Exception as erro:
        return [f"{nome}: não foi possível abrir {caminho.name}: {erro}"], 0, 0

    questoes = dados.get("questoes")
    if not isinstance(questoes, list):
        return [f'{nome}: a chave "questoes" deve conter uma lista.'], 0, 0
    if len(questoes) < 20:
        erros.append(f"{nome}: o banco precisa manter pelo menos 20 questões.")
    if nome == "PRICE" and len(questoes) != 60:
        erros.append(
            f"PRICE: o banco deve conter exatamente 60 questões; "
            f"foram encontradas {len(questoes)}."
        )

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
        *campos_extras,
    }
    ids: set[str] = set()
    imagens_validas = 0

    for numero, questao in enumerate(questoes, start=1):
        if not isinstance(questao, dict):
            erros.append(f"{nome}, questão {numero}: bloco JSON inválido.")
            continue

        ausentes = campos.difference(questao)
        if ausentes:
            erros.append(
                f"{nome}, questão {numero}: campos ausentes: {sorted(ausentes)}"
            )
            continue

        identificador = str(questao["id"])
        if identificador in ids:
            erros.append(f"{nome}: ID repetido: {identificador}.")
        ids.add(identificador)

        alternativas = questao["alternativas"]
        correta = questao["correta"]
        if not isinstance(alternativas, list) or len(alternativas) < 2:
            erros.append(
                f"{identificador}: inclua pelo menos duas alternativas."
            )
        elif not isinstance(correta, int) or not 0 <= correta < len(alternativas):
            erros.append(f"{identificador}: índice 'correta' inválido.")
        if nome == "PRICE" and isinstance(alternativas, list) and len(alternativas) != 5:
            erros.append(
                f"{identificador}: questões PRICE devem ter 5 alternativas."
            )

        imagem_informada = str(questao["imagem"])
        if imagem_informada.startswith(("http://", "https://")):
            erros.append(
                f"{identificador}: imagem remota proibida: {imagem_informada}."
            )
        else:
            imagem = ASSETS_DIR / imagem_informada
            if imagem.is_file():
                imagens_validas += 1
            else:
                erros.append(f"{identificador}: imagem ausente: {imagem}.")

        estudo = questao["estudo"]
        if not isinstance(estudo, dict) or not {
            "titulo",
            "texto",
            "formula",
            "exemplo",
        }.issubset(estudo):
            erros.append(f"{identificador}: bloco 'estudo' incompleto.")

        campos_matematicos: list[str] = [
            str(questao["enunciado"]),
            *(str(item) for item in alternativas),
            str(questao["explicacao"]),
        ]
        if isinstance(estudo, dict):
            campos_matematicos.extend(
                str(estudo.get(chave, ""))
                for chave in ("texto", "formula", "exemplo")
            )
        for texto in campos_matematicos:
            erros.extend(_validar_latex(identificador, texto))
            # Uma divisão matemática não pode sobreviver fora de \frac. Datas
            # e o nome PRICE/SAF não fazem parte destes campos de cálculo.
            sem_fracoes = re.sub(
                r"\\frac\{[^{}]*\}\{[^{}]*\}",
                "",
                texto,
            )
            sem_nome_modulo = sem_fracoes.replace("PRICE / SAF", "PRICE SAF")
            if "÷" in sem_nome_modulo:
                erros.append(
                    f"{identificador}: divisão textual não convertida para LaTeX."
                )
                break
            if re.search(r"(?<!https:)(?<!http:)[A-Za-z0-9)}\]]\s*/\s*[A-Za-z0-9({\[]", sem_nome_modulo):
                erros.append(
                    f"{identificador}: fração com barra não convertida para LaTeX."
                )
                break

        fonte = questao["fonte"]
        if not isinstance(fonte, dict) or not {
            "loja",
            "url",
            "consulta",
        }.issubset(fonte):
            erros.append(f"{identificador}: bloco 'fonte' incompleto.")

    return erros, len(questoes), imagens_validas


def validar_infraestrutura_visual() -> list[str]:
    """Confere teoria, mídias locais e assets_dir dos pontos de entrada."""

    erros: list[str] = []
    if str(BASE_DIR) not in sys.path:
        sys.path.insert(0, str(BASE_DIR))
    try:
        from nivel_2_juros import IMAGENS_TEORIA as IMAGENS_JUROS
        from nivel_2_juros import PAGINAS_TEORIA as TEORIA_JUROS
        from nivel_3_price import IMAGENS_TEORIA as IMAGENS_PRICE
        from nivel_3_price import PAGINAS_TEORIA as TEORIA_PRICE
    except Exception as erro:
        return [f"Não foi possível importar as páginas teóricas: {erro}"]

    for nome, paginas in (("Juros", TEORIA_JUROS), ("PRICE", TEORIA_PRICE)):
        for indice, pagina in enumerate(paginas, start=1):
            identificador = f"Teoria {nome}, página {indice}"
            for chave in ("definicao", "formula", "passos", "significados", "aplicacao"):
                valor = pagina.get(chave, "")
                textos = valor if isinstance(valor, list) else [valor]
                for texto in textos:
                    texto = str(texto)
                    erros.extend(_validar_latex(identificador, texto))
                    sem_nome = texto.replace("PRICE / SAF", "PRICE SAF")
                    if "÷" in sem_nome or re.search(
                        r"[A-Za-z0-9)}\]]\s*/\s*[A-Za-z0-9({\[]",
                        sem_nome,
                    ):
                        erros.append(
                            f"{identificador}: fração visual ainda usa barra."
                        )

    for nome, caminhos in (("Juros", IMAGENS_JUROS), ("PRICE", IMAGENS_PRICE)):
        for chave, relativo in caminhos.items():
            relativo = str(relativo)
            if relativo.startswith(("http://", "https://")):
                erros.append(f"Teoria {nome}/{chave}: imagem remota proibida.")
            elif not (ASSETS_DIR / relativo).is_file():
                erros.append(
                    f"Teoria {nome}/{chave}: imagem local ausente: {relativo}."
                )

    pontos_entrada = (
        BASE_DIR / "responda_ou_estuda.py",
        BASE_DIR / "nivel_1_porcentagem.py",
        BASE_DIR / "nivel_2_juros.py",
        BASE_DIR / "nivel_3_price.py",
    )
    for caminho in pontos_entrada:
        codigo = caminho.read_text(encoding="utf-8")
        configuracoes_validas = (
            "assets_dir=str(PASTA_ASSETS)",
            "assets_dir=str(ASSETS_DIR)",
        )
        if not any(item in codigo for item in configuracoes_validas):
            erros.append(f"{caminho.name}: assets_dir local não configurado.")
    return erros


def main() -> int:
    erros: list[str] = []
    resumos: list[tuple[str, int, int]] = []
    for nome, caminho, campos_extras in BANCOS:
        falhas, quantidade, imagens = validar_banco(
            nome,
            caminho,
            campos_extras,
        )
        erros.extend(falhas)
        resumos.append((nome, quantidade, imagens))

    erros.extend(validar_infraestrutura_visual())
    erros.extend(validar_textos_do_codigo())

    sons = sorted((ASSETS_DIR / "sons").glob("*.wav"))
    if len(sons) < 10:
        erros.append(
            f"Foram encontrados apenas {len(sons)} sons; são necessários 10."
        )

    if erros:
        print("VALIDAÇÃO REPROVADA")
        for erro in erros:
            print(f"- {erro}")
        return 1

    print("VALIDAÇÃO APROVADA")
    for nome, quantidade, imagens in resumos:
        print(f"- {nome}: {quantidade} questões e {imagens} imagens configuradas")
    print(f"- Trilhas sonoras: {len(sons)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
