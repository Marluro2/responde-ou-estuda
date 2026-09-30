"""Arquivo principal do jogo Responda ou Estuda em Flet 0.86.3.

DEPENDÊNCIAS:
    py -3.14 -m pip install "flet[all]==0.86.3" flet-audio==0.86.3

EXECUÇÃO:
    py -3.14 responda_ou_estuda.py

Esta edição pode ser aberta por ``iniciar_janela_app.py`` em uma janela
exclusiva, sem abas nem barra de endereço. A interface usa o mecanismo local do
Edge ou Chrome e não carrega o cliente Desktop do Flet bloqueado pelo Controle
Inteligente de Aplicativos do Windows. O servidor Python permanece local e não
publica o jogo na internet.

PARA ALTERAR O CONTEÚDO FUTURAMENTE:
1. Edite o dicionário ``TEXTOS_TELA``.
2. Edite a lista ``ASSUNTOS``.
3. Para trocar a arte, substitua ``assets/mascote_financeiro.webp``.
4. Mantenha ``nivel_1_porcentagem.py`` na mesma pasta deste arquivo.
5. Mantenha ``nivel_2_juros.py`` e ``dados/questoes_juros.json`` na pasta.

INTEGRAÇÃO COM OS MÓDULOS:
Os arquivos das etapas usam Flet e recebem o mesmo EstadoJogo. Assim, o saldo,
os acertos, os erros e os estudos permanecem acumulados entre os assuntos.

    def criar_tela_porcentagem(page, ao_voltar) -> ft.Control:
        ...

    def criar_tela_juros(page, ao_voltar, estado) -> ft.Control:
        ...
"""

# ============================================================================
# GUIA DE MODIFICAÇÃO MANUAL — LEIA ANTES DE ALTERAR
# ============================================================================
#
# Este arquivo foi comentado para facilitar mudanças visuais futuras.
# NENHUMA destas explicações altera o funcionamento atual do programa.
#
# ---------------------------------------------------------------------------
# 1. TÍTULOS E TEXTOS
# ---------------------------------------------------------------------------
# • O título exibido na barra da janela é definido em:
#       def _configurar_pagina()
#       self.page.title = "Responda ou Estuda - Educação Financeira"
#   Troque somente o texto entre aspas para mudar o título da janela.
#
# • O título grande visível na tela é montado em:
#       def _construir_painel_marca()
#   Procure os textos "RESPONDA" e "OU ESTUDA".
#   Em cada ft.Text:
#       size=43                  -> tamanho da letra;
#       color=...                -> cor da letra;
#       weight=ft.FontWeight...  -> espessura/negrito;
#       letter_spacing=...       -> espaço entre letras, quando existir;
#       shadow=[...]             -> sombra/brilho do texto.
#
# • O título acadêmico do projeto aparece na faixa própria criada em:
#       def _construir_titulo_projeto()
#   O texto é lido de TEXTOS_TELA["titulo_projeto"]. Assim, para trocar o nome
#   do projeto, altere somente o conteúdo dessa chave, sem mexer no layout.
#   Na função _construir_titulo_projeto():
#       size=18   -> tamanho da letra do título do projeto;
#       height=58 -> altura da faixa;
#       color=... -> cor da letra;
#       gradient  -> cores do fundo;
#       padding   -> distância do texto até as bordas.
#
# • Os textos gerais reunidos em TEXTOS_TELA podem ser trocados diretamente,
#   mantendo as chaves à esquerda e alterando apenas o conteúdo entre aspas.
#   Alguns textos específicos do layout profissional permanecem próximos dos
#   componentes que os exibem. Para localizá-los, pesquise o texto no arquivo.
#
# ---------------------------------------------------------------------------
# 2. CORES DO LAYOUT E DAS LETRAS
# ---------------------------------------------------------------------------
# • As cores principais ficam no dicionário CORES.
#   Cada valor hexadecimal tem o formato "#RRGGBB":
#       "fundo_topo", "fundo_meio", "fundo_base" -> fundo em degradê;
#       "azul_cartao", "azul_cartao_2"           -> cartões e caixas;
#       "azul_botao", "azul_bloqueado"           -> botões/etapas;
#       "branco", "texto_suave"                  -> textos;
#       "ciano", "ciano_2"                       -> destaques e contornos;
#       "amarelo", "laranja", "laranja_2"        -> destaques quentes;
#       "verde"                                  -> acertos/saldo positivo;
#       "vermelho"                               -> erros/saldo negativo.
#
# • Para alterar uma cor em TODOS os locais que usam a paleta, modifique o
#   valor correspondente em CORES e também nos temas de TEMAS_TELA_INICIAL.
#
# • Cada tema ("Financeiro", "Neon roxo", "Esmeralda", "Pôr do sol" e "Claro")
#   possui sua própria paleta em TEMAS_TELA_INICIAL. Altere ali as cores que
#   devem aparecer quando o usuário selecionar aquele tema.
#
# • Alguns fundos e contornos usam cores hexadecimais diretamente, por exemplo:
#       bgcolor=_cor_fixa("#071E4D")
#       border=_borda(_cor_fixa("#245F96"))
#   Nesses casos, altere o código hexadecimal no próprio componente.
#
# • Nos textos:
#       color=...   -> cor da letra;
#       bgcolor=... -> cor do fundo do componente, quando aplicável.
#
# IMPORTANTE: CORES["branco"] não precisa ser branco. É apenas o nome da chave.
# Se seu valor for alterado, todos os textos que usam essa chave mudarão juntos.
#
# ---------------------------------------------------------------------------
# 3. COMO ALTERAR BOTÕES
# ---------------------------------------------------------------------------
# Há três formatos de botão neste arquivo:
#   A) ft.Button / ft.OutlinedButton: IMPORTAR, RANKING e VOLTAR;
#   B) ft.Container com on_click: ATIVAR SOM e cartões das etapas;
#   C) ft.Dropdown: seletores de tema, música e quantidade de jogadores.
#
# Em qualquer botão ou contêiner clicável:
#       width=...          -> largura fixa;
#       height=...         -> altura;
#       padding=...        -> espaço entre o conteúdo e a borda;
#       bgcolor=...        -> cor de fundo;
#       color=...          -> cor do texto/ícone nos botões nativos;
#       border=...         -> cor e espessura da borda;
#       border_radius=...  -> arredondamento dos cantos;
#       shadow=...         -> sombra;
#       icon=...           -> ícone;
#       tooltip=...        -> texto mostrado ao repousar o mouse;
#       on_click=...       -> função executada ao clicar;
#       on_hover=...       -> efeito ao passar o mouse;
#       animate=...        -> duração da animação em milissegundos.
#
# Para AUMENTAR um botão:
#   aumente height, width (se existir), padding e, se necessário, o size do
#   ft.Text ou ft.Icon interno.
#
# Para DIMINUIR um botão:
#   reduza height, width, padding e os tamanhos do texto/ícone. Faça pequenas
#   alterações, pois reduzir apenas height pode cortar o conteúdo.
#
# NÃO altere on_click, on_select ou on_hover se quiser preservar a função.
#
# ---------------------------------------------------------------------------
# 4. CAIXAS DE TEXTO DOS NOMES
# ---------------------------------------------------------------------------
# As caixas estão em def _construir_painel_jogadores(), no ft.TextField.
# Principais comandos:
#       width=...            -> largura fixa, se for acrescentada;
#       height=42            -> altura da caixa;
#       text_size=12         -> tamanho do texto digitado;
#       label="..."          -> rótulo da caixa;
#       hint_text="Nome"     -> dica exibida quando a caixa está vazia;
#       bgcolor=...          -> fundo;
#       color=...            -> texto digitado;
#       border_color=...     -> borda normal;
#       focused_border_color -> borda quando a caixa está selecionada;
#       border_radius=11     -> cantos arredondados;
#       content_padding=...  -> espaço interno.
#
# COMO MOVER AS CAIXAS:
# • Mais para baixo: aumente o espaçamento acima delas ou o padding superior do
#   cartão/painel que as contém. Exemplo:
#       padding=ft.Padding.only(left=9, top=18, right=9, bottom=9)
# • Mais para cima: reduza o padding superior ou o spacing do ft.Column.
# • Mais para a direita: aumente o padding esquerdo do contêiner pai.
# • Mais para a esquerda: reduza o padding esquerdo.
# • Para separar duas caixas: aumente spacing ou run_spacing do
#   ft.ResponsiveRow que recebe controls=cartoes.
#
# Este layout é responsivo. Por isso, NÃO se recomenda usar coordenadas x/y nas
# caixas. A posição normal é determinada pela ordem em controls, por padding,
# spacing, alinhamentos e pela grade col.
#
# ---------------------------------------------------------------------------
# 5. POSIÇÃO DOS COMPONENTES E GRADE RESPONSIVA
# ---------------------------------------------------------------------------
# • controls=[A, B, C] determina a ordem visual dos componentes.
# • spacing controla o espaço entre itens na mesma linha/coluna.
# • run_spacing controla o espaço entre linhas quando ocorre quebra.
# • padding controla o espaço interno do contêiner:
#       ft.Padding.symmetric(horizontal=16, vertical=9)
#       horizontal -> esquerda e direita;
#       vertical   -> cima e baixo.
# • alignment em ft.Row controla a posição horizontal:
#       START         -> esquerda;
#       CENTER        -> centro;
#       END           -> direita;
#       SPACE_BETWEEN -> distribui os itens entre as extremidades.
# • horizontal_alignment em ft.Column controla esquerda/centro/direita.
# • vertical_alignment em ft.Row controla cima/centro/baixo.
#
# A grade usa 12 colunas. Exemplo:
#       col={"xs": 12, "sm": 6, "md": 4, "lg": 3}
# Significa:
#       xs -> ocupa 12/12 da largura em telas muito pequenas;
#       sm -> ocupa 6/12;
#       md -> ocupa 4/12;
#       lg -> ocupa 3/12.
# Para deixar uma caixa MAIS LARGA, aumente o número. Para deixá-la mais
# ESTREITA, diminua. A soma dos itens na mesma linha deve preferencialmente
# ficar em 12.
#
# Somente os elementos dentro de ft.Stack usam posição direta:
#       left  -> distância da esquerda;
#       right -> distância da direita;
#       top   -> distância de cima;
#       bottom-> distância de baixo.
# Aumentar left move para a direita; aumentar right move para a esquerda;
# aumentar top move para baixo; aumentar bottom move para cima.
#
# ---------------------------------------------------------------------------
# 6. TAMANHO DOS PAINÉIS, IMAGENS, AVATARES E ÍCONES
# ---------------------------------------------------------------------------
# • width e height controlam largura e altura.
# • ft.Image:
#       fit=ft.BoxFit.COVER   -> preenche e pode cortar as bordas;
#       fit=ft.BoxFit.CONTAIN -> mostra a imagem inteira e pode deixar margem.
# • size no ft.Icon controla o tamanho do ícone.
# • opacity vai de 0.0 (invisível) a 1.0 (totalmente visível).
# • rotate gira o elemento.
# • border_radius deve acompanhar aproximadamente metade de width/height para
#   imagens circulares. Exemplo: imagem 48 × 48 usa raio 24.
#
# A imagem da missão é definida por ARQUIVO_IMAGEM_MISSAO e configurada em
# def _construir_painel_missao(). Para trocar a arte sem alterar o código,
# substitua o arquivo na pasta assets mantendo o mesmo nome.
#
# ---------------------------------------------------------------------------
# 7. FONTES E APARÊNCIA DOS TEXTOS
# ---------------------------------------------------------------------------
# Em ft.Text:
#       size=...                         -> tamanho;
#       color=...                        -> cor;
#       weight=ft.FontWeight.BOLD        -> negrito;
#       text_align=ft.TextAlign.CENTER   -> alinhamento;
#       max_lines=1                      -> máximo de linhas;
#       overflow=ft.TextOverflow.ELLIPSIS-> mostra "..." se não couber;
#       style=ft.TextStyle(...)          -> sombra/espaçamento entre letras.
#
# Para mudar a fonte de toda a página, é possível configurar uma fonte no tema
# do Flet, mas isso exige adicionar o arquivo da fonte aos assets. Essa alteração
# não foi feita aqui para manter as características atuais.
#
# ---------------------------------------------------------------------------
# 8. JANELA, ROLAGEM E RESPONSIVIDADE
# ---------------------------------------------------------------------------
# Em def _configurar_pagina():
#       self.page.window.width/height       -> tamanho inicial da janela;
#       self.page.window.min_width/height   -> menor tamanho permitido;
#       self.page.padding                   -> margem geral da página.
#
# Em def _construir_tela_inicial():
#       scroll=ft.ScrollMode.AUTO
# mantém o conteúdo acessível quando a janela fica menor. Remover a rolagem
# pode esconder botões em telas pequenas.
#
# Se aumentar textos, cartões ou espaçamentos, talvez também seja necessário
# aumentar a altura da janela ou reduzir outro bloco para manter uma página.
#
# ---------------------------------------------------------------------------
# 9. SOM, TEMAS, ASSUNTOS E ARQUIVOS EXTERNOS
# ---------------------------------------------------------------------------
# • volume=0.80, dentro de __init__, controla o volume do áudio do Flet:
#       0.0 = silêncio; 1.0 = volume máximo.
# • ReleaseMode.LOOP repete a música.
# • ARQUIVO_QUIZ define o nome do módulo de Porcentagem.
# • PASTA_ASSETS define a pasta de imagens e sons.
# • ASSUNTOS define nome, descrição, status, ícone e se cada etapa está ativa.
#       ativo=True  -> etapa liberada;
#       ativo=False -> etapa bloqueada.
# Para preservar o programa atual, mantenha a primeira etapa como índice 0.
#
# ---------------------------------------------------------------------------
# 10. O QUE NÃO ALTERAR PARA PRESERVAR AS FUNÇÕES
# ---------------------------------------------------------------------------
# Não modifique, sem necessidade:
# • os nomes das funções iniciadas por def;
# • os parâmetros das funções;
# • on_click, on_select, on_change, on_blur e on_hover;
# • self.estado e seus métodos;
# • a importação de estado_jogo e nivel_1_porcentagem;
# • a função main(), iniciar() ou o bloco if __name__ == "__main__";
# • os caminhos de arquivos sem também renomear/mover o arquivo correspondente.
#
# DICA: faça uma alteração visual por vez, salve uma cópia e execute o programa.
# Assim fica fácil identificar e desfazer qualquer ajuste que não tenha o efeito
# esperado.

from __future__ import annotations

import importlib.metadata
import importlib.util
import io
import math
import re
import shutil
import struct
import sys
import uuid
import wave
from functools import partial
from pathlib import Path
from typing import Any, Callable

import flet as ft
from flet_audio import Audio, ReleaseMode
from estado_jogo import (
    EstadoJogo,
    TEMAS_DISPONIVEIS,
    formatar_reais,
)
from modo_admin import ADMIN_ATIVO, criar_estado_admin
import economia_tela
import recursos_jogo

# COMO USAR AS ANOTAÇÕES DE PERSONALIZAÇÃO:
# Quando um comentário aparece imediatamente depois de uma propriedade como
# "height=146", ele explica exatamente o que essa linha altera. Modifique
# somente o valor indicado e mantenha vírgulas, parênteses e nomes dos eventos.
# Linhas com on_click, on_select, on_change e on_blur controlam funções do jogo:
# não as remova se desejar preservar cliques, salvamento, ranking e navegação.

try:
    import winsound
except ImportError:  # Android, iOS, macOS e Linux usam o áudio do Flet.
    winsound = None


# ============================================================================
# TEXTOS FÁCEIS DE ALTERAR
# ============================================================================

# Altere somente os textos à direita dos dois-pontos.
# Não renomeie as chaves ("titulo", "subtitulo" etc.), pois o programa procura
# esses nomes exatos. O caractere \n força uma quebra de linha.
TEXTOS_TELA = {
    "titulo_projeto": (
        "Educação Financeira com Progressões: Uma Proposta Interativa"
    ),
    # Para trocar o título do projeto, altere somente o texto entre aspas acima.
    # Mantenha a chave "titulo_projeto", os parênteses, as aspas e a vírgula.
    "titulo": "RESPONDA OU ESTUDA",
    "subtitulo": "EDUCAÇÃO FINANCEIRA NA EDUCAÇÃO BÁSICA",
    "slogan": (
        "Desafios, estratégia, escolhas e conhecimento para jogar e aprender"
    ),
    "chamada": "ESCOLHA UM TEMA PARA COMEÇAR",
    "missao_selo": "MISSÃO: EDUCAÇÃO FINANCEIRA",
    "missao_titulo": "SUA MISSÃO",
    "missao_texto": (
        "Aprenda a tomar decisões financeiras, avance pelos desafios e "
        "transforme conhecimento em conquistas."
    ),
    "premio_rotulo": "PRÊMIO",
    "premio": "R$ 100,00",
    "premio_apoio": "POR ACERTO  •  ACUMULE E AVANCE",
    "imagem_vazia": "ADICIONE SUA IMAGEM\nNA PASTA ASSETS",
    "rodape": "PENSE  •  DECIDA  •  CONQUISTE",
    "instrucao": "Escolha Porcentagem, Juros, PRICE ou SAC para começar",
}


# BOTÕES/ETAPAS DO MENU LATERAL:
# Cada bloco abaixo representa um cartão de assunto.
#   "nome"      -> título da etapa;
#   "descricao" -> texto menor (use \n para quebrar a linha);
#   "status"    -> situação da etapa;
#   "icone"     -> símbolo exibido no botão;
#   "ativo"     -> True libera o clique; False mantém bloqueado.
# Os três assuntos futuros podem ser alterados aqui quando forem definidos.
ASSUNTOS = [
    {
        "nome": "PORCENTAGEM",
        "descricao": "Descontos, acréscimos\ne taxas",
        "status": "JOGAR AGORA",
        "icone": "%",
        "ativo": True,
    },
    {
        "nome": "JUROS",
        "descricao": "Simples e compostos",
        "status": "JOGAR AGORA",
        "icone": "J$",
        "ativo": True,
    },
    {
        "nome": "SISTEMA PRICE",
        "descricao": "SAF e prestações fixas",
        "status": "JOGAR AGORA",
        "icone": "P$",
        "ativo": True,
    },
    {
        "nome": "SISTEMA SAC",
        "descricao": "Amortização constante e PA",
        "status": "JOGAR AGORA",
        "icone": "S$",
        "ativo": True,
    },
    {
        "nome": "EM BREVE",
        "descricao": "Novo assunto\nem preparação",
        "status": "BLOQUEADO",
        "icone": "05",
        "ativo": False,
    },
]


# ============================================================================
# CONFIGURAÇÕES GERAIS
# ============================================================================

# VERSÃO: usada apenas para avisar no console quando o Flet instalado é outro.
FLET_VERSAO_ALVO = "0.86.3"

# PASTAS E ARQUIVOS:
# BASE_DIR é a pasta onde este .py se encontra.
# PASTA_ASSETS é a pasta de imagens e sons usada pelo Flet.
# Para renomear um arquivo abaixo, renomeie também o arquivo real na pasta.
BASE_DIR = Path(__file__).resolve().parent
PASTA_ASSETS = BASE_DIR / "assets"
ARQUIVO_QUIZ = "nivel_1_porcentagem.py"
ARQUIVO_QUIZ_JUROS = "nivel_2_juros.py"
ARQUIVO_QUIZ_PRICE = "nivel_3_price.py"
ARQUIVO_QUIZ_SAC = "nivel_4_sac.py"
ARQUIVO_IMAGEM_MISSAO = "mascote_financeiro.webp"
ARQUIVO_SOM_INICIAL = PASTA_ASSETS / "sons" / "01_aventura.wav"

# PALETA PRINCIPAL:
# Para trocar uma cor, substitua apenas o hexadecimal "#RRGGBB".
# Os nomes à esquerda são usados pelo restante do código e não devem ser
# renomeados. As funções usam CORES["nome_da_cor"] para buscar estes valores.
CORES = {
    "fundo_topo": "#071036",
    "fundo_meio": "#062866",
    "fundo_base": "#031744",
    "azul_cartao": "#08265F",
    "azul_cartao_2": "#0A347D",
    "azul_botao": "#074CAE",
    "azul_bloqueado": "#0A2557",
    "ciano": "#59F4FF",
    "ciano_2": "#00BDEB",
    "branco": "#FFFFFF",
    "texto_suave": "#BDEEFF",
    "amarelo": "#FFD34E",
    "laranja": "#FF8A20",
    "laranja_2": "#FFB52E",
    "verde": "#45E59A",
    "vermelho": "#FF6E86",
    # "sim" apenas no tema Alto contraste (ver _cor_fixa).
    "alto_contraste": "não",
}

# TEMAS:
# "Financeiro" copia a paleta principal. Os demais temas copiam CORES e
# substituem somente as cores listadas em cada bloco.
# Para criar outro tema, copie um bloco completo, dê um novo nome e mantenha
# todas as chaves de cor necessárias.
TEMAS_TELA_INICIAL = {
    "Financeiro": dict(CORES),
    "Neon roxo": {
        **CORES,
        "fundo_topo": "#160B35",
        "fundo_meio": "#4B167E",
        "fundo_base": "#12072D",
        "azul_cartao": "#2B1459",
        "azul_cartao_2": "#64239A",
        "azul_botao": "#64239A",
        "azul_bloqueado": "#291447",
        "ciano": "#70F6FF",
        "ciano_2": "#A95CFF",
        "texto_suave": "#E9D9FF",
        "amarelo": "#FFDF5D",
        "laranja": "#FF74B8",
        "laranja_2": "#FF9BD0",
        "verde": "#6EF7AD",
        "vermelho": "#FF74B8",
    },
    "Esmeralda": {
        **CORES,
        "fundo_topo": "#052D2B",
        "fundo_meio": "#087563",
        "fundo_base": "#032522",
        "azul_cartao": "#075247",
        "azul_cartao_2": "#0B8F78",
        "azul_botao": "#0B8F78",
        "azul_bloqueado": "#17443D",
        "ciano": "#77FFE0",
        "ciano_2": "#22CDA8",
        "texto_suave": "#D3FFF5",
        "amarelo": "#FFE179",
        "laranja": "#F0A94B",
        "laranja_2": "#FFD177",
        "verde": "#A6FF8C",
        "vermelho": "#FF8A8A",
    },
    "Pôr do sol": {
        **CORES,
        "fundo_topo": "#3A1032",
        "fundo_meio": "#A33A35",
        "fundo_base": "#2E0C2A",
        "azul_cartao": "#68253B",
        "azul_cartao_2": "#C45137",
        "azul_botao": "#C45137",
        "azul_bloqueado": "#54243B",
        "ciano": "#FFD08A",
        "ciano_2": "#FF9D66",
        "texto_suave": "#FFE1D9",
        "amarelo": "#FFF06A",
        "laranja": "#FF7F50",
        "laranja_2": "#FFB56B",
        "verde": "#9DFFB1",
        "vermelho": "#FF9EB2",
    },
    "Claro": {
        **CORES,
        "fundo_topo": "#163B5C",
        "fundo_meio": "#3B78A3",
        "fundo_base": "#244F70",
        "azul_cartao": "#1E5278",
        "azul_cartao_2": "#2D6C96",
        "azul_botao": "#2389C2",
        "azul_bloqueado": "#2C5875",
        "ciano": "#BCEEFF",
        "ciano_2": "#74D8FF",
        "branco": "#FFFFFF",
        "texto_suave": "#E3F7FF",
        "amarelo": "#FFE08A",
        "laranja": "#FF9A5C",
        "laranja_2": "#F29B57",
        "verde": "#8FF0BD",
        "vermelho": "#FF9BAD",
    },
    # ACESSIBILIDADE: fundo preto, texto branco, destaques amarelo e ciano.
    "Alto contraste": {
        **CORES,
        "fundo_topo": "#000000",
        "fundo_meio": "#000000",
        "fundo_base": "#000000",
        "azul_cartao": "#0E0E0E",
        "azul_cartao_2": "#1C1C1C",
        "azul_botao": "#1C1C1C",
        "azul_bloqueado": "#141414",
        "ciano": "#00FFFF",
        "ciano_2": "#00FFFF",
        "branco": "#FFFFFF",
        "texto_suave": "#F2F2F2",
        "amarelo": "#FFE600",
        "laranja": "#FFE600",
        "laranja_2": "#FFE600",
        "verde": "#3DFF7A",
        "vermelho": "#FF6B6B",
        # Marca usada por _cor_fixa() para trocar as cores fixas da tela.
        "alto_contraste": "sim",
    },
}


def _cor_fixa(hexa: str) -> str:
    """Cores escritas direto no código: no ALTO CONTRASTE viram preto/branco.

    Fundos escuros ficam quase pretos e bordas claras ficam brancas; nos demais
    temas a cor original é mantida.
    """
    if CORES.get("alto_contraste") != "sim":
        return hexa
    r, g, b = (int(hexa[i:i + 2], 16) for i in (1, 3, 5))
    luminancia = (0.2126 * r + 0.7152 * g + 0.0722 * b) / 255
    return "#FFFFFF" if luminancia > 0.25 else "#0E0E0E"


def _borda(cor: str, largura: float = 1) -> ft.Border:
    """Cria uma borda uniforme usando a API do Flet 0.86.3."""
    # "largura" é a espessura da borda. Ex.: _borda(cor, 2) cria 2 pixels.
    return ft.Border.all(width=largura, color=cor)


def _raio(valor: float) -> ft.BorderRadius:
    # Quanto maior o valor, mais arredondados ficam os quatro cantos.
    return ft.BorderRadius.all(valor)


def _sombra(cor: str, desfoque: float = 18, y: float = 6) -> ft.BoxShadow:
    # desfoque aumenta/reduz a suavidade; y move a sombra para baixo/cima.
    return ft.BoxShadow(
        color=cor,
        blur_radius=desfoque,
        spread_radius=0,
        offset=(0, y),
    )


def _versao_instalada(distribuicao: str) -> str:
    try:
        return importlib.metadata.version(distribuicao)
    except importlib.metadata.PackageNotFoundError:
        return "não instalada"


def _avisar_sobre_versoes() -> None:
    """Informa no console se o projeto não estiver usando a versão definida."""
    versoes = {
        "flet": _versao_instalada("flet"),
        "flet-audio": _versao_instalada("flet-audio"),
    }
    divergentes = [
        f"{nome}={versao}"
        for nome, versao in versoes.items()
        if versao != FLET_VERSAO_ALVO
    ]
    if divergentes:
        encontrados = ", ".join(divergentes)
        print(
            "Aviso: este arquivo foi desenvolvido para "
            f"Flet {FLET_VERSAO_ALVO}. Encontrado: {encontrados}."
        )


def _criar_tema_sonoro() -> bytes:
    """Gera uma trilha WAV curta em memória, compatível com desktop e celular."""
    # SOM GERADO PELO CÓDIGO:
    # taxa aumenta/diminui a qualidade; duracao está em segundos; volume varia
    # de 0.0 a 1.0. "acordes" guarda as frequências das notas. Alterar esses
    # valores muda a música gerada, portanto faça isso somente se quiser criar
    # outra trilha. A interface atual não depende de mudanças nesta função.
    taxa = 22_050
    duracao = 8.0
    volume = 0.10
    acordes = [
        (261.63, 329.63, 392.00),
        (293.66, 369.99, 440.00),
        (329.63, 415.30, 493.88),
        (392.00, 493.88, 587.33),
    ]

    quadros = bytearray()
    total = int(taxa * duracao)
    for indice in range(total):
        tempo = indice / taxa
        acorde = acordes[int(tempo / 2.0) % len(acordes)]
        onda = sum(
            (0.72 - posicao * 0.15) * math.sin(2 * math.pi * nota * tempo)
            for posicao, nota in enumerate(acorde)
        )
        pulso = 0.86 + 0.14 * math.sin(2 * math.pi * 0.5 * tempo)
        entrada = min(1.0, tempo / 0.7)
        saida = min(1.0, (duracao - tempo) / 0.8)
        amostra = onda / 2.8 * pulso * min(entrada, saida)
        valor = int(max(-32767, min(32767, 32767 * volume * amostra)))
        quadros.extend(struct.pack("<h", valor))

    memoria = io.BytesIO()
    with wave.open(memoria, "wb") as arquivo:
        arquivo.setnchannels(1)
        arquivo.setsampwidth(2)
        arquivo.setframerate(taxa)
        arquivo.writeframes(quadros)
    return memoria.getvalue()


class AplicativoRespondaOuEstuda:
    """Controla a abertura, a responsividade, o som e a ligação com o quiz."""

    def __init__(self, page: ft.Page):
        # INICIALIZAÇÃO:
        # Esta função cria o estado, o seletor de arquivos, o reprodutor de
        # áudio e a tela. Evite mudar a ordem destas instruções.
        self.page = page
        # MODO ADMINISTRADOR (INICIAR_ADMIN.bat): usa dados/estado_admin.json,
        # sem alterar os saldos dos jogadores reais nem o ranking.
        self.estado = criar_estado_admin() if ADMIN_ATIVO else EstadoJogo()
        CORES.update(TEMAS_TELA_INICIAL[self.estado.tema])
        self.som_ativo = False
        self.cartoes_assuntos: list[ft.Container] = []
        self.campos_nomes: list[ft.TextField] = []

        self._configurar_pagina()
        self.seletor_arquivo = ft.FilePicker()
        self.page.services.append(self.seletor_arquivo)
        self.audio = Audio(
            src=self.estado.trilhas_disponiveis()[self.estado.trilha],
            autoplay=False,
            # VOLUME: use um valor entre 0.0 e 1.0.
            volume=0.80,
            # LOOP faz a música recomeçar automaticamente quando termina.
            release_mode=ReleaseMode.LOOP,
        )
        self.page.services.append(self.audio)

        self.tela_inicial = recursos_jogo.sons_nos_botoes(self, self._construir_tela_inicial())
        # Um único controle permanece ligado à página durante toda a execução.
        # A navegação troca apenas seu conteúdo, evitando a antiga tela azul.
        self.host = ft.Container(
            content=self.tela_inicial,
            expand=True,
            bgcolor=CORES["fundo_topo"],
        )
        self.modulo_porcentagem: Any = None
        self.tela_porcentagem: ft.Control | None = None
        self.modulo_juros: Any = None
        self.tela_juros: ft.Control | None = None
        self.modulo_price: Any = None
        self.tela_price: ft.Control | None = None
        self.modulo_sac: Any = None
        self.tela_sac: ft.Control | None = None
        self.page.add(self.host)
        # MODO ECONOMIA: 1 minuto de jogo aberto = 1 "mês" (cofrinho e juros).
        economia_tela.iniciar_relogio(self.page, lambda: self.estado, self._ao_passar_mes)
        self.mostrar_inicio()

    def _configurar_pagina(self) -> None:
        # TÍTULO DA JANELA: altere somente o texto entre aspas.
        self.page.title = "Responda ou Estuda - Educação Financeira"
        # O texto acima aparece na barra superior da janela do programa.
        if ADMIN_ATIVO:
            self.page.title += " (MODO ADMINISTRADOR)"

        # TEMA DO FLET: DARK controla a aparência padrão de campos e menus.
        self.page.theme_mode = ft.ThemeMode.DARK
        # Troque DARK por LIGHT apenas se também revisar as cores claras.

        # COR atrás do layout. O fundo visível principal é o degradê criado em
        # _construir_tela_inicial(), mas esta cor evita áreas descobertas.
        self.page.bgcolor = CORES["fundo_topo"]
        # Para alterar esta cor, edite "fundo_topo" na paleta CORES.

        # MARGEM EXTERNA da página. Zero faz o layout ocupar toda a janela.
        self.page.padding = 0
        # Use 8, 12 etc. para criar uma margem ao redor de toda a página.

        # TAMANHO INICIAL DA JANELA, em pixels.
        self.page.window.width = 1440
        # Aumente para abrir a janela mais larga; diminua para abrir mais estreita.
        self.page.window.height = 820
        # Aumente para abrir a janela mais alta; diminua para abrir mais baixa.

        # TAMANHO MÍNIMO. Reduzir estes valores permite compactar mais a janela,
        # mas pode ativar a rolagem ou apertar os componentes.
        self.page.window.min_width = 360
        # Abaixo deste valor o usuário não conseguirá estreitar a janela.
        self.page.window.min_height = 600
        # Abaixo deste valor o usuário não conseguirá reduzir a altura.

        # Evento executado quando o usuário fecha a janela.
        self.page.on_close = self._ao_fechar

    # ------------------------------------------------------------------
    # Construção da interface
    # ------------------------------------------------------------------

    def _construir_tela_inicial(self) -> ft.Control:
        # BARRA SUPERIOR:
        # A grade tem 12 colunas. O cabeçalho usa 4 e os controles usam 8 em
        # telas médias/grandes. Para dar mais espaço ao título, aumente 4 e
        # reduza 8 na mesma proporção.
        barra_aplicativo = ft.Container(
            content=ft.ResponsiveRow(
                controls=[
                    ft.Container(
                        content=self._construir_cabecalho(),
                        col={"xs": 12, "sm": 12, "md": 3, "lg": 3},
                        # Em md/lg, 3/12 da barra ficam para o cabeçalho.
                    ),
                    ft.Container(
                        content=self._construir_barra_superior(),
                        col={"xs": 12, "sm": 12, "md": 9, "lg": 9},
                        # Em md/lg, 9/12 ficam para os botões (cabem em uma linha).
                    ),
                ],
                columns=12,
                spacing=12,
                # Distância horizontal entre cabeçalho e controles.
                run_spacing=8,
                # Distância vertical se a barra quebrar em duas linhas.
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            # MARGENS INTERNAS da barra: horizontal = lados; vertical = cima/baixo.
            padding=ft.Padding.symmetric(horizontal=14, vertical=9),
            # Aumente horizontal para afastar dos lados; vertical engrossa a barra.
            # FUNDO, BORDA, CANTOS E SOMBRA da barra superior.
            bgcolor=_cor_fixa("#071A45"),
            # Troque este hexadecimal para mudar o fundo da barra superior.
            border=_borda(_cor_fixa("#174F89")),
            # Troque este hexadecimal para mudar a borda da barra superior.
            border_radius=_raio(18),
            # Aumente para arredondar mais os cantos da barra.
            shadow=_sombra("#55000000", 14, 4),
            # 14 controla o desfoque e 4 o deslocamento vertical da sombra.
        )

        # COLUNA DIREITA DA ÁREA PRINCIPAL:
        # A ordem desta lista é a ordem mostrada na tela: missão primeiro e
        # título depois, conforme o modelo visual solicitado.
        painel_direito = ft.Column(
            controls=[
                self._construir_painel_missao(),
                # Para colocar o título acima da missão, mova esta linha para
                # antes de self._construir_painel_missao().
                self._construir_painel_marca(),
                # Para retirar o título desta coluna, remova somente a linha
                # acima. Isso não desativa nenhuma função do jogo.
            ],
            spacing=10,
            # Aumente este número para separar mais missão e título; diminua
            # para aproximar os dois painéis.
            horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
            col={"xs": 12, "sm": 12, "md": 8, "lg": 9},
            # Em telas grandes, lg=9 significa 75% da largura. Se usar lg=8
            # aqui, altere o menu lateral para lg=4 para manter o total 12.
        )

        # ÁREA PRINCIPAL:
        # O menu fica à esquerda e a coluna missão/título à direita.
        area_principal = ft.ResponsiveRow(
            controls=[
                ft.Container(
                    content=self._construir_seletor_assuntos(),
                    col={"xs": 12, "sm": 12, "md": 4, "lg": 3},
                    # Para deixar o menu mais largo, troque lg=3 por lg=4 e
                    # altere lg=9 do painel_direito para lg=8.
                ),
                painel_direito,
            ],
            columns=12,
            # A grade responsiva sempre soma 12 colunas.
            spacing=12,
            # Altere para aumentar/diminuir o espaço horizontal entre o menu
            # lateral e os dois painéis da direita.
            run_spacing=10,
            # Altere para controlar a distância quando a tela estreita quebrar
            # os painéis em linhas diferentes.
            vertical_alignment=ft.CrossAxisAlignment.START,
        )

        # PAINEL INFERIOR:
        # O cadastro dos jogadores fica fora da coluna direita para ocupar toda
        # a largura abaixo do menu, missão e título.
        painel_inferior = ft.Column(
            controls=[
                self._construir_painel_jogadores(),
                # Para ocultar apenas o rodapé visual, remova a próxima linha.
                # O salvamento automático e o ranking continuarão funcionando.
                self._construir_rodape(),
            ],
            spacing=7,
            # Aumente para separar mais o painel de jogadores do rodapé.
            horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
        )

        conteudo = ft.Column(
            controls=[
                barra_aplicativo,
                self._construir_titulo_projeto(),
                # Esta linha exibe a faixa com o título acadêmico do projeto.
                # Para mudar o texto, edite TEXTOS_TELA["titulo_projeto"].
                # Para mudar a aparência, use def _construir_titulo_projeto().
                area_principal,
                painel_inferior,
                # MARGEM FINAL: permite ver a parte de baixo dos cartões dos
                # jogadores e do rodapé ao rolar até o fim da tela inicial.
                ft.Container(height=12),
            ],
            # A ordem acima controla: configurações, título do projeto, área do
            # jogo e jogadores. Mova apenas linhas visuais, não os eventos.
            spacing=7,
            # Aumente para separar mais as faixas; diminua para aproximá-las.
            expand=True,
            horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
            # ALWAYS deixa a barra de rolagem visível para indicar que há
            # conteúdo abaixo. AUTO a esconde; HIDDEN pode cortar conteúdos.
            scroll=ft.ScrollMode.ALWAYS,
        )

        # MARGEM GERAL DO CONTEÚDO:
        # Aumentar horizontal afasta tudo das laterais; aumentar vertical afasta
        # tudo do topo e da base.
        camada_conteudo = ft.Container(
            content=ft.SafeArea(
                content=conteudo,
                minimum_padding=ft.Padding.symmetric(horizontal=8, vertical=6),
                # Ajusta o afastamento mínimo de áreas seguras da tela.
            ),
            padding=ft.Padding.symmetric(horizontal=16, vertical=9),
            # Esta é a margem geral: horizontal move tudo para dentro dos lados;
            # vertical afasta todo o layout do topo e da base.
            left=0,
            # Aumente para deslocar toda a camada para a direita.
            top=0,
            # Aumente para deslocar toda a camada para baixo.
            right=0,
            # Aumente para reduzir o limite direito da camada.
            bottom=0,
            # Aumente para elevar o limite inferior da camada.
        )

        # DECORAÇÕES DE FUNDO:
        # Estes quatro elementos ficam em um ft.Stack e, por isso, aceitam
        # left/right/top/bottom. opacity controla a transparência e rotate gira
        # os ícones. Eles não recebem cliques.
        decoracoes = [
            ft.Container(
                content=ft.Text(
                    "R$",
                    size=70,
                    weight=ft.FontWeight.BOLD,
                    color="#1A5DA0",
                ),
                left=22,
                top=158,
                opacity=0.18,
            ),
            ft.Container(
                content=ft.Text(
                    "%",
                    size=92,
                    weight=ft.FontWeight.BOLD,
                    color="#176EA2",
                ),
                right=32,
                top=122,
                opacity=0.16,
            ),
            ft.Container(
                content=ft.Icon(
                    ft.Icons.ATTACH_MONEY,
                    size=82,
                    color="#B66C20",
                ),
                left=44,
                bottom=58,
                opacity=0.16,
                rotate=-0.18,
            ),
            ft.Container(
                content=ft.Icon(
                    ft.Icons.TRENDING_UP,
                    size=86,
                    color="#208CB5",
                ),
                right=42,
                bottom=58,
                opacity=0.16,
                rotate=0.12,
            ),
        ]

        # FUNDO PRINCIPAL EM DEGRADÊ:
        # "colors" usa topo, meio e base. "stops" informa em que ponto (0 a 1)
        # cada cor predomina. TOP_CENTER -> BOTTOM_CENTER cria efeito vertical.
        return ft.Container(
            expand=True,
            gradient=ft.LinearGradient(
                begin=ft.Alignment.TOP_CENTER,
                end=ft.Alignment.BOTTOM_CENTER,
                colors=[
                    CORES["fundo_topo"],
                    CORES["fundo_meio"],
                    CORES["fundo_base"],
                ],
                stops=[0.0, 0.58, 1.0],
            ),
            content=ft.Stack(
                controls=[*decoracoes, camada_conteudo],
                fit=ft.StackFit.EXPAND,
            ),
        )

    def _construir_barra_superior(self) -> ft.Control:
        # ÍCONE E TEXTO DO SOM:
        # size muda o ícone; color muda sua cor. O texto usa size=9.
        self.icone_som = ft.Icon(
            ft.Icons.VOLUME_UP if self.som_ativo else ft.Icons.VOLUME_OFF,
            color=CORES["amarelo"],
            size=18,
        )
        self.texto_som = ft.Text(
            "MUTE" if self.som_ativo else "ATIVAR SOM",
            color=CORES["branco"],
            size=9,
            weight=ft.FontWeight.BOLD,
        )

        # BOTÃO ATIVAR SOM/MUTE:
        # Este botão é um Container clicável. Para aumentar/diminuir, altere
        # height, padding, o size do ícone acima e o size do texto acima.
        # bgcolor é o fundo; border é a borda; border_radius arredonda os cantos.
        botao_som = ft.Container(
            content=ft.Row(
                controls=[self.icone_som, self.texto_som],
                spacing=7,
                tight=True,
            ),
            height=42,
            padding=ft.Padding.symmetric(horizontal=12, vertical=7),
            bgcolor=_cor_fixa("#0B3472"),
            border=_borda(CORES["ciano_2"]),
            border_radius=_raio(12),
            ink=True,
            ink_color="#2459F4FF",
            on_click=self._alternar_som,
            tooltip="Ativar ou silenciar a trilha do jogo",
        )

        # SELETOR DE TEMA:
        # width controla a largura; dense=True reduz a altura interna.
        # Para aumentar o seletor, aumente width e use dense=False.
        # on_select deve permanecer apontando para _trocar_tema.
        seletor_tema = ft.Dropdown(
            value=self.estado.tema,
            options=[
                ft.DropdownOption(key=nome, text=nome)
                for nome in TEMAS_DISPONIVEIS
            ],
            label="Tema",
            leading_icon=ft.Icons.PALETTE,
            bgcolor=CORES["azul_cartao"],
            color=CORES["branco"],
            border_color=CORES["ciano_2"],
            focused_border_color=CORES["amarelo"],
            border_radius=11,
            dense=True,
            width=138,
            on_select=self._trocar_tema,
        )

        # SELETOR DE MÚSICA:
        # As opções vêm automaticamente de self.estado.trilhas_disponiveis().
        # width altera a largura visual sem mudar a lista de músicas.
        seletor_trilha = ft.Dropdown(
            value=self.estado.trilha,
            options=[
                ft.DropdownOption(key=nome, text=nome)
                for nome in self.estado.trilhas_disponiveis()
            ],
            label="Música",
            leading_icon=ft.Icons.MUSIC_NOTE,
            bgcolor=CORES["azul_cartao"],
            color=CORES["branco"],
            border_color=CORES["ciano_2"],
            focused_border_color=CORES["amarelo"],
            border_radius=11,
            dense=True,
            width=148,
            on_select=self._trocar_trilha,
        )

        # BOTÃO IMPORTAR:
        # content é o texto; icon é o símbolo; height é a altura.
        # Em ButtonStyle, color altera texto/ícone e side altera a borda.
        # Só o ícone, para a barra caber em uma linha; a dica aparece no mouse.
        botao_musica = ft.IconButton(
            icon=ft.Icons.LIBRARY_MUSIC,
            icon_color=CORES["branco"],
            style=ft.ButtonStyle(
                side=ft.BorderSide(width=1.5, color=CORES["ciano_2"]),
            ),
            on_click=self._selecionar_musica,
            tooltip="Importar música: escolher uma música do computador",
        )

        # BOTÃO RANKING:
        # bgcolor é o fundo amarelo e color é a cor escura do texto/ícone.
        # Para uniformizar a largura, acrescente width=... se desejar.
        botao_ranking = ft.Button(
            content="RANKING",
            icon=ft.Icons.LEADERBOARD,
            height=42,
            color=CORES["fundo_topo"],
            bgcolor=CORES["amarelo"],
            on_click=self._mostrar_ranking,
        )

        # BOTÃO NOVA TURMA:
        # Guarda os dados da turma atual em dados/turmas/<data> e começa do
        # zero (jogadores, saldos, ranking e respostas da pesquisa).
        botao_nova_turma = ft.OutlinedButton(
            content="NOVA TURMA",
            icon=ft.Icons.GROUP_ADD,
            height=42,
            style=ft.ButtonStyle(
                color=CORES["branco"],
                side=ft.BorderSide(width=1.5, color=CORES["ciano_2"]),
            ),
            on_click=self._confirmar_nova_turma,
            tooltip="Arquivar os dados desta turma e começar do zero",
        )

        # POSIÇÃO DOS CONTROLES SUPERIORES:
        # END alinha tudo à direita. CENTER centralizaria e START levaria à
        # esquerda. wrap=True quebra a linha quando faltar espaço.
        # spacing separa itens na linha; run_spacing separa linhas quebradas.
        return ft.Row(
            controls=[
                seletor_tema,
                seletor_trilha,
                botao_musica,
                botao_som,
                # EFEITOS: toques dos botões e sons de acerto, sem a música.
                recursos_jogo.botao_efeitos(
                    self, CORES["branco"], CORES["ciano_2"], CORES["amarelo"], compacto=True
                ),
                # ACESSIBILIDADE: tempo, animações e alto contraste.
                ft.OutlinedButton(
                    content="ACESSIBILIDADE",
                    icon=ft.Icons.ACCESSIBILITY_NEW,
                    height=42,
                    style=ft.ButtonStyle(
                        color=CORES["branco"],
                        side=ft.BorderSide(width=1.5, color=CORES["ciano_2"]),
                    ),
                    on_click=self._abrir_acessibilidade,
                    tooltip="Tempo por questão, animações e alto contraste",
                ),
                # LUPA (acessibilidade): liga/desliga a Lupa do Windows.
                recursos_jogo.botao_lupa(
                    CORES["branco"], CORES["ciano_2"], CORES["amarelo"], CORES["fundo_topo"]
                ),
                botao_nova_turma,
                botao_ranking,
            ],
            alignment=ft.MainAxisAlignment.END,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            wrap=True,
            run_spacing=7,
            spacing=8,
        )

    def _construir_cabecalho(self) -> ft.Control:
        # SÍMBOLO DO CABEÇALHO:
        # width/height controlam o quadrado; size controla apenas o ícone.
        # Para aumentar o conjunto, altere os três valores de forma proporcional.
        simbolo = ft.Container(
            content=ft.Icon(
                ft.Icons.SAVINGS,
                color=CORES["fundo_topo"],
                size=24,
            ),
            width=44,
            height=44,
            alignment=ft.Alignment.CENTER,
            gradient=ft.LinearGradient(
                begin=ft.Alignment.TOP_LEFT,
                end=ft.Alignment.BOTTOM_RIGHT,
                colors=[CORES["amarelo"], CORES["laranja"]],
            ),
            border=_borda(_cor_fixa("#FFE69A"), 2),
            border_radius=_raio(14),
            shadow=_sombra("#55FF8A20", 10, 2),
        )

        # TEXTOS DO CABEÇALHO:
        # Altere os textos entre aspas. size é o tamanho, color é a cor e
        # letter_spacing aumenta o espaço entre as letras do subtítulo.
        return ft.Row(
            controls=[
                simbolo,
                ft.Column(
                    controls=[
                        ft.Text(
                            "EDUCAÇÃO FINANCEIRA",
                            color=CORES["branco"],
                            size=15,
                            weight=ft.FontWeight.BOLD,
                        ),
                        ft.Text(
                            "MODO ADMINISTRADOR"
                            if ADMIN_ATIVO
                            else "ARENA DE DESAFIOS",
                            color=CORES["amarelo"] if ADMIN_ATIVO else CORES["ciano"],
                            size=10,
                            weight=ft.FontWeight.BOLD,
                            style=ft.TextStyle(letter_spacing=1.4),
                        ),
                    ],
                    spacing=0,
                ),
            ],
            spacing=11,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

    def _construir_titulo_projeto(self) -> ft.Control:
        """Cria a faixa superior reservada ao título acadêmico do projeto."""

        return ft.Container(
            content=ft.Row(
                controls=[
                    ft.Container(
                        content=ft.Icon(
                            ft.Icons.SCHOOL,
                            color=CORES["fundo_topo"],
                            size=20,
                            # Altere 20 para aumentar/diminuir o ícone do projeto.
                        ),
                        width=38,
                        # Altere junto com height para mudar a caixa do ícone.
                        height=38,
                        # Mantenha width e height iguais para preservar o formato.
                        alignment=ft.Alignment.CENTER,
                        gradient=ft.LinearGradient(
                            begin=ft.Alignment.TOP_LEFT,
                            end=ft.Alignment.BOTTOM_RIGHT,
                            colors=[CORES["amarelo"], CORES["laranja"]],
                            # Troque estas duas cores para alterar o fundo do ícone.
                        ),
                        border=_borda(_cor_fixa("#FFE69A"), 1),
                        border_radius=_raio(11),
                    ),
                    ft.Text(
                        TEXTOS_TELA["titulo_projeto"],
                        # Para trocar o título, edite "titulo_projeto" no
                        # dicionário TEXTOS_TELA, próximo ao início do arquivo.
                        color=CORES["branco"],
                        # Troque por CORES["amarelo"], CORES["ciano"] ou outra
                        # cor da paleta para alterar somente a letra do título.
                        size=35,
                        font_family="Arial",
                        # Aumente para ampliar o título; diminua para compactá-lo.
                        weight=ft.FontWeight.BOLD,
                        text_align=ft.TextAlign.CENTER,
                        max_lines=2,
                        # Use 1 para impedir quebra; mantenha 2 em telas estreitas.
                        overflow=ft.TextOverflow.ELLIPSIS,
                        expand=True,
                    ),
                    ft.Container(
                        width=38,
                        # Este espaço equilibra o ícone e mantém o título central.
                        height=38,
                    ),
                ],
                spacing=10,
                # Aumente para afastar o título do ícone.
                alignment=ft.MainAxisAlignment.CENTER,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            height=58,
            # Aumente para criar uma faixa mais alta; diminua para compactá-la.
            padding=ft.Padding.symmetric(horizontal=16, vertical=7),
            # horizontal afasta das laterais; vertical afasta do topo e da base.
            gradient=ft.LinearGradient(
                begin=ft.Alignment.CENTER_LEFT,
                end=ft.Alignment.CENTER_RIGHT,
                colors=[
                    CORES["fundo_meio"],
                    CORES["azul_cartao"],
                    CORES["fundo_meio"],
                ],
                # Altere estas cores para mudar o fundo da faixa do projeto.
            ),
            border=_borda(CORES["ciano_2"], 1),
            # Troque a cor ou o número 1 para mudar contorno/espessura.
            border_radius=_raio(14),
            # Aumente para deixar os cantos mais arredondados.
            shadow=_sombra("#4400BDEB", 10, 2),
        )

    def _construir_painel_marca(self) -> ft.Control:
        """Apresenta a identidade e as regras essenciais sem repetir chamadas."""

        # CARTÃO DE REGRA:
        # Esta função interna é reutilizada nos três cartões: acerto, erro e
        # estudar. Alterações de padding, fundo, borda, raio e tamanhos afetam
        # os três simultaneamente.
        def regra(
            icone: str,
            rotulo: str,
            valor: str,
            cor: str,
        ) -> ft.Control:
            return ft.Container(
                content=ft.Row(
                    controls=[
                        ft.Container(
                            content=ft.Icon(icone, color=CORES["fundo_topo"], size=18),
                            # size altera o símbolo dentro dos três cartões.
                            width=34,
                            # width altera a largura da caixa do símbolo.
                            height=34,
                            # height altera a altura da caixa do símbolo.
                            alignment=ft.Alignment.CENTER,
                            bgcolor=cor,
                            # A cor vem de cada regra: verde, vermelho ou ciano.
                            border_radius=_raio(11),
                        ),
                        ft.Column(
                            controls=[
                                ft.Text(
                                    rotulo,
                                    color=CORES["texto_suave"],
                                    size=8,
                                    # Altere para aumentar/diminuir ACERTO/ERRO/ESTUDAR.
                                    weight=ft.FontWeight.BOLD,
                                ),
                                ft.Text(
                                    valor,
                                    color=cor,
                                    size=15,
                                    # Altere para aumentar/diminuir os valores em reais.
                                    weight=ft.FontWeight.BOLD,
                                ),
                            ],
                            spacing=0,
                        ),
                    ],
                    spacing=9,
                    # Distância entre o ícone e os textos de cada regra.
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                padding=ft.Padding.symmetric(horizontal=10, vertical=7),
                # horizontal altera as laterais; vertical altera topo e base.
                bgcolor=_cor_fixa("#0A2A61"),
                # Troque este hexadecimal para mudar o fundo dos três cartões.
                border=_borda(_cor_fixa("#285D94")),
                # Troque este hexadecimal para mudar a borda dos três cartões.
                border_radius=_raio(13),
                col={"xs": 12, "sm": 4},
                # sm=4 coloca três regras lado a lado: 4 + 4 + 4 = 12.
            )

        # IDENTIDADE/TÍTULO PRINCIPAL:
        # Para mover este bloco em relação às regras, altere seu col logo abaixo
        # e o col do bloco "regras". Em md, atualmente são 7 + 5 = 12.
        identidade = ft.Column(
            controls=[
                ft.Container(
                    content=ft.Text(
                        "JOGO DE DECISÕES FINANCEIRAS",
                        color=CORES["ciano"],
                        size=9,
                        # Altere para aumentar/diminuir o selo acima do título.
                        weight=ft.FontWeight.BOLD,
                        style=ft.TextStyle(letter_spacing=1.5),
                    ),
                    padding=ft.Padding.symmetric(horizontal=10, vertical=4),
                    # Altere para ampliar/reduzir a caixa do selo.
                    bgcolor=_cor_fixa("#103B77"),
                    # Troque o hexadecimal para mudar o fundo do selo.
                    border=_borda(_cor_fixa("#2A73AA")),
                    border_radius=_raio(10),
                ),
                # TÍTULO GRANDE:
                # spacing=11 separa "RESPONDA" de "OU ESTUDA";
                # wrap=True permite quebrar a linha em janelas menores.
                ft.Row(
                    controls=[
                        ft.Text(
                            "RESPONDA",
                            color=CORES["amarelo"],
                            # TAMANHO DA PALAVRA "RESPONDA".
                            size=43,
                            # Altere este número para aumentar/diminuir RESPONDA.
                            weight=ft.FontWeight.BOLD,
                            style=ft.TextStyle(
                                shadow=[
                                    _sombra("#77000000", 4, 4),
                                    _sombra("#55FF8A20", 16, 0),
                                ]
                            ),
                        ),
                        ft.Text(
                            "OU ESTUDA",
                            color=CORES["ciano"],
                            # TAMANHO DA EXPRESSÃO "OU ESTUDA".
                            size=43,
                            # Altere este número para aumentar/diminuir OU ESTUDA.
                            weight=ft.FontWeight.BOLD,
                            style=ft.TextStyle(
                                shadow=[
                                    _sombra("#77000000", 4, 4),
                                    _sombra("#5500BDEB", 16, 0),
                                ]
                            ),
                        ),
                    ],
                    spacing=11,
                    # Aumente para separar mais RESPONDA de OU ESTUDA.
                    wrap=True,
                    # False impede quebra de linha, mas pode causar corte em
                    # janelas estreitas; por isso, recomenda-se manter True.
                    run_spacing=0,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                ft.Text(
                    "Decida com estratégia, aprenda no seu ritmo e lidere o ranking.",
                    color=CORES["branco"],
                    size=12,
                    # Altere para aumentar/diminuir a frase abaixo do título.
                    weight=ft.FontWeight.W_600,
                ),
            ],
            spacing=5,
            # Distância vertical entre selo, título e frase.
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.START,
            # Troque START por CENTER para centralizar o bloco de título.
            col={"xs": 12, "sm": 12, "md": 7},
            # Em tela média, o título usa 7/12 e as regras usam 5/12.
        )

        # REGRAS DO JOGO:
        # Para alterar os textos ou valores, mude "ACERTO", "+ R$ 100", "ERRO",
        # "− R$ 200", "ESTUDAR" e "R$ 0" nas chamadas abaixo.
        # As cores vêm de CORES["verde"], ["vermelho"] e ["ciano"].
        regras = ft.Container(
            content=ft.ResponsiveRow(
                controls=[
                    regra(
                        ft.Icons.CHECK_CIRCLE,
                        "ACERTO",
                        "+ R$ 100",
                        CORES["verde"],
                    ),
                    regra(
                        ft.Icons.CANCEL,
                        "ERRO",
                        "− R$ 200",
                        CORES["vermelho"],
                    ),
                    regra(
                        ft.Icons.MENU_BOOK,
                        "ESTUDAR",
                        "+ R$ 50",
                        CORES["ciano"],
                    ),
                ],
                columns=12,
                spacing=7,
                # Distância horizontal entre ACERTO, ERRO e ESTUDAR.
                run_spacing=7,
            ),
            col={"xs": 12, "sm": 12, "md": 5},
            # Para dar mais largura às regras, use md=6 e mude o título para md=6.
        )

        # PAINEL DO TÍTULO:
        # height controla a altura total do painel. Se aumentar a fonte do
        # título, talvez seja necessário aumentar height.
        # padding: horizontal afasta das laterais; vertical afasta topo/base.
        # As três cores em gradient formam o fundo.
        return ft.Container(
            content=ft.ResponsiveRow(
                controls=[identidade, regras],
                # Inverta os dois nomes se quiser as regras antes do título.
                columns=12,
                spacing=16,
                # Distância horizontal entre o título e as regras.
                run_spacing=9,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            height=164,
            # Aumente se ampliar muito o título; diminua para compactar o painel.
            padding=ft.Padding.symmetric(horizontal=22, vertical=15),
            # horizontal altera as laterais; vertical altera topo e base.
            gradient=ft.LinearGradient(
                begin=ft.Alignment.TOP_LEFT,
                end=ft.Alignment.BOTTOM_RIGHT,
                colors=[
                    CORES["azul_cartao"],
                    CORES["azul_botao"],
                    CORES["fundo_meio"],
                ],
                stops=[0.0, 0.52, 1.0],
                # Os números indicam onde cada cor do degradê se concentra.
            ),
            border=_borda(CORES["ciano_2"], 2),
            # O número 2 é a espessura da borda do painel do título.
            border_radius=_raio(18),
            # Aumente para deixar os cantos mais arredondados.
            shadow=[
                _sombra("#6600BDEB", 18, 0),
                _sombra("#55000000", 14, 5),
            ],
        )

    @staticmethod
    def _tema_economia() -> dict[str, str]:
        """Cores da tela inicial no formato das telas do Modo economia."""
        return {
            "texto": CORES["branco"],
            "primaria": CORES["ciano"],
            "destaque": CORES["amarelo"],
            "positivo": CORES["verde"],
            "negativo": CORES["vermelho"],
            "cartao": CORES["azul_cartao"],
            "cartao_2": CORES["azul_cartao_2"],
            "fundo_1": CORES["fundo_topo"],
            "suave": CORES["texto_suave"],
        }

    def _ao_passar_mes(self, avisos: list[str]) -> None:
        """Chamado a cada "mês" do Modo economia (avisos de juros e bônus)."""
        for aviso in avisos:
            if "teto" in aviso or "bônus" in aviso.lower():
                self._mostrar_aviso(aviso.upper())

    def _alternar_economia(self, evento: ft.ControlEvent) -> None:
        """Liga/desliga o Modo economia (cofrinho, ajudas, juros e bônus)."""
        self.estado.definir_economia(bool(evento.control.value))
        self._reconstruir_inicio()

    def _construir_painel_jogadores(self) -> ft.Control:
        """Cadastro e saldo ficam visíveis na própria tela inicial."""

        # SELETOR DA QUANTIDADE:
        # O intervalo range(2, 5) cria as opções 2, 3 e 4 jogadores.
        # width=210 muda a largura. dense=True mantém o campo compacto.
        # Não altere on_select para preservar o cadastro.
        seletor_quantidade = ft.Dropdown(
            value=str(self.estado.quantidade_jogadores),
            options=[
                # 1 = modo individual (útil com o Modo economia ligado).
                ft.DropdownOption(
                    key=str(numero),
                    text="1 jogador" if numero == 1 else f"{numero} jogadores",
                )
                for numero in range(1, 5)
            ],
            label="Quantidade de jogadores",
            leading_icon=ft.Icons.GROUPS,
            bgcolor=CORES["azul_cartao_2"],
            color=CORES["branco"],
            border_color=CORES["ciano"],
            focused_border_color=CORES["amarelo"],
            border_radius=12,
            dense=True,
            width=210,
            # Aumente para alargar a caixa de quantidade; diminua para estreitar.
            on_select=self._alterar_quantidade_jogadores,
            # Não remova: esta linha reconstrói os cartões ao mudar a quantidade.
        )

        self.campos_nomes = []
        cartoes = []
        for indice, jogador in enumerate(self.estado.jogadores_ativos()):
            # CAIXA DE TEXTO DO NOME:
            # height e text_size controlam o tamanho. content_padding move o
            # texto dentro da caixa. As cores e bordas podem ser trocadas aqui.
            # on_change atualiza o nome em memória; on_blur salva ao sair do campo.
            campo = ft.TextField(
                value=str(jogador["nome"]),
                label=f"Jogador {indice + 1}",
                hint_text="Nome",
                filled=True,
                bgcolor=CORES["azul_cartao_2"],
                color=CORES["branco"],
                border_color=CORES["ciano_2"],
                focused_border_color=CORES["amarelo"],
                border_radius=11,
                dense=True,
                text_size=12,
                # Altere para aumentar/diminuir o nome digitado.
                height=42,
                # Altere para aumentar/diminuir a altura da caixa de nome.
                content_padding=ft.Padding.symmetric(horizontal=10, vertical=7),
                # horizontal move o texto para dentro; vertical ajusta cima/baixo.
                on_change=partial(self._alterar_nome_local, indice),
                # Não remova: atualiza o nome enquanto o usuário digita.
                on_blur=partial(self._salvar_nome_jogador, indice),
                # Não remova: salva o nome quando o campo perde o foco.
            )
            self.campos_nomes.append(campo)

            imagem_relativa = str(jogador.get("imagem", ""))
            if imagem_relativa:
                # FOTO DO JOGADOR:
                # width/height definem o tamanho. COVER preenche o círculo,
                # podendo cortar as bordas da fotografia.
                avatar_conteudo: ft.Control = ft.Image(
                    src=imagem_relativa,
                    width=48,
                    # Altere junto com height para aumentar/diminuir a foto.
                    height=48,
                    # Use o mesmo valor de width para manter a foto quadrada.
                    fit=ft.BoxFit.COVER,
                    # COVER preenche o círculo e pode cortar bordas da imagem.
                    border_radius=_raio(24),
                    # Metade de 48 produz o formato circular.
                    error_content=ft.Icon(
                        ft.Icons.PERSON,
                        color=CORES["amarelo"],
                        size=28,
                    ),
                )
            else:
                # ÍCONE PADRÃO quando o jogador não escolheu uma imagem.
                avatar_conteudo = ft.Icon(
                    ft.Icons.PERSON,
                    color=CORES["amarelo"],
                    size=28,
                    # Altere para aumentar/diminuir o ícone sem foto.
                )

            # BOTÃO CIRCULAR DA FOTO:
            # O Stack sobrepõe o pequeno ícone de câmera à foto.
            # right=0 e bottom=0 colocam a câmera no canto inferior direito.
            # Para movê-la: aumente right para esquerda ou bottom para cima.
            avatar = ft.Container(
                content=ft.Stack(
                    controls=[
                        avatar_conteudo,
                        ft.Container(
                            content=ft.Icon(
                                ft.Icons.ADD_A_PHOTO,
                                color=CORES["fundo_topo"],
                                size=11,
                                # Altere para aumentar/diminuir o símbolo da câmera.
                            ),
                            width=20,
                            # Altere junto com height para mudar o botão da câmera.
                            height=20,
                            right=0,
                            # Aumente para deslocar a câmera para a esquerda.
                            bottom=0,
                            # Aumente para deslocar a câmera para cima.
                            alignment=ft.Alignment.CENTER,
                            bgcolor=CORES["amarelo"],
                            border_radius=_raio(10),
                        ),
                    ],
                    width=48,
                    # Área interna da foto; mantenha igual à imagem.
                    height=48,
                ),
                width=52,
                # Área externa com borda; deve ser um pouco maior que a foto.
                height=52,
                alignment=ft.Alignment.CENTER,
                bgcolor=CORES["fundo_topo"],
                border=_borda(CORES["ciano"], 2),
                border_radius=_raio(26),
                clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
                ink=True,
                on_click=partial(
                    self._selecionar_imagem_jogador,
                    indice,
                ),
                tooltip=(
                    "Trocar a imagem do jogador"
                    if imagem_relativa
                    else "Escolher uma imagem para o jogador"
                ),
            )
            saldo = float(jogador["saldo"])

            # CARTÃO INDIVIDUAL DO JOGADOR:
            # controls=[avatar, coluna] coloca a foto à esquerda dos dados.
            # Para colocar a foto à direita, inverta a ordem desses dois itens.
            # spacing separa a foto dos dados; padding é a margem interna.
            cartoes.append(
                ft.Container(
                    content=ft.Row(
                        controls=[
                            avatar,
                            ft.Column(
                                controls=[
                                    campo,
                                    ft.Row(
                                        controls=[
                                            ft.Text(
                                                "SALDO DAS QUESTÕES"
                                                if self.estado.economia_ativa
                                                else "PONTUAÇÃO TOTAL",
                                                color=CORES["texto_suave"],
                                                size=9,
                                                weight=ft.FontWeight.BOLD,
                                            ),
                                            ft.Text(
                                                formatar_reais(saldo),
                                                color=(
                                                    CORES["verde"]
                                                    if saldo >= 0
                                                    else CORES["vermelho"]
                                                ),
                                                size=15,
                                                weight=ft.FontWeight.BOLD,
                                            ),
                                        ],
                                        spacing=7,
                                        alignment=(
                                            ft.MainAxisAlignment.SPACE_BETWEEN
                                        ),
                                    ),
                                ],
                                spacing=3,
                                expand=True,
                                horizontal_alignment=(
                                    ft.CrossAxisAlignment.STRETCH
                                ),
                            ),
                        ],
                        spacing=9,
                        # Distância horizontal entre avatar e dados do jogador.
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    padding=9,
                    # Margem interna do cartão de cada jogador.
                    gradient=ft.LinearGradient(
                        begin=ft.Alignment.TOP_LEFT,
                        end=ft.Alignment.BOTTOM_RIGHT,
                        colors=[CORES["azul_cartao_2"], CORES["azul_cartao"]],
                    ),
                    border=_borda(CORES["ciano_2"]),
                    # Altere esta cor para mudar o contorno dos cartões.
                    border_radius=_raio(14),
                    # Aumente para arredondar mais os cartões.
                    shadow=_sombra("#33000000", 8, 2),
                    # LARGURA RESPONSIVA:
                    # lg=3 permite quatro cartões por linha (4 × 3 = 12).
                    # lg=4 mostraria três; lg=6 mostraria dois por linha.
                    col={"xs": 12, "sm": 6, "md": 6, "lg": 3},
                    # Se quiser dois cartões largos por linha, use lg=6.
                )
            )

        # PAINEL GERAL DE JOGADORES:
        # O primeiro Row contém o título e o seletor de quantidade.
        # O ResponsiveRow seguinte contém os cartões criados acima.
        # Para mover o seletor abaixo do título em qualquer largura, troque esse
        # primeiro ft.Row por uma ft.Column (isso altera somente o layout).
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Column(
                                controls=[
                                    ft.Row(
                                        controls=[
                                            ft.Icon(
                                                ft.Icons.GROUPS,
                                                color=CORES["ciano"],
                                                size=18,
                                            ),
                                            ft.Text(
                                            "JOGADORES",
                                            color=CORES["amarelo"],
                                            size=16,
                                            # Altere para aumentar/diminuir o título.
                                            weight=ft.FontWeight.BOLD,
                                            ),
                                        ],
                                        spacing=7,
                                    ),
                                    ft.Text(
                                        "PERFIS E SALDOS DA PARTIDA",
                                        color=CORES["texto_suave"],
                                        size=8,
                                        # Altere para aumentar/diminuir o subtítulo.
                                        weight=ft.FontWeight.BOLD,
                                        style=ft.TextStyle(letter_spacing=1.1),
                                    ),
                                ],
                                spacing=1,
                            ),
                            seletor_quantidade,
                            # Para colocar o seletor antes do título, mova esta
                            # linha para antes de ft.Column(...).
                            # MODO ECONOMIA: cofrinho, ajudas, juros e bônus.
                            # Desligado = jogo usado nas coletas da pesquisa.
                            ft.Switch(
                                label="MODO ECONOMIA",
                                value=self.estado.economia_ativa,
                                active_color=CORES["amarelo"],
                                label_text_style=ft.TextStyle(
                                    color=CORES["branco"], size=13, weight=ft.FontWeight.BOLD
                                ),
                                tooltip=(
                                    "Liga o cofrinho (1% por minuto de jogo), as ajudas "
                                    "(R$ 20,00), os juros sobre saldo negativo e o bônus "
                                    "de participação. Desligado, o jogo é o da pesquisa."
                                ),
                                on_change=self._alternar_economia,
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.START,
                        # START leva os dois blocos à esquerda; END leva à direita.
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        wrap=True,
                        run_spacing=10,
                    ),
                    *(
                        economia_tela.aplicar_no_placar(
                            self, cartoes, self.estado.jogadores_ativos(), self._tema_economia()
                        )
                        or []
                    ),
                    ft.ResponsiveRow(
                        controls=cartoes,
                        columns=12,
                        # Distância horizontal e vertical entre cartões.
                        spacing=8,
                        # Distância horizontal entre os cartões dos jogadores.
                        run_spacing=8,
                        # Distância vertical quando os cartões quebrarem de linha.
                    ),
                ],
                spacing=8,
                # Distância entre cabeçalho do painel e cartões.
            ),
            padding=10,
            # Margem interna do painel completo dos jogadores.
            bgcolor=_cor_fixa("#071E4D"),
            # Troque este hexadecimal para mudar o fundo do painel.
            border=_borda(_cor_fixa("#245F96")),
            # Troque este hexadecimal para mudar a borda do painel.
            border_radius=_raio(16),
            shadow=_sombra("#44000000", 12, 4),
        )

    def _construir_painel_missao(self) -> ft.Control:
        # IMAGEM/MASCOTE:
        # Troque ARQUIVO_IMAGEM_MISSAO nas configurações ou substitua o arquivo
        # dentro de assets. width/height alteram a área da imagem.
        # CONTAIN preserva a imagem inteira sem cortá-la.
        imagem = ft.Image(
            src=ARQUIVO_IMAGEM_MISSAO,
            # Para usar outra imagem, altere o nome em
            # ARQUIVO_IMAGEM_MISSAO, no início deste arquivo.
            width=170,
            # Para ampliar/reduzir a mascote, altere width e height juntos.
            # Exemplo maior: width=190. Exemplo menor: width=140.
            height=138,
            # Exemplo maior: height=170. Use valores próximos para não deformar.
            fit=ft.BoxFit.CONTAIN,
            # CONTAIN mostra a imagem inteira. COVER preenche toda a área, mas
            # pode cortar as bordas da foto.
            border_radius=_raio(12),
            # Aumente 12 para arredondar mais os cantos da imagem.
            semantics_label="Mascote do jogo Responda ou Estuda",
            error_content=ft.Column(
                controls=[
                    ft.Icon(
                        ft.Icons.IMAGE_OUTLINED,
                        color=CORES["amarelo"],
                        size=30,
                    ),
                    ft.Text(
                        TEXTOS_TELA["imagem_vazia"],
                        color=CORES["texto_suave"],
                        size=7,
                        weight=ft.FontWeight.BOLD,
                        text_align=ft.TextAlign.CENTER,
                    ),
                ],
                spacing=8,
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
        )

        # CARTÃO DA IMAGEM:
        # height controla a altura do cartão; padding cria margem ao redor da
        # imagem; sm/md=2 reserva 2 das 12 colunas em telas maiores.
        cartao_imagem = ft.Container(
            content=imagem,
            height=150,
            # Para aumentar a mascote, aumente esta altura (150) e também width/height
            # da imagem acima. Mantenha 150 nos três cartões desta faixa.
            alignment=ft.Alignment.CENTER,
            # TOP_CENTER move a mascote para cima; BOTTOM_CENTER move para baixo.
            padding=4,
            # Diminua para a mascote ocupar mais espaço; aumente para criar margem.
            bgcolor=_cor_fixa("#03163B"),
            # Troque este hexadecimal para alterar apenas o fundo da mascote.
            border=_borda(CORES["ciano"]),
            # Troque CORES["ciano"] por outra cor da paleta para mudar a borda.
            border_radius=_raio(14),
            col={"xs": 12, "sm": 3, "md": 3},
            # O valor 3 dá 3/12 da largura à mascote. Para usar 4/12, reduza a
            # estratégia para 5/12, mantendo a soma 4 + 5 + 3 = 12.
        )

        # CARTÃO "ESTRATÉGIA DA RODADA":
        # Para editar a frase, altere somente o texto entre aspas abaixo.
        # controls=[ícone, coluna] mantém o ícone à esquerda.
        # size do ícone e size dos ft.Text mudam suas dimensões.
        cartao_missao = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Icon(
                        ft.Icons.LIGHTBULB,
                        color=CORES["amarelo"],
                        size=34,
                        # Altere este valor para aumentar/diminuir a lâmpada.
                    ),
                    ft.Column(
                        controls=[
                            ft.Text(
                                "ESTRATÉGIA DA RODADA",
                                color=CORES["ciano"],
                                # Para mudar a cor, use outra chave de CORES.
                                size=10,
                                # Altere para aumentar/diminuir o título.
                                weight=ft.FontWeight.BOLD,
                                style=ft.TextStyle(letter_spacing=1.1),
                            ),
                            ft.Text(
                                (
                                    "Responder pode aumentar ou reduzir seu saldo. "
                                    "Estudar acrescenta R$ 50,00 ao saldo e prepara a próxima jogada."
                                ),
                                color=CORES["branco"],
                                # Troque por CORES["texto_suave"] para menos
                                # destaque ou por outra cor da paleta.
                                size=12,
                                # Altere para aumentar/diminuir a explicação.
                                weight=ft.FontWeight.W_600,
                            ),
                        ],
                        spacing=3,
                        expand=True,
                        alignment=ft.MainAxisAlignment.CENTER,
                    ),
                ],
                spacing=14,
                # Controla a distância entre a lâmpada e os textos.
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            height=150,
            # Mantenha igual à altura dos cartões de mascote e progresso.
            padding=ft.Padding.symmetric(horizontal=18, vertical=12),
            # horizontal move o conteúdo para dentro dos lados; vertical cria
            # distância do topo e da base.
            bgcolor=_cor_fixa("#08285C"),
            # Troque este hexadecimal para alterar só o fundo da estratégia.
            border=_borda(_cor_fixa("#245F96")),
            # Troque este hexadecimal para alterar só a borda da estratégia.
            border_radius=_raio(14),
            col={"xs": 12, "sm": 6, "md": 6},
            # Aumente 6 para alargar a estratégia e reduza outra coluna para que
            # mascote + estratégia + progresso continuem somando 12.
        )

        # CARTÃO DE PROGRESSO:
        # "01" e "/ 05 ETAPAS" são os textos exibidos.
        # value=0.2 preenche 20% da barra; valores possíveis vão de 0.0 a 1.0.
        # color é a parte preenchida; bgcolor é a parte restante.
        cartao_progresso = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text(
                        "PROGRESSO",
                        color=CORES["texto_suave"],
                        size=9,
                        # Altere para aumentar/diminuir o rótulo PROGRESSO.
                        weight=ft.FontWeight.BOLD,
                        style=ft.TextStyle(letter_spacing=1.0),
                    ),
                    ft.Row(
                        controls=[
                            ft.Text(
                                "01",
                                color=CORES["amarelo"],
                                size=38,
                                # Altere para aumentar/diminuir o número da etapa.
                                weight=ft.FontWeight.BOLD,
                            ),
                            ft.Text(
                                "/ 05 ETAPAS",
                                color=CORES["ciano"],
                                size=12,
                                # Altere para aumentar/diminuir este complemento.
                                weight=ft.FontWeight.BOLD,
                            ),
                        ],
                        spacing=7,
                        alignment=ft.MainAxisAlignment.CENTER,
                        vertical_alignment=ft.CrossAxisAlignment.END,
                    ),
                    ft.ProgressBar(
                        value=0.2,
                        # Use 0.4 para 2/5, 0.6 para 3/5, 0.8 para 4/5 e 1.0
                        # para 5/5 quando as próximas etapas forem implementadas.
                        color=CORES["amarelo"],
                        # Cor da parte preenchida da barra.
                        bgcolor=_cor_fixa("#174C75"),
                        # Cor da parte ainda não preenchida.
                        height=7,
                        # Altere para deixar a barra mais fina ou mais grossa.
                        border_radius=_raio(3),
                    ),
                ],
                spacing=8,
                # Controla a distância vertical entre rótulo, número e barra.
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
            ),
            height=150,
            # Mantenha igual à altura dos cartões de mascote e estratégia.
            padding=ft.Padding.symmetric(horizontal=15, vertical=12),
            # Aumente horizontal para afastar a barra das laterais.
            bgcolor=_cor_fixa("#063653"),
            # Troque este hexadecimal para alterar apenas o fundo do progresso.
            border=_borda(CORES["verde"]),
            # Troque CORES["verde"] por outra cor para mudar o contorno.
            border_radius=_raio(14),
            col={"xs": 12, "sm": 3, "md": 3},
            # Para alargar o progresso, aumente 3 e reduza a estratégia.
        )

        # ORGANIZAÇÃO DOS TRÊS CARTÕES:
        # Em telas sm/md: 3 + 6 + 3 = 12 colunas.
        # Para aumentar a missão, aumente seu col e reduza imagem/progresso.
        # spacing e run_spacing controlam as distâncias entre os cartões.
        return ft.Container(
            content=ft.ResponsiveRow(
                controls=[cartao_imagem, cartao_missao, cartao_progresso],
                # Para mudar a ordem, reorganize somente estes três nomes.
                columns=12,
                spacing=8,
                # Distância horizontal entre os três cartões.
                run_spacing=8,
                # Distância vertical quando eles quebrarem em telas estreitas.
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=8,
            # Margem interna do painel completo de missão.
            bgcolor=_cor_fixa("#071E4D"),
            # Fundo externo que envolve mascote, estratégia e progresso.
            border=_borda(_cor_fixa("#245F96")),
            border_radius=_raio(16),
            shadow=_sombra("#44020A25", 12, 4),
        )

    def _construir_seletor_assuntos(self) -> ft.Control:
        # MENU LATERAL DAS ETAPAS:
        # Os cartões são gerados com os dados da lista ASSUNTOS.
        # Para mudar a ordem das etapas, mude a ordem dos blocos em ASSUNTOS.
        self.cartoes_assuntos.clear()
        controles = [
            self._construir_cartao_assunto(indice, assunto)
            for indice, assunto in enumerate(ASSUNTOS)
        ]

        # CABEÇALHO "MAPA DO JOGO":
        # size muda ícone/textos; width/height alteram o fundo quadrado do ícone.
        chamada = ft.Row(
            controls=[
                ft.Container(
                    content=ft.Icon(
                        ft.Icons.MAP,
                        color=CORES["fundo_topo"],
                        size=17,
                    ),
                    width=34,
                    height=34,
                    alignment=ft.Alignment.CENTER,
                    bgcolor=CORES["ciano"],
                    border_radius=_raio(11),
                ),
                ft.Column(
                    controls=[
                        ft.Text(
                            "MAPA DO JOGO",
                            color=CORES["branco"],
                            size=14,
                            weight=ft.FontWeight.BOLD,
                        ),
                        ft.Text(
                            "ESCOLHA UMA ETAPA",
                            color=CORES["ciano"],
                            size=8,
                            weight=ft.FontWeight.BOLD,
                            style=ft.TextStyle(letter_spacing=1.0),
                        ),
                    ],
                    spacing=0,
                ),
            ],
            spacing=10,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

        # PAINEL DO MENU:
        # spacing=8 é a distância vertical entre cabeçalho, linha e botões.
        # padding=11 é a margem interna. bgcolor/border definem fundo e contorno.
        return ft.Container(
            content=ft.Column(
                controls=[
                    chamada,
                    ft.Container(
                        height=1,
                        gradient=ft.LinearGradient(
                            begin=ft.Alignment.CENTER_LEFT,
                            end=ft.Alignment.CENTER_RIGHT,
                            colors=[CORES["ciano_2"], "#00174F89"],
                        ),
                    ),
                    *controles,
                ],
                spacing=6,
                horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
            ),
            padding=11,
            bgcolor=_cor_fixa("#071E4D"),
            border=_borda(_cor_fixa("#245F96")),
            border_radius=_raio(16),
            shadow=_sombra("#66020A25", 14, 5),
        )

    def _construir_cartao_assunto(
        self,
        indice: int,
        assunto: dict[str, Any],
    ) -> ft.Container:
        # CORES DO BOTÃO ATIVO/BLOQUEADO:
        # Todas são escolhidas automaticamente conforme assunto["ativo"].
        # Altere as referências abaixo para personalizar cada estado.
        ativo = bool(assunto["ativo"])
        cor_fundo = CORES["azul_botao"] if ativo else CORES["azul_bloqueado"]
        cor_contorno = CORES["ciano"] if ativo else "#3B76A9"
        cor_texto = CORES["amarelo"] if ativo else "#A4CDE2"
        descricao = str(assunto["descricao"]).replace("\n", " ")
        nome_exibicao = str(assunto["nome"]) if ativo else f"ETAPA {indice + 1}"

        # ÍCONE DO BOTÃO:
        # width/height alteram a caixa; size altera somente o símbolo.
        # bgcolor, border e border_radius alteram sua aparência.
        icone = ft.Container(
            content=ft.Text(
                str(assunto["icone"]),
                color=CORES["branco"] if ativo else "#8FB9D6",
                size=18 if ativo else 14,
                weight=ft.FontWeight.BOLD,
            ),
            width=38,
            height=38,
            alignment=ft.Alignment.CENTER,
            bgcolor=CORES["laranja"] if ativo else "#12386C",
            border=_borda(
                CORES["amarelo"] if ativo else "#3C6A97",
                2,
            ),
            border_radius=_raio(12),
        )

        # CARTÃO/BOTÃO DA ETAPA:
        # height=62 é usado no ativo e 54 nos bloqueados.
        # padding altera a margem interna e spacing separa número, ícone e texto.
        # on_click mantém a ação; on_hover mantém a animação.
        cartao = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Container(
                        content=ft.Text(
                            f"{indice + 1:02d}",
                            color=(
                                CORES["texto_suave"] if ativo else "#6E9CC0"
                            ),
                            size=9,
                            weight=ft.FontWeight.BOLD,
                        ),
                        width=20,
                        alignment=ft.Alignment.CENTER,
                    ),
                    icone,
                    ft.Column(
                        controls=[
                            ft.Row(
                                controls=[
                                    ft.Text(
                                        nome_exibicao,
                                        color=cor_texto,
                                        size=13,
                                        weight=ft.FontWeight.BOLD,
                                        expand=True,
                                    ),
                                    ft.Icon(
                                        (
                                            ft.Icons.LOCK_OPEN
                                            if ativo
                                            else ft.Icons.LOCK
                                        ),
                                        color=(
                                            CORES["verde"]
                                            if ativo
                                            else "#6E9CC0"
                                        ),
                                        size=13,
                                    ),
                                ],
                                spacing=5,
                            ),
                            (
                                ft.Text(
                                    descricao,
                                    color=CORES["branco"],
                                    size=9,
                                    weight=ft.FontWeight.W_600,
                                    max_lines=1,
                                    overflow=ft.TextOverflow.ELLIPSIS,
                                )
                                if ativo
                                else ft.Container(height=1)
                            ),
                            (
                                ft.Text(
                                    "JOGAR",
                                    color=CORES["verde"],
                                    size=9,
                                    weight=ft.FontWeight.BOLD,
                                )
                                if ativo
                                else ft.Container(height=1)
                            ),
                        ],
                        spacing=1,
                        expand=True,
                    ),
                ],
                spacing=8,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            height=56 if ativo else 46,
            # Altura das etapas reduzida para a tela inicial caber sem rolar.
            padding=ft.Padding.symmetric(horizontal=8, vertical=4),
            bgcolor=cor_fundo,
            border=_borda(cor_contorno, 2),
            border_radius=_raio(13),
            shadow=_sombra(
                "#4400BDEB" if ativo else "#22000000",
                8,
                2,
            ),
            ink=True,
            ink_color="#2459F4FF",
            on_click=partial(self._selecionar_assunto, indice),
            on_hover=lambda evento, numero=indice: self._animar_hover(
                numero,
                evento,
            ),
            animate=180,
            animate_scale=180,
            animate_offset=180,
            # TOOLTIP: texto mostrado quando o mouse repousa no cartão.
            tooltip=(
                f"Abrir o desafio de {assunto['nome'].lower()}"
                if ativo
                else "Assunto ainda bloqueado"
            ),
        )
        self.cartoes_assuntos.append(cartao)
        return cartao

    def _construir_rodape(self) -> ft.Control:
        # RODAPÉ:
        # O texto principal vem de TEXTOS_TELA["rodape"].
        # SPACE_BETWEEN coloca um item em cada extremidade.
        # wrap=False evita quebra de linha; mude para True se aumentar os textos.
        return ft.Row(
            controls=[
                ft.Text(
                    TEXTOS_TELA["rodape"],
                    color="#6BCBE9",
                    size=10,
                    weight=ft.FontWeight.BOLD,
                    text_align=ft.TextAlign.CENTER,
                ),
                ft.Row(
                    controls=[
                        ft.Icon(
                            ft.Icons.CLOUD_DONE,
                            color=CORES["verde"],
                            size=13,
                        ),
                        ft.Text(
                            "PROGRESSO SALVO",
                            color=CORES["texto_suave"],
                            size=8,
                            weight=ft.FontWeight.BOLD,
                        ),
                    ],
                    spacing=4,
                    tight=True,
                ),
            ],
            spacing=12,
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            wrap=False,
        )

    # ------------------------------------------------------------------
    # Interações
    # ------------------------------------------------------------------

    def _reconstruir_inicio(self) -> None:
        # Reconstrói a tela para aplicar tema, nomes, imagens e saldos atualizados.
        # Esta função não é um ponto de personalização visual.
        CORES.update(TEMAS_TELA_INICIAL[self.estado.tema])
        self.tela_inicial = recursos_jogo.sons_nos_botoes(self, self._construir_tela_inicial())
        self.host.content = self.tela_inicial
        self.host.bgcolor = CORES["fundo_topo"]
        self.page.bgcolor = CORES["fundo_topo"]
        # Os atalhos de teclado valem só dentro dos módulos.
        self.page.on_keyboard_event = None
        self.page.update()

    # ------------------------------------------------------------------
    # Acessibilidade
    # ------------------------------------------------------------------

    def _abrir_acessibilidade(self, _evento: ft.ControlEvent) -> None:
        """Janela com as opções de acessibilidade (salvas no estado)."""
        preferencias = self.estado.acessibilidade

        def mudar_tempo(evento: ft.ControlEvent) -> None:
            self.estado.definir_acessibilidade(tempo=int(evento.control.value))

        def mudar_animacoes(evento: ft.ControlEvent) -> None:
            self.estado.definir_acessibilidade(sem_animacoes=bool(evento.control.value))

        def mudar_contraste(evento: ft.ControlEvent) -> None:
            if evento.control.value:
                if self.estado.tema != "Alto contraste":
                    self.estado.definir_acessibilidade(tema_anterior=self.estado.tema)
                self.estado.definir_tema("Alto contraste")
            else:
                anterior = preferencias.get("tema_anterior") or "Financeiro"
                self.estado.definir_tema(anterior if anterior != "Alto contraste" else "Financeiro")

        def fechar(_e: ft.ControlEvent) -> None:
            self.page.pop_dialog()
            self._reconstruir_inicio()

        def titulo_secao(texto: str) -> ft.Control:
            return ft.Text(texto, weight=ft.FontWeight.BOLD, size=15)

        def explicacao(texto: str) -> ft.Control:
            return ft.Text(texto, size=12, color=ft.Colors.ON_SURFACE_VARIANT)

        self._mostrar_dialogo(
            ft.AlertDialog(
                modal=True,
                title=ft.Row(
                    controls=[
                        ft.Icon(ft.Icons.ACCESSIBILITY_NEW),
                        ft.Text("Acessibilidade"),
                    ],
                    spacing=10,
                ),
                content=ft.Container(
                    width=560,
                    content=ft.Column(
                        tight=True,
                        spacing=10,
                        controls=[
                            titulo_secao("Tempo para cada questão"),
                            ft.RadioGroup(
                                value=str(preferencias.get("tempo", 60)),
                                on_change=mudar_tempo,
                                content=ft.Row(
                                    controls=[
                                        ft.Radio(value="60", label="60 s"),
                                        ft.Radio(value="90", label="90 s"),
                                        ft.Radio(value="120", label="120 s"),
                                        ft.Radio(value="0", label="Sem limite"),
                                    ],
                                    wrap=True,
                                ),
                            ),
                            explicacao(
                                "Mais tempo ajuda quem lê com a lupa, com leitor de voz "
                                "ou tem dislexia/TDAH. A opção usada fica registrada "
                                "nos dados da pesquisa."
                            ),
                            ft.Divider(),
                            ft.Switch(
                                label="Sem animações (transições, pulsos e saldo animado)",
                                value=bool(preferencias.get("sem_animacoes")),
                                on_change=mudar_animacoes,
                            ),
                            ft.Switch(
                                label="Tema de alto contraste (preto, branco e amarelo)",
                                value=self.estado.tema == "Alto contraste",
                                on_change=mudar_contraste,
                            ),
                            ft.Divider(),
                            titulo_secao("Sempre disponíveis"),
                            explicacao(
                                "• Acerto e erro são indicados com cor, ícone e palavra "
                                "(✓ CORRETA / ✗ SUA ESCOLHA).\n"
                                "• LUPA: amplia o que estiver sob o mouse.\n"
                                "• OUVIR QUESTÃO: leitura em voz alta, com velocidade ajustável.\n"
                                "• Atalhos: R responder · E estudar · A–E ou 1–5 alternativas "
                                "· Enter avançar."
                            ),
                        ],
                    ),
                ),
                actions=[
                    ft.Button(content="SALVAR E FECHAR", icon=ft.Icons.CHECK, on_click=fechar),
                ],
            )
        )

    # ------------------------------------------------------------------
    # Nova turma
    # ------------------------------------------------------------------

    def _confirmar_nova_turma(self, _evento: ft.ControlEvent) -> None:
        """Pergunta antes de arquivar a turma atual."""

        def fechar(_e: ft.ControlEvent) -> None:
            self.page.pop_dialog()

        def confirmar(_e: ft.ControlEvent) -> None:
            self.page.pop_dialog()
            self._arquivar_turma()

        self._mostrar_dialogo(
            ft.AlertDialog(
                modal=True,
                title=ft.Text("Começar uma nova turma?"),
                content=ft.Text(
                    "Os jogadores, saldos, ranking e respostas registradas serão "
                    "guardados na pasta dados/turmas e o jogo recomeçará do zero.\n\n"
                    "Nada é apagado: os dados da turma atual continuam "
                    "disponíveis nessa pasta."
                ),
                actions=[
                    ft.TextButton(content="CANCELAR", on_click=fechar),
                    ft.Button(
                        content="ARQUIVAR E COMEÇAR",
                        icon=ft.Icons.ARCHIVE,
                        on_click=confirmar,
                    ),
                ],
            )
        )

    def _arquivar_turma(self) -> None:
        """Move os dados da turma para dados/turmas/AAAA-MM-DD_HHhMM."""
        from datetime import datetime

        import recursos_jogo

        pasta_dados = self.estado.caminho.parent
        destino = pasta_dados / "turmas" / datetime.now().strftime("%Y-%m-%d_%Hh%M")
        arquivos = [
            self.estado.caminho,
            recursos_jogo.ARQUIVO_RESPOSTAS,
            recursos_jogo.ARQUIVO_POR_QUESTAO,
            recursos_jogo.ARQUIVO_POR_JOGADOR,
        ]
        if self.estado.gerar_ranking:
            arquivos.append(pasta_dados / "ranking.xlsx")
        preferencias = {
            chave: self.estado.dados.get(chave)
            for chave in ("tema", "trilha", "trilhas_personalizadas")
        }
        try:
            destino.mkdir(parents=True, exist_ok=True)
            movidos = 0
            for arquivo in arquivos:
                if arquivo.exists():
                    shutil.move(str(arquivo), str(destino / arquivo.name))
                    movidos += 1
            # Recria o estado vazio mantendo tema e músicas escolhidos.
            self.estado = (
                criar_estado_admin()
                if ADMIN_ATIVO
                else EstadoJogo(gerar_ranking=self.estado.gerar_ranking)
            )
            self.estado.dados.update(
                {chave: valor for chave, valor in preferencias.items() if valor}
            )
            self.estado.salvar()
            self._reconstruir_inicio()
            self._mostrar_aviso(
                f"NOVA TURMA INICIADA. {movidos} ARQUIVOS GUARDADOS EM "
                f"dados/turmas/{destino.name}"
            )
        except Exception as erro:
            print(f"Erro ao arquivar a turma: {erro}")
            self._mostrar_aviso("NÃO FOI POSSÍVEL ARQUIVAR A TURMA")

    def _alterar_quantidade_jogadores(
        self,
        evento: ft.ControlEvent,
    ) -> None:
        # Salva os nomes, muda a quantidade e redesenha os cartões.
        self._sincronizar_nomes_campos()
        self.estado.definir_quantidade(int(evento.control.value))
        self._reconstruir_inicio()

    def _alterar_nome_local(
        self,
        indice: int,
        evento: ft.ControlEvent,
    ) -> None:
        # Atualiza o nome enquanto o usuário digita.
        self.estado.jogadores[indice]["nome"] = str(evento.control.value).strip()

    def _salvar_nome_jogador(
        self,
        indice: int,
        evento: ft.ControlEvent,
    ) -> None:
        # Salva definitivamente o nome quando o campo perde o foco.
        self.estado.definir_nome(indice, str(evento.control.value))

    def _sincronizar_nomes_campos(self) -> None:
        # Garante que os nomes digitados sejam preservados antes de trocar telas.
        for indice, campo in enumerate(self.campos_nomes):
            self.estado.jogadores[indice]["nome"] = (campo.value or "").strip()
            self.estado.jogadores[indice]["atualizado_em"] = (
                self.estado.jogadores[indice].get("atualizado_em", "")
            )
        self.estado.salvar()

    @staticmethod
    def _nome_seguro(nome: str) -> str:
        # Remove caracteres inadequados antes de usar um nome em arquivo.
        base = re.sub(r"[^A-Za-z0-9._-]+", "_", nome.strip())
        return base.strip("._") or "arquivo"

    @staticmethod
    def _gravar_arquivo_escolhido(
        arquivo: Any,
        destino: Path,
    ) -> None:
        # Copia a imagem ou música escolhida para a pasta interna do jogo.
        destino.parent.mkdir(parents=True, exist_ok=True)
        if getattr(arquivo, "path", None):
            shutil.copy2(str(arquivo.path), destino)
            return
        conteudo = getattr(arquivo, "bytes", None)
        if conteudo is not None:
            destino.write_bytes(conteudo)
            return
        raise OSError("O arquivo selecionado não pôde ser lido.")

    async def _selecionar_imagem_jogador(
        self,
        indice: int,
        _evento: ft.ControlEvent,
    ) -> None:
        # TIPOS DE IMAGEM ACEITOS:
        # Para permitir/remover formatos, edite allowed_extensions.
        # Não é recomendável mudar file_type=IMAGE.
        arquivos = await self.seletor_arquivo.pick_files(
            dialog_title=f"Escolha a imagem do jogador {indice + 1}",
            file_type=ft.FilePickerFileType.IMAGE,
            allowed_extensions=["png", "jpg", "jpeg", "webp", "gif", "bmp"],
            allow_multiple=False,
            with_data=True,
        )
        if not arquivos:
            return
        arquivo = arquivos[0]
        extensao = Path(arquivo.name).suffix.lower() or ".png"
        nome = f"{uuid.uuid4().hex}_{self._nome_seguro(Path(arquivo.name).stem)}"
        destino = PASTA_ASSETS / "perfis" / f"{nome}{extensao}"
        try:
            self._gravar_arquivo_escolhido(arquivo, destino)
            relativo = destino.relative_to(PASTA_ASSETS).as_posix()
            self.estado.definir_imagem(indice, relativo)
            self._reconstruir_inicio()
        except OSError as erro:
            print(f"Erro ao copiar a imagem: {erro}")
            self._mostrar_aviso("NÃO FOI POSSÍVEL CARREGAR ESSA IMAGEM")

    async def _selecionar_musica(self, _evento: ft.ControlEvent) -> None:
        # TIPOS DE ÁUDIO ACEITOS:
        # Para permitir/remover formatos, edite allowed_extensions.
        # WAV é reproduzido nativamente no Windows; outros formatos usam Flet.
        arquivos = await self.seletor_arquivo.pick_files(
            dialog_title="Escolha uma música para o jogo",
            file_type=ft.FilePickerFileType.AUDIO,
            allowed_extensions=[
                "wav",
                "mp3",
                "ogg",
                "m4a",
                "aac",
                "flac",
            ],
            allow_multiple=False,
            with_data=True,
        )
        if not arquivos:
            return
        arquivo = arquivos[0]
        extensao = Path(arquivo.name).suffix.lower()
        nome_arquivo = (
            f"{uuid.uuid4().hex}_{self._nome_seguro(Path(arquivo.name).stem)}"
            f"{extensao}"
        )
        destino = PASTA_ASSETS / "sons_personalizados" / nome_arquivo
        try:
            if self.som_ativo:
                await self._parar_audio_atual()
            self._gravar_arquivo_escolhido(arquivo, destino)
            relativo = destino.relative_to(PASTA_ASSETS).as_posix()
            nome_exibicao = self.estado.adicionar_trilha(
                f"Minha música - {Path(arquivo.name).stem}",
                relativo,
            )
            self.audio.src = relativo
            self.audio.update()
            self.som_ativo = False
            self._reconstruir_inicio()
            self._mostrar_aviso(f"MÚSICA SELECIONADA: {nome_exibicao}")
        except OSError as erro:
            print(f"Erro ao copiar a música: {erro}")
            self._mostrar_aviso("NÃO FOI POSSÍVEL CARREGAR ESSA MÚSICA")

    async def _trocar_tema(self, evento: ft.ControlEvent) -> None:
        # Aplica a paleta escolhida e reconstrói a abertura.
        nome = str(evento.control.value)
        self._sincronizar_nomes_campos()
        self.estado.definir_tema(nome)
        self._reconstruir_inicio()

    async def _trocar_trilha(self, evento: ft.ControlEvent) -> None:
        # Troca a música preservando o estado ligado/desligado do som.
        nome = str(evento.control.value)
        if nome not in self.estado.trilhas_disponiveis():
            return
        estava_ativo = self.som_ativo
        if estava_ativo:
            await self._parar_audio_atual()
        self.estado.definir_trilha(nome)
        self.audio.src = self.estado.trilhas_disponiveis()[nome]
        self.audio.update()
        if estava_ativo:
            await self._iniciar_audio_atual()
        self._reconstruir_inicio()

    def _cartao_desempenho(self) -> ft.Control:
        """Resumo das questões com menor índice de acerto nesta turma."""
        import recursos_jogo

        resumo = [
            q
            for q in recursos_jogo.resumo_por_questao(recursos_jogo.ler_respostas())
            if q["tentativas"] > 0
        ]
        respostas = sum(q["tentativas"] for q in resumo)
        dificeis = sorted(resumo, key=lambda q: q["percentual_acerto"])[:5]
        linhas: list[ft.Control] = []
        for q in dificeis:
            percentual = q["percentual_acerto"]
            linhas.append(
                ft.Row(
                    controls=[
                        ft.Container(
                            content=ft.Text(
                                f"{percentual:.0f}%",
                                color=CORES["fundo_topo"],
                                weight=ft.FontWeight.BOLD,
                                size=13,
                            ),
                            bgcolor=CORES["amarelo"] if percentual >= 50 else "#FF8A9E",
                            padding=ft.Padding.symmetric(horizontal=8, vertical=3),
                            border_radius=_raio(8),
                            width=58,
                            alignment=ft.Alignment.CENTER,
                        ),
                        ft.Text(
                            f"{q['modulo']} · {q['questao_id']} · {q['titulo']}",
                            color=CORES["branco"],
                            size=13,
                            expand=True,
                        ),
                        ft.Text(
                            f"{q['acertos']}/{q['tentativas']} acertos",
                            color=CORES["texto_suave"],
                            size=12,
                        ),
                    ],
                    spacing=10,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                )
            )
        if not linhas:
            linhas.append(
                ft.Text(
                    "Ainda não há respostas registradas nesta turma.",
                    color=CORES["texto_suave"],
                    size=13,
                )
            )
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Icon(ft.Icons.INSIGHTS, color=CORES["amarelo"]),
                            ft.Text(
                                "DESEMPENHO DA TURMA · QUESTÕES COM MENOS ACERTOS",
                                color=CORES["amarelo"],
                                weight=ft.FontWeight.BOLD,
                            ),
                        ],
                        spacing=10,
                        wrap=True,
                    ),
                    *linhas,
                    ft.Text(
                        (
                            f"{respostas} respostas registradas. Relatórios completos "
                            "(abrem no Excel): dados/respostas.csv, "
                            "dados/relatorio_por_questao.csv e "
                            "dados/relatorio_por_jogador.csv"
                        ),
                        color=CORES["texto_suave"],
                        size=12,
                    ),
                ],
                spacing=8,
            ),
            padding=14,
            bgcolor=CORES["azul_cartao"],
            border=_borda(CORES["amarelo"]),
            border_radius=_raio(14),
        )

    def _mostrar_ranking(self, _evento: ft.ControlEvent) -> None:
        # TELA DO RANKING:
        # Esta função apenas monta a visualização. A ordenação e a planilha são
        # fornecidas por self.estado.ranking() e self.estado.salvar().
        self._sincronizar_nomes_campos()
        classificacao = self.estado.ranking()
        linhas: list[ft.Control] = []
        for posicao, jogador in enumerate(classificacao, start=1):
            saldo = float(jogador["saldo"])
            patrimonio = economia_tela.eco.patrimonio(jogador)
            imagem = str(jogador.get("imagem", ""))
            avatar: ft.Control
            if imagem:
                # FOTO NO RANKING: width/height=52 e raio=26 formam um círculo.
                avatar = ft.Image(
                    src=imagem,
                    width=52,
                    height=52,
                    fit=ft.BoxFit.COVER,
                    border_radius=_raio(26),
                )
            else:
                avatar = ft.Icon(
                    ft.Icons.PERSON,
                    color=CORES["ciano"],
                    size=38,
                )
            linhas.append(
                # LINHA DE CADA JOGADOR:
                # A grade usa 12 colunas. Em telas sm, os campos ocupam
                # 1 + 1 + 3 + 3 + 4 = 12.
                # padding, bgcolor, border e border_radius mudam o cartão.
                ft.Container(
                    content=ft.ResponsiveRow(
                        controls=[
                            ft.Text(
                                f"{posicao}º",
                                color=CORES["amarelo"],
                                size=22,
                                weight=ft.FontWeight.BOLD,
                                col={"xs": 2, "sm": 1},
                            ),
                            ft.Container(
                                content=avatar,
                                alignment=ft.Alignment.CENTER,
                                col={"xs": 3, "sm": 1},
                            ),
                            ft.Text(
                                str(jogador["nome"]),
                                color=CORES["branco"],
                                size=18,
                                weight=ft.FontWeight.BOLD,
                                col={"xs": 7, "sm": 3},
                            ),
                            ft.Column(
                                controls=[
                                    ft.Text("SALDO DAS QUESTÕES", color=CORES["texto_suave"], size=9,
                                            weight=ft.FontWeight.BOLD),
                                    ft.Text(
                                        formatar_reais(saldo),
                                        color=(
                                            CORES["verde"]
                                            if saldo >= 0
                                            else CORES["vermelho"]
                                        ),
                                        size=18,
                                        weight=ft.FontWeight.BOLD,
                                    ),
                                ],
                                spacing=0,
                                col={"xs": 6, "sm": 2},
                            ),
                            # PATRIMÔNIO = carteira + cofrinho (Modo economia).
                            ft.Column(
                                controls=[
                                    ft.Text("PATRIMÔNIO", color=CORES["texto_suave"], size=9,
                                            weight=ft.FontWeight.BOLD),
                                    ft.Text(
                                        formatar_reais(patrimonio),
                                        color=(
                                            CORES["amarelo"]
                                            if patrimonio >= 0
                                            else CORES["vermelho"]
                                        ),
                                        size=18,
                                        weight=ft.FontWeight.BOLD,
                                    ),
                                ],
                                spacing=0,
                                col={"xs": 6, "sm": 2},
                            ),
                            ft.Text(
                                (
                                    f"✓ {jogador['acertos']}  "
                                    f"✗ {jogador['erros']}  "
                                    f"📖 {jogador['estudos']}"
                                ),
                                color=CORES["texto_suave"],
                                size=13,
                                col={"xs": 12, "sm": 3},
                            ),
                        ],
                        columns=12,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    padding=14,
                    bgcolor=CORES["azul_cartao_2"],
                    border=_borda(
                        CORES["amarelo"] if posicao == 1 else CORES["ciano_2"],
                        2 if posicao == 1 else 1,
                    ),
                    border_radius=_raio(15),
                )
            )
        if not linhas:
            linhas.append(
                ft.Text(
                    "Cadastre os jogadores para iniciar o ranking.",
                    color=CORES["texto_suave"],
                    size=16,
                    text_align=ft.TextAlign.CENTER,
                )
            )

        self.host.content = ft.Container(
            # FUNDO DA TELA DE RANKING:
            # Troque as duas cores abaixo para alterar apenas esta tela.
            expand=True,
            gradient=ft.LinearGradient(
                begin=ft.Alignment.TOP_CENTER,
                end=ft.Alignment.BOTTOM_CENTER,
                colors=[CORES["fundo_topo"], CORES["fundo_meio"]],
            ),
            content=ft.SafeArea(
                content=ft.Column(
                    controls=[
                        ft.Row(
                            controls=[
                                ft.OutlinedButton(
                                    content="VOLTAR",
                                    icon=ft.Icons.ARROW_BACK,
                                    style=ft.ButtonStyle(
                                        color=CORES["branco"],
                                        side=ft.BorderSide(
                                            width=1.5,
                                            color=CORES["ciano"],
                                        ),
                                    ),
                                    on_click=self.mostrar_inicio,
                                ),
                                ft.Text(
                                    "RANKING GERAL",
                                    color=CORES["amarelo"],
                                    size=32,
                                    weight=ft.FontWeight.BOLD,
                                ),
                            ],
                            spacing=18,
                            wrap=True,
                        ),
                        ft.Text(
                            (
                                "Classificação pelo saldo acumulado em todas "
                                "as etapas."
                            ),
                            color=CORES["texto_suave"],
                            size=14,
                        ),
                        *linhas,
                        ft.Container(
                            content=ft.Row(
                                controls=[
                                    ft.Icon(
                                        ft.Icons.TABLE_VIEW,
                                        color=CORES["verde"],
                                    ),
                                    ft.Text(
                                        (
                                            "Planilha atualizada: "
                                            "dados/ranking.xlsx"
                                        ),
                                        color=CORES["branco"],
                                        weight=ft.FontWeight.BOLD,
                                    ),
                                ],
                                spacing=10,
                                wrap=True,
                            ),
                            padding=14,
                            bgcolor=CORES["azul_cartao"],
                            border=_borda(CORES["verde"]),
                            border_radius=_raio(14),
                        ),
                        # DESEMPENHO POR QUESTÃO (dados da pesquisa).
                        self._cartao_desempenho(),
                        # MARGEM FINAL: evita que o último cartão fique cortado.
                        ft.Container(height=12),
                    ],
                    spacing=14,
                    # ALWAYS permite rolar e mostra a barra quando há muitos
                    # jogadores ou a janela está compactada.
                    scroll=ft.ScrollMode.ALWAYS,
                ),
                minimum_padding=ft.Padding.all(20),
            ),
            padding=ft.Padding.symmetric(horizontal=24, vertical=16),
        )
        recursos_jogo.sons_nos_botoes(self, self.host.content)
        self.page.update()

    def _mostrar_dialogo(self, dialogo: ft.AlertDialog) -> None:
        """Abre uma janela com som de clique nos seus botões."""
        self.page.show_dialog(recursos_jogo.sons_nos_botoes(self, dialogo))

    def mostrar_inicio(self, _evento: Any = None) -> None:
        # Salva os dados e volta à tela inicial sem zerar os saldos.
        self.estado.salvar()
        self._reconstruir_inicio()

    def _animar_hover(self, indice: int, evento: ft.ControlEvent) -> None:
        # EFEITO AO PASSAR O MOUSE NOS BOTÕES DE ETAPA:
        # scale=1.025 aumenta 2,5%; offset negativo move um pouco para cima.
        # As cores seguintes são exclusivas do estado de hover.
        cartao = self.cartoes_assuntos[indice]
        sobre = str(evento.data).lower() == "true"
        ativo = bool(ASSUNTOS[indice]["ativo"])
        # SEM ANIMAÇÕES (Acessibilidade): o cartão só muda de cor, sem crescer.
        movimento = sobre and not self.estado.acessibilidade.get("sem_animacoes")
        cartao.scale = 1.025 if movimento else 1.0
        cartao.offset = (0, -0.025) if movimento else (0, 0)
        cartao.bgcolor = (
            "#0B62D2"
            if sobre and ativo
            else "#0A2A61"
            if sobre
            else CORES["azul_botao"]
            if ativo
            else CORES["azul_bloqueado"]
        )
        cartao.border = _borda(
            CORES["amarelo"]
            if sobre and ativo
            else CORES["ciano_2"]
            if sobre
            else CORES["ciano"]
            if ativo
            else "#3B76A9",
            3 if ativo else 2,
        )
        cartao.update()

    async def _selecionar_assunto(
        self,
        indice: int,
        _evento: ft.ControlEvent,
    ) -> None:
        # Índices: 0 abre Porcentagem, 1 Juros, 2 PRICE / SAF e 3 SAC.
        # As etapas seguintes exibem aviso enquanto estiverem bloqueadas.
        if indice == 0 and ASSUNTOS[indice]["ativo"]:
            await self._abrir_porcentagem()
            return
        if indice == 1 and ASSUNTOS[indice]["ativo"]:
            await self._abrir_juros()
            return
        if indice == 2 and ASSUNTOS[indice]["ativo"]:
            await self._abrir_price()
            return
        if indice == 3 and ASSUNTOS[indice]["ativo"]:
            await self._abrir_sac()
            return
        self._mostrar_aviso("ESTE ASSUNTO ESTARÁ DISPONÍVEL EM BREVE")

    async def _abrir_porcentagem(self) -> None:
        # INTEGRAÇÃO COM O QUIZ:
        # Carrega nivel_1_porcentagem.py e chama criar_tela_porcentagem().
        # Não altere esta rotina para mudanças meramente visuais da abertura.
        caminho = BASE_DIR / ARQUIVO_QUIZ
        if not caminho.exists():
            self._mostrar_aviso(
                f"COLOQUE {ARQUIVO_QUIZ} NA MESMA PASTA DESTE ARQUIVO"
            )
            return

        try:
            self._sincronizar_nomes_campos()
            nomes_validos, mensagem = self.estado.nomes_validos()
            if not nomes_validos:
                self._mostrar_aviso(mensagem.upper())
                return

            if self.som_ativo:
                await self._parar_audio_atual()
                self.som_ativo = False
                self.icone_som.icon = ft.Icons.VOLUME_OFF
                self.texto_som.value = "ATIVAR SOM"

            spec = importlib.util.spec_from_file_location(
                "quiz_porcentagem_flet",
                caminho,
            )
            if spec is None or spec.loader is None:
                raise ImportError("Não foi possível preparar o módulo do quiz.")
            modulo = importlib.util.module_from_spec(spec)
            sys.modules["quiz_porcentagem_flet"] = modulo
            spec.loader.exec_module(modulo)

            fabrica: Callable[..., ft.Control] | None = getattr(
                modulo,
                "criar_tela_porcentagem",
                None,
            )
            if fabrica is None:
                if hasattr(modulo, "abrir_nivel_1"):
                    self._mostrar_aviso(
                        "O QUIZ AINDA USA TKINTER E TAMBÉM PRECISA SER "
                        "MIGRADO PARA FLET"
                    )
                else:
                    self._mostrar_aviso(
                        "CRIE A FUNÇÃO criar_tela_porcentagem NO ARQUIVO DO QUIZ"
                    )
                return

            tela_quiz = fabrica(self.page, self.mostrar_inicio, self.estado)
            if tela_quiz is None:
                return
            if not isinstance(tela_quiz, ft.Control):
                raise TypeError(
                    "criar_tela_porcentagem deve devolver um controle do Flet."
                )

            # Mantém o módulo e sua interface vivos e troca somente o conteúdo
            # do host permanente. Assim, a página nunca fica vazia.
            self.modulo_porcentagem = modulo
            self.tela_porcentagem = tela_quiz
            self.host.content = tela_quiz
            self.host.bgcolor = CORES["fundo_topo"]
            self.page.update()
        except Exception as erro:
            print(f"Erro ao abrir o quiz: {erro}")
            self._mostrar_aviso("NÃO FOI POSSÍVEL ABRIR O QUIZ DE PORCENTAGEM")

    async def _abrir_juros(self) -> None:
        """Carrega a Etapa 2 e reutiliza o estado global dos jogadores."""
        caminho = BASE_DIR / ARQUIVO_QUIZ_JUROS
        if not caminho.exists():
            self._mostrar_aviso(
                f"COLOQUE {ARQUIVO_QUIZ_JUROS} NA MESMA PASTA DESTE ARQUIVO"
            )
            return

        try:
            self._sincronizar_nomes_campos()
            nomes_validos, mensagem = self.estado.nomes_validos()
            if not nomes_validos:
                self._mostrar_aviso(mensagem.upper())
                return

            if self.som_ativo:
                await self._parar_audio_atual()
                self.som_ativo = False
                self.icone_som.icon = ft.Icons.VOLUME_OFF
                self.texto_som.value = "ATIVAR SOM"

            spec = importlib.util.spec_from_file_location(
                "quiz_juros_flet",
                caminho,
            )
            if spec is None or spec.loader is None:
                raise ImportError(
                    "Não foi possível preparar o módulo de Juros."
                )
            modulo = importlib.util.module_from_spec(spec)
            sys.modules["quiz_juros_flet"] = modulo
            spec.loader.exec_module(modulo)

            fabrica: Callable[..., ft.Control] | None = getattr(
                modulo,
                "criar_tela_juros",
                None,
            )
            if fabrica is None:
                self._mostrar_aviso(
                    "CRIE A FUNÇÃO criar_tela_juros NO ARQUIVO DA ETAPA 2"
                )
                return

            # O MESMO self.estado usado em Porcentagem é passado à Etapa 2.
            # Não substitua por EstadoJogo(), pois isso separaria a sessão atual.
            tela_quiz = fabrica(self.page, self.mostrar_inicio, self.estado)
            if tela_quiz is None:
                return
            if not isinstance(tela_quiz, ft.Control):
                raise TypeError(
                    "criar_tela_juros deve devolver um controle do Flet."
                )

            self.modulo_juros = modulo
            self.tela_juros = tela_quiz
            self.host.content = tela_quiz
            self.host.bgcolor = CORES["fundo_topo"]
            self.page.update()
        except Exception as erro:
            print(f"Erro ao abrir o módulo de Juros: {erro}")
            self._mostrar_aviso(
                "NÃO FOI POSSÍVEL ABRIR O MÓDULO DE JUROS"
            )

    async def _abrir_price(self) -> None:
        """Carrega a Etapa 3 e mantém o mesmo estado global dos jogadores."""
        caminho = BASE_DIR / ARQUIVO_QUIZ_PRICE
        if not caminho.exists():
            self._mostrar_aviso(
                f"COLOQUE {ARQUIVO_QUIZ_PRICE} NA MESMA PASTA DESTE ARQUIVO"
            )
            return

        try:
            self._sincronizar_nomes_campos()
            nomes_validos, mensagem = self.estado.nomes_validos()
            if not nomes_validos:
                self._mostrar_aviso(mensagem.upper())
                return

            if self.som_ativo:
                await self._parar_audio_atual()
                self.som_ativo = False
                self.icone_som.icon = ft.Icons.VOLUME_OFF
                self.texto_som.value = "ATIVAR SOM"

            spec = importlib.util.spec_from_file_location(
                "quiz_price_flet",
                caminho,
            )
            if spec is None or spec.loader is None:
                raise ImportError(
                    "Não foi possível preparar o módulo PRICE / SAF."
                )
            modulo = importlib.util.module_from_spec(spec)
            sys.modules["quiz_price_flet"] = modulo
            spec.loader.exec_module(modulo)

            fabrica: Callable[..., ft.Control] | None = getattr(
                modulo,
                "criar_tela_price",
                None,
            )
            if fabrica is None:
                self._mostrar_aviso(
                    "CRIE A FUNÇÃO criar_tela_price NO ARQUIVO DA ETAPA 3"
                )
                return

            # ESTADO GLOBAL: a mesma instância acumula os saldos conquistados
            # em Porcentagem, Juros e PRICE. Não crie EstadoJogo() neste ponto.
            tela_quiz = fabrica(self.page, self.mostrar_inicio, self.estado)
            if tela_quiz is None:
                return
            if not isinstance(tela_quiz, ft.Control):
                raise TypeError(
                    "criar_tela_price deve devolver um controle do Flet."
                )

            self.modulo_price = modulo
            self.tela_price = tela_quiz
            self.host.content = tela_quiz
            self.host.bgcolor = CORES["fundo_topo"]
            self.page.update()
        except Exception as erro:
            print(f"Erro ao abrir o módulo PRICE / SAF: {erro}")
            self._mostrar_aviso(
                "NÃO FOI POSSÍVEL ABRIR O MÓDULO PRICE / SAF"
            )

    async def _abrir_sac(self) -> None:
        """Carrega a Etapa 4 (SAC) e mantém o mesmo estado global dos jogadores."""
        caminho = BASE_DIR / ARQUIVO_QUIZ_SAC
        if not caminho.exists():
            self._mostrar_aviso(
                f"COLOQUE {ARQUIVO_QUIZ_SAC} NA MESMA PASTA DESTE ARQUIVO"
            )
            return

        try:
            self._sincronizar_nomes_campos()
            nomes_validos, mensagem = self.estado.nomes_validos()
            if not nomes_validos:
                self._mostrar_aviso(mensagem.upper())
                return

            if self.som_ativo:
                await self._parar_audio_atual()
                self.som_ativo = False
                self.icone_som.icon = ft.Icons.VOLUME_OFF
                self.texto_som.value = "ATIVAR SOM"

            spec = importlib.util.spec_from_file_location(
                "quiz_sac_flet",
                caminho,
            )
            if spec is None or spec.loader is None:
                raise ImportError(
                    "Não foi possível preparar o módulo SAC."
                )
            modulo = importlib.util.module_from_spec(spec)
            sys.modules["quiz_sac_flet"] = modulo
            spec.loader.exec_module(modulo)

            fabrica: Callable[..., ft.Control] | None = getattr(
                modulo,
                "criar_tela_sac",
                None,
            )
            if fabrica is None:
                self._mostrar_aviso(
                    "CRIE A FUNÇÃO criar_tela_sac NO ARQUIVO DA ETAPA 4"
                )
                return

            # ESTADO GLOBAL: a mesma instância acumula os saldos conquistados
            # em Porcentagem, Juros, PRICE e SAC. Não crie EstadoJogo() neste ponto.
            tela_quiz = fabrica(self.page, self.mostrar_inicio, self.estado)
            if tela_quiz is None:
                return
            if not isinstance(tela_quiz, ft.Control):
                raise TypeError(
                    "criar_tela_sac deve devolver um controle do Flet."
                )

            self.modulo_sac = modulo
            self.tela_sac = tela_quiz
            self.host.content = tela_quiz
            self.host.bgcolor = CORES["fundo_topo"]
            self.page.update()
        except Exception as erro:
            print(f"Erro ao abrir o módulo SAC: {erro}")
            self._mostrar_aviso(
                "NÃO FOI POSSÍVEL ABRIR O MÓDULO SAC"
            )

    def _mostrar_aviso(self, texto: str) -> None:
        # AVISO INFERIOR (SNACKBAR):
        # bgcolor muda o fundo, duration está em milissegundos e margin afasta o
        # aviso das bordas. O texto recebido pelo parâmetro aparece no centro.
        aviso = ft.SnackBar(
            content=ft.Text(
                texto,
                color=CORES["branco"],
                weight=ft.FontWeight.BOLD,
                text_align=ft.TextAlign.CENTER,
            ),
            bgcolor=_cor_fixa("#102C67"),
            show_close_icon=True,
            close_icon_color=CORES["ciano"],
            duration=3200,
            margin=ft.Margin.all(18),
        )
        self.page.show_dialog(aviso)

    # ------------------------------------------------------------------
    # Som
    # ------------------------------------------------------------------

    def _trilha_atual(self) -> tuple[str, Path]:
        # Retorna o caminho relativo usado pelo Flet e o caminho completo local.
        relativo = self.estado.trilhas_disponiveis()[self.estado.trilha]
        return relativo, PASTA_ASSETS / relativo

    async def _iniciar_audio_atual(self) -> None:
        # WAV usa o reprodutor nativo do Windows. Outros formatos e sistemas
        # usam o serviço de áudio do Flet.
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
        # Interrompe a reprodução sem apagar a música escolhida.
        _relativo, caminho = self._trilha_atual()
        if winsound is not None and caminho.suffix.lower() == ".wav":
            winsound.PlaySound(None, 0)
        else:
            await self.audio.pause()
        self.som_ativo = False

    async def _alternar_som(self, _evento: ft.ControlEvent) -> None:
        # Alterna entre tocar e pausar e atualiza o ícone/texto do botão.
        try:
            if self.som_ativo:
                await self._parar_audio_atual()
            else:
                await self._iniciar_audio_atual()
        except Exception as erro:
            print(f"Erro ao controlar o áudio: {erro}")
            self._mostrar_aviso("NÃO FOI POSSÍVEL ALTERAR O SOM")
            return

        self.icone_som.icon = (
            ft.Icons.VOLUME_UP if self.som_ativo else ft.Icons.VOLUME_OFF
        )
        self.texto_som.value = "MUTE" if self.som_ativo else "ATIVAR SOM"
        self.page.update()

    async def _ao_fechar(self, _evento: ft.ControlEvent) -> None:
        # Libera o áudio e salva o estado quando a janela é fechada.
        try:
            if winsound is not None:
                winsound.PlaySound(None, 0)
            await self.audio.release()
            self.estado.salvar()
        except Exception:
            pass


def main(page: ft.Page) -> None:
    # PONTO DE ENTRADA DO FLET: verifica a versão e cria o aplicativo.
    _avisar_sobre_versoes()
    AplicativoRespondaOuEstuda(page)


def iniciar() -> None:
    # assets_dir informa ao Flet onde buscar imagens e sons.
    # "name" identifica internamente o aplicativo.
    # JANELA EXCLUSIVA: AppView.WEB_BROWSER mantém o servidor web local e evita
    # o executável Desktop armazenado em .flet/client/.../flet.exe. O iniciador
    # abre esse endereço local no Edge/Chrome com --app, ocultando abas, barra
    # de endereço e menus. Não remova este parâmetro neste pacote.
    ft.run(
        main,
        name="responda_ou_estuda",
        assets_dir=str(PASTA_ASSETS),
        view=ft.AppView.WEB_BROWSER,
    )


if __name__ == "__main__":
    # Executa iniciar() somente quando este arquivo é aberto diretamente.
    iniciar()
