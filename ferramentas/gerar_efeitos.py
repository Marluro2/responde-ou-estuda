"""Gera os efeitos sonoros curtos do jogo (acerto, erro, tique e conquista).

Mesma técnica de gerar_sons.py: WAV sintetizado, sem dependências externas.
Os arquivos ficam em assets/sons/efeitos/.
"""

from __future__ import annotations

import math
import struct
import wave
from pathlib import Path


DESTINO = Path(__file__).resolve().parents[1] / "assets" / "sons" / "efeitos"
TAXA = 22_050

NOTAS = {
    "G3": 196.00, "C4": 261.63, "E4": 329.63, "G4": 392.00,
    "C5": 523.25, "E5": 659.25, "G5": 783.99, "C6": 1046.50,
}

# nome do arquivo: lista de (nota ou frequência, duração em segundos, timbre)
EFEITOS = {
    # Arpejo ascendente e brilhante.
    "acerto.wav": [("C5", 0.09, "brilhante"), ("E5", 0.09, "brilhante"),
                   ("G5", 0.09, "brilhante"), ("C6", 0.26, "brilhante")],
    # Dois tons graves descendentes.
    "erro.wav": [(233.0, 0.16, "grave"), (174.6, 0.34, "grave")],
    # Clique curto de relógio (últimos 10 segundos).
    "tique.wav": [(1800.0, 0.035, "clique")],
    # Pequena fanfarra para o pódio.
    "conquista.wav": [("G4", 0.12, "brilhante"), ("C5", 0.12, "brilhante"),
                      ("E5", 0.12, "brilhante"), ("G5", 0.12, "brilhante"),
                      ("E5", 0.10, "brilhante"), ("G5", 0.42, "brilhante")],
}

VOLUMES = {"acerto.wav": 0.42, "erro.wav": 0.40, "tique.wav": 0.30, "conquista.wav": 0.40}


def onda(timbre: str, fase: float) -> float:
    seno = math.sin(fase)
    if timbre == "brilhante":
        return 0.70 * seno + 0.22 * math.sin(2 * fase) + 0.08 * math.sin(3 * fase)
    if timbre == "grave":
        return 0.62 * (1.0 if seno >= 0 else -1.0) * 0.5 + 0.5 * seno
    return seno


def gerar(nome: str, notas: list[tuple], volume: float) -> None:
    quadros = bytearray()
    for nota, duracao, timbre in notas:
        frequencia = NOTAS.get(nota, nota) if isinstance(nota, str) else float(nota)
        total = int(TAXA * duracao)
        for indice in range(total):
            tempo = indice / TAXA
            ataque = min(1.0, tempo / 0.006)
            if timbre == "clique":
                queda = math.exp(-tempo * 90)
            else:
                queda = min(1.0, (duracao - tempo) / 0.04)
            envelope = max(0.0, min(ataque, queda))
            amostra = onda(timbre, 2 * math.pi * frequencia * tempo) * envelope
            valor = int(max(-32767, min(32767, amostra * volume * 32767)))
            quadros.extend(struct.pack("<h", valor))
    # Pequeno silêncio final evita estalo ao terminar.
    quadros.extend(b"\x00\x00" * int(TAXA * 0.03))
    with wave.open(str(DESTINO / nome), "wb") as arquivo:
        arquivo.setnchannels(1)
        arquivo.setsampwidth(2)
        arquivo.setframerate(TAXA)
        arquivo.writeframes(quadros)


def main() -> None:
    DESTINO.mkdir(parents=True, exist_ok=True)
    for nome, notas in EFEITOS.items():
        gerar(nome, notas, VOLUMES[nome])
    print(f"{len(EFEITOS)} efeitos criados em {DESTINO}")


if __name__ == "__main__":
    main()
