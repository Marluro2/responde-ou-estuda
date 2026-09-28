"""Recursos compartilhados pelos três módulos (Porcentagem, Juros e PRICE).

Tudo o que é igual nos módulos e foi criado depois deles fica aqui, para que
uma melhoria valha para as três etapas de uma só vez:

    • efeitos sonoros (acerto, erro, tique do cronômetro, conquista);
    • saldo que "rola" até o novo valor no placar;
    • destaque da alternativa escolhida antes da resolução;
    • transição suave entre as telas;
    • atalhos de teclado;
    • sequência de acertos, conquistas e pódio no resultado;
    • registro das respostas para a pesquisa (dados/respostas.csv) e
      relatórios de desempenho por questão e por jogador.

Os módulos chamam estas funções em poucos pontos; procure por
"recursos_jogo" em nivel_1_porcentagem.py, nivel_2_juros.py e nivel_3_price.py.
"""

from __future__ import annotations

import asyncio
import csv
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

import flet as ft
from flet_audio import Audio

from estado_jogo import DADOS_DIR


ADMIN_ATIVO = os.environ.get("RESPONDA_ADMIN", "").strip() == "1"
LETRAS = "ABCDEFGHIJ"


# ======================================================================
# EFEITOS SONOROS
# ======================================================================
# Os efeitos só tocam quando o som do jogo está ligado (botão ATIVAR SOM).
# Para recriar os arquivos: py -3.14 ferramentas\gerar_efeitos.py
EFEITOS = {
    "acerto": "sons/efeitos/acerto.wav",
    "erro": "sons/efeitos/erro.wav",
    "tique": "sons/efeitos/tique.wav",
    "conquista": "sons/efeitos/conquista.wav",
}


class EfeitosSonoros:
    """Toca os efeitos pelo navegador, sem interromper a trilha de fundo."""

    def __init__(self, page: ft.Page) -> None:
        self.page = page
        self.audios: dict[str, Audio] = {}
        for nome, caminho in EFEITOS.items():
            audio = Audio(src=caminho, autoplay=False, volume=0.9)
            self.page.services.append(audio)
            self.audios[nome] = audio

    def tocar(self, jogo: Any, nome: str) -> None:
        if not getattr(jogo, "som_ativo", False) or nome not in self.audios:
            return
        self.page.run_task(self._tocar, nome)

    async def _tocar(self, nome: str) -> None:
        try:
            await self.audios[nome].play(0)
        except Exception:
            pass


def efeitos(jogo: Any) -> EfeitosSonoros:
    """Cria (uma vez por módulo) e devolve o tocador de efeitos."""
    if getattr(jogo, "_efeitos", None) is None:
        jogo._efeitos = EfeitosSonoros(jogo.page)
    return jogo._efeitos


# ======================================================================
# SALDO ANIMADO NO PLACAR
# ======================================================================
# Guarda o último valor mostrado de cada jogador; quando o saldo muda, o
# número "rola" do valor antigo até o novo e dá um leve pulo.
_SALDOS_EXIBIDOS: dict[str, float] = {}
DURACAO_SALDO = 0.9  # segundos


def texto_saldo(
    jogo: Any,
    jogador: dict[str, Any],
    formatar: Any,
    *,
    cor_positiva: str,
    cor_negativa: str,
    tamanho: float,
) -> ft.Text:
    identificador = str(jogador.get("id", jogador.get("nome", "")))
    valor = float(jogador.get("saldo", 0.0))
    anterior = _SALDOS_EXIBIDOS.get(identificador, valor)
    _SALDOS_EXIBIDOS[identificador] = valor

    def cor(v: float) -> str:
        return cor_positiva if v >= 0 else cor_negativa

    texto = ft.Text(
        formatar(anterior),
        color=cor(anterior),
        size=tamanho,
        weight=ft.FontWeight.BOLD,
        scale=1.0,
        animate_scale=ft.Animation(250, ft.AnimationCurve.EASE_OUT),
    )
    if abs(anterior - valor) > 0.004:
        jogo.page.run_task(_rolar_saldo, texto, anterior, valor, formatar, cor)
    else:
        texto.value = formatar(valor)
        texto.color = cor(valor)
    return texto


async def _rolar_saldo(texto: ft.Text, inicio: float, fim: float, formatar: Any, cor: Any) -> None:
    await asyncio.sleep(0.12)  # espera o controle aparecer na tela
    passos = 18
    try:
        texto.scale = 1.18
        for passo in range(1, passos + 1):
            fracao = passo / passos
            suave = 1 - (1 - fracao) ** 3
            atual = inicio + (fim - inicio) * suave
            texto.value = formatar(atual)
            texto.color = cor(atual)
            if passo == passos - 3:
                texto.scale = 1.0
            texto.update()
            await asyncio.sleep(DURACAO_SALDO / passos)
        texto.value = formatar(fim)
        texto.color = cor(fim)
        texto.scale = 1.0
        texto.update()
    except Exception:
        pass  # a tela mudou durante a animação


# ======================================================================
# DESTAQUE DA ALTERNATIVA ESCOLHIDA
# ======================================================================
# Depois do clique, a alternativa escolhida fica verde (acerto) ou vermelha
# (erro) e a correta fica marcada, por ESPERA_DESTAQUE segundos, antes de
# abrir a resolução.
ESPERA_DESTAQUE = 1.1


def cores_alternativa(jogo: Any, indice: int, tema: dict[str, str]) -> tuple[str, str, float] | None:
    """(fundo, borda, espessura) da alternativa durante o destaque, ou None."""
    destaque = getattr(jogo, "_destaque_resposta", None)
    if not destaque:
        return None
    escolhida, correta = destaque["escolhida"], destaque["correta"]
    if indice == escolhida and escolhida == correta:
        return ("#1E7A4F", tema["positivo"], 3)
    if indice == escolhida:
        return ("#8A2338", tema["negativo"], 3)
    if indice == correta:
        return (tema["cartao_2"], tema["positivo"], 3)
    return None


def iniciar_destaque(jogo: Any, escolhida: int, correta: int, ir_para_resolucao: Any) -> None:
    """Mostra o destaque, toca o efeito e depois chama ir_para_resolucao()."""
    jogo._destaque_resposta = {"escolhida": escolhida, "correta": correta}
    efeitos(jogo).tocar(jogo, "acerto" if escolhida == correta else "erro")

    async def seguir() -> None:
        await asyncio.sleep(ESPERA_DESTAQUE)
        jogo._destaque_resposta = None
        ir_para_resolucao()

    jogo.page.run_task(seguir)


# ======================================================================
# TRANSIÇÃO ENTRE TELAS
# ======================================================================
def com_transicao(jogo: Any, conteudo: ft.Control) -> ft.Control:
    """Esmaece a tela nova ao mudar de etapa (situação, alternativas...)."""
    chave = (
        getattr(jogo, "tela_atual", ""),
        getattr(jogo, "indice_questao", 0),
        getattr(jogo, "pagina_estudo", 0),
        getattr(jogo, "etapa_teoria", 0),
    )
    mudou = chave != getattr(jogo, "_ultima_chave_tela", None)
    jogo._ultima_chave_tela = chave
    envoltorio = ft.Container(
        content=conteudo,
        opacity=0.0 if mudou else 1.0,
        offset=ft.Offset(0, 0.015) if mudou else ft.Offset(0, 0),
        animate_opacity=ft.Animation(320, ft.AnimationCurve.EASE_OUT),
        animate_offset=ft.Animation(320, ft.AnimationCurve.EASE_OUT),
    )
    if mudou:
        async def aparecer() -> None:
            await asyncio.sleep(0.03)
            try:
                envoltorio.opacity = 1.0
                envoltorio.offset = ft.Offset(0, 0)
                envoltorio.update()
            except Exception:
                pass

        jogo.page.run_task(aparecer)
    return envoltorio


# ======================================================================
# CRONÔMETRO: TENSÃO NOS ÚLTIMOS 10 SEGUNDOS
# ======================================================================
def pulsar_cronometro(jogo: Any) -> None:
    """Chamado a cada segundo: nos últimos 10 s o número pulsa e faz tique."""
    texto = getattr(jogo, "texto_cronometro", None)
    restante = int(getattr(jogo, "tempo_restante", 99))
    if texto is None:
        return
    if 0 < restante <= 10:
        texto.scale = 1.3 if restante % 2 == 0 else 1.0
        efeitos(jogo).tocar(jogo, "tique")
    else:
        texto.scale = 1.0


# ======================================================================
# ATALHOS DE TECLADO
# ======================================================================
# Situação:     R = responder   E = estudar
# Alternativas: A, B, C, D, E  ou  1, 2, 3, 4, 5
# Estudo:       Enter ou Espaço = avançar a página / concluir
# Resolução:    Enter ou Espaço = passar a vez
ATALHOS_TEXTO = "Atalhos: R responder · E estudar · A–E ou 1–5 alternativas · Enter avançar / passar a vez"


def ativar_teclado(jogo: Any) -> None:
    jogo.page.on_keyboard_event = lambda evento: _tecla(jogo, evento)


def _tecla(jogo: Any, evento: ft.KeyboardEvent) -> None:
    if evento.ctrl or getattr(jogo, "_destaque_resposta", None):
        return
    tecla = str(evento.key or "").upper()
    tela = getattr(jogo, "tela_atual", "")
    try:
        if tela == "jogada" and not getattr(jogo, "_rodada_finalizada", False):
            if tecla == "R":
                jogo._escolher_responder(None)
            elif tecla == "E":
                jogo._escolher_estudar(None)
        elif tela == "pergunta" and not getattr(jogo, "_rodada_finalizada", False):
            total = len(jogo.questao_atual.get("alternativas", []))
            indice = None
            if len(tecla) == 1 and tecla in LETRAS[:total]:
                indice = LETRAS.index(tecla)
            elif tecla.isdigit() and 1 <= int(tecla) <= total:
                indice = int(tecla) - 1
            if indice is not None:
                jogo._responder(indice, None)
        elif tela == "feedback" and tecla in {"ENTER", " ", "SPACE"}:
            jogo._proxima_rodada(None)
        elif tela == "estudo" and tecla in {"ENTER", " ", "SPACE"}:
            # Estudo em páginas: Enter avança; na última página, conclui.
            pagina = int(getattr(jogo, "pagina_estudo", 0))
            if hasattr(jogo, "_total_paginas_estudo"):  # PRICE
                if pagina < jogo._total_paginas_estudo() - 1:
                    jogo._avancar_pagina_estudo(None)
                else:
                    jogo._concluir_estudo(None)
            elif pagina == 0:
                jogo._alterar_pagina_estudo(1)
            else:
                jogo._proxima_rodada(None)
    except Exception as erro:
        print(f"Atalho de teclado ignorado: {erro}")


# ======================================================================
# SESSÃO: SEQUÊNCIA DE ACERTOS E CONQUISTAS
# ======================================================================
class Sessao:
    """Estatísticas da partida atual (não altera saldo nem ranking)."""

    def __init__(self, modulo: str) -> None:
        self.modulo = modulo
        self.identificador = datetime.now().strftime("%Y%m%d-%H%M%S-") + uuid.uuid4().hex[:4]
        self.jogadores: dict[str, dict[str, Any]] = {}

    def dados(self, jogador: dict[str, Any]) -> dict[str, Any]:
        chave = str(jogador.get("id", jogador.get("nome")))
        if chave not in self.jogadores:
            self.jogadores[chave] = {
                "nome": jogador.get("nome", ""),
                "acertos": 0, "erros": 0, "esgotados": 0, "estudos": 0,
                "sequencia": 0, "melhor_sequencia": 0, "tempos_acerto": [],
            }
        return self.jogadores[chave]

    def registrar(self, jogador: dict[str, Any], resultado: str, tempo: float | None) -> None:
        d = self.dados(jogador)
        if resultado == "acerto":
            d["acertos"] += 1
            d["sequencia"] += 1
            d["melhor_sequencia"] = max(d["melhor_sequencia"], d["sequencia"])
            if tempo is not None:
                d["tempos_acerto"].append(tempo)
        else:
            d["sequencia"] = 0
            chave = {"erro": "erros", "tempo_esgotado": "esgotados", "estudo": "estudos"}.get(resultado)
            if chave:
                d[chave] += 1

    def conquistas(self) -> list[tuple[str, str, str, str]]:
        """(ícone, título, nome, detalhe) — só aparece quem se destacou."""
        lista: list[tuple[str, str, str, str]] = []
        jogadores = list(self.jogadores.values())

        def melhor(chave, filtro=lambda d: True, menor=False):
            candidatos = [d for d in jogadores if filtro(d)]
            if not candidatos:
                return None
            return (min if menor else max)(candidatos, key=chave)

        respondeu = lambda d: d["acertos"] + d["erros"] + d["esgotados"] >= 3  # noqa: E731
        preciso = melhor(lambda d: d["acertos"] / max(1, d["acertos"] + d["erros"] + d["esgotados"]), respondeu)
        if preciso and preciso["acertos"]:
            total = preciso["acertos"] + preciso["erros"] + preciso["esgotados"]
            lista.append(("🎯", "Mais preciso", preciso["nome"], f"{preciso['acertos']} de {total} respostas certas"))
        sequencia = melhor(lambda d: d["melhor_sequencia"])
        if sequencia and sequencia["melhor_sequencia"] >= 2:
            lista.append(("🔥", "Maior sequência", sequencia["nome"], f"{sequencia['melhor_sequencia']} acertos seguidos"))
        rapido = melhor(
            lambda d: sum(d["tempos_acerto"]) / len(d["tempos_acerto"]),
            lambda d: len(d["tempos_acerto"]) >= 2,
            menor=True,
        )
        if rapido:
            media = sum(rapido["tempos_acerto"]) / len(rapido["tempos_acerto"])
            lista.append(("⚡", "Mais rápido", rapido["nome"], f"acertos em {media:.0f} s, em média"))
        estudioso = melhor(lambda d: d["estudos"])
        if estudioso and estudioso["estudos"] >= 2:
            lista.append(("📚", "Mais estudioso", estudioso["nome"], f"estudou {estudioso['estudos']} vezes"))
        return lista


def sessao(jogo: Any, modulo: str) -> Sessao:
    if getattr(jogo, "_sessao", None) is None:
        jogo._sessao = Sessao(modulo)
    return jogo._sessao


def nova_sessao(jogo: Any, modulo: str) -> None:
    """Chamado ao iniciar uma nova partida."""
    jogo._sessao = Sessao(modulo)
    jogo._destaque_resposta = None


def faixa_sequencia(jogo: Any, tema: dict[str, str]) -> ft.Control | None:
    """Mensagem na resolução quando o jogador acerta 2 ou mais seguidas."""
    s = getattr(jogo, "_sessao", None)
    if s is None:
        return None
    d = s.dados(jogo.jogador_atual)
    if d["sequencia"] < 2:
        return None
    return ft.Container(
        content=ft.Text(
            f"🔥 {d['sequencia']} acertos seguidos! Continue assim!",
            color=tema["fundo_1"],
            size=16,
            weight=ft.FontWeight.BOLD,
            text_align=ft.TextAlign.CENTER,
        ),
        bgcolor=tema["destaque"],
        padding=ft.Padding.symmetric(horizontal=16, vertical=8),
        border_radius=ft.BorderRadius.all(12),
        alignment=ft.Alignment.CENTER,
    )


# ======================================================================
# PÓDIO E CONQUISTAS NO RESULTADO
# ======================================================================
def podio(jogo: Any, jogadores: list[dict[str, Any]], tema: dict[str, str], formatar: Any) -> ft.Control:
    """Pódio animado (1º, 2º e 3º) e cartões de conquistas da partida."""
    ordenados = sorted(jogadores, key=lambda j: float(j.get("saldo", 0)), reverse=True)[:3]
    alturas = {0: 150, 1: 110, 2: 80}
    cores = {0: "#FFD34E", 1: "#C9D6E3", 2: "#E09A5B"}
    posicoes_visuais = [1, 0, 2] if len(ordenados) >= 2 else [0]
    colunas: list[ft.Control] = []
    barras: list[tuple[ft.Container, int]] = []
    for posicao in posicoes_visuais:
        if posicao >= len(ordenados):
            continue
        jogador = ordenados[posicao]
        barra = ft.Container(
            content=ft.Text(f"{posicao + 1}º", size=30, weight=ft.FontWeight.BOLD, color="#06143C"),
            width=120,
            height=10,
            bgcolor=cores[posicao],
            alignment=ft.Alignment.TOP_CENTER,
            padding=ft.Padding.only(top=8),
            border_radius=ft.BorderRadius.only(top_left=12, top_right=12),
            animate=ft.Animation(900 + 250 * (2 - posicao), ft.AnimationCurve.EASE_OUT),
        )
        barras.append((barra, alturas[posicao]))
        colunas.append(
            ft.Column(
                controls=[
                    ft.Text("👑" if posicao == 0 else " ", size=22),
                    ft.Text(str(jogador.get("nome", "")), color=tema["texto"], size=16, weight=ft.FontWeight.BOLD),
                    ft.Text(formatar(float(jogador.get("saldo", 0))), color=tema["destaque"], size=14, weight=ft.FontWeight.BOLD),
                    barra,
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                alignment=ft.MainAxisAlignment.END,
                spacing=4,
            )
        )

    async def subir() -> None:
        await asyncio.sleep(0.2)
        try:
            for barra, altura in barras:
                barra.height = altura
                barra.update()
        except Exception:
            pass

    jogo.page.run_task(subir)
    efeitos(jogo).tocar(jogo, "conquista")

    cartoes: list[ft.Control] = []
    s = getattr(jogo, "_sessao", None)
    for icone, titulo, nome, detalhe in (s.conquistas() if s else []):
        cartoes.append(
            ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Text(f"{icone} {titulo.upper()}", color=tema["destaque"], size=13, weight=ft.FontWeight.BOLD),
                        ft.Text(nome, color=tema["texto"], size=16, weight=ft.FontWeight.BOLD),
                        ft.Text(detalhe, color=tema["suave"], size=12),
                    ],
                    spacing=2,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                padding=12,
                bgcolor=tema["cartao_2"],
                border=ft.Border.all(1.5, tema["destaque"]),
                border_radius=ft.BorderRadius.all(14),
                col={"xs": 12, "sm": 6, "md": 3},
            )
        )

    return ft.Container(
        content=ft.Column(
            controls=[
                ft.Row(controls=colunas, alignment=ft.MainAxisAlignment.CENTER,
                       vertical_alignment=ft.CrossAxisAlignment.END, spacing=18),
                *(
                    [ft.ResponsiveRow(controls=cartoes, columns=12, spacing=10, run_spacing=10)]
                    if cartoes else []
                ),
            ],
            spacing=14,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        padding=ft.Padding.symmetric(horizontal=16, vertical=14),
        bgcolor=tema["cartao"],
        border=ft.Border.all(2, tema["destaque"]),
        border_radius=ft.BorderRadius.all(20),
    )


# ======================================================================
# REGISTRO DAS RESPOSTAS PARA A PESQUISA
# ======================================================================
# Cada jogada vira uma linha em dados/respostas.csv (aberto no Excel).
# Os relatórios por questão e por jogador são refeitos a cada jogada.
# No modo administrador os arquivos recebem o sufixo "_admin", para que os
# testes do professor não se misturem aos dados dos estudantes.
SUFIXO = "_admin" if ADMIN_ATIVO else ""
ARQUIVO_RESPOSTAS = DADOS_DIR / f"respostas{SUFIXO}.csv"
ARQUIVO_POR_QUESTAO = DADOS_DIR / f"relatorio_por_questao{SUFIXO}.csv"
ARQUIVO_POR_JOGADOR = DADOS_DIR / f"relatorio_por_jogador{SUFIXO}.csv"

CAMPOS_RESPOSTA = [
    "data_hora", "sessao", "modulo", "nivel", "questao_id", "titulo",
    "jogador", "resultado", "alternativa_escolhida", "alternativa_correta",
    "tempo_resposta_s",
]


def _escrever_csv(caminho: Path, campos: list[str], linhas: list[dict[str, Any]], anexar: bool = False) -> None:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    novo = not caminho.exists() or not anexar
    # utf-8-sig e ponto e vírgula: o Excel em português abre sem ajustes.
    with caminho.open("a" if anexar else "w", encoding="utf-8-sig" if novo else "utf-8", newline="") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=campos, delimiter=";")
        if novo:
            escritor.writeheader()
        escritor.writerows(linhas)


def _numero(valor: float) -> str:
    return f"{valor:.1f}".replace(".", ",")


def registrar_resposta(
    jogo: Any,
    modulo: str,
    resultado: str,
    *,
    escolhida: int | None = None,
    tempo_total: int | None = None,
) -> None:
    """resultado: 'acerto', 'erro', 'tempo_esgotado' ou 'estudo'."""
    try:
        questao = jogo.questao_atual
        jogador = jogo.jogador_atual
        tempo = None
        if tempo_total is not None and hasattr(jogo, "tempo_restante") and not ADMIN_ATIVO:
            tempo = max(0.0, float(tempo_total) - float(jogo.tempo_restante))
        s = sessao(jogo, modulo)
        s.registrar(jogador, resultado, tempo)
        correta = int(questao.get("correta", -1))
        linha = {
            "data_hora": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
            "sessao": s.identificador,
            "modulo": modulo,
            "nivel": questao.get("nivel", ""),
            "questao_id": questao.get("id", ""),
            "titulo": str(questao.get("titulo", "")),
            "jogador": jogador.get("nome", ""),
            "resultado": resultado,
            "alternativa_escolhida": LETRAS[escolhida] if escolhida is not None and escolhida < len(LETRAS) else "",
            "alternativa_correta": LETRAS[correta] if 0 <= correta < len(LETRAS) else "",
            "tempo_resposta_s": _numero(tempo) if tempo is not None else "",
        }
        _escrever_csv(ARQUIVO_RESPOSTAS, CAMPOS_RESPOSTA, [linha], anexar=True)
        gerar_relatorios()
    except Exception as erro:
        print(f"Não foi possível registrar a resposta: {erro}")


def ler_respostas(caminho: Path | None = None) -> list[dict[str, str]]:
    caminho = caminho or ARQUIVO_RESPOSTAS
    if not caminho.exists():
        return []
    with caminho.open("r", encoding="utf-8-sig", newline="") as arquivo:
        return list(csv.DictReader(arquivo, delimiter=";"))


def resumo_por_questao(respostas: list[dict[str, str]]) -> list[dict[str, Any]]:
    grupos: dict[tuple[str, str], dict[str, Any]] = {}
    for r in respostas:
        chave = (r.get("modulo", ""), r.get("questao_id", ""))
        g = grupos.setdefault(chave, {
            "modulo": chave[0], "questao_id": chave[1], "nivel": r.get("nivel", ""),
            "titulo": r.get("titulo", ""), "acertos": 0, "erros": 0,
            "tempo_esgotado": 0, "estudos": 0, "tempos": [],
        })
        resultado = r.get("resultado", "")
        if resultado == "acerto":
            g["acertos"] += 1
        elif resultado == "erro":
            g["erros"] += 1
        elif resultado == "tempo_esgotado":
            g["tempo_esgotado"] += 1
        elif resultado == "estudo":
            g["estudos"] += 1
        tempo = (r.get("tempo_resposta_s") or "").replace(",", ".")
        if resultado in {"acerto", "erro"} and tempo:
            g["tempos"].append(float(tempo))
    resumo = []
    for g in grupos.values():
        tentativas = g["acertos"] + g["erros"] + g["tempo_esgotado"]
        resumo.append({
            "modulo": g["modulo"], "questao_id": g["questao_id"], "nivel": g["nivel"],
            "titulo": g["titulo"], "tentativas": tentativas, "acertos": g["acertos"],
            "erros": g["erros"], "tempo_esgotado": g["tempo_esgotado"], "estudos": g["estudos"],
            "percentual_acerto": (100 * g["acertos"] / tentativas) if tentativas else None,
            "tempo_medio_s": (sum(g["tempos"]) / len(g["tempos"])) if g["tempos"] else None,
        })
    resumo.sort(key=lambda x: (x["modulo"], x["percentual_acerto"] if x["percentual_acerto"] is not None else 101))
    return resumo


def gerar_relatorios() -> None:
    respostas = ler_respostas()
    por_questao = resumo_por_questao(respostas)
    _escrever_csv(
        ARQUIVO_POR_QUESTAO,
        ["modulo", "questao_id", "nivel", "titulo", "tentativas", "acertos", "erros",
         "tempo_esgotado", "estudos", "percentual_acerto", "tempo_medio_s"],
        [
            {**q,
             "percentual_acerto": _numero(q["percentual_acerto"]) if q["percentual_acerto"] is not None else "",
             "tempo_medio_s": _numero(q["tempo_medio_s"]) if q["tempo_medio_s"] is not None else ""}
            for q in por_questao
        ],
    )
    jogadores: dict[tuple[str, str], dict[str, Any]] = {}
    for r in respostas:
        chave = (r.get("jogador", ""), r.get("modulo", ""))
        j = jogadores.setdefault(chave, {"jogador": chave[0], "modulo": chave[1], "acertos": 0,
                                         "erros": 0, "tempo_esgotado": 0, "estudos": 0})
        if r.get("resultado") in {"acerto", "erro", "tempo_esgotado", "estudo"}:
            campo = {"acerto": "acertos", "erro": "erros", "tempo_esgotado": "tempo_esgotado",
                     "estudo": "estudos"}[r["resultado"]]
            j[campo] += 1
    linhas = []
    for j in sorted(jogadores.values(), key=lambda x: (x["jogador"].casefold(), x["modulo"])):
        tentativas = j["acertos"] + j["erros"] + j["tempo_esgotado"]
        linhas.append({**j, "respostas": tentativas,
                       "percentual_acerto": _numero(100 * j["acertos"] / tentativas) if tentativas else ""})
    _escrever_csv(
        ARQUIVO_POR_JOGADOR,
        ["jogador", "modulo", "respostas", "acertos", "erros", "tempo_esgotado", "estudos", "percentual_acerto"],
        linhas,
    )
