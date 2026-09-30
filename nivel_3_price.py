"""Jogo do Sistema PRICE / SAF "Responda ou Estuda" em Flet 0.86.3.

Integração:
    from nivel_3_price import criar_tela_price
    controle = criar_tela_price(page, funcao_para_voltar)

Questões:
    dados/questoes_price.json

Imagens:
    assets/imagens/price/

Sons:
    assets/sons/
"""

from __future__ import annotations

import asyncio
import base64
import json
import random
import re
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
import economia_tela as et
import recursos_jogo as rj

try:
    import winsound
except ImportError:  # Android, iOS, macOS e Linux usam o áudio do Flet.
    winsound = None


BASE_DIR = Path(__file__).resolve().parent
ASSETS_DIR = BASE_DIR / "assets"
ARQUIVO_QUESTOES = BASE_DIR / "dados" / "questoes_price.json"

PREMIO_ACERTO = 100.0
PENALIDADE_ERRO = 200.0
PREMIO_ESTUDO = 50.0

# CRONÔMETRO: altere 60 para definir quantos segundos o jogador terá em cada
# questão. O tempo começa quando a situação-problema é apresentada.
TEMPO_POR_QUESTAO = 60

# Nome do módulo nos relatórios de pesquisa (dados/respostas.csv).
MODULO_PESQUISA = "PRICE"

# ROLAGEM DAS TELAS: espaço livre, em pixels, no fim de cada tela do módulo.
ESPACO_FINAL_ROLAGEM = 12

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

# IMAGENS LOCAIS DA REVISÃO PRICE:
# Para trocar uma imagem, mantenha o novo arquivo dentro de assets e altere
# somente o caminho relativo. As mesmas imagens ilustram as questões.
IMAGENS_TEORIA = {
    "automovel": "imagens/price/automovel_corolla.webp",
    "console": "imagens/price/console_playstation5.webp",
    "geladeira": "imagens/price/geladeira_liebherr.webp",
    "camera": "imagens/price/camera_canon_eos5d.webp",
}

# NÍVEIS DO BANCO PRICE:
# O arquivo de questões possui 15 itens em cada uma destas quatro categorias.
# A chave corresponde exatamente ao campo ``nivel`` do JSON; ``rotulo`` é o
# texto exibido na interface. A seleção ocorre antes da primeira rodada.
NIVEIS_PRICE = {
    "Super fácil": {
        "rotulo": "SUPERFÁCIL",
        "descricao": "Reconhecimento das ideias básicas do Sistema PRICE e da PG.",
        "icone": ft.Icons.AUTO_AWESOME,
        "cor": "positivo",
    },
    "Fácil": {
        "rotulo": "FÁCIL",
        "descricao": "Taxa decimal, termos e soma da PG, juros, amortização e saldo.",
        "icone": ft.Icons.SENTIMENT_SATISFIED,
        "cor": "primaria",
    },
    "Médio": {
        "rotulo": "MÉDIO",
        "descricao": "Cálculo da prestação fixa com o modelo matemático do Sistema PRICE.",
        "icone": ft.Icons.PSYCHOLOGY,
        "cor": "destaque",
    },
    "Difícil": {
        "rotulo": "DIFÍCIL",
        "descricao": "Carência, equivalência financeira, limites e análise avançada.",
        "icone": ft.Icons.LOCAL_FIRE_DEPARTMENT,
        "cor": "negativo",
    },
}

# O parser do Markdown do Flet pode interpretar o cifrão de ``\text{R\$}``
# como delimitador e deixar comandos LaTeX visíveis. As alternativas PRICE são
# segmentadas antes da renderização: fórmula, moeda e explicação recebem
# controles independentes, sem alterar o texto armazenado no banco.
PADRAO_BLOCO_MATEMATICO = re.compile(
    r"(?<!\\)\$\$((?:\\.|(?!\$\$)[\s\S])*)(?<!\\)\$\$"
    r"|(?<!\\)\$((?:\\.|[^$])*)(?<!\\)\$",
    re.DOTALL,
)
PADRAO_MOEDA_LATEX = re.compile(
    r"\\(?:text|mathrm)\{R\\\$\s*\}(?:\\,)?\s*([0-9][0-9{}.,]*)"
)

# CONTEÚDO PAGINADO DA REVISÃO:
# Cada dicionário abaixo corresponde a uma etapa da teoria. Para alterar textos,
# fórmulas ou exemplos, edite somente os campos da página desejada. A quantidade
# de etapas é calculada automaticamente a partir desta lista.
PAGINAS_TEORIA = [
    {
        "titulo": "SISTEMA PRICE / SAF",
        "subtitulo": "Prestações fixas com composição interna variável",
        "imagem": "automovel",
        "definicao": (
            "O Sistema de Amortização Francês, conhecido como Sistema PRICE, "
            "organiza um financiamento em prestações periódicas iguais. Dentro "
            "de cada prestação, porém, a parte de juros diminui e a amortização "
            "do principal aumenta."
        ),
        "formula": (
            r"$$PMT=SD\cdot\frac{i\cdot(1+i)^n}{(1+i)^n-1}$$"
        ),
        "significados": (
            r"$PMT$ = prestação fixa  •  $SD$ = saldo financiado  •  "
            r"$i$ = taxa por período  •  $n$ = número de prestações"
        ),
        "exemplo_titulo": "Exemplo didático: financiamento de R$ 7.000,00",
        "passos": [
            r"Dados: saldo financiado de R\$ 7.000,00; "
            r"$i=2\%=0{,}02$ ao mês; $n=4$ meses.",
            r"$$PMT=7.000\cdot\frac{0{,}02\cdot(1{,}02)^4}{(1{,}02)^4-1}$$",
            r"A prestação fixa é aproximadamente R\$ 1.838,37.",
        ],
        "aplicacao": (
            "É comum em financiamentos de veículos, eletrodomésticos, crédito "
            "pessoal e outros contratos com parcelas iguais."
        ),
        "narracao": (
            "Parte um de quatro. Sistema Price ou Sistema de Amortização Francês. "
            "As prestações são fixas. Em cada prestação, os juros diminuem e a "
            "amortização aumenta. O modelo matemático da prestação é PMT igual ao saldo "
            "devedor vezes i vezes um mais i elevado a n, dividido por um mais i "
            "elevado a n menos um. No exemplo, sete mil reais financiados a dois "
            "por cento ao mês em quatro prestações produzem parcela aproximada "
            "de mil oitocentos e trinta e oito reais e trinta e sete centavos."
        ),
    },
    {
        "titulo": "PRICE E PROGRESSÃO GEOMÉTRICA",
        "subtitulo": "Os valores presentes das prestações formam uma PG",
        "imagem": "console",
        "definicao": (
            "Para comparar pagamentos que vencem em datas diferentes, cada "
            "prestação é trazida para a data da compra. Esses valores presentes "
            "formam uma Progressão Geométrica decrescente."
        ),
        "formula": (
            r"$$SD=\frac{PMT}{1+i}+\frac{PMT}{(1+i)^2}+"
            r"\cdots+\frac{PMT}{(1+i)^n}$$"
        ),
        "significados": (
            r"$a_1=\frac{PMT}{1+i}$  •  $q=\frac{1}{1+i}$  •  "
            r"$S_n=a_1\cdot\frac{1-q^n}{1-q}=SD$"
        ),
        "exemplo_titulo": "Como o modelo matemático nasce da soma da PG",
        "passos": [
            r"O primeiro termo é o valor presente da primeira prestação: "
            r"$\frac{PMT}{1+i}$.",
            r"Cada termo seguinte é o anterior multiplicado por "
            r"$q=\frac{1}{1+i}$.",
            r"Somando a PG e isolando $PMT$, obtém-se o modelo matemático da prestação PRICE.",
        ],
        "aplicacao": (
            "A relação com PG permite justificar o modelo, em vez de apenas "
            "memorizá-lo, e ajuda a analisar prazos e taxas diferentes."
        ),
        "narracao": (
            "Parte dois de quatro. Price e Progressão Geométrica. Ao trazer cada "
            "prestação para a data da compra, formamos uma P G decrescente. O "
            "primeiro termo é PMT dividido por um mais i. A razão é um dividido "
            "por um mais i. A soma dos valores presentes é igual ao saldo "
            "financiado. Isolando PMT, obtemos o modelo matemático da prestação fixa."
        ),
    },
    {
        "titulo": "EVOLUÇÃO DA AMORTIZAÇÃO",
        "subtitulo": "Juros decrescentes e amortização crescente",
        "imagem": "geladeira",
        "definicao": (
            "Os juros de cada mês incidem sobre o saldo anterior. Como o saldo "
            "diminui, os juros também diminuem. A diferença entre a prestação "
            "fixa e os juros é a amortização, que cresce ao longo do contrato."
        ),
        "formula": (
            r"$$J_t=i\cdot SD_{t-1}\qquad A_t=PMT-J_t\qquad "
            r"SD_t=SD_{t-1}-A_t$$"
        ),
        "significados": (
            r"Exemplo: saldo inicial de R\$ 7.000,00; taxa de $2\%$ ao mês; "
            r"prestação aproximada de R\$ 1.838,37; $n=4$."
        ),
        "exemplo_titulo": "Tabela PRICE demonstrativa simplificada",
        "passos": [
            "A prestação permanece igual em todas as linhas da tabela.",
            r"Os juros caem de R\$ 140,00 para aproximadamente R\$ 36,05.",
            "A amortização cresce até liquidar o saldo devedor.",
        ],
        "tabela": [
            ["1", "R$ 1.838,37", "R$ 140,00", "R$ 1.698,37", "R$ 5.301,63"],
            ["2", "R$ 1.838,37", "R$ 106,03", "R$ 1.732,33", "R$ 3.569,30"],
            ["3", "R$ 1.838,37", "R$ 71,39", "R$ 1.766,98", "R$ 1.802,32"],
            ["4", "R$ 1.838,37", "R$ 36,05", "R$ 1.802,32", "R$ 0,00"],
        ],
        "aplicacao": (
            "Os valores foram calculados sem arredondar a cada linha; por isso, "
            "conferindo à mão, pode aparecer diferença de 1 centavo (ex.: linha 2). "
            "Nos contratos, as instituições costumam ajustar a última parcela."
        ),
        "narracao": (
            "Parte três de quatro. Evolução da amortização. Os juros incidem "
            "sobre o saldo anterior. Como o saldo diminui, os juros diminuem. "
            "A amortização é a prestação menos os juros e cresce a cada mês. "
            "Na tabela do exemplo, a prestação permanece em mil oitocentos e "
            "trinta e oito reais e trinta e sete centavos. Os juros caem de "
            "cento e quarenta reais para cerca de trinta e seis reais, enquanto "
            "a amortização aumenta até liquidar o saldo."
        ),
    },
    {
        "titulo": "CUSTO TOTAL E DECISÃO FINANCEIRA",
        "subtitulo": "Parcela menor não significa necessariamente menor custo",
        "imagem": "camera",
        "definicao": (
            "No PRICE, ampliar o prazo geralmente reduz a prestação, mas aumenta "
            "o total de juros pagos. A decisão deve considerar renda, orçamento, "
            "custo total e reserva para imprevistos."
        ),
        "formula": (
            r"$$C_{total}=n\cdot PMT\qquad E=C_{total}-SD$$"
        ),
        "significados": (
            "Compare também o CET, que pode reunir juros, tarifas, seguros e "
            "outros encargos do contrato."
        ),
        "exemplo_titulo": "Roteiro para comparar propostas",
        "passos": [
            "Confirme se a taxa e o prazo estão na mesma unidade de tempo.",
            "Calcule a prestação e o total desembolsado em cada alternativa.",
            "Verifique se a parcela cabe no orçamento sem comprometer despesas essenciais.",
        ],
        "aplicacao": (
            "Em compras como automóvel, console, geladeira, bicicleta, câmera, "
            "ar-condicionado ou lavadora, compare o preço à vista com o total "
            "pago nas prestações antes de decidir."
        ),
        "narracao": (
            "Parte quatro de quatro. Custo total e decisão financeira. Aumentar "
            "o prazo costuma reduzir a prestação, mas eleva o total de juros. "
            "Multiplique o número de parcelas pela prestação para encontrar o "
            "total desembolsado. Compare esse valor com o saldo financiado e "
            "observe também o custo efetivo total, as tarifas e os seguros. A "
            "parcela precisa caber no orçamento sem comprometer despesas essenciais."
        ),
    },
]

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
    "Alto contraste": {
        # ACESSIBILIDADE: fundo preto, texto branco, destaques amarelo/ciano.
        "fundo_1": "#000000",
        "fundo_2": "#000000",
        "cartao": "#0E0E0E",
        "cartao_2": "#1C1C1C",
        "primaria": "#00FFFF",
        "destaque": "#FFE600",
        "positivo": "#3DFF7A",
        "negativo": "#FF6B6B",
        "texto": "#FFFFFF",
        "suave": "#F2F2F2",
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
    if not isinstance(questoes, list) or len(questoes) != 60:
        raise ValueError("O banco PRICE deve conter exatamente 60 questões.")

    campos = {
        "id",
        "titulo",
        "produto",
        "nivel",
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

    quantidades_por_nivel = {
        nivel: sum(1 for questao in questoes if questao.get("nivel") == nivel)
        for nivel in NIVEIS_PRICE
    }
    if any(quantidade != 15 for quantidade in quantidades_por_nivel.values()):
        raise ValueError(
            "O banco PRICE deve conter 15 questões em cada nível: "
            + ", ".join(
                f"{nivel}={quantidade}"
                for nivel, quantidade in quantidades_por_nivel.items()
            )
        )

    return questoes


class JogoPrice:
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
        self.nivel_selecionado: str | None = None
        self.jogadores: list[dict[str, Any]] = []
        self.indice_jogador = 0
        self.indice_questao = 0
        self.tela_atual = "cadastro"
        # NAVEGAÇÃO INTERNA: cada item guarda (nome da tela, página da teoria).
        # O módulo é exibido dentro de um Container do aplicativo principal; por
        # isso, esta pilha substitui page.views sem duplicar Views na página.
        self._historico_telas: list[tuple[str, int]] = []
        self.etapa_teoria = 0
        # PAGINAÇÃO DO ESTUDO: controlada separadamente da revisão teórica.
        # Superfácil e Fácil usam uma página, Médio usa duas e Difícil usa quatro
        # páginas curtas para manter a leitura confortável.
        self.pagina_estudo = 0
        self.tema_nome = self.estado.tema
        self.trilha_nome = self.estado.trilha
        self.som_ativo = False
        self.ultimo_resultado: dict[str, Any] | None = None
        self.tempo_restante = self.tempo_por_questao or TEMPO_POR_QUESTAO
        self._token_cronometro = 0
        self._questao_cronometro: str | None = None
        self._cronometro_rodando = False
        self._rodada_finalizada = False
        self._estudo_em_andamento = False
        self.texto_cronometro: ft.Text | None = None
        self.barra_cronometro: ft.ProgressBar | None = None
        self.icone_cronometro: ft.Icon | None = None
        self.narracao_ativa = False
        self._ultima_questao_narrada: str | None = None
        self._processo_narracao: subprocess.Popen[Any] | None = None
        # speech_rate é a taxa de fala usada pelo mecanismo de voz nativo.
        # Use 0.75, 1.0, 1.5 ou 2.0 para definir a velocidade inicial.
        self.speech_rate = 1.0
        # VELOCIDADE INICIAL: troque 1.0 por 0.75, 1.5 ou 2.0 para mudar
        # a velocidade selecionada quando o módulo PRICE / SAF for aberto.

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

    @property
    def tempo_por_questao(self) -> int:
        """Segundos por questão definidos em ACESSIBILIDADE (0 = sem limite)."""
        return rj.tempo_limite(self.estado, TEMPO_POR_QUESTAO)

    def _preparar_nova_partida(self) -> None:
        """Inicia as rodadas sem zerar o saldo acumulado dos jogadores."""
        rj.nova_sessao(self, MODULO_PESQUISA)
        self.jogadores = self.estado.jogadores_ativos()
        # As questões só são sorteadas depois que o usuário escolhe um dos
        # quatro níveis. Isso impede misturar dificuldades na mesma partida.
        self.questoes = []
        self.nivel_selecionado = None
        self.indice_jogador = 0
        self.indice_questao = 0
        self.ultimo_resultado = None
        self._questao_cronometro = None
        self._rodada_finalizada = False
        self._estudo_em_andamento = False
        self._parar_cronometro()
        self._parar_narracao()
        self._historico_telas.clear()
        self.etapa_teoria = 0
        self.pagina_estudo = 0
        # Toda nova partida começa pela escolha entre rever e ir às questões.
        self.tela_atual = "revisao"

    def _rota_atual(self) -> tuple[str, int]:
        """Retorna a tela atual e a etapa da teoria para o histórico."""
        return self.tela_atual, self.etapa_teoria

    def _navegar(
        self,
        destino: str,
        *,
        etapa_teoria: int | None = None,
        registrar: bool = True,
    ) -> None:
        """Troca a tela sem criar Views duplicadas no aplicativo principal."""
        etapa_destino = (
            self.etapa_teoria if etapa_teoria is None else etapa_teoria
        )
        rota_destino = (destino, etapa_destino)
        if rota_destino == self._rota_atual():
            self._renderizar()
            return

        if registrar:
            self._historico_telas.append(self._rota_atual())

        # Ao sair de uma questão para uma tela sem tempo, encerra o ciclo atual.
        # Se o jogador retornar depois, um novo ciclo de 60 segundos será criado.
        telas_com_tempo = {"jogada", "pergunta"}
        if (
            self.tela_atual in telas_com_tempo
            and destino not in telas_com_tempo
        ):
            self._parar_cronometro()
            self._questao_cronometro = None

        self._parar_narracao()
        self._ultima_questao_narrada = None
        self.tela_atual = destino
        self.etapa_teoria = etapa_destino
        self._renderizar()

    async def _voltar_tela(self, evento: ft.ControlEvent) -> None:
        """Desempilha a tela interna anterior ou retorna ao menu principal."""
        if self.tela_atual == "estudo" and self.pagina_estudo > 0:
            self._alterar_pagina_estudo(self.pagina_estudo - 1)
            return
        if self.tela_atual == "estudo":
            # ESTUDAR É DEFINITIVO: o estudo mostra a resposta correta, então
            # não se volta à questão (evita responder depois de ver a resposta).
            self._avisar("Conclua o estudo para passar a vez.")
            return
        if not self._historico_telas:
            await self._voltar_ao_inicio(evento)
            return

        destino, etapa = self._historico_telas.pop()
        self._navegar(
            destino,
            etapa_teoria=etapa,
            registrar=False,
        )

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
            "revisao": self._tela_revisao,
            "teoria": self._tela_teoria,
            "niveis": self._tela_niveis,
            "jogada": self._tela_jogada,
            "pergunta": self._tela_pergunta,
            "estudo": self._tela_estudo,
            "feedback": self._tela_feedback,
            "resultado": self._tela_resultado,
            "erro": self._tela_erro,
        }
        construtor = telas.get(self.tela_atual, self._tela_cadastro)
        try:
            conteudo_tela = construtor()
        except Exception as erro:
            # PROTEÇÃO CONTRA PÁGINA EM BRANCO: se qualquer tela apresentar
            # erro de montagem, mantém o cabeçalho e mostra uma mensagem visível.
            print(
                f"Erro ao renderizar a tela {self.tela_atual!r}: {erro}"
            )
            conteudo_tela = self._tela_erro()
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
                        content=rj.com_transicao(self, conteudo_tela),
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
        rj.sons_nos_botoes(self, self.raiz.content)  # clique em todos os botões
        try:
            self.raiz.update()
        except RuntimeError:
            # Na primeira construção a raiz ainda não foi adicionada à página.
            pass
        except Exception as erro:
            # Se o cliente rejeitar algum controle durante a atualização, troca
            # imediatamente por uma tela de erro; o usuário nunca fica preso em
            # uma página vazia e ainda dispõe de Tela Anterior e Início.
            print(f"Erro ao atualizar a interface: {erro}")
            self.raiz.content = ft.SafeArea(
                content=ft.Column(
                    controls=[
                        self._cabecalho(),
                        ft.Container(
                            content=self._tela_erro(),
                            padding=16,
                        ),
                    ],
                    spacing=2,
                    scroll=ft.ScrollMode.AUTO,
                    expand=True,
                ),
                minimum_padding=ft.Padding.all(6),
            )
            try:
                self.raiz.update()
            except RuntimeError:
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
        # NAVEGAÇÃO GLOBAL: estes dois botões aparecem em todas as telas porque
        # o cabeçalho é criado por _renderizar(), antes do conteúdo específico.
        botao_tela_anterior = ft.OutlinedButton(
            content="TELA ANTERIOR",
            icon=ft.Icons.ARROW_BACK,
            style=ft.ButtonStyle(
                color=tema["texto"],
                side=_lado(tema["primaria"], 1.5),
            ),
            on_click=self._voltar_tela,
        )
        botao_inicio = ft.Button(
            content="INÍCIO",
            icon=ft.Icons.HOME,
            color=tema["fundo_1"],
            bgcolor=tema["destaque"],
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
                    "DESAFIO DO SISTEMA PRICE",
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
                    # LUPA (acessibilidade): liga/desliga a Lupa do Windows.
                    rj.botao_efeitos(self, tema["texto"], tema["primaria"], tema["destaque"], compacto=True),
                    rj.botao_lupa(tema["texto"], tema["primaria"], tema["destaque"], tema["fundo_1"]),
                    botao_tela_anterior,
                    botao_inicio,
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
                ft.DropdownOption(key=str(numero), text="1 jogador" if numero == 1 else f"{numero} jogadores")
                for numero in range(1, 5)
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
                        ft.Icons.SAVINGS,
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
    # Revisão do assunto antes das questões
    # ------------------------------------------------------------------

    def _imagem_teoria(
        self,
        chave: str,
        legenda: str,
        altura: float = 170,
    ) -> ft.Control:
        """Cria uma imagem local da teoria com tratamento visual e acessível."""
        tema = self.tema
        return ft.Container(
            content=ft.Image(
                src=IMAGENS_TEORIA[chave],
                fit=ft.BoxFit.CONTAIN,
                # CONTAIN mostra a imagem inteira dentro do retângulo, sem cortes.
                height=altura,
                width=1200,
                semantics_label=legenda,
                error_content=ft.Column(
                    controls=[
                        ft.Icon(
                            ft.Icons.IMAGE_NOT_SUPPORTED_OUTLINED,
                            color=tema["negativo"],
                            size=42,
                        ),
                        ft.Text(
                            "Imagem não encontrada na pasta assets.",
                            color=tema["suave"],
                            size=11,
                            text_align=ft.TextAlign.CENTER,
                        ),
                    ],
                    spacing=6,
                    alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                ),
            ),
            height=altura,
            padding=6,
            alignment=ft.Alignment.CENTER,
            bgcolor=tema["fundo_1"],
            border=_borda(tema["primaria"], 1.5),
            border_radius=_raio(16),
            clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
        )

    def _tela_revisao(self) -> ft.Control:
        """Pergunta se o jogador deseja estudar a teoria antes do quiz."""
        tema = self.tema
        return ft.Column(
            controls=[
                self._placar(compacto=True),
                ft.Container(
                    content=ft.ResponsiveRow(
                        controls=[
                            ft.Container(
                                content=self._imagem_teoria(
                                    "automovel",
                                    (
                                        "Dinheiro usado para representar "
                                        "empréstimos e investimentos"
                                    ),
                                    300,
                                ),
                                col={"xs": 12, "md": 5},
                            ),
                            ft.Container(
                                content=ft.Column(
                                    controls=[
                                        ft.Icon(
                                            ft.Icons.SAVINGS,
                                            color=tema["destaque"],
                                            size=66,
                                        ),
                                        ft.Text(
                                        "SISTEMA PRICE / SAF",
                                            color=tema["destaque"],
                                            size=34,
                                            weight=ft.FontWeight.BOLD,
                                            text_align=ft.TextAlign.CENTER,
                                        ),
                                        ft.Text(
                                            "Deseja rever o assunto antes de começar?",
                                            color=tema["texto"],
                                            size=24,
                                            weight=ft.FontWeight.BOLD,
                                            text_align=ft.TextAlign.CENTER,
                                        ),
                                        ft.Text(
                                            (
                                                "A revisão apresenta prestações fixas, "
                                                "relação com PG, amortização, juros, "
                                                "saldo devedor e custo total."
                                            ),
                                            color=tema["suave"],
                                            size=17,
                                            text_align=ft.TextAlign.CENTER,
                                        ),
                                        self._controles_narracao(),
                                        ft.ResponsiveRow(
                                            controls=[
                                                ft.Button(
                                                    content="REVER O ASSUNTO",
                                                    icon=ft.Icons.AUTO_STORIES,
                                                    color=tema["fundo_1"],
                                                    bgcolor=tema["primaria"],
                                                    height=58,
                                                    on_click=self._abrir_teoria,
                                                    col={"xs": 12, "sm": 6},
                                                ),
                                                ft.Button(
                                                    content="IR DIRETO ÀS QUESTÕES",
                                                    icon=ft.Icons.PLAY_ARROW,
                                                    color=tema["fundo_1"],
                                                    bgcolor=tema["destaque"],
                                                    height=58,
                                                    on_click=self._ir_para_questoes,
                                                    col={"xs": 12, "sm": 6},
                                                ),
                                            ],
                                            columns=12,
                                            spacing=10,
                                            run_spacing=10,
                                        ),
                                    ],
                                    spacing=13,
                                    horizontal_alignment=(
                                        ft.CrossAxisAlignment.STRETCH
                                    ),
                                ),
                                col={"xs": 12, "md": 7},
                            ),
                        ],
                        columns=12,
                        spacing=18,
                        run_spacing=18,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    padding=22,
                    bgcolor=tema["cartao"],
                    border=_borda(tema["primaria"], 2),
                    border_radius=_raio(24),
                    shadow=_sombra("#55000000", 24, 8),
                ),
            ],
            spacing=14,
        )

    def _passo_teoria(self, numero: int, texto: str) -> ft.Control:
        """Monta uma linha numerada do exemplo exibido na revisão."""
        tema = self.tema
        return ft.Row(
            controls=[
                ft.Container(
                    content=ft.Text(
                        str(numero),
                        color=tema["fundo_1"],
                        size=14,
                        weight=ft.FontWeight.BOLD,
                    ),
                    width=29,
                    height=29,
                    alignment=ft.Alignment.CENTER,
                    bgcolor=tema["destaque"],
                    border_radius=_raio(14),
                ),
                markdown_matematico(
                    texto,
                    cor=tema["texto"],
                    tamanho=15,
                    expandir=True,
                ),
            ],
            spacing=8,
            vertical_alignment=ft.CrossAxisAlignment.START,
        )

    def _tabela_price(self, linhas: list[list[str]]) -> ft.Control:
        """Monta a tabela simplificada de prestação, juros e amortização."""
        tema = self.tema
        cabecalhos = ["MÊS", "PRESTAÇÃO", "JUROS", "AMORTIZAÇÃO", "SALDO"]
        larguras = [54, 122, 104, 126, 122]

        def linha_tabela(
            valores: list[str],
            *,
            cabecalho: bool = False,
        ) -> ft.Control:
            return ft.Row(
                controls=[
                    ft.Container(
                        content=ft.Text(
                            valor,
                            color=(
                                tema["fundo_1"]
                                if cabecalho
                                else tema["texto"]
                            ),
                            size=10,
                            weight=ft.FontWeight.BOLD,
                            text_align=ft.TextAlign.CENTER,
                        ),
                        width=larguras[indice],
                        padding=3,
                        bgcolor=(
                            tema["destaque"]
                            if cabecalho
                            else tema["cartao_2"]
                        ),
                        border=_borda(tema["primaria"], 0.8),
                        border_radius=_raio(7),
                    )
                    for indice, valor in enumerate(valores)
                ],
                spacing=2,
            )

        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[linha_tabela(cabecalhos, cabecalho=True)],
                        scroll=ft.ScrollMode.AUTO,
                    ),
                    *[
                        ft.Row(
                            controls=[linha_tabela(linha)],
                            scroll=ft.ScrollMode.AUTO,
                        )
                        for linha in linhas
                    ],
                ],
                spacing=2,
            ),
            padding=4,
            bgcolor=tema["fundo_1"],
            border=_borda(tema["primaria"], 1.2),
            border_radius=_raio(12),
        )

    def _tela_teoria(self) -> ft.Control:
        """Apresenta uma etapa curta da teoria, evitando uma tela extensa."""
        tema = self.tema
        total_paginas = len(PAGINAS_TEORIA)
        # SEGURANÇA DE RENDERIZAÇÃO: impede um índice inválido de produzir uma
        # página em branco ao avançar ou voltar rapidamente.
        self.etapa_teoria = max(
            0,
            min(self.etapa_teoria, total_paginas - 1),
        )
        pagina = PAGINAS_TEORIA[self.etapa_teoria]
        ultima_pagina = self.etapa_teoria == total_paginas - 1
        icones = [
            ft.Icons.ACCOUNT_BALANCE,
            ft.Icons.FUNCTIONS,
            ft.Icons.TABLE_CHART,
            ft.Icons.COMPARE_ARROWS,
        ]

        painel_texto = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Icon(
                                icones[self.etapa_teoria],
                                color=tema["destaque"],
                                size=29,
                            ),
                            ft.Column(
                                controls=[
                                    ft.Text(
                                        pagina["titulo"],
                                        color=tema["destaque"],
                                        size=23,
                                        weight=ft.FontWeight.BOLD,
                                    ),
                                    ft.Text(
                                        pagina["subtitulo"],
                                        color=tema["primaria"],
                                        size=14,
                                        weight=ft.FontWeight.BOLD,
                                    ),
                                ],
                                spacing=1,
                                expand=True,
                            ),
                        ],
                        spacing=12,
                    ),
                    markdown_matematico(
                        pagina["definicao"],
                        cor=tema["texto"],
                        tamanho=16,
                    ),
                    ft.Container(
                        content=ft.Column(
                            controls=[
                                markdown_matematico(
                                    pagina["formula"],
                                    cor=tema["fundo_1"],
                                    tamanho=20,
                                    peso=ft.FontWeight.BOLD,
                                    alinhamento=ft.MainAxisAlignment.CENTER,
                                    escala_latex=1.10,
                                ),
                                markdown_matematico(
                                    pagina["significados"],
                                    cor=tema["fundo_1"],
                                    tamanho=13,
                                    alinhamento=ft.MainAxisAlignment.CENTER,
                                ),
                            ],
                            spacing=2,
                            horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
                        ),
                        padding=7,
                        bgcolor=tema["destaque"],
                        border_radius=_raio(12),
                    ),
                    ft.Text(
                        pagina["exemplo_titulo"],
                        color=tema["primaria"],
                        size=15,
                        weight=ft.FontWeight.BOLD,
                    ),
                    *(
                        [self._tabela_price(pagina["tabela"])]
                        if pagina.get("tabela")
                        else []
                    ),
                    *[
                        self._passo_teoria(numero, texto)
                        for numero, texto in enumerate(
                            pagina["passos"],
                            start=1,
                        )
                    ],
                    ft.Container(
                        content=markdown_matematico(
                            pagina["aplicacao"],
                            cor=tema["texto"],
                            tamanho=14,
                        ),
                        padding=6,
                        bgcolor=tema["cartao_2"],
                        border=_borda(tema["primaria"]),
                        border_radius=_raio(11),
                    ),
                ],
                spacing=5,
                horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
            ),
            padding=10,
            bgcolor=tema["cartao"],
            border=_borda(tema["primaria"], 2),
            border_radius=_raio(20),
            col={"xs": 12, "md": 7},
        )

        painel_imagem = ft.Container(
            content=ft.Column(
                controls=[
                    self._imagem_teoria(
                        pagina["imagem"],
                        pagina["titulo"],
                        205,
                    ),
                    self._controles_narracao(compacto=True),
                    ft.Text(
                        (
                            f"PARTE {self.etapa_teoria + 1} DE "
                            f"{total_paginas}"
                        ),
                        color=tema["destaque"],
                        size=13,
                        weight=ft.FontWeight.BOLD,
                        text_align=ft.TextAlign.CENTER,
                    ),
                    ft.ProgressBar(
                        value=(self.etapa_teoria + 1) / total_paginas,
                        color=tema["destaque"],
                        bgcolor=tema["cartao_2"],
                        height=8,
                    ),
                ],
                spacing=8,
                horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
            ),
            col={"xs": 12, "md": 5},
        )

        return ft.Column(
            controls=[
                self._placar(compacto=True),
                ft.Text(
                    "REVISÃO DO ASSUNTO",
                    color=tema["destaque"],
                    size=20,
                    weight=ft.FontWeight.BOLD,
                    text_align=ft.TextAlign.CENTER,
                ),
                ft.ResponsiveRow(
                    controls=[painel_imagem, painel_texto],
                    columns=12,
                    spacing=14,
                    run_spacing=14,
                    vertical_alignment=ft.CrossAxisAlignment.START,
                ),
                ft.ResponsiveRow(
                    controls=[
                        ft.OutlinedButton(
                            content="VOLTAR",
                            icon=ft.Icons.ARROW_BACK,
                            style=ft.ButtonStyle(
                                color=tema["texto"],
                                side=_lado(tema["primaria"], 1.5),
                            ),
                            disabled=self.etapa_teoria == 0,
                            height=38,
                            on_click=self._voltar_etapa_teoria,
                            col={"xs": 12, "sm": 6},
                        ),
                        ft.Button(
                            content=(
                                "AVANÇAR PARA AS QUESTÕES"
                                if ultima_pagina
                                else "AVANÇAR"
                            ),
                            icon=(
                                ft.Icons.PLAY_ARROW
                                if ultima_pagina
                                else ft.Icons.ARROW_FORWARD
                            ),
                            color=tema["fundo_1"],
                            bgcolor=tema["destaque"],
                            height=38,
                            on_click=(
                                self._ir_para_questoes
                                if ultima_pagina
                                else self._avancar_teoria
                            ),
                            col={"xs": 12, "sm": 6},
                        ),
                    ],
                    columns=12,
                    spacing=12,
                    run_spacing=12,
                ),
            ],
            # AJUSTE DE ALTURA DA TEORIA: diminua este valor para aproximar os
            # blocos; aumente para criar mais espaço vertical entre eles.
            spacing=7,
        )

    def _abrir_teoria(self, _evento: ft.ControlEvent) -> None:
        self._navegar("teoria", etapa_teoria=0)

    def _avancar_teoria(self, _evento: ft.ControlEvent) -> None:
        """Exibe a próxima parte da teoria e registra a etapa no histórico."""
        proxima = min(self.etapa_teoria + 1, len(PAGINAS_TEORIA) - 1)
        self._navegar("teoria", etapa_teoria=proxima)

    def _voltar_etapa_teoria(self, _evento: ft.ControlEvent) -> None:
        """Retorna uma parte da teoria sem voltar diretamente ao menu."""
        if self.etapa_teoria <= 0:
            return
        anterior = self.etapa_teoria - 1
        # Remove a etapa que foi empilhada pelo botão Avançar, quando presente.
        if self._historico_telas and self._historico_telas[-1] == (
            "teoria",
            anterior,
        ):
            self._historico_telas.pop()
        self._navegar(
            "teoria",
            etapa_teoria=anterior,
            registrar=False,
        )

    def _voltar_para_revisao(self, _evento: ft.ControlEvent) -> None:
        self._navegar("revisao")

    def _ir_para_questoes(self, _evento: ft.ControlEvent) -> None:
        """Abre a escolha de dificuldade antes de iniciar o cronômetro."""
        self._navegar("niveis")

    def _tela_niveis(self) -> ft.Control:
        """Permite escolher um dos quatro blocos de 15 questões PRICE."""
        tema = self.tema
        botoes: list[ft.Control] = []
        for nivel, configuracao in NIVEIS_PRICE.items():
            quantidade = sum(
                1
                for questao in self.questoes_originais
                if questao.get("nivel") == nivel
            )
            cor = tema[str(configuracao["cor"])]
            botoes.append(
                ft.OutlinedButton(
                    content=ft.Row(
                        controls=[
                            ft.Container(
                                content=ft.Icon(
                                    configuracao["icone"],
                                    color=tema["fundo_1"],
                                    size=32,
                                ),
                                width=58,
                                height=58,
                                alignment=ft.Alignment.CENTER,
                                bgcolor=cor,
                                border_radius=_raio(13),
                            ),
                            ft.Column(
                                controls=[
                                    ft.Text(
                                        str(configuracao["rotulo"]),
                                        color=cor,
                                        size=23,
                                        weight=ft.FontWeight.BOLD,
                                    ),
                                    ft.Text(
                                        f"{quantidade} questões",
                                        color=tema["texto"],
                                        size=15,
                                        weight=ft.FontWeight.BOLD,
                                    ),
                                    ft.Text(
                                        str(configuracao["descricao"]),
                                        color=tema["suave"],
                                        size=15,
                                    ),
                                ],
                                spacing=2,
                                expand=True,
                            ),
                            ft.Icon(
                                ft.Icons.ARROW_FORWARD_IOS,
                                color=cor,
                                size=18,
                            ),
                        ],
                        spacing=11,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    style=ft.ButtonStyle(
                        color=tema["texto"],
                        bgcolor=tema["cartao_2"],
                        side=_lado(cor, 2),
                        shape=ft.RoundedRectangleBorder(radius=18),
                        padding=ft.Padding.all(12),
                    ),
                    height=132,
                    on_click=(
                        lambda evento, nivel_escolhido=nivel:
                        self._selecionar_nivel(nivel_escolhido, evento)
                    ),
                    col={"xs": 12, "md": 6},
                    tooltip=(
                        f"Iniciar as {quantidade} questões do nível "
                        f"{configuracao['rotulo']}"
                    ),
                )
            )

        return ft.Column(
            controls=[
                self._placar(compacto=True),
                ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Icon(
                                ft.Icons.TUNE,
                                color=tema["destaque"],
                                size=44,
                            ),
                            ft.Text(
                                "ESCOLHA O NÍVEL DAS QUESTÕES",
                                color=tema["destaque"],
                                size=30,
                                weight=ft.FontWeight.BOLD,
                                text_align=ft.TextAlign.CENTER,
                            ),
                            ft.Text(
                                (
                                    "Cada nível possui 15 questões. A partida "
                                    "apresentará somente a dificuldade escolhida."
                                ),
                                color=tema["texto"],
                                size=17,
                                text_align=ft.TextAlign.CENTER,
                            ),
                            ft.ResponsiveRow(
                                controls=botoes,
                                columns=12,
                                spacing=10,
                                run_spacing=10,
                            ),
                            self._controles_narracao(compacto=True),
                            ft.Text(
                                (
                                    "Você poderá escolher outro nível ao iniciar "
                                    "uma nova partida. A pontuação global será "
                                    "mantida."
                                ),
                                color=tema["suave"],
                                size=14,
                                text_align=ft.TextAlign.CENTER,
                            ),
                        ],
                        spacing=10,
                        horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
                    ),
                    width=1240,
                    padding=ft.Padding.all(16),
                    bgcolor=tema["cartao"],
                    border=_borda(tema["primaria"], 2),
                    border_radius=_raio(24),
                    shadow=_sombra("#55000000", 24, 8),
                    alignment=ft.Alignment.CENTER,
                ),
            ],
            spacing=6,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )

    def _selecionar_nivel(
        self,
        nivel: str,
        _evento: ft.ControlEvent,
    ) -> None:
        """Sorteia apenas as 15 questões da dificuldade escolhida."""
        if nivel not in NIVEIS_PRICE:
            self._avisar("Nível PRICE inválido.")
            return

        questoes_do_nivel = [
            questao
            for questao in self.questoes_originais
            if questao.get("nivel") == nivel
        ]
        if len(questoes_do_nivel) != 15:
            self._avisar(
                f"O nível {nivel} deve possuir exatamente 15 questões."
            )
            return

        self.nivel_selecionado = nivel
        self.questoes = random.sample(
            questoes_do_nivel,
            k=len(questoes_do_nivel),
        )
        if ADMIN_ATIVO:
            # Modo administrador: mantém a ordem do banco de questões.
            self.questoes = list(questoes_do_nivel)
        self.indice_jogador = 0
        self.indice_questao = 0
        self.ultimo_resultado = None
        self._questao_cronometro = None
        self._rodada_finalizada = False
        self._navegar("jogada")

    # ------------------------------------------------------------------
    # Elementos compartilhados durante as rodadas
    # ------------------------------------------------------------------

    def _placar(self, *, compacto: bool = False) -> ft.Control:
        if ADMIN_ATIVO:
            # Modo administrador: saldos de teste ficam ocultos (economiza espaço).
            return ft.Container()
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
            conteudo_cartao: ft.Control
            if compacto:
                conteudo_cartao = ft.Row(
                    controls=[
                        avatar,
                        ft.Column(
                            controls=[
                                ft.Text(
                                    jogador["nome"],
                                    color=tema["texto"],
                                    size=12,
                                    weight=ft.FontWeight.BOLD,
                                ),
                                ft.Text(
                                    "SALDO DAS QUESTÕES" if self.estado.economia_ativa else "PONTUAÇÃO TOTAL",
                                    color=tema["suave"],
                                    size=8,
                                    weight=ft.FontWeight.BOLD,
                                ),
                            ],
                            spacing=0,
                            expand=True,
                        ),
                        rj.texto_saldo(
                            self,
                            jogador,
                            formatar_reais,
                            cor_positiva=tema["positivo"],
                            cor_negativa=tema["negativo"],
                            tamanho=17,
                        ),
                    ],
                    spacing=7,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                )
            else:
                conteudo_cartao = ft.Column(
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
                        ft.Text(
                            "SALDO DAS QUESTÕES" if self.estado.economia_ativa else "PONTUAÇÃO TOTAL",
                            color=tema["suave"],
                            size=9,
                            weight=ft.FontWeight.BOLD,
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
                    spacing=2,
                )

            cartoes.append(
                ft.Container(
                    content=conteudo_cartao,
                    padding=8 if compacto else 12,
                    bgcolor=tema["cartao_2"],
                    border=_borda(
                        tema["destaque"] if ativo else tema["primaria"],
                        2 if ativo else 1,
                    ),
                    border_radius=_raio(12 if compacto else 14),
                    col={"xs": 6, "sm": 3},
                )
            )
        # MODO ECONOMIA: carteira e cofrinho ao lado do saldo.
        et.aplicar_no_placar(self, cartoes, self.jogadores, tema)
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
        configuracao_nivel = NIVEIS_PRICE.get(
            self.nivel_selecionado or "",
            {},
        )
        rotulo_nivel = str(configuracao_nivel.get("rotulo", "PRICE"))
        return ft.Column(
            controls=[
                ft.Row(
                    controls=[
                        ft.Text(
                            f"NÍVEL {rotulo_nivel}  •  RODADA {atual} DE {total}",
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
        telas_com_narracao = {
            "revisao",
            "teoria",
            "niveis",
            "jogada",
            "pergunta",
            "estudo",
        }

        if (
            self.tela_atual in telas_com_tempo
            and self.questoes
            and not self._rodada_finalizada
        ):
            identificador = str(self.questao_atual["id"])
            if identificador != self._questao_cronometro:
                self._iniciar_cronometro(identificador)
        else:
            self._parar_cronometro()

        telas_sem_questao = {"revisao", "teoria", "niveis"}
        if (
            self.tela_atual in telas_com_narracao
            and (self.questoes or self.tela_atual in telas_sem_questao)
        ):
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
        rj.marcar_inicio(self)  # tempo de resposta para a pesquisa
        self.tempo_restante = self.tempo_por_questao or TEMPO_POR_QUESTAO
        self._cronometro_rodando = True
        self._rodada_finalizada = False
        if ADMIN_ATIVO or not self.tempo_por_questao:
            # Modo administrador ou SEM LIMITE DE TEMPO (Acessibilidade):
            # o cronômetro fica desligado.
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
            if getattr(self, "_cofrinho_aberto", False):
                # MODO ECONOMIA: o tempo da questão pausa enquanto o jogador
                # investe no cofrinho durante a sua vez.
                continue
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
                self.texto_cronometro.value = rj.texto_tempo(self)
                self.texto_cronometro.color = cor
                rj.pulsar_cronometro(self)
                self.texto_cronometro.update()
            if self.barra_cronometro is not None:
                self.barra_cronometro.value = (
                    min(1.0, self.tempo_restante / (self.tempo_por_questao or TEMPO_POR_QUESTAO))
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
            tempo_total=self.tempo_por_questao or TEMPO_POR_QUESTAO,
        )
        rj.efeitos(self).tocar(self, "erro")
        self.ultimo_resultado = {
            "acertou": False,
            "resposta": None,
            "variacao": -PENALIDADE_ERRO,
            "tempo_esgotado": True,
        }
        self._navegar("feedback")

    def _controle_cronometro(self, *, compacto: bool = False) -> ft.Control:
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
            rj.texto_tempo(self),
            color=cor,
            size=24,
            weight=ft.FontWeight.BOLD,
            semantics_label=(
                f"{self.tempo_restante} segundos restantes para responder"
            ),
        )
        self.barra_cronometro = ft.ProgressBar(
            value=min(1.0, self.tempo_restante / (self.tempo_por_questao or TEMPO_POR_QUESTAO)),
            bar_height=9,
            color=cor,
            bgcolor=tema["fundo_1"],
            border_radius=5,
            semantics_label="Tempo restante da questão",
            semantics_value=self.tempo_restante,
        )
        if compacto:
            return ft.Container(
                content=ft.Row(
                    controls=[
                        self.icone_cronometro,
                        ft.Text(
                            "TEMPO",
                            color=tema["suave"],
                            size=10,
                            weight=ft.FontWeight.BOLD,
                        ),
                        ft.Container(
                            content=self.barra_cronometro,
                            expand=True,
                        ),
                        self.texto_cronometro,
                    ],
                    spacing=8,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                padding=7,
                bgcolor=tema["cartao_2"],
                border=_borda(cor, 1.3),
                border_radius=_raio(12),
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
                        (
                        "Nos últimos 10 segundos o indicador ficará vermelho."
                        if self.tempo_por_questao
                        else "Sem limite de tempo (opção de Acessibilidade)."
                    ),
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
        if self.tela_atual == "revisao":
            return (
                "Módulo do Sistema Price, ou Sistema de Amortização Francês. "
                "Você deseja rever o assunto ou ir direto para as questões? "
                "Na revisão serão apresentadas as prestações fixas, a relação "
                "com Progressão Geométrica, a tabela de amortização e o custo total."
            )
        if self.tela_atual == "teoria":
            indice = max(
                0,
                min(self.etapa_teoria, len(PAGINAS_TEORIA) - 1),
            )
            # A voz acompanha a paginação: lê somente a parte que está visível.
            return str(PAGINAS_TEORIA[indice]["narracao"])
        if self.tela_atual == "niveis":
            return (
                "Escolha o nível das questões do Sistema Price. "
                "Superfácil, Fácil, Médio ou Difícil. Cada nível possui "
                "quinze questões e a pontuação global será mantida."
            )

        questao = self.questao_atual
        if self.tela_atual == "estudo":
            estudo = questao["estudo"]
            resposta_correta = questao["alternativas"][questao["correta"]]
            total = self._total_paginas_estudo()
            conceito = (
                f"Momento de estudo. {estudo['titulo']}. "
                f"Explicação. {estudo['texto']}. "
                f"Modelo matemático. {estudo['formula']}. "
                f"Exemplo. {estudo['exemplo']}."
            )
            estrategia = (
                "Estratégia e modelo matemático. "
                f"Estratégia. {estudo['texto']}. "
                f"Modelo matemático. {estudo['formula']}."
            )
            calculo = (
                "Cálculo e justificativa. "
                f"{questao['explicacao']}."
            )
            resposta = f"Resposta correta. {resposta_correta}."
            if total == 1:
                return f"{conceito} {estrategia} {calculo} {resposta}"
            if self.pagina_estudo == 0:
                return conceito
            if total == 4:
                if self.pagina_estudo == 1:
                    return estrategia
                if self.pagina_estudo == 2:
                    return calculo
                return resposta
            return f"{estrategia} {calculo} {resposta}"

        texto_questao = (
            f"Questão do Sistema Price. {questao['titulo']}. "
            f"{questao['enunciado']}"
        )

        if self.tela_atual == "pergunta":
            # NARRAÇÃO DAS ALTERNATIVAS: este bloco é executado quando os
            # botões A, B, C, D e E estão visíveis. Para mudar o modo de leitura,
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
        if self.tela_atual == "revisao":
            return "price:revisao"
        if self.tela_atual == "teoria":
            return f"price:teoria:{self.etapa_teoria}"
        if self.tela_atual == "niveis":
            return "price:niveis"
        if self.tela_atual == "estudo":
            alvo = f"estudo:{self.pagina_estudo}"
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
        if (
            not self.questoes
            and self.tela_atual not in {"revisao", "teoria", "niveis"}
        ):
            return False
        identificador = self._chave_da_narracao()
        if not forcar and identificador == self._ultima_questao_narrada:
            return True

        texto = texto_para_narracao(self._texto_da_narracao())
        taxa = self.speech_rate
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
        self.speech_rate = velocidade
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
        elif self.tela_atual == "niveis":
            alvo = "NÍVEIS"
        elif self.tela_atual in {"revisao", "teoria"}:
            alvo = "REVISÃO"
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

    def _controles_narracao(self, *, compacto: bool = False) -> ft.Control:
        """Agrupa o botão de voz e o seletor visual de velocidade."""
        tema = self.tema
        seletor_velocidade = ft.Dropdown(
            value=str(self.speech_rate),
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
        if compacto:
            return ft.ResponsiveRow(
                controls=[
                    ft.Container(
                        content=self._botao_narracao(),
                        col={"xs": 12, "sm": 6},
                    ),
                    ft.Container(
                        content=seletor_velocidade,
                        col={"xs": 12, "sm": 6},
                    ),
                ],
                columns=12,
                spacing=8,
                run_spacing=6,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
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

    def _painel_interacao(self, *, compacto: bool = False) -> ft.Control:
        """Preenche a lateral com mascote, timer e acessibilidade.

        Na tela das alternativas, a versão compacta mantém todos os controles
        existentes sem ocupar a altura necessária às cinco respostas.
        """
        tema = self.tema
        return ft.Container(
            content=ft.Column(
                controls=[
                    # MODO ECONOMIA: na vez do jogador, o cartão MEU COFRINHO ocupa
                    # o lugar do mascote (incentivo ao investimento).
                    *(
                        cofrinho
                        if self.tela_atual == "jogada"
                        and (cofrinho := et.cartao_cofrinho(self, tema))
                        else [
                        self._imagem_mascote(68 if compacto else 140),
                        ft.Text(
                            "MASCOTE FINANCEIRO",
                            color=tema["primaria"],
                            size=11 if compacto else 13,
                            weight=ft.FontWeight.BOLD,
                            text_align=ft.TextAlign.CENTER,
                        ),
                        ]
                    ),
                    self._controle_cronometro(compacto=compacto),
                    self._controles_narracao(),
                    *(
                        []
                        if compacto
                        else [
                            ft.Text(
                                "A narração é opcional e pode ser interrompida a qualquer momento.",
                                color=tema["suave"],
                                size=12,
                                text_align=ft.TextAlign.CENTER,
                            )
                        ]
                    ),
                ],
                spacing=6 if compacto else 7,
                horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
            ),
            padding=8 if compacto else 10,
            bgcolor=tema["cartao"],
            border=_borda(tema["primaria"], 2),
            border_radius=_raio(18),
            col={"xs": 12, "lg": 3},
        )

    def _area_questao(self, mostrar_alternativas: bool) -> ft.Control:
        """Organiza todo o conteúdo da questão em uma única tela.

        A etapa de escolha usa três áreas lado a lado no computador: contexto,
        alternativas e controles. Em janelas estreitas, a quebra responsiva e
        a rolagem da página continuam garantindo acesso integral ao conteúdo.
        """
        if mostrar_alternativas:
            ajudas = et.barra_ajudas(self, self.tema)
            recursos = ft.Container(
                content=ft.ResponsiveRow(
                    controls=[
                        ft.Container(
                            content=self._controle_cronometro(compacto=True),
                            col={"xs": 12, "md": 4 if ajudas else 6},
                        ),
                        ft.Container(
                            content=self._controles_narracao(compacto=True),
                            col={"xs": 12, "md": 3 if ajudas else 6},
                        ),
                        # MODO ECONOMIA: ajudas compradas com a carteira.
                        *[ft.Container(content=a, col={"xs": 12, "md": 5}) for a in ajudas],
                    ],
                    columns=12,
                    spacing=10,
                    run_spacing=8,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                padding=6,
                bgcolor=self.tema["cartao"],
                border=_borda(self.tema["primaria"], 1.5),
                border_radius=_raio(15),
            )
            if self.questao_atual["nivel"] == "Difícil":
                conteudo: ft.Control = ft.Column(
                    controls=[
                        self._cartao_contexto_dificil(),
                        self._painel_alternativas(),
                    ],
                    spacing=8,
                    horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
                )
            else:
                conteudo = ft.ResponsiveRow(
                    controls=[
                        ft.Container(
                            content=self._cartao_contexto_questao(compacto=True),
                            col={"xs": 12, "lg": 4},
                        ),
                        ft.Container(
                            content=self._painel_alternativas(),
                            col={"xs": 12, "lg": 8},
                        ),
                    ],
                    columns=12,
                    spacing=10,
                    run_spacing=10,
                    vertical_alignment=ft.CrossAxisAlignment.START,
                )
            return ft.Column(
                controls=[recursos, conteudo],
                spacing=7,
                horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
            )

        return ft.ResponsiveRow(
            controls=[
                ft.Container(
                    content=self._cartao_questao(False),
                    col={"xs": 12, "lg": 9},
                ),
                self._painel_interacao(compacto=True),
            ],
            columns=12,
            spacing=14,
            run_spacing=14,
            vertical_alignment=ft.CrossAxisAlignment.START,
        )

    @staticmethod
    def _segmentar_alternativa(
        texto: str,
    ) -> list[tuple[str, str]]:
        """Separa texto comum e blocos LaTeX sem confundir o cifrão."""
        segmentos: list[tuple[str, str]] = []
        cursor = 0
        for correspondencia in PADRAO_BLOCO_MATEMATICO.finditer(str(texto)):
            if correspondencia.start() > cursor:
                segmentos.append(
                    ("texto", str(texto)[cursor : correspondencia.start()])
                )
            formula = (
                correspondencia.group(1)
                if correspondencia.group(1) is not None
                else correspondencia.group(2)
            )
            segmentos.append(("formula", formula or ""))
            cursor = correspondencia.end()
        if cursor < len(str(texto)):
            segmentos.append(("texto", str(texto)[cursor:]))
        return segmentos

    @staticmethod
    def _numero_latex_para_texto(numero: str) -> str:
        """Converte ``1{.}234{,}56`` para ``1.234,56`` fora do LaTeX."""
        return (
            str(numero)
            .replace("{.}", ".")
            .replace("{,}", ",")
            .replace("{", "")
            .replace("}", "")
        )

    def _controles_formula_alternativa(
        self,
        formula: str,
        *,
        tamanho: float,
    ) -> list[ft.Control]:
        """Renderiza fórmula e moeda separadamente para proteger o LaTeX."""
        tema = self.tema
        controles: list[ft.Control] = []
        cursor = 0
        for correspondencia in PADRAO_MOEDA_LATEX.finditer(formula):
            trecho = formula[cursor : correspondencia.start()].strip()
            if trecho:
                controles.append(
                    ft.Container(
                        content=markdown_matematico(
                            f"$${trecho}$$",
                            cor=tema["texto"],
                            tamanho=tamanho,
                            peso=ft.FontWeight.W_600,
                            alinhamento=ft.MainAxisAlignment.CENTER,
                            escala_latex=1.0,
                        ),
                        padding=ft.Padding.symmetric(vertical=4),
                        alignment=ft.Alignment.CENTER,
                    )
                )
            controles.append(
                ft.Text(
                    "R$ "
                    + self._numero_latex_para_texto(
                        correspondencia.group(1)
                    ),
                    color=tema["texto"],
                    size=tamanho,
                    weight=ft.FontWeight.W_600,
                )
            )
            cursor = correspondencia.end()

        trecho_final = formula[cursor:].strip()
        if trecho_final:
            controles.append(
                ft.Container(
                    content=markdown_matematico(
                        f"$${trecho_final}$$",
                        cor=tema["texto"],
                        tamanho=tamanho,
                        peso=ft.FontWeight.W_600,
                        alinhamento=ft.MainAxisAlignment.CENTER,
                        escala_latex=1.0,
                    ),
                    padding=ft.Padding.symmetric(vertical=4),
                    alignment=ft.Alignment.CENTER,
                )
            )
        return controles

    @staticmethod
    def _dividir_explicacao_alternativa(
        segmentos: list[tuple[str, str]],
    ) -> tuple[list[tuple[str, str]], list[tuple[str, str]]]:
        """Mantém todas as fórmulas juntas e separa a interpretação final.

        Questões avançadas podem apresentar quatro expressões separadas por
        ponto e vírgula. A versão anterior quebrava após a primeira expressão,
        misturando o restante da fórmula com a explicação. O corte agora ocorre
        somente depois do último bloco matemático.
        """
        indices_formula = [
            indice
            for indice, (tipo, _valor) in enumerate(segmentos)
            if tipo == "formula"
        ]
        if not indices_formula:
            return segmentos, []

        ultimo = indices_formula[-1]
        principal = list(segmentos[: ultimo + 1])
        explicacao: list[tuple[str, str]] = []
        for tipo, valor in segmentos[ultimo + 1 :]:
            if tipo == "texto":
                valor = valor.lstrip(" \t\r\n;,.:-")
            if valor.strip():
                explicacao.append((tipo, valor))
        return principal, explicacao

    def _linha_segmentada_alternativa(
        self,
        segmentos: list[tuple[str, str]],
        *,
        tamanho: float,
        justificar_texto: bool = False,
    ) -> ft.Control:
        """Monta uma linha flexível sem juntar texto comum aos comandos LaTeX."""
        tema = self.tema
        if all(tipo == "texto" for tipo, _ in segmentos):
            texto = " ".join(
                valor.strip()
                for _, valor in segmentos
                if valor.strip()
            )
            return markdown_matematico(
                texto,
                cor=(
                    tema["suave"]
                    if justificar_texto
                    else tema["texto"]
                ),
                tamanho=tamanho,
                peso=ft.FontWeight.W_500,
                expandir=True,
            )

        formulas = [valor for tipo, valor in segmentos if tipo == "formula"]
        textos = [
            re.sub(r"\s+", " ", valor)
            .replace(r"R\$", "R$")
            .lstrip(" \t\r\n;,.:-")
            .strip()
            for tipo, valor in segmentos
            if tipo == "texto"
            and valor.strip(" \t\r\n;,.:-")
        ]

        blocos_formula: list[ft.Control] = []
        for formula in formulas:
            tamanho_formula = (
                10.5
                if (
                    self.questao_atual["nivel"] == "Difícil"
                    and len(formula) > 35
                )
                else tamanho
            )
            blocos_formula.append(
                ft.Container(
                    content=ft.Row(
                        controls=self._controles_formula_alternativa(
                            formula,
                            tamanho=tamanho_formula,
                        ),
                        spacing=5,
                        run_spacing=4,
                        wrap=True,
                        alignment=ft.MainAxisAlignment.CENTER,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    padding=ft.Padding.symmetric(horizontal=3, vertical=2),
                    alignment=ft.Alignment.CENTER,
                )
            )

        if len(blocos_formula) >= 3:
            area_formula: ft.Control = ft.ResponsiveRow(
                controls=[
                    ft.Container(
                        content=bloco,
                        col={"xs": 12, "sm": 6},
                    )
                    for bloco in blocos_formula
                ],
                columns=12,
                spacing=4,
                run_spacing=2,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            )
        else:
            area_formula = ft.Column(
                controls=blocos_formula,
                spacing=2,
                horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
            )

        controles_finais: list[ft.Control] = [area_formula]
        controles_finais.extend(
            markdown_matematico(
                texto,
                cor=tema["texto"],
                tamanho=tamanho,
                peso=ft.FontWeight.W_500,
            )
            for texto in textos
        )
        return ft.Column(
            controls=controles_finais,
            spacing=3,
            horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
        )

    def _conteudo_alternativa_price(
        self,
        alternativa: str,
        *,
        tamanho: float = 17,
    ) -> ft.Control:
        """Cria o conteúdo profissional usado na questão, estudo e feedback."""
        segmentos = self._segmentar_alternativa(alternativa)
        principal, explicacao = self._dividir_explicacao_alternativa(segmentos)
        controles: list[ft.Control] = [
            self._linha_segmentada_alternativa(
                principal,
                tamanho=tamanho,
            )
        ]
        if explicacao:
            controles.extend(
                [
                    ft.Divider(height=1, color=self.tema["primaria"]),
                    self._linha_segmentada_alternativa(
                        explicacao,
                        tamanho=max(15, tamanho - 1),
                        justificar_texto=True,
                    ),
                ]
            )
        return ft.Column(
            controls=controles,
            spacing=8,
            horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
        )

    def _explicacao_em_ordem(
        self,
        texto: str,
        *,
        tamanho: float = 15,
    ) -> ft.Control:
        """Mostra frases e fórmulas de destaque na ordem em que foram escritas.

        Usada nas resoluções ("Calcule e justifique" e "Justificativa"), em
        que cada frase apresenta a fórmula seguinte. Fórmulas em $$...$$ ficam
        centralizadas em linha própria; fórmulas curtas em $...$ permanecem
        dentro da frase.
        """
        tema = self.tema
        controles: list[ft.Control] = []
        cursor = 0
        texto = str(texto)
        for bloco in re.finditer(r"(?<!\\)\$\$((?:\\.|(?!\$\$)[\s\S])*)(?<!\\)\$\$", texto):
            frase = texto[cursor : bloco.start()].strip()
            if frase:
                controles.append(
                    markdown_matematico(
                        frase,
                        cor=tema["texto"],
                        tamanho=tamanho,
                        peso=ft.FontWeight.W_500,
                    )
                )
            formula = bloco.group(1).strip()
            # TAMANHO DAS FÓRMULAS LONGAS: aumente 12 para ampliá-las; valores
            # muito altos podem ultrapassar a largura do cartão.
            tamanho_formula = 12 if len(formula) > 45 else tamanho
            controles.append(
                ft.Container(
                    content=ft.Row(
                        controls=self._controles_formula_alternativa(
                            formula,
                            tamanho=tamanho_formula,
                        ),
                        spacing=5,
                        run_spacing=4,
                        wrap=True,
                        alignment=ft.MainAxisAlignment.CENTER,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    alignment=ft.Alignment.CENTER,
                )
            )
            cursor = bloco.end()
        final = texto[cursor:].strip()
        if final:
            controles.append(
                markdown_matematico(
                    final,
                    cor=tema["texto"],
                    tamanho=tamanho,
                    peso=ft.FontWeight.W_500,
                )
            )
        return ft.Column(
            controls=controles,
            spacing=4,
            horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
        )

    def _identificacao_questao(self) -> ft.Control:
        """Exibe número e nível sem depender do texto do enunciado."""
        tema = self.tema
        questao = self.questao_atual
        numero = str(questao["id"]).removeprefix("PRI").lstrip("0") or "0"
        configuracao = NIVEIS_PRICE.get(str(questao["nivel"]), {})
        rotulo = str(configuracao.get("rotulo", questao["nivel"]))
        return ft.Row(
            controls=[
                ft.Container(
                    content=ft.Text(
                        f"QUESTÃO {numero}",
                        color=tema["fundo_1"],
                        size=12,
                        weight=ft.FontWeight.BOLD,
                    ),
                    padding=ft.Padding.symmetric(horizontal=10, vertical=6),
                    bgcolor=tema["destaque"],
                    border_radius=_raio(10),
                ),
                ft.Container(
                    content=ft.Text(
                        f"NÍVEL {rotulo}",
                        color=tema["fundo_1"],
                        size=12,
                        weight=ft.FontWeight.BOLD,
                    ),
                    padding=ft.Padding.symmetric(horizontal=10, vertical=6),
                    bgcolor=tema["primaria"],
                    border_radius=_raio(10),
                ),
            ],
            spacing=8,
            wrap=True,
        )

    def _imagem_questao(self, altura: float) -> ft.Control:
        tema = self.tema
        questao = self.questao_atual
        produto = str(questao["titulo"]).split(" - ", 1)[-1]
        return ft.Container(
            content=ft.Image(
                src=questao["imagem"],
                fit=ft.BoxFit.CONTAIN,
                # CONTAIN mostra a imagem inteira dentro do retângulo, sem cortes.
                border_radius=_raio(10),
                semantics_label=f"Imagem ilustrativa: {produto}",
                error_content=ft.Icon(
                    ft.Icons.BROKEN_IMAGE,
                    color=tema["negativo"],
                    size=56,
                ),
            ),
            height=altura,
            padding=6,
            alignment=ft.Alignment.CENTER,
            bgcolor=tema["fundo_1"],
            border=_borda(tema["primaria"], 1.5),
            border_radius=_raio(16),
            clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
        )

    def _cartao_contexto_questao(self, *, compacto: bool) -> ft.Control:
        """Monta número, nível, imagem e enunciado em um cartão legível."""
        tema = self.tema
        questao = self.questao_atual
        # TAMANHO DO ENUNCIADO: maior na tela de situação (compacto=False),
        # que tem mais espaço; um pouco menor ao lado das alternativas.
        tamanho_enunciado = (
            (19 if questao["nivel"] in {"Super fácil", "Fácil"} else 18)
            if compacto
            else (23 if questao["nivel"] in {"Super fácil", "Fácil"} else 21)
        )
        if questao["nivel"] == "Difícil":
            altura_imagem = 105
        elif questao["nivel"] == "Médio":
            altura_imagem = 150
        else:
            altura_imagem = 175
        produto = str(questao["titulo"]).split(" - ", 1)[-1]
        return ft.Container(
            content=ft.Column(
                controls=[
                    self._identificacao_questao(),
                    ft.Text(
                        produto.upper(),
                        color=tema["primaria"],
                        size=17,
                        weight=ft.FontWeight.BOLD,
                    ),
                    self._imagem_questao(altura_imagem if compacto else 245),
                    markdown_matematico(
                        str(questao["enunciado"]),
                        cor=tema["texto"],
                        tamanho=tamanho_enunciado,
                        peso=ft.FontWeight.W_600,
                        escala_latex=1.02,
                    ),
                ],
                spacing=9,
                horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
            ),
            padding=12 if compacto else 18,
            bgcolor=tema["cartao"],
            border=_borda(tema["primaria"], 2),
            border_radius=_raio(18),
        )

    def _cartao_contexto_dificil(self) -> ft.Control:
        """Usa a largura da tela para manter enunciados avançados sem rolagem."""
        tema = self.tema
        questao = self.questao_atual
        produto = str(questao["titulo"]).split(" - ", 1)[-1]
        return ft.Container(
            content=ft.ResponsiveRow(
                controls=[
                    ft.Container(
                        content=ft.Column(
                            controls=[
                                self._identificacao_questao(),
                                self._imagem_questao(92),
                            ],
                            spacing=7,
                            horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
                        ),
                        col={"xs": 12, "md": 3},
                    ),
                    ft.Container(
                        content=ft.Column(
                            controls=[
                                ft.Text(
                                    produto.upper(),
                                    color=tema["primaria"],
                                    size=14,
                                    weight=ft.FontWeight.BOLD,
                                ),
                                markdown_matematico(
                                    str(questao["enunciado"]),
                                    cor=tema["texto"],
                                    tamanho=14.5,
                                    peso=ft.FontWeight.W_600,
                                    alinhamento=ft.MainAxisAlignment.START,
                                    escala_latex=1.0,
                                ),
                            ],
                            spacing=5,
                            alignment=ft.MainAxisAlignment.CENTER,
                            horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
                        ),
                        col={"xs": 12, "md": 9},
                    ),
                ],
                columns=12,
                spacing=10,
                run_spacing=8,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=10,
            bgcolor=tema["cartao"],
            border=_borda(tema["primaria"], 1.6),
            border_radius=_raio(16),
        )

    def _painel_alternativas(self) -> ft.Control:
        """Exibe A a E em grade, com fórmula e explicação em áreas próprias."""
        tema = self.tema
        questao = self.questao_atual
        letras = "ABCDE"
        botoes: list[ft.Control] = []
        nivel_dificil = questao["nivel"] == "Difícil"
        for indice, alternativa in enumerate(questao["alternativas"]):
            texto_alternativa = str(alternativa)
            # TAMANHO DAS LETRAS DAS ALTERNATIVAS (PRICE). O Difícil mantém cinco
            # colunas por causa das fórmulas longas da carência.
            tamanho = (
                13.5
                if nivel_dificil
                else 17
                if len(texto_alternativa) > 180
                else 19
                if len(texto_alternativa) > 90
                else 22
            )
            destaque = rj.cores_alternativa(self, indice, tema) or (
                tema["cartao_2"], tema["primaria"], 1.4
            )
            botoes.append(
                ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Row(
                                controls=[
                                    ft.Container(
                                        content=ft.Text(
                                            letras[indice],
                                            color=tema["fundo_1"],
                                            size=14 if nivel_dificil else 16,
                                            weight=ft.FontWeight.BOLD,
                                        ),
                                        width=28 if nivel_dificil else 32,
                                        height=28 if nivel_dificil else 32,
                                        alignment=ft.Alignment.CENTER,
                                        bgcolor=tema["primaria"],
                                        border_radius=_raio(10),
                                    ),
                                    ft.Text(
                                        rj.rotulo_alternativa(self, indice) + f"ALTERNATIVA {letras[indice]}",
                                        color=tema["primaria"],
                                        size=10 if nivel_dificil else 11,
                                        weight=ft.FontWeight.BOLD,
                                    ),
                                ],
                                spacing=8,
                                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                            ),
                            self._conteudo_alternativa_price(
                                texto_alternativa,
                                tamanho=tamanho,
                            ),
                        ],
                        spacing=3 if nivel_dificil else 5,
                        horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
                    ),
                    padding=ft.Padding.symmetric(
                        horizontal=6 if nivel_dificil else 11,
                        vertical=5 if nivel_dificil else 13,
                    ),
                    bgcolor=destaque[0],
                    border=_borda(destaque[1], destaque[2]),
                    border_radius=_raio(15),
                    ink=True,
                    ink_color="#2259F4FF",
                    on_click=lambda evento, resposta=indice: self._responder(
                        resposta,
                        evento,
                    ),
                    col=(
                        {
                            "xs": 12,
                            "sm": 6,
                            "lg": 2.4,
                        }
                        if nivel_dificil
                        else {
                            "xs": 12,
                            "sm": 12 if indice == 4 else 6,
                        }
                    ),
                    tooltip=f"Selecionar alternativa {letras[indice]}",
                )
            )

        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text(
                        "ESCOLHA UMA ALTERNATIVA",
                        color=tema["destaque"],
                        size=16,
                        weight=ft.FontWeight.BOLD,
                        text_align=ft.TextAlign.CENTER,
                    ),
                    ft.ResponsiveRow(
                        controls=[rj.vibrar_se_acertou(self, i, b) for i, b in enumerate(et.marcadas(self, botoes))],
                        columns=12,
                        spacing=8,
                        run_spacing=8,
                    ),
                ],
                spacing=9,
                horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
            ),
            padding=10,
            bgcolor=tema["cartao"],
            border=_borda(tema["destaque"], 2),
            border_radius=_raio(18),
        )

    def _cartao_questao(self, mostrar_alternativas: bool) -> ft.Control:
        """Mantém compatibilidade com os testes e com a tela inicial da rodada."""
        if mostrar_alternativas:
            return ft.ResponsiveRow(
                controls=[
                    ft.Container(
                        content=self._cartao_contexto_questao(compacto=True),
                        col={"xs": 12, "md": 5},
                    ),
                    ft.Container(
                        content=self._painel_alternativas(),
                        col={"xs": 12, "md": 7},
                    ),
                ],
                columns=12,
                spacing=12,
                run_spacing=12,
                vertical_alignment=ft.CrossAxisAlignment.START,
            )

        tema = self.tema
        questao = self.questao_atual
        produto = str(questao["titulo"]).split(" - ", 1)[-1]
        imagem = ft.Container(
            content=self._imagem_questao(330),
            col={"xs": 12, "md": 5},
        )
        texto = ft.Container(
            content=ft.Column(
                controls=[
                    self._identificacao_questao(),
                    ft.Text(
                        produto.upper(),
                        color=tema["primaria"],
                        size=21,
                        weight=ft.FontWeight.BOLD,
                    ),
                    markdown_matematico(
                        str(questao["enunciado"]),
                        cor=tema["texto"],
                        # Enunciado na tela de situação: o Difícil tem textos
                        # longos e usa letra menor para os botões caberem.
                        tamanho=(
                            24
                            if questao["nivel"] in {"Super fácil", "Fácil"}
                            else 21
                            if questao["nivel"] == "Médio"
                            else 18
                        ),
                        peso=ft.FontWeight.W_600,
                        alinhamento=(
                            ft.MainAxisAlignment.START
                            if questao["nivel"] == "Difícil"
                            else ft.MainAxisAlignment.SPACE_BETWEEN
                        ),
                        escala_latex=1.02,
                    ),
                ],
                spacing=11,
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
            ),
            padding=18,
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
            vertical_alignment=ft.CrossAxisAlignment.START,
        )

    # ------------------------------------------------------------------
    # Jogada, resposta, estudo e feedback
    # ------------------------------------------------------------------

    def _tela_jogada(self) -> ft.Control:
        tema = self.tema
        investir = et.botao_investir(self, tema)
        return ft.Column(
            controls=[
                self._placar(compacto=True),
                self._progresso(),
                self._area_questao(mostrar_alternativas=False),
                ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Text(
                                f"{self.jogador_atual['nome']}, qual é sua escolha?",
                                color=tema["texto"],
                                size=21,
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
                                        height=52,
                                        # ALTURA DO BOTÃO RESPONDER: altere
                                        # 46 para aumentar ou diminuir.
                                        on_click=self._escolher_responder,
                                        col={"xs": 12, "sm": 4 if investir else 6},
                                    ),
                                    ft.Button(
                                        content="ESTUDAR",
                                        icon=ft.Icons.MENU_BOOK,
                                        color=tema["fundo_1"],
                                        bgcolor=tema["primaria"],
                                        height=52,
                                        # ALTURA DO BOTÃO ESTUDAR: altere
                                        # 46 para aumentar ou diminuir.
                                        on_click=self._escolher_estudar,
                                        col={"xs": 12, "sm": 4 if investir else 6},
                                    ),
                                        *investir,
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
                                size=14,
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
        self._navegar("pergunta")

    def _escolher_estudar(self, _evento: ft.ControlEvent) -> None:
        if self._rodada_finalizada:
            return
        self._rodada_finalizada = True
        self.pagina_estudo = 0
        self._estudo_em_andamento = True
        self._navegar("estudo")

    def _concluir_estudo(self, _evento: ft.ControlEvent) -> None:
        """Registra uma única vez o estudo e passa a vez."""
        if not self._estudo_em_andamento:
            return
        self.estado.registrar_resultado(
            str(self.jogador_atual["id"]),
            "estudo",
        )
        rj.registrar_resposta(
            self,
            MODULO_PESQUISA,
            "estudo",
            tempo_total=None,
        )
        self._estudo_em_andamento = False
        self._proxima_rodada(_evento)

    def _tela_pergunta(self) -> ft.Control:
        return ft.Column(
            controls=[
                self._placar(compacto=True),
                self._progresso(),
                self._area_questao(mostrar_alternativas=True),
            ],
            spacing=7,
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
            tempo_total=self.tempo_por_questao or TEMPO_POR_QUESTAO,
        )
        self._parar_cronometro()
        # DESTAQUE: a alternativa escolhida fica verde/vermelha por alguns
        # instantes (recursos_jogo.ESPERA_DESTAQUE) antes da resolução.
        indice_questao = self.indice_questao

        def abrir_resolucao() -> None:
            if self.tela_atual == "pergunta" and self.indice_questao == indice_questao:
                self._navegar("feedback")
        rj.iniciar_destaque(self, indice_resposta, int(questao["correta"]), abrir_resolucao)
        self._renderizar()

    def _cartao_exemplo_estudo(
        self,
        titulo: str,
        texto: str,
    ) -> ft.Control:
        tema = self.tema
        texto_seguro = PADRAO_MOEDA_LATEX.sub(
            lambda correspondencia: (
                correspondencia.group(1) + r"\,\text{ reais}"
            ),
            str(texto),
        )
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text(
                        titulo,
                        color=tema["primaria"],
                        size=12 + self._extra_estudo(),
                        weight=ft.FontWeight.BOLD,
                    ),
                    markdown_matematico(
                        texto_seguro,
                        cor=tema["texto"],
                        tamanho=15 + self._extra_estudo(),
                        alinhamento=ft.MainAxisAlignment.START,
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
        texto: str | None = None,
        *,
        conteudo: ft.Control | None = None,
    ) -> ft.Control:
        tema = self.tema
        conteudo_passo = conteudo or markdown_matematico(
            texto or "",
            cor=tema["texto"],
            tamanho=15 + self._extra_estudo(),
            expandir=True,
        )
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
                        size=13 + self._extra_estudo(),
                        weight=ft.FontWeight.BOLD,
                        ),
                        conteudo_passo,
                    ],
                    spacing=2,
                    expand=True,
                ),
            ],
            spacing=10,
            vertical_alignment=ft.CrossAxisAlignment.START,
        )

    def _extra_estudo(self) -> int:
        """Pontos a somar às letras do estudo conforme o espaço da página.

        Super fácil e Fácil mostram tudo em uma página (+1). No Médio e no
        Difícil o conteúdo é dividido em páginas, que têm mais espaço (+3).
        """
        return 1 if self._total_paginas_estudo() == 1 else 3

    def _total_paginas_estudo(self) -> int:
        """Dimensiona o estudo sem comprimir textos ou criar rolagem vertical."""
        nivel = self.questao_atual["nivel"]
        if nivel in {"Super fácil", "Fácil"}:
            return 1
        if nivel == "Médio":
            return 2
        return 4

    def _alterar_pagina_estudo(self, pagina: int) -> None:
        total = self._total_paginas_estudo()
        nova_pagina = max(0, min(int(pagina), total - 1))
        if nova_pagina == self.pagina_estudo:
            return
        self._parar_narracao()
        self._ultima_questao_narrada = None
        self.pagina_estudo = nova_pagina
        self._renderizar()

    def _avancar_pagina_estudo(self, _evento: ft.ControlEvent) -> None:
        self._alterar_pagina_estudo(self.pagina_estudo + 1)

    def _voltar_pagina_estudo(self, _evento: ft.ControlEvent) -> None:
        self._alterar_pagina_estudo(self.pagina_estudo - 1)

    def _bloco_conceito_estudo(self) -> ft.Control:
        """Apresenta apenas o conteúdo externo vinculado à questão."""
        tema = self.tema
        estudo = self.questao_atual["estudo"]
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text(
                        estudo["titulo"],
                        color=tema["primaria"],
                        size=20 + self._extra_estudo(),
                        weight=ft.FontWeight.BOLD,
                        text_align=ft.TextAlign.CENTER,
                    ),
                    markdown_matematico(
                        estudo["texto"],
                        cor=tema["texto"],
                        tamanho=16 + self._extra_estudo(),
                    ),
                    ft.Container(
                        content=markdown_matematico(
                            estudo["formula"],
                            cor=tema["fundo_1"],
                            tamanho=18 + self._extra_estudo(),
                            peso=ft.FontWeight.BOLD,
                            alinhamento=ft.MainAxisAlignment.CENTER,
                            escala_latex=1.08,
                        ),
                        padding=10,
                        bgcolor=tema["destaque"],
                        border_radius=_raio(13),
                    ),
                    self._cartao_exemplo_estudo(
                        "EXEMPLO CURTO",
                        estudo["exemplo"],
                    ),
                ],
                spacing=9,
                horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
            ),
            padding=14,
            bgcolor=tema["cartao_2"],
            border=_borda(tema["primaria"], 1.5),
            border_radius=_raio(16),
        )

    def _bloco_resolucao_estudo(
        self,
        passos: tuple[int, ...] = (1, 2, 3, 4),
    ) -> ft.Control:
        """Apresenta somente os passos previstos para a página atual."""
        tema = self.tema
        questao = self.questao_atual
        estudo = questao["estudo"]
        resposta_correta = questao["alternativas"][questao["correta"]]
        todos_passos = {
            1: self._passo_resolucao(
                1,
                "IDENTIFIQUE A ESTRATÉGIA",
                estudo["texto"],
            ),
            2: self._passo_resolucao(
                2,
                "MONTE O MODELO MATEMÁTICO",
                estudo["formula"],
            ),
            3: self._passo_resolucao(
                3,
                "CALCULE E JUSTIFIQUE",
                conteudo=self._explicacao_em_ordem(
                    str(questao["explicacao"]),
                    tamanho=15 + self._extra_estudo(),
                ),
            ),
            4: self._passo_resolucao(
                4,
                "CONFIRA A RESPOSTA",
                conteudo=self._conteudo_alternativa_price(
                    str(resposta_correta),
                    tamanho=15 + self._extra_estudo(),
                ),
            ),
        }
        titulo = (
            "ESTRATÉGIA E MODELO MATEMÁTICO"
            if passos == (1, 2)
            else "CÁLCULO E JUSTIFICATIVA"
            if passos == (3,)
            else "RESPOSTA CORRETA"
            if passos == (4,)
            else "CÁLCULO E RESPOSTA"
            if passos == (3, 4)
            else "RESOLUÇÃO PASSO A PASSO"
        )
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text(
                        titulo,
                        color=tema["destaque"],
                        size=18,
                        weight=ft.FontWeight.BOLD,
                        text_align=ft.TextAlign.CENTER,
                    ),
                    *[
                        todos_passos[numero]
                        for numero in passos
                        if numero in todos_passos
                    ],
                ],
                spacing=9,
                horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
            ),
            padding=14,
            bgcolor=tema["cartao_2"],
            border=_borda(tema["destaque"], 1.5),
            border_radius=_raio(16),
        )

    def _painel_estudo_detalhado(self) -> ft.Control:
        """Compatibilidade com o validador e testes isolados do módulo."""
        return ft.Column(
            controls=[
                self._bloco_conceito_estudo(),
                self._bloco_resolucao_estudo(),
            ],
            spacing=10,
        )

    def _conteudo_pagina_estudo(self) -> ft.Control:
        """Distribui cada página em colunas equivalentes às usadas em Juros."""
        total = self._total_paginas_estudo()
        if total == 1:
            return ft.ResponsiveRow(
                controls=[
                    ft.Container(
                        content=self._bloco_conceito_estudo(),
                        col={"xs": 12, "lg": 6},
                    ),
                    ft.Container(
                        content=self._bloco_resolucao_estudo(),
                        col={"xs": 12, "lg": 6},
                    ),
                ],
                columns=12,
                spacing=12,
                run_spacing=12,
                vertical_alignment=ft.CrossAxisAlignment.START,
            )

        if self.pagina_estudo == 0:
            return ft.ResponsiveRow(
                controls=[
                    ft.Container(
                        content=self._bloco_conceito_estudo(),
                        col={"xs": 12, "lg": 8},
                    ),
                    ft.Container(
                        content=ft.Column(
                            controls=[
                                self._imagem_questao(170),
                                ft.Text(
                                    "Leia o conceito e observe o modelo matemático antes de avançar.",
                                    color=self.tema["suave"],
                                    size=13,
                                    text_align=ft.TextAlign.CENTER,
                                ),
                            ],
                            spacing=10,
                        ),
                        col={"xs": 12, "lg": 4},
                    ),
                ],
                columns=12,
                spacing=12,
                run_spacing=12,
                vertical_alignment=ft.CrossAxisAlignment.START,
            )

        if total == 4:
            if self.pagina_estudo == 1:
                return self._bloco_resolucao_estudo((1, 2))
            if self.pagina_estudo == 2:
                return self._bloco_resolucao_estudo((3,))
            return self._bloco_resolucao_estudo((4,))

        return self._bloco_resolucao_estudo()

    def _tela_estudo(self) -> ft.Control:
        tema = self.tema
        total = self._total_paginas_estudo()
        self.pagina_estudo = max(0, min(self.pagina_estudo, total - 1))
        ultima_pagina = self.pagina_estudo == total - 1

        return ft.Column(
            controls=[
                self._placar(compacto=True),
                self._progresso(),
                ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.ResponsiveRow(
                                controls=[
                                    ft.Row(
                                        controls=[
                                            ft.Icon(
                                                ft.Icons.AUTO_STORIES,
                                                color=tema["destaque"],
                                                size=32,
                                            ),
                                            ft.Column(
                                                controls=[
                                                    ft.Text(
                                                        "MOMENTO DE ESTUDO",
                                                        color=tema["destaque"],
                                                        size=20,
                                                        weight=ft.FontWeight.BOLD,
                                                    ),
                                                    ft.Text(
                                                        f"PÁGINA {self.pagina_estudo + 1} DE {total}",
                                                        color=tema["primaria"],
                                                        size=12,
                                                        weight=ft.FontWeight.BOLD,
                                                    ),
                                                ],
                                                spacing=1,
                                            ),
                                        ],
                                        spacing=10,
                                        col={"xs": 12, "md": 8},
                                    ),
                                    ft.Container(
                                        content=self._controles_narracao(
                                            compacto=True
                                        ),
                                        col={"xs": 12, "md": 4},
                                    ),
                                ],
                                columns=12,
                                spacing=12,
                                run_spacing=10,
                                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                            ),
                            ft.ProgressBar(
                                value=(self.pagina_estudo + 1) / total,
                                color=tema["destaque"],
                                bgcolor=tema["fundo_1"],
                                bar_height=8,
                                border_radius=4,
                            ),
                            self._conteudo_pagina_estudo(),
                            *(
                                [
                                    ft.Container(
                                        content=ft.Text(
                                            (
                                                f"Ao concluir, {self.jogador_atual['nome']} "
                                                f"receberá {formatar_reais(PREMIO_ESTUDO)} "
                                                "por estudar e a vez passará ao próximo jogador."
                                            ),
                                            color=tema["positivo"],
                                            size=14,
                                            weight=ft.FontWeight.BOLD,
                                            text_align=ft.TextAlign.CENTER,
                                        ),
                                        padding=8,
                                        bgcolor=tema["cartao_2"],
                                        border=_borda(tema["positivo"]),
                                        border_radius=_raio(12),
                                    )
                                ]
                                if ultima_pagina
                                else []
                            ),
                            ft.ResponsiveRow(
                                controls=[
                                    # VOLTAR só entre páginas do estudo. Não há
                                    # volta à questão: o estudo mostra a resposta
                                    # correta (estudar é definitivo).
                                    *(
                                        [
                                            ft.OutlinedButton(
                                                content="VOLTAR",
                                                icon=ft.Icons.ARROW_BACK,
                                                style=ft.ButtonStyle(
                                                    color=tema["texto"],
                                                    side=_lado(tema["primaria"], 1.5),
                                                ),
                                                height=42,
                                                on_click=self._voltar_pagina_estudo,
                                                col={"xs": 12, "sm": 6},
                                            )
                                        ]
                                        if self.pagina_estudo > 0
                                        else []
                                    ),
                                    ft.Button(
                                        content=(
                                            "CONCLUIR ESTUDO E PASSAR A VEZ"
                                            if ultima_pagina
                                            else "AVANÇAR"
                                        ),
                                        icon=(
                                            ft.Icons.SWAP_HORIZ
                                            if ultima_pagina
                                            else ft.Icons.ARROW_FORWARD
                                        ),
                                        color=tema["fundo_1"],
                                        bgcolor=tema["destaque"],
                                        height=42,
                                        on_click=(
                                            self._concluir_estudo
                                            if ultima_pagina
                                            else self._avancar_pagina_estudo
                                        ),
                                        col={"xs": 12, "sm": 6 if self.pagina_estudo > 0 else 12},
                                    ),
                                ],
                                columns=12,
                                spacing=12,
                                run_spacing=10,
                            ),
                        ],
                        spacing=8,
                        horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
                    ),
                    padding=12,
                    bgcolor=tema["cartao"],
                    border=_borda(tema["primaria"], 2),
                    border_radius=_raio(20),
                    shadow=_sombra("#55000000", 20, 6),
                ),
            ],
            spacing=10,
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
                self._placar(compacto=True),
                self._progresso(),
                *(
                    [faixa]
                    if (faixa := rj.faixa_sequencia(self, tema))
                    else []
                ),
                ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.ResponsiveRow(
                                controls=[
                                    ft.Row(
                                        controls=[
                                            ft.Icon(icone, color=cor, size=48),
                                            ft.Column(
                                                controls=[
                                                    ft.Text(
                                                        titulo,
                                                        color=cor,
                                                        size=28,
                                                        weight=ft.FontWeight.BOLD,
                                                    ),
                                                    ft.Text(
                                                        (
                                                            "A questão foi registrada automaticamente como erro."
                                                            if tempo_esgotado
                                                            else "Confira a resolução desta situação-problema."
                                                        ),
                                                        color=tema["suave"],
                                                        size=14,
                                                    ),
                                                ],
                                                spacing=1,
                                                expand=True,
                                            ),
                                        ],
                                        spacing=10,
                                        col={"xs": 12, "md": 8},
                                    ),
                                    ft.Container(
                                        content=ft.Text(
                                            valor,
                                            color=cor,
                                            size=32,
                                            weight=ft.FontWeight.BOLD,
                                            text_align=ft.TextAlign.CENTER,
                                        ),
                                        alignment=ft.Alignment.CENTER,
                                        col={"xs": 12, "md": 4},
                                    ),
                                ],
                                columns=12,
                                spacing=10,
                                run_spacing=6,
                                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                            ),
                            ft.ResponsiveRow(
                                controls=[
                                    ft.Container(
                                        content=ft.Column(
                                            controls=[
                                                ft.Text(
                                                    "RESPOSTA CORRETA",
                                                    color=tema["destaque"],
                                                    size=15,
                                                    weight=ft.FontWeight.BOLD,
                                                    text_align=ft.TextAlign.CENTER,
                                                ),
                                                self._conteudo_alternativa_price(
                                                    resposta_correta,
                                                    tamanho=21,
                                                ),
                                            ],
                                            spacing=5,
                                            horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
                                        ),
                                        padding=11,
                                        bgcolor=tema["cartao_2"],
                                        border=_borda(tema["destaque"], 1.5),
                                        border_radius=_raio(14),
                                        col={"xs": 12, "md": 4},
                                    ),
                                    ft.Container(
                                        content=ft.Column(
                                            controls=[
                                                ft.Text(
                                                    "JUSTIFICATIVA",
                                                    color=tema["primaria"],
                                                    size=15,
                                                    weight=ft.FontWeight.BOLD,
                                                ),
                                                self._explicacao_em_ordem(
                                                    self.questao_atual["explicacao"],
                                                    tamanho=21,
                                                ),
                                            ],
                                            spacing=5,
                                            horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
                                        ),
                                        padding=11,
                                        bgcolor=tema["cartao_2"],
                                        border=_borda(tema["primaria"]),
                                        border_radius=_raio(14),
                                        col={"xs": 12, "md": 8},
                                    ),
                                ],
                                columns=12,
                                spacing=10,
                                run_spacing=8,
                                vertical_alignment=ft.CrossAxisAlignment.START,
                            ),
                            # MODO ECONOMIA: convite a guardar parte no cofrinho.
                            *et.lembrete_investir(self, tema),
                            ft.ResponsiveRow(
                                controls=[
                                    ft.Container(
                                        content=ft.Column(
                                            controls=[
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
                                                    "A vez será alternada após esta questão.",
                                                    color=tema["suave"],
                                                    size=13,
                                                ),
                                            ],
                                            spacing=1,
                                        ),
                                        col={"xs": 12, "md": 8},
                                    ),
                                    ft.Button(
                                        content="PASSAR A VEZ",
                                        icon=ft.Icons.SWAP_HORIZ,
                                        color=tema["fundo_1"],
                                        bgcolor=tema["destaque"],
                                        height=50,
                                        on_click=self._proxima_rodada,
                                        col={"xs": 12, "md": 4},
                                    ),
                                ],
                                columns=12,
                                spacing=10,
                                run_spacing=6,
                                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                            ),
                        ],
                        spacing=9,
                        horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
                    ),
                    width=1200,
                    padding=ft.Padding.all(16),
                    bgcolor=tema["cartao"],
                    border=_borda(cor, 2),
                    border_radius=_raio(24),
                    shadow=_sombra("#55000000", 24, 8),
                    alignment=ft.Alignment.CENTER,
                ),
            ],
            spacing=8,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )

    def _proxima_rodada(self, _evento: ft.ControlEvent) -> None:
        self._estudo_em_andamento = False
        self.indice_questao += 1
        if self.indice_questao >= len(self.questoes):
            # A partida foi concluída: não reabre uma questão já pontuada ao
            # usar "Tela anterior". O botão global volta ao menu principal.
            self._historico_telas.clear()
            self.tela_atual = "resultado"
            self._renderizar()
            return

        self.indice_jogador = (self.indice_jogador + 1) % len(self.jogadores)
        self.ultimo_resultado = None
        self._rodada_finalizada = False
        self._questao_cronometro = None
        self.pagina_estudo = 0
        # Uma nova rodada é uma transação nova. O histórico anterior é limpo
        # para impedir que o usuário reabra e pontue novamente uma questão.
        self._historico_telas.clear()
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

        # RESULTADO EM DUAS COLUNAS (cabe na tela sem rolar):
        # esquerda = vencedor, classificação e botões; direita = pódio e conquistas.
        coluna_resumo = ft.Column(
            controls=[
                ft.Row(
                    controls=[
                        ft.Icon(
                            ft.Icons.EMOJI_EVENTS,
                            color=tema["destaque"],
                            size=46,
                        ),
                        ft.Column(
                            controls=[
                                ft.Text(
                                    "FIM DO JOGO",
                                    color=tema["destaque"],
                                    size=28,
                                    weight=ft.FontWeight.BOLD,
                                ),
                                ft.Text(
                                    mensagem,
                                    color=tema["texto"],
                                    size=19,
                                    weight=ft.FontWeight.BOLD,
                                ),
                            ],
                            spacing=0,
                            expand=True,
                        ),
                    ],
                    spacing=12,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                ft.Text(
                    "✓ acertos  •  ✗ erros  •  📖 escolhas de estudo",
                    color=tema["suave"],
                    size=12,
                ),
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
            spacing=10,
            horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
        )
        return ft.Container(
            content=ft.ResponsiveRow(
                controls=[
                    ft.Container(content=coluna_resumo, col={"xs": 12, "lg": 6}),
                    ft.Container(
                        content=ft.Column(
                            controls=[
                                rj.podio(self, self.jogadores, tema, formatar_reais),
                                # MODO ECONOMIA: questões × cofrinho × patrimônio.
                                *et.painel_resultado(self, tema),
                            ],
                            spacing=10,
                        ),
                        col={"xs": 12, "lg": 6},
                    ),
                ],
                columns=12,
                spacing=18,
                run_spacing=14,
                vertical_alignment=ft.CrossAxisAlignment.START,
            ),
            padding=ft.Padding.symmetric(horizontal=22, vertical=18),
            bgcolor=tema["cartao"],
            border=_borda(tema["destaque"], 2),
            border_radius=_raio(24),
            shadow=_sombra("#55000000", 24, 8),
            margin=ft.Margin.symmetric(vertical=6),
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
        self._historico_telas.clear()
        self.etapa_teoria = 0
        self.pagina_estudo = 0
        self._estudo_em_andamento = False
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
        self._estudo_em_andamento = False
        # INÍCIO sempre encerra o fluxo atual; ao reabrir o módulo, uma nova
        # pilha será criada sem rotas antigas ou controles acumulados.
        self._historico_telas.clear()
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
                            "Confira o arquivo dados/questoes_price.json, os "
                            "campos obrigatórios e as imagens em "
                            "assets/imagens/price."
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


def criar_tela_price(
    page: ft.Page,
    ao_voltar: Callable[..., Any],
    estado: EstadoJogo | None = None,
) -> ft.Control:
    """Fábrica exigida pelo arquivo principal."""
    try:
        jogo = JogoPrice(page, ao_voltar, estado)
        return jogo.raiz
    except Exception as erro:
        print(f"Erro ao criar o jogo do Sistema PRICE / SAF: {erro}")

        async def retornar_ao_menu(_evento: ft.ControlEvent) -> None:
            retorno = ao_voltar()
            if hasattr(retorno, "__await__"):
                await retorno

        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Icon(
                        ft.Icons.ERROR_OUTLINE,
                        color="#FF6E86",
                        size=72,
                    ),
                    ft.Text(
                        "ERRO AO CARREGAR O MÓDULO PRICE / SAF",
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
                    ft.ResponsiveRow(
                        controls=[
                            ft.OutlinedButton(
                                content="TELA ANTERIOR",
                                icon=ft.Icons.ARROW_BACK,
                                on_click=retornar_ao_menu,
                                col={"xs": 12, "sm": 6},
                            ),
                            ft.Button(
                                content="INÍCIO",
                                icon=ft.Icons.HOME,
                                on_click=retornar_ao_menu,
                                col={"xs": 12, "sm": 6},
                            ),
                        ],
                        columns=12,
                        spacing=10,
                        run_spacing=10,
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
    page.title = "Responda ou Estuda - Sistema PRICE / SAF"
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 0
    page.window.width = 1280
    page.window.height = 820
    page.window.min_width = 360
    page.window.min_height = 640

    host = ft.Container(expand=True)
    estado = EstadoJogo()

    def reiniciar() -> None:
        host.content = criar_tela_price(page, reiniciar, estado)
        host.update()

    host.content = criar_tela_price(page, reiniciar, estado)
    page.add(host)


if __name__ == "__main__":
    ft.run(
        main,
        name="responde_ou_estuda_price",
        assets_dir=str(ASSETS_DIR),
    )
