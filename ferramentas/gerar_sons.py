"""Gera dez trilhas WAV leves e sem dependências externas para o jogo."""

from __future__ import annotations

import math
import struct
import wave
from pathlib import Path


DESTINO = Path(__file__).resolve().parents[1] / "assets" / "sons"
TAXA = 11_025
DURACAO = 10.0

NOTAS = {
    "C3": 130.81,
    "D3": 146.83,
    "E3": 164.81,
    "F3": 174.61,
    "G3": 196.00,
    "A3": 220.00,
    "B3": 246.94,
    "C4": 261.63,
    "D4": 293.66,
    "E4": 329.63,
    "F4": 349.23,
    "G4": 392.00,
    "A4": 440.00,
    "B4": 493.88,
    "C5": 523.25,
    "D5": 587.33,
    "E5": 659.25,
    "G5": 783.99,
    "A5": 880.00,
    "R": 0.0,
}

TRILHAS = [
    (
        "01_aventura.wav",
        ["C4", "E4", "G4", "C5", "G4", "E4", "D4", "G4"],
        0.50,
        "seno",
        0.24,
    ),
    (
        "02_arcade.wav",
        ["C5", "G4", "E5", "G4", "D5", "G4", "C5", "R"],
        0.25,
        "quadrada",
        0.13,
    ),
    (
        "03_conquista.wav",
        ["C4", "E4", "G4", "C5", "E5", "D5", "C5", "G4"],
        0.50,
        "brilhante",
        0.20,
    ),
    (
        "04_suspense.wav",
        ["C3", "R", "D3", "R", "C3", "E3", "D3", "R"],
        0.50,
        "escura",
        0.20,
    ),
    (
        "05_quiz.wav",
        ["E4", "G4", "A4", "G4", "E4", "D4", "C4", "D4"],
        0.25,
        "seno",
        0.20,
    ),
    (
        "06_futurista.wav",
        ["C4", "G4", "D5", "A4", "E5", "D5", "G4", "A4"],
        0.50,
        "futurista",
        0.18,
    ),
    (
        "07_8_bits.wav",
        ["C5", "E5", "G5", "E5", "D5", "G5", "A5", "G5"],
        0.25,
        "quadrada",
        0.12,
    ),
    (
        "08_jornada.wav",
        ["A3", "C4", "E4", "A4", "G4", "E4", "D4", "E4"],
        0.50,
        "suave",
        0.23,
    ),
    (
        "09_neon.wav",
        ["C4", "D4", "G4", "A4", "C5", "A4", "G4", "D4"],
        0.25,
        "futurista",
        0.18,
    ),
    (
        "10_desafio.wav",
        ["E4", "E4", "G4", "A4", "R", "A4", "G4", "D4"],
        0.25,
        "brilhante",
        0.19,
    ),
]


def onda(tipo: str, fase: float) -> float:
    seno = math.sin(fase)
    if tipo == "quadrada":
        return 0.72 if seno >= 0 else -0.72
    if tipo == "brilhante":
        return 0.72 * seno + 0.20 * math.sin(2 * fase)
    if tipo == "escura":
        return 0.80 * seno + 0.12 * math.sin(0.5 * fase)
    if tipo == "futurista":
        return 0.66 * seno + 0.18 * math.sin(3 * fase)
    if tipo == "suave":
        return 0.82 * seno + 0.08 * math.sin(2 * fase)
    return seno


def gerar(
    nome: str,
    sequencia: list[str],
    passo: float,
    timbre: str,
    volume: float,
) -> None:
    quadros = bytearray()
    total = int(TAXA * DURACAO)
    tamanho_ciclo = len(sequencia) * passo

    for indice in range(total):
        tempo = indice / TAXA
        posicao_ciclo = tempo % tamanho_ciclo
        posicao_nota = posicao_ciclo % passo
        nota = sequencia[int(posicao_ciclo / passo)]
        frequencia = NOTAS[nota]

        ataque = min(1.0, posicao_nota / 0.035)
        queda = min(1.0, (passo - posicao_nota) / 0.055)
        envelope = max(0.0, min(ataque, queda))
        pulso = 0.88 + 0.12 * math.sin(2 * math.pi * 2 * tempo)

        if frequencia == 0:
            amostra = 0.0
        else:
            fase = 2 * math.pi * frequencia * tempo
            principal = onda(timbre, fase)
            baixo = 0.20 * math.sin(2 * math.pi * (frequencia / 2) * tempo)
            amostra = (principal + baixo) * envelope * pulso

        valor = int(max(-32767, min(32767, amostra * volume * 32767)))
        quadros.extend(struct.pack("<h", valor))

    caminho = DESTINO / nome
    with wave.open(str(caminho), "wb") as arquivo:
        arquivo.setnchannels(1)
        arquivo.setsampwidth(2)
        arquivo.setframerate(TAXA)
        arquivo.writeframes(quadros)


def main() -> None:
    DESTINO.mkdir(parents=True, exist_ok=True)
    for configuracao in TRILHAS:
        gerar(*configuracao)
    print(f"{len(TRILHAS)} trilhas criadas em {DESTINO}")


if __name__ == "__main__":
    main()
