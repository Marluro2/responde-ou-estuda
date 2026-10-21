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
import inspect
import csv
import os
import sys
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

import flet as ft
from flet.utils.object_model import get_param_count
from flet_audio import Audio

import economia_tela as et
import formatacao_matematica

from estado_jogo import DADOS_DIR


ADMIN_ATIVO = os.environ.get("RESPONDA_ADMIN", "").strip() == "1"
LETRAS = "ABCDEFGHIJ"
PASTA_ASSETS = Path(__file__).resolve().parent / "assets"
NO_NAVEGADOR = sys.platform == "emscripten"
# CELULAR: abaixo desta largura (em pixels) os módulos usam o layout de
# celular (cronômetro acima da questão, sem mascote nem seletores de tema e
# trilha no cabeçalho). É o mesmo limite da tela inicial.
LARGURA_CELULAR = 600


def tela_de_celular(page: Any) -> bool:
    """True quando a página é mais estreita que LARGURA_CELULAR.

    Também avisa formatacao_matematica, para as fórmulas da tela que está
    sendo montada caberem no celular (toda tela consulta esta função antes
    de montar os textos, a começar pelo cabeçalho).
    """
    largura = getattr(page, "width", None)
    celular = bool(largura) and float(largura) < LARGURA_CELULAR
    formatacao_matematica.definir_tela_estreita(celular)
    return celular


def narracao_disponivel() -> bool:
    """A narração usa a voz do sistema (Windows/macOS/Linux), que o site não tem."""
    return not NO_NAVEGADOR


# ======================================================================
# FOTO DO JOGADOR
# ======================================================================
def foto_jogador(caminho_relativo: str) -> str | bytes:
    """Fonte da foto do jogador para ft.Image (caminho dentro de assets).

    NO SITE a foto escolhida é gravada só na memória da página, e não no
    endereço do jogo; por isso ela vai para a tela como bytes. Se a página
    foi recarregada, o arquivo já não existe: devolve "" e a tela mostra o
    ícone padrão.
    """
    if NO_NAVEGADOR and caminho_relativo:
        try:
            return (PASTA_ASSETS / caminho_relativo).read_bytes()
        except OSError:
            return ""
    return caminho_relativo


# ======================================================================
# PREFERÊNCIAS DE ACESSIBILIDADE
# ======================================================================
# Definidas no botão ACESSIBILIDADE da tela inicial e salvas no estado.
def preferencias(estado: Any) -> dict[str, Any]:
    dados = getattr(estado, "dados", {}) or {}
    return {"tempo": 60, "sem_animacoes": False, "efeitos": True, **dados.get("acessibilidade", {})}


def tempo_limite(estado: Any, padrao: int = 60) -> int:
    """Segundos por questão; 0 significa sem limite de tempo."""
    try:
        return int(preferencias(estado).get("tempo", padrao))
    except (TypeError, ValueError):
        return padrao


def sem_animacoes(jogo: Any) -> bool:
    return bool(preferencias(getattr(jogo, "estado", None)).get("sem_animacoes"))


def texto_tempo(jogo: Any) -> str:
    """Texto do cronômetro: "45s" ou "∞" quando não há limite de tempo."""
    if not getattr(jogo, "tempo_por_questao", 60):
        return "∞"
    return f"{int(getattr(jogo, 'tempo_restante', 0)):02d}s"


def marcar_inicio(jogo: Any) -> None:
    """Guarda o instante em que a questão apareceu (tempo de resposta)."""
    import time

    jogo._inicio_questao = time.monotonic()


# ======================================================================
# EFEITOS SONOROS
# ======================================================================
# Os efeitos têm botão próprio (EFEITOS), separado da música de fundo
# (ATIVAR SOM): dá para ouvir os toques dos botões com a música desligada.
# Para recriar os arquivos: py -3.14 ferramentas\gerar_efeitos.py
EFEITOS = {
    "acerto": "sons/efeitos/acerto.wav",
    "erro": "sons/efeitos/erro.wav",
    "tique": "sons/efeitos/tique.wav",
    "conquista": "sons/efeitos/conquista.wav",
    "clique": "sons/efeitos/clique.wav",
    "moeda": "sons/efeitos/moeda.wav",
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
        if not efeitos_ligados(jogo) or nome not in self.audios:
            return
        self.page.run_task(self._tocar, nome)

    async def _tocar(self, nome: str) -> None:
        try:
            await self.audios[nome].play(0)
        except Exception:
            pass


def efeitos_ligados(jogo: Any) -> bool:
    return bool(preferencias(getattr(jogo, "estado", None)).get("efeitos", True))


def botao_efeitos(
    jogo: Any, cor_texto: str, cor_borda: str, cor_destaque: str, compacto: bool = False
) -> ft.Control:
    """Botão EFEITOS: liga/desliga os sons de toque e de acerto (não a música).

    compacto=True mostra só o ícone (tela inicial, onde falta espaço).
    """
    dica = "Sons dos botões e do acerto/erro (a música de fundo fica no ATIVAR SOM)"
    botao: Any = ft.IconButton(tooltip=dica) if compacto else ft.OutlinedButton(height=42, tooltip=dica)

    def pintar() -> None:
        ligados = efeitos_ligados(jogo)
        icone = ft.Icons.TOUCH_APP if ligados else ft.Icons.DO_NOT_TOUCH
        lado = ft.BorderSide(1.5, cor_destaque if ligados else cor_borda)
        if compacto:
            botao.icon = icone
            botao.icon_color = cor_destaque if ligados else cor_texto
            botao.style = ft.ButtonStyle(side=lado)
            botao.tooltip = ("Efeitos LIGADOS. " if ligados else "Efeitos DESLIGADOS. ") + dica
        else:
            botao.content = "EFEITOS" if ligados else "SEM EFEITOS"
            botao.icon = icone
            botao.style = ft.ButtonStyle(color=cor_texto, side=lado)

    def clicar(_evento: ft.ControlEvent) -> None:
        jogo.estado.definir_acessibilidade(efeitos=not efeitos_ligados(jogo))
        # Toca o toque depois de ligar, para confirmar que o som voltou.
        efeitos(jogo).tocar(jogo, "clique")
        pintar()
        try:
            botao.update()
        except Exception:
            pass

    clicar._com_clique = True  # type: ignore[attr-defined]
    pintar()
    botao.on_click = clicar
    return botao


def efeitos(jogo: Any) -> EfeitosSonoros:
    """Cria (uma vez por módulo) e devolve o tocador de efeitos."""
    if getattr(jogo, "_efeitos", None) is None:
        jogo._efeitos = EfeitosSonoros(jogo.page)
        # Envia os tocadores ao navegador já agora; se isso ficasse para o
        # primeiro clique, o primeiro toque se perderia.
        try:
            jogo.page.update()
        except Exception:
            pass
    return jogo._efeitos


# ======================================================================
# SOM DE CLIQUE EM TODOS OS BOTÕES
# ======================================================================
# Percorre a tela montada e faz todo controle clicável (botões, cartões,
# ícones) tocar o "clique" antes de executar sua ação. Assim nenhum botão
# novo precisa ser alterado um a um. Respeita o botão ATIVAR SOM/MUTE.
_FILHOS = ("content", "controls", "actions", "title", "leading", "trailing", "subtitle")


def sons_nos_botoes(jogo: Any, raiz: Any) -> Any:
    """Liga o som de clique em todos os controles clicáveis de ``raiz``."""
    efeitos(jogo)  # prepara os tocadores antes do primeiro clique
    pendentes = [raiz]
    vistos: set[int] = set()
    while pendentes:
        controle = pendentes.pop()
        if controle is None or id(controle) in vistos:
            continue
        vistos.add(id(controle))
        if isinstance(controle, (list, tuple)):
            pendentes.extend(controle)
            continue
        if not isinstance(controle, ft.BaseControl):
            continue
        acao = getattr(controle, "on_click", None)
        if acao is not None and not getattr(acao, "_com_clique", False):
            controle.on_click = _acao_com_clique(jogo, acao)
        for nome in _FILHOS:
            filho = getattr(controle, nome, None)
            if filho is not None and not isinstance(filho, str):
                pendentes.append(filho)
    return raiz


def _acao_com_clique(jogo: Any, acao: Any) -> Any:
    # O Flet chama a ação com ou sem o evento conforme ela o aceite;
    # o envoltório repete esse comportamento.
    sem_evento = get_param_count(acao) == 0
    if inspect.isgeneratorfunction(acao) or inspect.isasyncgenfunction(acao):
        return acao
    if inspect.iscoroutinefunction(acao):
        async def com_clique_async(evento: Any = None) -> Any:
            efeitos(jogo).tocar(jogo, "clique")
            return await (acao() if sem_evento else acao(evento))
        com_clique_async._com_clique = True  # type: ignore[attr-defined]
        return com_clique_async

    def com_clique(evento: Any = None) -> Any:
        efeitos(jogo).tocar(jogo, "clique")
        return acao() if sem_evento else acao(evento)
    com_clique._com_clique = True  # type: ignore[attr-defined]
    return com_clique


# ======================================================================
# VIBRAÇÃO DA ALTERNATIVA CORRETA
# ======================================================================
# Ao acertar, o cartão da alternativa correta "vibra" junto com os aplausos.
# Fica desligado com a opção "Sem animações" (Acessibilidade).
# AJUSTE: TREMORES = quantas idas e vindas; AMPLITUDE = quanto se desloca.
TREMORES = 7
AMPLITUDE_TREMOR = 0.025


def vibrar_se_acertou(jogo: Any, indice: int, cartao: ft.Control) -> ft.Control:
    """Devolve o cartão; se for a alternativa acertada, ele vibra."""
    destaque = getattr(jogo, "_destaque_resposta", None)
    if (
        not destaque
        or indice != destaque["correta"]
        or destaque["escolhida"] != destaque["correta"]
        or sem_animacoes(jogo)
    ):
        return cartao
    envoltorio = ft.Container(
        content=cartao,
        col=getattr(cartao, "col", None),
        offset=ft.Offset(0, 0),
        scale=1.0,
        animate_offset=ft.Animation(45, ft.AnimationCurve.EASE_IN_OUT),
        animate_scale=ft.Animation(160, ft.AnimationCurve.EASE_OUT),
    )

    async def vibrar() -> None:
        try:
            await asyncio.sleep(0.05)
            envoltorio.scale = 1.04
            for passo in range(TREMORES):
                lado = AMPLITUDE_TREMOR if passo % 2 == 0 else -AMPLITUDE_TREMOR
                envoltorio.offset = ft.Offset(lado, 0)
                envoltorio.update()
                await asyncio.sleep(0.05)
            envoltorio.offset = ft.Offset(0, 0)
            envoltorio.scale = 1.0
            envoltorio.update()
        except Exception:
            pass

    jogo.page.run_task(vibrar)
    return envoltorio


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
    if abs(anterior - valor) > 0.004 and not sem_animacoes(jogo):
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


def rotulo_alternativa(jogo: Any, indice: int) -> str:
    """Marca em palavras (não só por cor) a alternativa correta e a escolhida.

    Acessibilidade para daltonismo: durante o destaque, a alternativa
    certa recebe "✓ CORRETA" e a escolhida errada recebe "✗ SUA ESCOLHA".
    """
    destaque = getattr(jogo, "_destaque_resposta", None)
    if not destaque:
        return ""
    if indice == destaque["correta"]:
        return "✓ CORRETA · " if indice != destaque["escolhida"] else "✓ CORRETA (SUA ESCOLHA) · "
    if indice == destaque["escolhida"]:
        return "✗ SUA ESCOLHA · "
    return ""


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
    if sem_animacoes(jogo):
        return conteudo
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
        if not sem_animacoes(jogo):
            texto.scale = 1.3 if restante % 2 == 0 else 1.0
        efeitos(jogo).tocar(jogo, "tique")
    else:
        texto.scale = 1.0


# ======================================================================
# LUPA (ACESSIBILIDADE)
# ======================================================================
# Liga/desliga a Lupa do Windows no modo "lente": um retângulo ampliado que
# acompanha o mouse. Atalhos do próprio Windows: Windows + "+" liga/aumenta,
# Windows + "−" diminui e Windows + Esc desliga.
_MAGNIFY = Path(os.environ.get("WINDIR", r"C:\Windows")) / "System32" / "Magnify.exe"


def lupa_disponivel() -> bool:
    return os.name == "nt" and _MAGNIFY.exists()


def lupa_ativa() -> bool:
    """Verifica se a Lupa do Windows está aberta."""
    if not lupa_disponivel():
        return False
    import subprocess

    try:
        saida = subprocess.run(
            ["tasklist", "/FI", "IMAGENAME eq Magnify.exe", "/NH"],
            capture_output=True,
            text=True,
            timeout=5,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        ).stdout
        return "magnify.exe" in saida.lower()
    except Exception:
        return False


def alternar_lupa() -> bool:
    """Abre a lupa em modo lente ou a fecha. Devolve True se ficou ligada."""
    import subprocess

    if not lupa_disponivel():
        return False
    sem_janela = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    if lupa_ativa():
        subprocess.run(["taskkill", "/IM", "Magnify.exe"], capture_output=True,
                       timeout=5, creationflags=sem_janela)
        if lupa_ativa():
            _teclas_windows_esc()  # atalho oficial para fechar a Lupa
        return lupa_ativa()
    # A Lupa é um aplicativo de acessibilidade do Windows (uiAccess): precisa
    # ser aberta pelo ShellExecute, como um atalho, e não por CreateProcess.
    os.startfile(str(_MAGNIFY), arguments="/lens")
    return True


def _teclas_windows_esc() -> None:
    """Envia Windows + Esc (fecha a Lupa do Windows)."""
    import ctypes
    import time

    usuario = ctypes.windll.user32
    tecla_windows, tecla_esc, soltar = 0x5B, 0x1B, 0x0002
    usuario.keybd_event(tecla_windows, 0, 0, 0)
    usuario.keybd_event(tecla_esc, 0, 0, 0)
    usuario.keybd_event(tecla_esc, 0, soltar, 0)
    usuario.keybd_event(tecla_windows, 0, soltar, 0)
    time.sleep(0.8)


def botao_lupa(cor_texto: str, cor_borda: str, cor_destaque: str, cor_fundo_ativo: str) -> ft.Control:
    """Botão LUPA para os cabeçalhos (tela inicial e módulos)."""
    if not lupa_disponivel():
        return ft.Container()
    ativa = lupa_ativa()
    botao = ft.OutlinedButton(height=42, tooltip=(
        "Lupa do Windows: amplia o que estiver sob o mouse. "
        "Atalhos: Windows + \"+\" aumenta, Windows + \"−\" diminui, Windows + Esc desliga."
    ))

    def pintar(ligada: bool) -> None:
        botao.content = "LUPA LIGADA" if ligada else "LUPA"
        botao.icon = ft.Icons.ZOOM_OUT if ligada else ft.Icons.ZOOM_IN
        botao.style = ft.ButtonStyle(
            color=cor_fundo_ativo if ligada else cor_texto,
            bgcolor=cor_destaque if ligada else None,
            side=ft.BorderSide(1.5, cor_destaque if ligada else cor_borda),
        )

    def clicar(_evento: ft.ControlEvent) -> None:
        pintar(alternar_lupa())
        try:
            botao.update()
        except Exception:
            pass

    pintar(ativa)
    botao.on_click = clicar
    return botao


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
            if indice is not None and indice not in et.eliminadas(jogo):
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
    parado = sem_animacoes(jogo)
    colunas: list[ft.Control] = []
    barras: list[tuple[ft.Container, int]] = []
    for posicao in posicoes_visuais:
        if posicao >= len(ordenados):
            continue
        jogador = ordenados[posicao]
        barra = ft.Container(
            content=ft.Text(f"{posicao + 1}º", size=30, weight=ft.FontWeight.BOLD, color="#06143C"),
            width=120,
            height=alturas[posicao] if parado else 10,
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

    if not parado:
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
    # Condições de acessibilidade em que a resposta foi dada:
    "tempo_limite_s", "sem_animacoes", "tema",
    # Modo economia: se estava ligado e quais ajudas foram compradas.
    "modo_economia", "ajudas",
]


def _escrever_csv(caminho: Path, campos: list[str], linhas: list[dict[str, Any]], anexar: bool = False) -> None:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    if anexar and caminho.exists():
        # Arquivo criado por uma versão anterior, com menos colunas: reescreve
        # com o cabeçalho novo, preservando todas as linhas já registradas.
        with caminho.open("r", encoding="utf-8-sig", newline="") as arquivo:
            leitor = csv.DictReader(arquivo, delimiter=";")
            if leitor.fieldnames and list(leitor.fieldnames) != campos:
                antigas = list(leitor)
                anexar = False
                linhas = antigas + list(linhas)
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
        if tempo_total is not None and not ADMIN_ATIVO:
            inicio = getattr(jogo, "_inicio_questao", None)
            if inicio is not None:
                # Relógio real: vale também quando não há limite de tempo.
                import time

                tempo = max(0.0, time.monotonic() - inicio)
            elif hasattr(jogo, "tempo_restante") and tempo_total:
                tempo = max(0.0, float(tempo_total) - float(jogo.tempo_restante))
        preferencias_atuais = preferencias(getattr(jogo, "estado", None))
        limite = int(preferencias_atuais.get("tempo", 60) or 0)
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
            "tempo_limite_s": str(limite) if limite else "sem limite",
            "sem_animacoes": "sim" if preferencias_atuais.get("sem_animacoes") else "não",
            "tema": getattr(jogo, "tema_nome", ""),
            "modo_economia": "sim" if getattr(getattr(jogo, "estado", None), "economia_ativa", False) else "não",
            "ajudas": et.texto_ajudas_para_pesquisa(jogo),
        }
        et.contar_questao(jogador)
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
