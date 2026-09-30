"""Gera os efeitos sonoros do jogo (acerto com aplausos, erro, tique, conquista, clique).

Mesma técnica de gerar_sons.py: WAV sintetizado, sem dependências externas.
Os arquivos ficam em assets/sons/efeitos/.
"""

from __future__ import annotations

import math
import random
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
    # Fanfarra de vitória (os aplausos entram por cima, ver main()).
    "acerto.wav": [("C5", 0.09, "brilhante"), ("E5", 0.09, "brilhante"),
                   ("G5", 0.09, "brilhante"), ("C6", 0.16, "brilhante"),
                   ("G5", 0.08, "brilhante"), ("C6", 0.40, "brilhante")],
    # Dois tons graves descendentes.
    "erro.wav": [(233.0, 0.16, "grave"), (174.6, 0.34, "grave")],
    # Clique curto de relógio (últimos 10 segundos).
    "tique.wav": [(1800.0, 0.035, "clique")],
    # Moeda caindo no cofrinho (rendimento do Modo economia).
    "moeda.wav": [(1975.5, 0.06, "brilhante"), (2637.0, 0.22, "brilhante")],
    # Pequena fanfarra para o pódio.
    "conquista.wav": [("G4", 0.12, "brilhante"), ("C5", 0.12, "brilhante"),
                      ("E5", 0.12, "brilhante"), ("G5", 0.12, "brilhante"),
                      ("E5", 0.10, "brilhante"), ("G5", 0.42, "brilhante")],
}

VOLUMES = {"acerto.wav": 0.42, "erro.wav": 0.40, "tique.wav": 0.30, "conquista.wav": 0.40, "moeda.wav": 0.30}

# ACERTO: duração e volume dos aplausos que acompanham a fanfarra.
DURACAO_APLAUSOS = 2.2
VOLUME_APLAUSOS = 0.55
# TOQUE DOS BOTÕES: volume do "tec" (0 a 1).
VOLUME_CLIQUE = 0.55


def onda(timbre: str, fase: float) -> float:
    seno = math.sin(fase)
    if timbre == "brilhante":
        return 0.70 * seno + 0.22 * math.sin(2 * fase) + 0.08 * math.sin(3 * fase)
    if timbre == "grave":
        return 0.62 * (1.0 if seno >= 0 else -1.0) * 0.5 + 0.5 * seno
    return seno


def notas_em_amostras(notas: list[tuple], volume: float) -> list[float]:
    saida: list[float] = []
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
            saida.append(onda(timbre, 2 * math.pi * frequencia * tempo) * envelope * volume)
    return saida


def aplausos(duracao: float, volume: float, semente: int = 7) -> list[float]:
    """Plateia batendo palmas: muitas palmas curtas (ruído filtrado) sobrepostas.

    A intensidade cresce rápido, se mantém e vai sumindo, como um aplauso real.
    """
    sorteio = random.Random(semente)
    total = int(TAXA * duracao)
    saida = [0.0] * total
    tamanho_palma = int(TAXA * 0.045)
    instante = 0.0
    while True:
        progresso = instante / duracao
        # Palmas por segundo: sobe no começo e diminui no fim.
        densidade = 70 * min(1.0, 0.15 + progresso / 0.12)
        densidade *= 1.0 - 0.8 * max(0.0, progresso - 0.45) / 0.55
        instante += sorteio.expovariate(max(8.0, densidade))
        if instante >= duracao - 0.05:
            break
        inicio = int(instante * TAXA)
        # Cada palma é um ruído passado por um ressonador (o "timbre" da mão).
        frequencia = sorteio.uniform(900, 2600)
        raio = 0.86
        c1 = 2 * raio * math.cos(2 * math.pi * frequencia / TAXA)
        c2 = -raio * raio
        y1 = y2 = 0.0
        forca = sorteio.uniform(0.35, 1.0) * (1.0 - 0.8 * progresso ** 2)
        for k in range(min(tamanho_palma, total - inicio)):
            x = sorteio.uniform(-1, 1) * math.exp(-k / (TAXA * 0.006))
            y = x + c1 * y1 + c2 * y2
            y2, y1 = y1, y
            saida[inicio + k] += y * forca
    maior = max(abs(v) for v in saida) or 1.0
    return [v / maior * volume for v in saida]


def clique(volume: float) -> list[float]:
    """Toque seco de botão (como um "tec"): dura só 30 milésimos de segundo.

    Um estalo inicial de ruído + duas ressonâncias que somem muito rápido,
    sem tom sustentado.
    """
    sorteio = random.Random(3)
    saida = []
    for indice in range(int(TAXA * 0.030)):
        tempo = indice / TAXA
        estalo = sorteio.uniform(-1, 1) * math.exp(-tempo / 0.0015)
        corpo = (0.7 * math.sin(2 * math.pi * 1900 * tempo) * math.exp(-tempo / 0.004)
                 + 0.5 * math.sin(2 * math.pi * 750 * tempo) * math.exp(-tempo / 0.006))
        saida.append((0.45 * estalo + corpo) * volume)
    return saida


def salvar(nome: str, amostras: list[float]) -> None:
    quadros = bytearray()
    for amostra in amostras:
        quadros.extend(struct.pack("<h", int(max(-32767, min(32767, amostra * 32767)))))
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
        amostras = notas_em_amostras(notas, VOLUMES[nome])
        if nome == "acerto.wav":
            # ACERTO: fanfarra de vitória + aplausos da plateia por cima.
            palmas = aplausos(DURACAO_APLAUSOS, VOLUME_APLAUSOS)
            atraso = int(TAXA * 0.20)
            amostras += [0.0] * max(0, atraso + len(palmas) - len(amostras))
            for k, valor in enumerate(palmas):
                amostras[atraso + k] += valor
        salvar(nome, amostras)
    salvar("clique.wav", clique(VOLUME_CLIQUE))
    print(f"{len(EFEITOS) + 1} efeitos criados em {DESTINO}")


if __name__ == "__main__":
    main()
