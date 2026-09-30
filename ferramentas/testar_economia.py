"""Testa as regras do Modo economia sem abrir o jogo (usa pasta temporária)."""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE_DIR))

import economia  # noqa: E402
import estado_jogo as modulo_estado  # noqa: E402
from estado_jogo import EstadoJogo  # noqa: E402


def verificar(condicao: bool, mensagem: str) -> None:
    if not condicao:
        raise AssertionError(mensagem)
    print("OK ", mensagem)


with tempfile.TemporaryDirectory() as pasta:
    pasta = Path(pasta)
    modulo_estado.ARQUIVO_RANKING = pasta / "ranking.xlsx"
    economia.ARQUIVO_ECONOMIA = pasta / "economia.csv"
    estado = EstadoJogo(pasta / "estado.json")
    estado.definir_quantidade(2)
    estado.definir_nome(0, "Ana")
    estado.definir_nome(1, "Bia")
    ana, bia = estado.jogadores[0], estado.jogadores[1]
    verificar(not estado.economia_ativa, "modo economia começa desligado")
    estado.definir_economia(True)

    # --- cofrinho
    ana["saldo"] = 300.0
    ok, _ = economia.aplicar(estado, ana, 500)
    verificar(not ok, "não aplica mais do que a carteira")
    ok, _ = economia.aplicar(estado, ana, 100)
    verificar(ok and economia.carteira(ana) == 200 and ana["cofrinho"] == 100, "aplica R$ 100")
    verificar(ana["saldo"] == 300, "saldo das questões não muda ao aplicar")
    for _ in range(3):
        economia.passar_mes(estado)
    verificar(ana["cofrinho"] == 103.03, "3 meses a 1%: 100 -> 103,03 (juros compostos)")
    ok, msg = economia.resgatar(estado, ana)
    verificar(not ok and "2 min" in msg, "carência de 5 minutos bloqueia o resgate")
    for _ in range(2):
        economia.passar_mes(estado)
    ok, _ = economia.resgatar(estado, ana)
    verificar(ok and ana["cofrinho"] == 0 and economia.carteira(ana) == 305.1, "resgate após 5 meses: 105,10 volta")

    # --- ajuda
    ok, _ = economia.comprar_ajuda(estado, ana, "eliminar", "PCT001")
    verificar(ok and economia.carteira(ana) == 285.1, "ajuda custa R$ 20")
    bia["saldo"] = 10.0
    ok, _ = economia.comprar_ajuda(estado, bia, "dica")
    verificar(not ok, "sem saldo, não compra ajuda")

    # --- dívida com teto de 100%
    bia["saldo"] = -100.0
    for _ in range(60):
        economia.passar_mes(estado)
    verificar(bia["juros_pagos"] == 100.0, "juros da dívida param no teto de 100% (R$ 100)")
    verificar(economia.carteira(bia) == -200.0, "dívida de 100 vira no máximo 200")
    bia["saldo"] = 400.0
    economia.passar_mes(estado)
    verificar(bia["juros_ciclo"] == 0.0, "ao sair da dívida, o ciclo de juros zera")
    bia["saldo"] = -100.0 - 100.0 * 0 + 0  # nova dívida
    bia["economia_ajuste"] = 0.0
    economia.passar_mes(estado)
    verificar(bia["juros_ciclo"] == 8.0, "nova dívida: 8% ao mês sobre R$ 100")

    # --- bônus
    economia.conceder_bonus(estado, ana)
    verificar(ana["bonus_recebidos"] == 1 and economia.carteira(ana) == 485.1, "bônus de R$ 200")

    # --- desligado não mexe no saldo das questões
    verificar(ana["saldo"] == 300.0, "saldo das questões intacto durante toda a economia")
    linhas = (pasta / "economia.csv").read_text(encoding="utf-8-sig").splitlines()
    verificar(len(linhas) > 10, f"movimentos registrados em economia.csv ({len(linhas) - 1})")
print("TESTE DA ECONOMIA APROVADO")
