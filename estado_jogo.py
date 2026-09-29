"""Estado persistente, pontuação acumulada e planilha de ranking do jogo.

Este módulo usa somente a biblioteca padrão do Python. O arquivo
``dados/estado_jogo.json`` preserva os jogadores e as preferências, enquanto
``dados/ranking.xlsx`` é atualizado automaticamente a cada mudança de saldo.
"""

from __future__ import annotations

import json
import os
import uuid
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from xml.sax.saxutils import escape


BASE_DIR = Path(__file__).resolve().parent
DADOS_DIR = BASE_DIR / "dados"
ARQUIVO_ESTADO = DADOS_DIR / "estado_jogo.json"
ARQUIVO_RANKING = DADOS_DIR / "ranking.xlsx"

TRILHAS_PADRAO = {
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

TEMAS_DISPONIVEIS = (
    "Financeiro",
    "Neon roxo",
    "Esmeralda",
    "Pôr do sol",
    "Claro",
    "Alto contraste",
)

# PREFERÊNCIAS DE ACESSIBILIDADE (botão ACESSIBILIDADE na tela inicial):
#   tempo: segundos por questão (60, 90 ou 120); 0 = sem limite de tempo.
#   sem_animacoes: True desliga transições, pulsos e animações do saldo.
#   efeitos: sons de toque dos botões e de acerto/erro (independente da música).
ACESSIBILIDADE_PADRAO = {"tempo": 60, "sem_animacoes": False, "efeitos": True}
TEMPOS_PERMITIDOS = (60, 90, 120, 0)


def formatar_reais(valor: float) -> str:
    return (
        f"R$ {valor:,.2f}"
        .replace(",", "X")
        .replace(".", ",")
        .replace("X", ".")
    )


def _agora() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def _novo_jogador() -> dict[str, Any]:
    return {
        "id": uuid.uuid4().hex,
        "nome": "",
        "imagem": "",
        "saldo": 0.0,
        "acertos": 0,
        "erros": 0,
        "estudos": 0,
        "rodadas": 0,
        "atualizado_em": _agora(),
    }


class EstadoJogo:
    """Mantém o mesmo saldo entre telas, etapas e novas execuções."""

    def __init__(
        self,
        caminho: Path = ARQUIVO_ESTADO,
        gerar_ranking: bool = True,
    ) -> None:
        self.caminho = caminho
        # O modo administrador usa gerar_ranking=False para não alterar a
        # planilha dados/ranking.xlsx dos jogadores reais.
        self.gerar_ranking = gerar_ranking
        self.erro_ranking = ""
        self.dados = self._carregar()
        self._normalizar()
        self.salvar()

    def _padrao(self) -> dict[str, Any]:
        return {
            "versao": 1,
            "quantidade_jogadores": 2,
            "jogadores": [_novo_jogador() for _ in range(4)],
            "tema": "Financeiro",
            "trilha": "Aventura",
            "trilhas_personalizadas": {},
        }

    def _carregar(self) -> dict[str, Any]:
        if not self.caminho.exists():
            return self._padrao()
        try:
            with self.caminho.open("r", encoding="utf-8") as arquivo:
                dados = json.load(arquivo)
            if isinstance(dados, dict):
                return dados
        except (OSError, json.JSONDecodeError) as erro:
            print(f"Não foi possível ler o estado anterior: {erro}")
        return self._padrao()

    def _normalizar(self) -> None:
        quantidade = self.dados.get("quantidade_jogadores", 2)
        try:
            quantidade = int(quantidade)
        except (TypeError, ValueError):
            quantidade = 2
        self.dados["quantidade_jogadores"] = min(4, max(2, quantidade))

        jogadores = self.dados.get("jogadores")
        if not isinstance(jogadores, list):
            jogadores = []
        while len(jogadores) < 4:
            jogadores.append(_novo_jogador())
        jogadores = jogadores[:4]
        for indice, jogador in enumerate(jogadores):
            padrao = _novo_jogador()
            if not isinstance(jogador, dict):
                jogador = padrao
                jogadores[indice] = jogador
            else:
                for chave, valor in padrao.items():
                    jogador.setdefault(chave, valor)
                jogador["nome"] = str(jogador.get("nome", "")).strip()
                jogador["imagem"] = str(jogador.get("imagem", ""))
                jogador["saldo"] = float(jogador.get("saldo", 0.0))
                for chave in ("acertos", "erros", "estudos", "rodadas"):
                    jogador[chave] = int(jogador.get(chave, 0))
        self.dados["jogadores"] = jogadores

        tema = str(self.dados.get("tema", "Financeiro"))
        self.dados["tema"] = (
            tema if tema in TEMAS_DISPONIVEIS else "Financeiro"
        )
        personalizadas = self.dados.get("trilhas_personalizadas")
        if not isinstance(personalizadas, dict):
            personalizadas = {}
        self.dados["trilhas_personalizadas"] = {
            str(nome): str(caminho)
            for nome, caminho in personalizadas.items()
        }
        if self.dados.get("trilha") not in self.trilhas_disponiveis():
            self.dados["trilha"] = "Aventura"

        acessibilidade = self.dados.get("acessibilidade")
        if not isinstance(acessibilidade, dict):
            acessibilidade = {}
        acessibilidade = {**ACESSIBILIDADE_PADRAO, **acessibilidade}
        try:
            acessibilidade["tempo"] = int(acessibilidade["tempo"])
        except (TypeError, ValueError):
            acessibilidade["tempo"] = 60
        if acessibilidade["tempo"] not in TEMPOS_PERMITIDOS:
            acessibilidade["tempo"] = 60
        acessibilidade["sem_animacoes"] = bool(acessibilidade["sem_animacoes"])
        acessibilidade["efeitos"] = bool(acessibilidade["efeitos"])
        self.dados["acessibilidade"] = acessibilidade

    @property
    def quantidade_jogadores(self) -> int:
        return int(self.dados["quantidade_jogadores"])

    @property
    def tema(self) -> str:
        return str(self.dados["tema"])

    @property
    def trilha(self) -> str:
        return str(self.dados["trilha"])

    @property
    def jogadores(self) -> list[dict[str, Any]]:
        return self.dados["jogadores"]

    def jogadores_ativos(self) -> list[dict[str, Any]]:
        return self.jogadores[: self.quantidade_jogadores]

    def nomes_validos(self) -> tuple[bool, str]:
        nomes = [str(item["nome"]).strip() for item in self.jogadores_ativos()]
        if any(not nome for nome in nomes):
            return False, "Digite o nome de todos os jogadores."
        if len({nome.casefold() for nome in nomes}) != len(nomes):
            return False, "Use nomes diferentes para identificar os jogadores."
        return True, ""

    def definir_quantidade(self, quantidade: int) -> None:
        self.dados["quantidade_jogadores"] = min(4, max(2, int(quantidade)))
        self.salvar()

    def definir_nome(self, indice: int, nome: str) -> None:
        self.jogadores[indice]["nome"] = nome.strip()
        self.jogadores[indice]["atualizado_em"] = _agora()
        self.salvar()

    def definir_imagem(self, indice: int, caminho_relativo: str) -> None:
        self.jogadores[indice]["imagem"] = caminho_relativo
        self.jogadores[indice]["atualizado_em"] = _agora()
        self.salvar()

    def definir_tema(self, nome: str) -> None:
        if nome in TEMAS_DISPONIVEIS:
            self.dados["tema"] = nome
            self.salvar()

    @property
    def acessibilidade(self) -> dict[str, Any]:
        return self.dados["acessibilidade"]

    def definir_acessibilidade(self, **valores: Any) -> None:
        """Ex.: definir_acessibilidade(tempo=90) ou (sem_animacoes=True)."""
        self.dados["acessibilidade"].update(valores)
        self._normalizar()
        self.salvar()

    def trilhas_disponiveis(self) -> dict[str, str]:
        return {
            **TRILHAS_PADRAO,
            **self.dados.get("trilhas_personalizadas", {}),
        }

    def definir_trilha(self, nome: str) -> None:
        if nome in self.trilhas_disponiveis():
            self.dados["trilha"] = nome
            self.salvar()

    def adicionar_trilha(self, nome: str, caminho_relativo: str) -> str:
        base = nome.strip() or "Música personalizada"
        nome_final = base
        contador = 2
        existentes = self.trilhas_disponiveis()
        while nome_final in existentes:
            nome_final = f"{base} ({contador})"
            contador += 1
        self.dados["trilhas_personalizadas"][nome_final] = caminho_relativo
        self.dados["trilha"] = nome_final
        self.salvar()
        return nome_final

    def registrar_resultado(self, jogador_id: str, resultado: str) -> None:
        jogador = next(
            (item for item in self.jogadores if item["id"] == jogador_id),
            None,
        )
        if jogador is None:
            raise ValueError("Jogador não encontrado no estado compartilhado.")

        if resultado == "acerto":
            jogador["saldo"] = float(jogador["saldo"]) + 100.0
            jogador["acertos"] = int(jogador["acertos"]) + 1
        elif resultado == "erro":
            jogador["saldo"] = float(jogador["saldo"]) - 200.0
            jogador["erros"] = int(jogador["erros"]) + 1

        elif resultado == "estudo":
            jogador["saldo"] = float(jogador["saldo"]) + 50.0
            jogador["estudos"] = int(jogador["estudos"]) + 1

       
        else:
            raise ValueError(f"Resultado desconhecido: {resultado}")

        jogador["rodadas"] = int(jogador["rodadas"]) + 1
        jogador["atualizado_em"] = _agora()
        self.salvar()

    def ranking(self) -> list[dict[str, Any]]:
        cadastrados = [
            jogador
            for jogador in self.jogadores
            if str(jogador.get("nome", "")).strip()
        ]
        return sorted(
            cadastrados,
            key=lambda item: (
                float(item["saldo"]),
                int(item["acertos"]),
                -int(item["erros"]),
                str(item["nome"]).casefold(),
            ),
            reverse=True,
        )

    def salvar(self) -> None:
        self.caminho.parent.mkdir(parents=True, exist_ok=True)
        temporario = self.caminho.with_suffix(".json.tmp")
        with temporario.open("w", encoding="utf-8") as arquivo:
            json.dump(
                self.dados,
                arquivo,
                ensure_ascii=False,
                indent=2,
            )
        os.replace(temporario, self.caminho)
        if not self.gerar_ranking:
            return
        try:
            self._gerar_ranking_xlsx()
            self.erro_ranking = ""
        except OSError as erro:
            self.erro_ranking = str(erro)
            print(
                "O estado foi salvo, mas a planilha de ranking não pôde ser "
                f"atualizada: {erro}"
            )

    def _gerar_ranking_xlsx(self) -> None:
        """Gera um XLSX real sem exigir openpyxl no computador do jogador."""
        ARQUIVO_RANKING.parent.mkdir(parents=True, exist_ok=True)
        temporario = ARQUIVO_RANKING.with_suffix(".xlsx.tmp")
        classificacao = self.ranking()

        colunas = [
            ("Posição", "texto"),
            ("Jogador", "texto"),
            ("Saldo acumulado (R$)", "numero"),
            ("Acertos", "numero"),
            ("Erros", "numero"),
            ("Estudos", "numero"),
            ("Rodadas", "numero"),
            ("Última atualização", "texto"),
        ]
        linhas = []
        for posicao, jogador in enumerate(classificacao, start=1):
            linhas.append(
                [
                    posicao,
                    jogador["nome"],
                    float(jogador["saldo"]),
                    int(jogador["acertos"]),
                    int(jogador["erros"]),
                    int(jogador["estudos"]),
                    int(jogador["rodadas"]),
                    jogador["atualizado_em"],
                ]
            )

        def letra_coluna(numero: int) -> str:
            resultado = ""
            while numero:
                numero, resto = divmod(numero - 1, 26)
                resultado = chr(65 + resto) + resultado
            return resultado

        def celula(ref: str, valor: Any, estilo: int = 0) -> str:
            if isinstance(valor, (int, float)) and not isinstance(valor, bool):
                return f'<c r="{ref}" s="{estilo}"><v>{valor}</v></c>'
            texto = escape(str(valor))
            return (
                f'<c r="{ref}" t="inlineStr" s="{estilo}">'
                f"<is><t>{texto}</t></is></c>"
            )

        linhas_xml = []
        cabecalho = "".join(
            celula(f"{letra_coluna(indice)}1", titulo, 1)
            for indice, (titulo, _tipo) in enumerate(colunas, start=1)
        )
        linhas_xml.append(f'<row r="1" ht="28" customHeight="1">{cabecalho}</row>')
        for numero_linha, valores in enumerate(linhas, start=2):
            conteudo = []
            for numero_coluna, valor in enumerate(valores, start=1):
                estilo = 2 if numero_coluna == 3 else 0
                conteudo.append(
                    celula(
                        f"{letra_coluna(numero_coluna)}{numero_linha}",
                        valor,
                        estilo,
                    )
                )
            linhas_xml.append(f'<row r="{numero_linha}">{"".join(conteudo)}</row>')

        fim_filtro = max(1, len(linhas) + 1)
        planilha = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
  <sheetViews><sheetView workbookViewId="0"><pane ySplit="1" topLeftCell="A2" activePane="bottomLeft" state="frozen"/></sheetView></sheetViews>
  <cols>
    <col min="1" max="1" width="11" customWidth="1"/>
    <col min="2" max="2" width="28" customWidth="1"/>
    <col min="3" max="3" width="24" customWidth="1"/>
    <col min="4" max="7" width="13" customWidth="1"/>
    <col min="8" max="8" width="28" customWidth="1"/>
  </cols>
  <sheetData>{"".join(linhas_xml)}</sheetData>
  <autoFilter ref="A1:H{fim_filtro}"/>
</worksheet>"""

        estilos = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
  <numFmts count="1"><numFmt numFmtId="164" formatCode="R$ #,##0.00;[Red]-R$ #,##0.00"/></numFmts>
  <fonts count="2">
    <font><sz val="11"/><name val="Calibri"/></font>
    <font><b/><color rgb="FFFFFFFF"/><sz val="11"/><name val="Calibri"/></font>
  </fonts>
  <fills count="3">
    <fill><patternFill patternType="none"/></fill>
    <fill><patternFill patternType="gray125"/></fill>
    <fill><patternFill patternType="solid"><fgColor rgb="FF073B7A"/><bgColor indexed="64"/></patternFill></fill>
  </fills>
  <borders count="1"><border><left/><right/><top/><bottom/><diagonal/></border></borders>
  <cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs>
  <cellXfs count="3">
    <xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/>
    <xf numFmtId="0" fontId="1" fillId="2" borderId="0" xfId="0" applyFill="1" applyFont="1"/>
    <xf numFmtId="164" fontId="0" fillId="0" borderId="0" xfId="0" applyNumberFormat="1"/>
  </cellXfs>
  <cellStyles count="1"><cellStyle name="Normal" xfId="0" builtinId="0"/></cellStyles>
</styleSheet>"""

        tipos = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>
  <Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>
  <Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>
  <Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>
  <Override PartName="/docProps/app.xml" ContentType="application/vnd.openxmlformats-officedocument.extended-properties+xml"/>
</Types>"""

        relacoes = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>
  <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/>
  <Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties" Target="docProps/app.xml"/>
</Relationships>"""

        pasta_trabalho = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
  <sheets><sheet name="Ranking" sheetId="1" r:id="rId1"/></sheets>
</workbook>"""

        relacoes_pasta = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>
  <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>
</Relationships>"""

        instante = datetime.now(timezone.utc).isoformat(timespec="seconds").replace(
            "+00:00", "Z"
        )
        propriedades = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:dcterms="http://purl.org/dc/terms/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <dc:title>Ranking - Responda ou Estuda</dc:title>
  <dc:creator>Responda ou Estuda</dc:creator>
  <dcterms:created xsi:type="dcterms:W3CDTF">{instante}</dcterms:created>
  <dcterms:modified xsi:type="dcterms:W3CDTF">{instante}</dcterms:modified>
</cp:coreProperties>"""

        aplicativo = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties" xmlns:vt="http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes">
  <Application>Responda ou Estuda</Application>
</Properties>"""

        with zipfile.ZipFile(
            temporario,
            "w",
            compression=zipfile.ZIP_DEFLATED,
        ) as arquivo:
            arquivo.writestr("[Content_Types].xml", tipos)
            arquivo.writestr("_rels/.rels", relacoes)
            arquivo.writestr("xl/workbook.xml", pasta_trabalho)
            arquivo.writestr("xl/_rels/workbook.xml.rels", relacoes_pasta)
            arquivo.writestr("xl/worksheets/sheet1.xml", planilha)
            arquivo.writestr("xl/styles.xml", estilos)
            arquivo.writestr("docProps/core.xml", propriedades)
            arquivo.writestr("docProps/app.xml", aplicativo)
        os.replace(temporario, ARQUIVO_RANKING)
