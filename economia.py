"""MODO ECONOMIA: cofrinho, ajudas, juros sobre dívida e bônus de participação.

Regras (definidas com o professor, 29/09/2026):
    • Só funciona com o "Modo economia" ligado (tela inicial). Desligado, o
      jogo é exatamente o da pesquisa: só +100 / −200 / +50.
    • 1 minuto de jogo ABERTO = 1 "mês". Com o jogo fechado nada acontece.
    • Cofrinho: rende 1% ao "mês" (juros compostos, M = C·1,01^t); o resgate
      só é liberado 5 "meses" (minutos) depois da última aplicação.
    • Dívida: se a carteira ficar negativa, cobra-se a taxa do cheque especial
      (limite legal de 8% ao mês) com TETO: os juros de uma dívida não passam
      de 100% dela (regra inspirada na Lei 14.690/2023, do rotativo).
    • Ajuda: R$ 20,00 cada (eliminar 2 alternativas, dica, +30 segundos).
    • Bônus: R$ 200,00 depois de 10 minutos de jogo E pelo menos 5 questões
      respondidas ou estudadas na sessão (uma vez por sessão e jogador).

Dinheiro de cada jogador (tudo fica em estado_jogo.json):
    saldo            -> SALDO DAS QUESTÕES (pesquisa): só +100 / −200 / +50.
    economia_ajuste  -> soma dos movimentos da economia (bônus, ajudas, juros,
                        aplicações e resgates).
    carteira         =  saldo + economia_ajuste   (dinheiro disponível)
    cofrinho         -> valor aplicado, rendendo.
    patrimônio       =  carteira + cofrinho

Cada movimento é registrado em dados/economia.csv para a pesquisa.
"""

from __future__ import annotations

import csv
import os
from datetime import datetime
from pathlib import Path
from typing import Any

# ----------------------------------------------------------------- regras
TAXA_COFRINHO = 0.01          # 1% ao "mês"
CARENCIA_MESES = 5            # resgate liberado após 5 "meses"
PRECO_AJUDA = 20.0            # R$ por ajuda
BONUS_VALOR = 200.0           # R$
BONUS_MINUTOS = 10            # minutos de jogo aberto
BONUS_QUESTOES = 5            # questões respondidas ou estudadas na sessão
# TAXA DA DÍVIDA: cheque especial. Limite legal de 8% ao mês (Resolução CMN
# 4.765/2019). Atualize o valor e a data da consulta quando necessário.
TAXA_DIVIDA = 0.08
TAXA_DIVIDA_FONTE = "Cheque especial: limite legal de 8% ao mês (CMN 4.765/2019)"
TETO_JUROS_DIVIDA = 1.0       # juros de uma dívida não passam de 100% dela

# SEGUNDOS POR "MÊS": 60 no jogo. Para testar mais rápido, defina a variável
# de ambiente RESPONDA_SEGUNDOS_POR_MES (ex.: 5).
try:
    SEGUNDOS_POR_MES = max(1.0, float(os.environ.get("RESPONDA_SEGUNDOS_POR_MES", "60")))
except ValueError:
    SEGUNDOS_POR_MES = 60.0

AJUDAS = {
    "eliminar": "Eliminar 2 alternativas erradas",
    "dica": "Dica: fórmula e estratégia",
    "tempo": "+30 segundos",
}

_CAMPOS_JOGADOR = {
    "economia_ajuste": 0.0,
    "cofrinho": 0.0,
    "cofrinho_ultimo_aporte": 0,   # "mês" (minuto de jogo) da última aplicação
    "cofrinho_aplicado": 0.0,      # total aplicado (para mostrar o rendimento)
    "cofrinho_historico": [],      # valores do cofrinho mês a mês (extrato)
    "juros_ciclo": 0.0,            # juros cobrados na dívida atual
    "juros_pagos": 0.0,            # total de juros pagos (dívida)
    "ultimo_rendimento": 0.0,      # rendimento do último "mês" (animação)
    "rendimento_total": 0.0,       # tudo o que o cofrinho já rendeu
    "ajudas_compradas": 0,
    "bonus_recebidos": 0,
}


def _r2(valor: float) -> float:
    return round(float(valor) + 1e-9, 2)


# ----------------------------------------------------------------- estado
def normalizar(dados: dict[str, Any]) -> None:
    """Garante os campos da economia no estado (chamado por EstadoJogo)."""
    economia = dados.get("economia")
    if not isinstance(economia, dict):
        economia = {}
    economia.setdefault("ativo", False)
    economia["ativo"] = bool(economia["ativo"])
    try:
        economia["meses"] = int(economia.get("meses", 0))
    except (TypeError, ValueError):
        economia["meses"] = 0
    dados["economia"] = economia
    for jogador in dados.get("jogadores", []):
        if not isinstance(jogador, dict):
            continue
        for chave, padrao in _CAMPOS_JOGADOR.items():
            valor = jogador.get(chave, padrao)
            if isinstance(padrao, list):
                jogador[chave] = [float(v) for v in valor][-24:] if isinstance(valor, list) else []
            elif isinstance(padrao, int):
                try:
                    jogador[chave] = int(valor)
                except (TypeError, ValueError):
                    jogador[chave] = padrao
            else:
                try:
                    jogador[chave] = float(valor)
                except (TypeError, ValueError):
                    jogador[chave] = padrao


def ativo(estado: Any) -> bool:
    return bool(getattr(estado, "dados", {}).get("economia", {}).get("ativo", False))


def meses(estado: Any) -> int:
    return int(estado.dados.get("economia", {}).get("meses", 0))


def carteira(jogador: dict[str, Any]) -> float:
    return _r2(float(jogador.get("saldo", 0.0)) + float(jogador.get("economia_ajuste", 0.0)))


def patrimonio(jogador: dict[str, Any]) -> float:
    return _r2(carteira(jogador) + float(jogador.get("cofrinho", 0.0)))


def meses_para_resgate(estado: Any, jogador: dict[str, Any]) -> int:
    """0 = resgate liberado; senão, quantos "meses" (minutos) faltam."""
    if float(jogador.get("cofrinho", 0.0)) <= 0:
        return 0
    passados = meses(estado) - int(jogador.get("cofrinho_ultimo_aporte", 0))
    return max(0, CARENCIA_MESES - passados)


# ----------------------------------------------------------------- registro
ARQUIVO_ECONOMIA = Path(__file__).resolve().parent / "dados" / "economia.csv"
CAMPOS_REGISTRO = ["data_hora", "jogador_id", "jogador", "tipo", "valor",
                   "carteira", "cofrinho", "saldo_questoes", "mes_jogo", "detalhe"]


def _registrar(estado: Any, jogador: dict[str, Any], tipo: str, valor: float, detalhe: str = "") -> None:
    caminho = ARQUIVO_ECONOMIA
    if getattr(estado, "caminho", None) is not None and "admin" in str(estado.caminho):
        caminho = caminho.with_name("economia_admin.csv")
    try:
        caminho.parent.mkdir(parents=True, exist_ok=True)
        novo = not caminho.exists()
        with caminho.open("a", encoding="utf-8-sig", newline="") as arquivo:
            escritor = csv.DictWriter(arquivo, fieldnames=CAMPOS_REGISTRO, delimiter=";")
            if novo:
                escritor.writeheader()
            escritor.writerow({
                "data_hora": datetime.now().isoformat(timespec="seconds"),
                "jogador_id": jogador.get("id", ""),
                "jogador": jogador.get("nome", ""),
                "tipo": tipo,
                "valor": f"{valor:.2f}".replace(".", ","),
                "carteira": f"{carteira(jogador):.2f}".replace(".", ","),
                "cofrinho": f"{float(jogador.get('cofrinho', 0.0)):.2f}".replace(".", ","),
                "saldo_questoes": f"{float(jogador.get('saldo', 0.0)):.2f}".replace(".", ","),
                "mes_jogo": meses(estado),
                "detalhe": detalhe,
            })
    except OSError as erro:
        print(f"Não foi possível registrar a economia: {erro}")


# ----------------------------------------------------------------- ações
def aplicar(estado: Any, jogador: dict[str, Any], valor: float) -> tuple[bool, str]:
    valor = _r2(valor)
    if valor <= 0:
        return False, "Digite um valor maior que zero."
    if valor > carteira(jogador) + 1e-9:
        return False, "Saldo insuficiente na carteira."
    jogador["economia_ajuste"] = _r2(jogador["economia_ajuste"] - valor)
    if float(jogador["cofrinho"]) <= 0:
        jogador["cofrinho_historico"] = []
    jogador["cofrinho"] = _r2(jogador["cofrinho"] + valor)
    jogador["cofrinho_aplicado"] = _r2(jogador["cofrinho_aplicado"] + valor)
    jogador["cofrinho_ultimo_aporte"] = meses(estado)
    jogador["cofrinho_historico"] = (jogador["cofrinho_historico"] + [jogador["cofrinho"]])[-24:]
    estado.salvar()
    _registrar(estado, jogador, "aplicacao", -valor)
    return True, "Valor aplicado no cofrinho."


def resgatar(estado: Any, jogador: dict[str, Any]) -> tuple[bool, str]:
    valor = _r2(jogador["cofrinho"])
    if valor <= 0:
        return False, "O cofrinho está vazio."
    faltam = meses_para_resgate(estado, jogador)
    if faltam:
        return False, f"Resgate liberado em {faltam} min (carência de {CARENCIA_MESES} min)."
    rendimento = _r2(valor - jogador["cofrinho_aplicado"])
    jogador["economia_ajuste"] = _r2(jogador["economia_ajuste"] + valor)
    jogador["cofrinho"] = 0.0
    jogador["cofrinho_aplicado"] = 0.0
    jogador["cofrinho_historico"] = []
    estado.salvar()
    _registrar(estado, jogador, "resgate", valor, f"rendimento={rendimento:.2f}")
    return True, "Resgate concluído: o valor voltou para a carteira."


def comprar_ajuda(estado: Any, jogador: dict[str, Any], tipo: str, questao_id: str = "") -> tuple[bool, str]:
    if tipo not in AJUDAS:
        return False, "Ajuda desconhecida."
    if carteira(jogador) < PRECO_AJUDA - 1e-9:
        return False, "Saldo insuficiente na carteira para comprar ajuda."
    jogador["economia_ajuste"] = _r2(jogador["economia_ajuste"] - PRECO_AJUDA)
    jogador["ajudas_compradas"] = int(jogador["ajudas_compradas"]) + 1
    estado.salvar()
    _registrar(estado, jogador, f"ajuda_{tipo}", -PRECO_AJUDA, questao_id)
    return True, AJUDAS[tipo]


def conceder_bonus(estado: Any, jogador: dict[str, Any]) -> None:
    jogador["economia_ajuste"] = _r2(jogador["economia_ajuste"] + BONUS_VALOR)
    jogador["bonus_recebidos"] = int(jogador["bonus_recebidos"]) + 1
    estado.salvar()
    _registrar(estado, jogador, "bonus", BONUS_VALOR, f"{BONUS_MINUTOS} min e {BONUS_QUESTOES} questões")


def passar_mes(estado: Any) -> list[str]:
    """Avança 1 "mês" (1 minuto de jogo aberto). Devolve avisos para a tela."""
    avisos: list[str] = []
    estado.dados["economia"]["meses"] = meses(estado) + 1
    for jogador in estado.jogadores_ativos():
        jogador["ultimo_rendimento"] = 0.0
        # Cofrinho: juros compostos de 1% sobre o valor acumulado.
        if float(jogador["cofrinho"]) > 0:
            rendimento = _r2(jogador["cofrinho"] * TAXA_COFRINHO)
            jogador["cofrinho"] = _r2(jogador["cofrinho"] + rendimento)
            jogador["ultimo_rendimento"] = rendimento
            jogador["rendimento_total"] = _r2(jogador["rendimento_total"] + rendimento)
            jogador["cofrinho_historico"] = (jogador["cofrinho_historico"] + [jogador["cofrinho"]])[-24:]
            _registrar(estado, jogador, "rendimento", rendimento)
        # Dívida: juros do cheque especial, com teto de 100% da dívida.
        disponivel = carteira(jogador)
        if disponivel < 0:
            principal = max(0.0, -disponivel - float(jogador["juros_ciclo"]))
            limite = max(0.0, principal * TETO_JUROS_DIVIDA - float(jogador["juros_ciclo"]))
            juros = _r2(min(-disponivel * TAXA_DIVIDA, limite))
            if juros > 0:
                jogador["economia_ajuste"] = _r2(jogador["economia_ajuste"] - juros)
                jogador["juros_ciclo"] = _r2(jogador["juros_ciclo"] + juros)
                jogador["juros_pagos"] = _r2(jogador["juros_pagos"] + juros)
                _registrar(estado, jogador, "juros_divida", -juros)
                avisos.append(f"{jogador['nome']}: juros de R$ {juros:.2f}".replace(".", ",")
                              + " sobre a dívida.")
                if float(jogador["juros_ciclo"]) >= principal * TETO_JUROS_DIVIDA - 0.005:
                    # Avisa uma única vez, no mês em que o teto é atingido.
                    avisos.append(f"{jogador['nome']}: juros da dívida chegaram ao teto de 100%.")
        else:
            jogador["juros_ciclo"] = 0.0
    estado.salvar()
    return avisos
