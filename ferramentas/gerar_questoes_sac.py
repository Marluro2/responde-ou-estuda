"""Gera dados/questoes_sac.json (Etapa 4 - Sistema de Amortização Constante).

Todas as contas são feitas aqui, com Decimal e arredondamento comercial,
para que enunciado, alternativas, resolução e estudo usem os mesmos números.
Base teórica: Rodrigues (2013), dissertação PROFMAT/UTFPR, seções 2.7 e 4.2:
    A = SD/n        SD_k = A(n - k)        J_k = i·A·(n - k + 1)
    P_k = A[1 + i(n - k + 1)]        prestações e juros em PA de razão -i·A

Uso:  py -3.14 ferramentas\\gerar_questoes_sac.py
"""

from __future__ import annotations

import json
import re
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
DESTINO = BASE_DIR / "dados" / "questoes_sac.json"
CONSULTA = "29/09/2026"
FONTE_DISSERTACAO = "Adaptado de Rodrigues (2013), dissertação PROFMAT/UTFPR"

IMAGENS = {
    "Casa própria": "imagens/juros/reforma_residencial.webp",
    "Apartamento": "imagens/juros/reforma_residencial.webp",
    "Reforma": "imagens/juros/reforma_residencial.webp",
    "Terreno": "imagens/juros/investimento_e_planejamento.webp",
    "Automóvel": "imagens/price/automovel_corolla.webp",
    "Veículo": "imagens/juros/financiamento_veiculo.webp",
    "Motocicleta": "imagens/price/motocicleta_honda_cb500.webp",
    "Crédito empresarial": "imagens/juros/emprestimo_e_credito.webp",
    "Notebook": "imagens/price/notebook_system76.webp",
    "Geladeira": "imagens/price/geladeira_liebherr.webp",
    "Televisor": "imagens/price/televisor_samsung.webp",
    "Lavadora": "imagens/price/lavadora_sharp.webp",
    "Ar-condicionado": "imagens/price/ar_condicionado_panasonic.webp",
    "Bicicleta": "imagens/price/bicicleta_mountain_bike.webp",
    "Console": "imagens/price/console_playstation5.webp",
    "Câmera": "imagens/price/camera_canon_eos5d.webp",
    "Smartphone": "imagens/price/smartphone_iphone_xr.webp",
    "Violão": "imagens/price/violao_yamaha_fgx04.webp",
    "Patinete elétrico": "imagens/price/patinete_eletrico.webp",
    "Robô aspirador": "imagens/price/robo_aspirador_xiaomi.webp",
    "Micro-ondas": "imagens/price/microondas_daewoo.webp",
}

# Posição da alternativa correta em cada nível (3 vezes cada letra A-E).
POSICOES = {
    "Super fácil": [3, 0, 2, 4, 1, 0, 4, 1, 3, 2, 1, 3, 0, 2, 4],
    "Fácil": [1, 4, 0, 2, 3, 4, 2, 0, 1, 3, 2, 0, 3, 4, 1],
    "Médio": [2, 3, 4, 0, 1, 3, 1, 4, 2, 0, 4, 2, 1, 0, 3],
    "Difícil": [4, 1, 3, 0, 2, 1, 0, 2, 4, 3, 3, 4, 2, 1, 0],
}


# ---------------------------------------------------------------- números
def D(valor) -> Decimal:
    return Decimal(str(valor))


def c(valor) -> Decimal:
    """Arredonda aos centavos (5 para cima)."""
    return D(valor).quantize(Decimal("0.01"), ROUND_HALF_UP)


def _milhar(inteiro: str, sep: str) -> str:
    grupos = []
    while len(inteiro) > 3:
        grupos.insert(0, inteiro[-3:])
        inteiro = inteiro[:-3]
    grupos.insert(0, inteiro)
    return sep.join(grupos)


def br(valor, casas: int = 2) -> str:
    """1234.5 -> 1.234,50 (texto)."""
    v = D(valor).quantize(Decimal(1).scaleb(-casas), ROUND_HALF_UP)
    sinal = "−" if v < 0 else ""
    inteiro, _, frac = f"{abs(v):f}".partition(".")
    return sinal + _milhar(inteiro, ".") + ("," + frac if casas else "")


def rs(valor) -> str:
    """Valor monetário para texto Markdown: R\\$ 1.234,50."""
    return "R\\$ " + br(valor)


def lx(valor, casas: int = 2, *, fixo: bool = False) -> str:
    """Número para LaTeX: 1{.}234{,}50 (inteiros sem ,00, salvo fixo=True)."""
    v = D(valor).quantize(Decimal(1).scaleb(-casas), ROUND_HALF_UP)
    sinal = "-" if v < 0 else ""
    inteiro, _, frac = f"{abs(v):f}".partition(".")
    if not fixo and frac and set(frac) == {"0"}:
        frac = ""
    return sinal + _milhar(inteiro, "{.}") + ("{,}" + frac if frac else "")


def lrs(valor) -> str:
    """Valor monetário dentro de fórmula: \\text{R\\$}\\,1{.}234{,}50."""
    return "\\text{R\\$}\\," + lx(valor, fixo=True)


def taxa(i) -> str:
    """0.015 -> 1,5%."""
    p = (D(i) * 100).normalize()
    return f"{p:f}".replace(".", ",") + "%"


def taxa_dec(i) -> str:
    """0.015 -> 0{,}015 (LaTeX)."""
    return f"{D(i).normalize():f}".replace(".", "{,}")


def T(modelo: str, **valores: str) -> str:
    """Substitui <<nome>> sem conflito com as chaves do LaTeX."""
    for nome, valor in valores.items():
        modelo = modelo.replace(f"<<{nome}>>", str(valor))
    if "<<" in modelo:
        raise ValueError(f"marcador sem valor em: {modelo[:80]}")
    return modelo


def sac(sd, n, i):
    """Devolve A, lista de juros, prestações e saldos (após cada mês)."""
    sd, i = D(sd), D(i)
    a = sd / n
    juros = [i * a * (n - k + 1) for k in range(1, n + 1)]
    prest = [a + j for j in juros]
    saldos = [a * (n - k) for k in range(1, n + 1)]
    return a, juros, prest, saldos


def pa_visual(rotulo: str, termos: list, razao, *, inicio: int = 1) -> dict:
    """Faixa da PA mostrada no estudo: primeiros termos, reticências e o último."""
    textos = [br(t) for t in termos]
    if len(textos) > 4:
        textos = textos[:3] + ["…", textos[-1]]
    return {"rotulo": rotulo, "termos": textos, "razao": br(razao), "inicio": inicio}


def alt(formulas: list[str], texto: str = "") -> str:
    """Alternativa no formato aceito pela tela: fórmulas separadas por "; " e,
    opcionalmente, uma frase final sem fórmulas."""
    corpo = "; ".join(f"${f}$" for f in formulas)
    return corpo + (". " + texto if texto else ".")


_BLOCO = re.compile(r"(?<!\\)\$(?:\\.|[^$])*?(?<!\\)\$")


def formato_valido(alternativa: str) -> bool:
    """A tela mostra primeiro as fórmulas e depois o texto final. Por isso não
    pode haver texto antes da 1ª fórmula nem texto entre fórmulas."""
    blocos = list(_BLOCO.finditer(alternativa))
    if not blocos:
        return True
    if alternativa[: blocos[0].start()].strip():
        return False
    for anterior, seguinte in zip(blocos, blocos[1:]):
        if alternativa[anterior.end(): seguinte.start()].strip(" ;,.\n"):
            return False
    return True


# ---------------------------------------------------------------- banco
questoes: list[dict] = []
contagem = {nivel: 0 for nivel in POSICOES}


def q(nivel: str, contexto: str, enunciado: str, correta: str, distratores: list[str],
      explicacao: str, estudo: tuple[str, str, str, str], *, pa: dict | None = None,
      fonte: str | None = None) -> None:
    if len(distratores) != 4:
        raise ValueError(f"{contexto}: são necessários 4 distratores")
    if correta in distratores or len(set(distratores)) != 4:
        raise ValueError(f"{contexto}: alternativas repetidas")
    for item in (correta, *distratores):
        if not formato_valido(item):
            raise ValueError(f"{contexto}: texto misturado com fórmulas: {item[:70]}")
    posicao = POSICOES[nivel][contagem[nivel]]
    contagem[nivel] += 1
    alternativas = list(distratores)
    alternativas.insert(posicao, correta)
    numero = len(questoes) + 1
    item = {
        "id": f"SAC{numero:03d}",
        "titulo": f"Questão {numero} - {contexto}",
        "produto": f"Nível {nivel}: Sistema SAC",
        "nivel": nivel,
        "imagem": IMAGENS[contexto],
        "enunciado": enunciado,
        "alternativas": alternativas,
        "correta": posicao,
        "explicacao": explicacao,
        "estudo": {
            "titulo": estudo[0],
            "texto": estudo[1],
            "formula": estudo[2],
            "exemplo": estudo[3],
        },
        "fonte": {
            "loja": fonte or "Imagem local incluída no aplicativo",
            "url": "Arquivo local incluído no aplicativo",
            "consulta": CONSULTA,
        },
    }
    if pa:
        item["pa"] = pa
    questoes.append(item)


# Exemplo 2.3 da dissertação (Marcos): R$ 24.000,00, 12 prestações, 1% a.m.
A_M, J_M, P_M, S_M = sac(24000, 12, "0.01")

# ======================================================================
# SUPER FÁCIL — ideias do SAC e reconhecimento de PA
# ======================================================================
N = "Super fácil"
q(N, "Casa própria",
  "No financiamento de uma casa pelo Sistema SAC, o que permanece **constante** em todas as prestações?",
  "A amortização.",
  ["O valor da prestação.", "Os juros do mês.", "O saldo devedor.", "O total já pago."],
  "No SAC, a dívida é dividida em partes iguais: $$A=\\frac{SD}{n}.$$ Por isso a amortização é a mesma em todos os meses.",
  ("Amortização constante",
   "O nome do sistema já revela sua característica: cada prestação devolve a mesma parte da dívida.",
   "$$A_1=A_2=\\cdots=A_n=\\frac{SD}{n}$$",
   "Uma dívida de R\\$ 12.000,00 em 12 meses tem amortização de R\\$ 1.000,00 em todos os meses."),
  pa=pa_visual("AMORTIZAÇÕES (PA CONSTANTE)", [1000] * 12, 0))

q(N, "Apartamento",
  "Na sigla **SAC**, usada em financiamentos, o que significa cada letra?",
  "Sistema de Amortização Constante.",
  ["Sistema de Aplicação Composta.", "Saldo Amortizado Corrigido.",
   "Sistema Americano de Crédito.", "Sistema de Acréscimo Contínuo."],
  "SAC é o **Sistema de Amortização Constante**: a parte da prestação que reduz a dívida é sempre a mesma.",
  ("O que é o SAC",
   "No SAC, a prestação é formada por uma amortização fixa mais os juros do período.",
   "$$P_k=A+J_k$$",
   "Se $A=\\text{R\\$ }500{,}00$ e $J_1=\\text{R\\$ }80{,}00$, a primeira prestação é R\\$ 580,00."))

q(N, "Automóvel",
  "Como se comportam as prestações de um financiamento pelo Sistema SAC?",
  "Diminuem sempre do mesmo valor: formam uma PA decrescente.",
  ["São todas iguais.", "Aumentam sempre do mesmo valor: PA crescente.",
   "Diminuem na mesma proporção: PG decrescente.", "Variam sem nenhuma regra."],
  "Os juros caem sempre o mesmo valor ($i\\cdot A$) e a amortização é fixa. Assim, $$P_{k+1}-P_k=-i\\cdot A,$$ uma razão constante e negativa: PA decrescente.",
  ("Prestações em PA",
   "Duas prestações seguidas diferem sempre pelo mesmo valor, e essa diferença é a razão da PA.",
   "$$r=P_{k+1}-P_k=-i\\cdot A$$",
   "No exemplo de Marcos (R\\$ 24.000,00, 12 meses, 1%): 2.240; 2.220; 2.200; … a razão é −20."),
  pa=pa_visual("PRESTAÇÕES DE MARCOS", P_M, -20), fonte=FONTE_DISSERTACAO)

q(N, "Notebook",
  "No SAC, como se calcula o valor da amortização $A$ de uma dívida $SD$ paga em $n$ prestações?",
  "$A=\\frac{SD}{n}$",
  ["$A=SD\\cdot i$", "$A=SD\\cdot n$", "$A=\\frac{SD}{i}$", "$A=SD-n$"],
  "A dívida é repartida igualmente entre as $n$ prestações: $$A=\\frac{SD}{n}.$$",
  ("Cálculo da amortização",
   "Divida o saldo devedor inicial pelo número de prestações.",
   "$$A=\\frac{SD}{n}$$",
   "R\\$ 6.000,00 em 10 prestações: $A=\\frac{6.000}{10}=600$, ou seja, R\\$ 600,00 por mês."))

q(N, "Geladeira",
  "No SAC, os juros pagos em cada mês formam que tipo de sequência?",
  "Uma PA decrescente.",
  ["Uma PG crescente.", "Uma sequência constante.", "Uma PA crescente.", "Uma sequência sem padrão."],
  "Os juros incidem sobre o saldo, que cai $A$ por mês. Logo $$J_{k+1}-J_k=-i\\cdot A,$$ razão constante e negativa.",
  ("Juros em PA",
   "Como o saldo diminui sempre $A$, os juros diminuem sempre $i\\cdot A$.",
   "$$J_k=i\\cdot SD_{k-1}\\qquad r=-i\\cdot A$$",
   "Com $A=\\text{R\\$ }2.000{,}00$ e $i=1\\%$, os juros caem R\\$ 20,00 por mês: 240; 220; 200; …"),
  pa=pa_visual("JUROS DE MARCOS", J_M, -20), fonte=FONTE_DISSERTACAO)

q(N, "Terreno",
  "No SAC, o saldo devedor diminui todo mês **sempre do mesmo valor**. Que valor é esse?",
  "A amortização.",
  ["A prestação do mês.", "Os juros do mês.", "A taxa de juros.", "O saldo inicial."],
  "Cada pagamento abate exatamente $A$ da dívida: $$SD_k=SD_{k-1}-A.$$ Os saldos formam uma PA de razão $-A$.",
  ("Saldo devedor em PA",
   "O saldo cai sempre a mesma quantia: a amortização.",
   "$$SD_k=SD_{k-1}-A$$",
   "Saldos de Marcos: 24.000; 22.000; 20.000; … razão −2.000."),
  pa=pa_visual("SALDOS DE MARCOS", [24000] + S_M[:-1], -2000, inicio=0), fonte=FONTE_DISSERTACAO)

q(N, "Televisor",
  "Em uma progressão aritmética (PA), como se chama a diferença constante entre um termo e o anterior?",
  "Razão.",
  ["Quociente.", "Termo geral.", "Soma dos termos.", "Média."],
  "Na PA $(a_1, a_2, a_3, \\ldots)$, a diferença $$r=a_{k+1}-a_k$$ é constante e recebe o nome de razão.",
  ("Razão de uma PA",
   "Subtraia qualquer termo do termo seguinte: o resultado é sempre o mesmo.",
   "$$r=a_2-a_1=a_3-a_2=\\cdots$$",
   "Na PA 50; 47; 44; 41, a razão é $r=47-50=-3$."))

q(N, "Lavadora",
  "Qual é a fórmula do **termo geral** de uma progressão aritmética?",
  "$a_n=a_1+(n-1)\\cdot r$",
  ["$a_n=a_1\\cdot q^{n-1}$", "$a_n=a_1+n\\cdot r$", "$a_n=\\frac{(a_1+a_n)\\cdot n}{2}$", "$a_n=a_1\\cdot r^n$"],
  "Do 1º ao $n$-ésimo termo somamos a razão $(n-1)$ vezes: $$a_n=a_1+(n-1)\\cdot r.$$",
  ("Termo geral da PA",
   "Para chegar ao termo $n$, partimos de $a_1$ e somamos $(n-1)$ razões.",
   "$$a_n=a_1+(n-1)\\cdot r$$",
   "Na PA 2.240; 2.220; 2.200; …, o 12º termo é $2.240+11\\cdot(-20)=2.020$."),
  fonte=FONTE_DISSERTACAO)

q(N, "Ar-condicionado",
  "No Sistema SAC, qual prestação tem o **maior** valor?",
  "A primeira.",
  ["A última.", "A do meio do contrato.", "Todas têm o mesmo valor.", "Depende do mês de pagamento."],
  "A primeira prestação carrega os juros sobre a dívida inteira: $$P_1=A+i\\cdot SD.$$ Depois disso as prestações só diminuem.",
  ("A maior prestação do SAC",
   "Como a PA das prestações é decrescente, o primeiro termo é o maior.",
   "$$P_1=A+i\\cdot SD$$",
   "Marcos: $P_1=2.000+0{,}01\\cdot24.000=2.240$, a maior das 12 prestações."),
  fonte=FONTE_DISSERTACAO)

q(N, "Bicicleta",
  "Uma progressão aritmética é **decrescente** quando sua razão $r$ é:",
  "Negativa (menor que zero).",
  ["Positiva (maior que zero).", "Igual a zero.", "Maior que 1.", "Um número entre 0 e 1."],
  "Se $r<0$, cada termo é menor que o anterior: $$a_{k+1}=a_k+r<a_k.$$",
  ("Sinal da razão",
   "Razão positiva: PA crescente. Razão zero: PA constante. Razão negativa: PA decrescente.",
   "$$r<0\\;\\Rightarrow\\;a_1>a_2>a_3>\\cdots$$",
   "No SAC as prestações têm razão $r=-i\\cdot A<0$: por isso diminuem."))

q(N, "Console",
  "No SAC, a sequência das amortizações $(A, A, A, \\ldots, A)$ é uma PA. Qual é a sua razão?",
  "$r=0$",
  ["$r=A$", "$r=-A$", "$r=i$", "$r=1$"],
  "Todos os termos são iguais, então $$r=A-A=0.$$ É uma PA constante.",
  ("PA constante",
   "Quando todos os termos são iguais, a diferença entre eles é zero.",
   "$$r=a_{k+1}-a_k=A-A=0$$",
   "A sequência 800; 800; 800; … é uma PA de razão 0."),
  pa=pa_visual("AMORTIZAÇÕES", [800] * 10, 0))

q(N, "Câmera",
  "No SAC, os juros de cada mês são calculados sobre qual valor?",
  "Sobre o saldo devedor do mês anterior.",
  ["Sobre o valor da prestação.", "Sobre a amortização.",
   "Sempre sobre o saldo inicial.", "Sobre o total já pago."],
  "Os juros remuneram o que ainda se deve: $$J_k=i\\cdot SD_{k-1}.$$",
  ("Base de cálculo dos juros",
   "A taxa incide sobre a dívida que existia antes do pagamento.",
   "$$J_k=i\\cdot SD_{k-1}$$",
   "Saldo de R\\$ 20.000,00 a 1% ao mês gera R\\$ 200,00 de juros."))

q(N, "Smartphone",
  "Por que as prestações do SAC diminuem com o tempo?",
  "Porque a amortização é fixa e os juros diminuem.",
  ["Porque a taxa de juros cai a cada mês.", "Porque a amortização diminui.",
   "Porque o saldo devedor aumenta.", "Porque o banco concede descontos."],
  "Temos $$P_k=A+J_k,$$ com $A$ constante e $J_k$ decrescente (o saldo cai). Logo $P_k$ decresce.",
  ("Composição da prestação",
   "Prestação = amortização (fixa) + juros (em queda).",
   "$$P_k=A+J_k$$",
   "Marcos: 2.000 + 240 = 2.240; depois 2.000 + 220 = 2.220; …"),
  fonte=FONTE_DISSERTACAO)

q(N, "Apartamento",
  "Segundo a literatura de Matemática Financeira, em que tipo de financiamento o SAC é muito utilizado no Brasil?",
  "No financiamento imobiliário.",
  ["No rotativo do cartão de crédito.", "No cheque especial.",
   "Em compras à vista.", "Na caderneta de poupança."],
  "O SAC é muito usado em financiamentos imobiliários (RODRIGUES, 2013; SOBRINHO, 2000): a dívida cai mais depressa e o total de juros é menor que no PRICE.",
  ("Onde o SAC aparece",
   "Contratos longos, como os de imóveis, costumam usar o SAC.",
   "$$\\text{SAC: prestações em PA decrescente}$$",
   "Um imóvel de R\\$ 100.000,00 em 100 meses tem amortização de R\\$ 1.000,00."),
  fonte=FONTE_DISSERTACAO)

q(N, "Casa própria",
  "Depois do pagamento da última prestação de um financiamento SAC, qual é o saldo devedor?",
  "Zero.",
  ["Igual à amortização.", "Igual à última prestação.", "Igual aos juros do último mês.",
   "Igual ao saldo inicial."],
  "Após $n$ amortizações iguais, $$SD_n=SD-n\\cdot A=SD-n\\cdot\\frac{SD}{n}=0.$$",
  ("Quitação da dívida",
   "O saldo é o último termo de uma PA que termina exatamente em zero.",
   "$$SD_k=A\\cdot(n-k)\\qquad SD_n=0$$",
   "Marcos: 12 amortizações de R\\$ 2.000,00 quitam R\\$ 24.000,00."),
  fonte=FONTE_DISSERTACAO)

# ======================================================================
# FÁCIL — um passo de cálculo com a PA
# ======================================================================
N = "Fácil"
q(N, "Casa própria",
  "Uma casa de R\\$ 240.000,00 será financiada pelo SAC em 240 prestações mensais. Qual é o valor da amortização mensal?",
  rs(1000), [rs(240), rs(2400), rs(10000), rs(24000)],
  "$$A=\\frac{SD}{n}=\\frac{240{.}000}{240}=1{.}000.$$ A amortização é R\\$ 1.000,00 em todos os meses.",
  ("Amortização constante", "Divida o valor financiado pelo número de prestações.",
   "$$A=\\frac{SD}{n}$$", "R\\$ 90.000,00 em 180 meses: $A=\\frac{90.000}{180}=500$."))

q(N, "Automóvel",
  "Um automóvel foi financiado pelo SAC com saldo de R\\$ 60.000,00 à taxa de 1% ao mês. Qual é o juro do primeiro mês?",
  rs(600), [rs(60), rs(6000), rs(1000), rs(61000)],
  "$$J_1=i\\cdot SD=0{,}01\\cdot60{.}000=600.$$ O juro do 1º mês é R\\$ 600,00.",
  ("Primeiro termo da PA dos juros", "O primeiro juro incide sobre toda a dívida.",
   "$$J_1=i\\cdot SD$$", "R\\$ 30.000,00 a 2%: $J_1=0{,}02\\cdot30.000=600$."))

a, j, p, s = sac(36000, 12, "0.01")
q(N, "Motocicleta",
  "Uma moto de R\\$ 36.000,00 será paga pelo SAC em 12 meses a 1% ao mês. A amortização é R\\$ 3.000,00 e o juro do 1º mês é R\\$ 360,00. Qual é a **primeira prestação**?",
  rs(p[0]), [rs(3000), rs(2640), rs(3036), rs(3600)],
  T("$$P_1=A+J_1=3{.}000+360=<<p1>>.$$ A primeira prestação é <<rs>>.", p1=lx(p[0]), rs=rs(p[0])),
  ("Prestação = amortização + juros", "Some a parte fixa (amortização) aos juros do mês.",
   "$$P_1=A+J_1$$", "$A=1.000$ e $J_1=150$: $P_1=1.150$."),
  pa=pa_visual("PRESTAÇÕES", p, -30))

q(N, "Veículo",
  "Um veículo de R\\$ 48.000,00 foi financiado pelo SAC em 24 meses. Os saldos devedores formam a PA 48.000; 46.000; 44.000; … Qual é a **razão** dessa PA?",
  rs(-2000), [rs(2000), rs(-200), rs(-48000), rs(24)],
  "$$r=46{.}000-48{.}000=-2{.}000.$$ A razão é $-A$: o saldo cai R\\$ 2.000,00 por mês.",
  ("Razão da PA dos saldos", "O saldo diminui exatamente uma amortização por mês.",
   "$$r_{SD}=-A=-\\frac{SD}{n}$$", "R\\$ 30.000,00 em 10 meses: saldos 30.000; 27.000; … razão −3.000."),
  pa=pa_visual("SALDOS", [48000, 46000, 44000, 42000, 0], -2000, inicio=0))

q(N, "Casa própria",
  "No exemplo de Marcos (R\\$ 24.000,00, 12 meses, 1% ao mês), as primeiras prestações SAC foram R\\$ 2.240,00; R\\$ 2.220,00; R\\$ 2.200,00. Qual é a **razão** dessa PA?",
  rs(-20), [rs(20), rs(-200), rs(-2000), rs(-220)],
  "$$r=2{.}220-2{.}240=-20.$$ Confirme: $r=-i\\cdot A=-0{,}01\\cdot2{.}000=-20$.",
  ("Razão das prestações", "Subtraia uma prestação da anterior ou use $r=-i\\cdot A$.",
   "$$r=P_2-P_1=-i\\cdot A$$", "$A=1.500$ e $i=2\\%$: $r=-30$."),
  pa=pa_visual("PRESTAÇÕES DE MARCOS", P_M, -20), fonte=FONTE_DISSERTACAO)

q(N, "Casa própria",
  "Continuando a PA das prestações de Marcos (R\\$ 2.240,00; R\\$ 2.220,00; R\\$ 2.200,00; …), qual é a **4ª prestação**?",
  rs(2180), [rs(2160), rs(2200), rs(2190), rs(2220)],
  "$$P_4=P_3+r=2{.}200+(-20)=2{.}180.$$",
  ("Próximo termo da PA", "Some a razão ao termo anterior.",
   "$$a_{k+1}=a_k+r$$", "Na PA 900; 885; 870, o próximo termo é 855."),
  pa=pa_visual("PRESTAÇÕES DE MARCOS", P_M, -20), fonte=FONTE_DISSERTACAO)

q(N, "Crédito empresarial",
  "Um empréstimo empresarial pelo SAC tem amortização de R\\$ 2.000,00 e taxa de 1% ao mês. Qual é a razão da PA dos **juros** mensais?",
  rs(-20), [rs(20), rs(-2000), rs(-200), rs(-2)],
  "$$r=-i\\cdot A=-0{,}01\\cdot2{.}000=-20.$$ Os juros caem R\\$ 20,00 por mês.",
  ("Razão da PA dos juros", "Os juros caem $i$ vezes a amortização a cada mês.",
   "$$r_J=-i\\cdot A$$", "$A=5.000$ e $i=0{,}8\\%$: $r=-40$."))

q(N, "Terreno",
  "Um terreno foi financiado pelo SAC com amortização de R\\$ 1.500,00 em 20 prestações. Qual é o saldo devedor após **8 pagamentos**?",
  rs(18000), [rs(12000), rs(28500), rs(1500), rs(30000)],
  "Usando o termo geral dos saldos: $$SD_k=A\\cdot(n-k)=1{.}500\\cdot(20-8)=18{.}000.$$",
  ("Saldo após k pagamentos", "Restam $(n-k)$ amortizações a pagar.",
   "$$SD_k=A\\cdot(n-k)$$", "$A=2.000$, $n=12$, $k=5$: $SD_5=14.000$."),
  fonte=FONTE_DISSERTACAO)

q(N, "Apartamento",
  "Um apartamento tem saldo financiado de R\\$ 90.000,00 pelo SAC, a 0,8% ao mês. Qual é o juro do primeiro mês?",
  rs(720), [rs(72), rs(7200), rs(900), rs(800)],
  "$$J_1=0{,}008\\cdot90{.}000=720.$$",
  ("Taxa decimal", "Converta 0,8% em 0,008 e multiplique pelo saldo.",
   "$$0{,}8\\%=\\frac{0{,}8}{100}=0{,}008$$", "R\\$ 50.000,00 a 0,6%: juros de R\\$ 300,00."))

a, j, p, s = sac(18000, 12, "0.02")
q(N, "Notebook",
  "Um financiamento de R\\$ 18.000,00 pelo SAC terá 12 prestações a 2% ao mês. Qual é a **primeira prestação**?",
  rs(p[0]), [rs(1500), rs(1830), rs(1860 + 360), rs(1536)],
  T("$$A=\\frac{18{.}000}{12}=1{.}500\\qquad J_1=0{,}02\\cdot18{.}000=360$$ $$P_1=1{.}500+360=<<p>>.$$", p=lx(p[0])),
  ("Primeira prestação do SAC", "Calcule a amortização e some os juros sobre a dívida toda.",
   "$$P_1=\\frac{SD}{n}+i\\cdot SD$$", "R\\$ 10.000,00 em 10 meses a 1%: $P_1=1.000+100=1.100$."),
  pa=pa_visual("PRESTAÇÕES", p, -30))

q(N, "Geladeira",
  "Uma geladeira foi financiada pelo SAC em 36 prestações mensais. A sequência das prestações, da 1ª à última, é uma PA com quantos termos?",
  "36 termos.", ["35 termos.", "37 termos.", "12 termos.", "1 termo."],
  "Cada prestação é um termo: da 1ª à 36ª há $$n=36$$ termos.",
  ("Número de termos", "O número de termos da PA é o número de prestações.",
   "$$(P_1, P_2, \\ldots, P_n)\\;\\to\\;n\\text{ termos}$$", "Um contrato de 120 meses gera uma PA de 120 prestações."))

q(N, "Televisor",
  "Os juros de um financiamento SAC começam em R\\$ 500,00 e a PA dos juros tem razão −10. Qual é o juro do **2º mês**?",
  rs(490), [rs(510), rs(500), rs(480), rs(450)],
  "$$J_2=J_1+r=500+(-10)=490.$$",
  ("Segundo termo", "Some a razão (negativa) ao primeiro termo.",
   "$$J_2=J_1+r$$", "$J_1=300$ e $r=-6$: $J_2=294$."))

q(N, "Reforma",
  "Os saldos devedores de uma reforma financiada pelo SAC são R\\$ 30.000,00; R\\$ 27.500,00; R\\$ 25.000,00; … Qual é a **amortização** mensal?",
  rs(2500), [rs(30000), rs(-2500), rs(250), rs(27500)],
  "A razão dos saldos é $-A$: $$r=27{.}500-30{.}000=-2{.}500\\;\\Rightarrow\\;A=2{.}500.$$",
  ("Amortização a partir dos saldos", "A queda do saldo em um mês é a amortização.",
   "$$A=SD_{k-1}-SD_k$$", "Saldos 9.000; 8.250: $A=750$."),
  pa=pa_visual("SALDOS", [30000, 27500, 25000, 22500, 0], -2500, inicio=0))

q(N, "Lavadora",
  "Qual das sequências abaixo pode representar as prestações de um financiamento pelo **SAC**?",
  "1.500; 1.480; 1.460; 1.440",
  ["1.500; 1.500; 1.500; 1.500", "1.500; 1.520; 1.540; 1.560",
   "1.500; 1.350; 1.215; 1.093,50", "1.500; 1.430; 1.470; 1.410"],
  "No SAC as prestações formam uma PA decrescente: $$1{.}480-1{.}500=1{.}460-1{.}480=-20.$$ A sequência constante é típica do PRICE; a de razão multiplicativa 0,9 é uma PG.",
  ("Reconhecendo o SAC", "Procure diferenças iguais e negativas entre termos vizinhos.",
   "$$P_{k+1}-P_k=r<0\\;\\text{(constante)}$$", "800; 790; 780 é PA de razão −10; 800; 720; 648 é PG de razão 0,9."))

q(N, "Casa própria",
  "No SAC, a última prestação vale $P_n=A\\cdot(1+i)$. Com amortização de R\\$ 1.000,00 e taxa de 1,5% ao mês, qual é a última prestação?",
  rs(1015), [rs(1000), rs(1150), rs(2500), rs(15)],
  "$$P_n=1{.}000\\cdot(1+0{,}015)=1{.}015.$$ No último mês, os juros incidem só sobre a última amortização.",
  ("Último termo da PA", "No último mês, o saldo anterior é igual a uma amortização.",
   "$$P_n=A+i\\cdot A=A\\cdot(1+i)$$", "Madalena (R\\$ 100.000,00; 100 meses; 1,5%): $P_{100}=1.015$."),
  fonte=FONTE_DISSERTACAO)

# ======================================================================
# MÉDIO — termo geral, soma da PA e função afim
# ======================================================================
N = "Médio"
a, j, p, s = sac(100000, 100, "0.015")
q(N, "Casa própria",
  "Madalena financiou sua casa de R\\$ 100.000,00 pelo SAC em 100 prestações mensais, a 1,5% ao mês. A 1ª prestação é R\\$ 2.500,00. Qual é a **15ª prestação**?",
  rs(p[14]), [rs(2275), rs(2485), rs(2290 + 15), rs(1015)],
  T("A razão é $r=-i\\cdot A=-0{,}015\\cdot1{.}000=-15$. Pelo termo geral: $$P_{15}=P_1+(15-1)\\cdot r=2{.}500-14\\cdot15=<<p>>.$$", p=lx(p[14])),
  ("Termo geral das prestações", "Identifique $P_1$ e a razão; depois aplique o termo geral da PA.",
   "$$P_k=P_1+(k-1)\\cdot r\\qquad r=-i\\cdot A$$", "$P_1=3.200$ e $r=-20$: $P_{11}=3.200-10\\cdot20=3.000$."),
  pa=pa_visual("PRESTAÇÕES DE MADALENA", p, -15), fonte=FONTE_DISSERTACAO)

a, j, p, s = sac(120000, 60, "0.01")
q(N, "Apartamento",
  "Um apartamento de R\\$ 120.000,00 foi financiado pelo SAC em 60 meses a 1% ao mês. Qual é a **25ª prestação**?",
  rs(p[24]), [rs(3200), rs(2700), rs(2740), rs(2000)],
  T("$$A=\\frac{120{.}000}{60}=2{.}000\\qquad P_1=2{.}000+1{.}200=3{.}200\\qquad r=-20$$ $$P_{25}=3{.}200+24\\cdot(-20)=<<p>>.$$", p=lx(p[24])),
  ("Termo geral aplicado", "Calcule $A$, $P_1$ e $r$; depois use $P_k=P_1+(k-1)r$.",
   "$$P_k=A\\cdot[1+i\\cdot(n-k+1)]$$", "Conferência: $P_{25}=2.000\\cdot(1+0{,}01\\cdot36)=2.720$."),
  pa=pa_visual("PRESTAÇÕES", p, -20))

a, j, p, s = sac(72000, 36, "0.012")
q(N, "Veículo",
  "Um veículo de R\\$ 72.000,00 foi financiado pelo SAC em 36 meses a 1,2% ao mês. Quanto se paga de **juros na 10ª prestação**?",
  rs(j[9]), [rs(864), rs(672), rs(624), rs(2648)],
  T("$$A=\\frac{72{.}000}{36}=2{.}000$$ $$J_{10}=i\\cdot A\\cdot(n-k+1)=0{,}012\\cdot2{.}000\\cdot(36-10+1)=<<j>>.$$", j=lx(j[9])),
  ("Juros da k-ésima parcela", "Antes da parcela $k$ ainda restam $(n-k+1)$ amortizações.",
   "$$J_k=i\\cdot A\\cdot(n-k+1)$$", "$A=1.000$, $i=2\\%$, $n=12$, $k=3$: $J_3=0{,}02\\cdot1.000\\cdot10=200$."),
  pa=pa_visual("JUROS", j, -24), fonte=FONTE_DISSERTACAO)

q(N, "Casa própria",
  "No exemplo de Marcos (R\\$ 24.000,00, 12 meses, 1% ao mês), os juros formam a PA 240; 220; …; 20. Qual é o **total de juros** pago?",
  rs(1560), [rs(1440), rs(2880), rs(1300), rs(3120)],
  "Soma da PA: $$S_{12}=\\frac{(J_1+J_{12})\\cdot12}{2}=\\frac{(240+20)\\cdot12}{2}=1{.}560.$$",
  ("Soma dos termos da PA", "Some o primeiro e o último termo, multiplique pelo número de termos e divida por 2.",
   "$$S_n=\\frac{(a_1+a_n)\\cdot n}{2}$$", "PA 100; 90; …; 10 (10 termos): $S=\\frac{110\\cdot10}{2}=550$."),
  pa=pa_visual("JUROS DE MARCOS", J_M, -20), fonte=FONTE_DISSERTACAO)

a, j, p, s = sac(60000, 24, "0.015")
total_j = sum(j)
q(N, "Automóvel",
  "Um automóvel de R\\$ 60.000,00 foi financiado pelo SAC em 24 meses a 1,5% ao mês. Qual é o **total pago** (amortizações + juros)?",
  rs(60000 + total_j), [rs(total_j), rs(81600), rs(60000 + 900 * 12), rs(69000)],
  T("$$J_1=0{,}015\\cdot60{.}000=900\\qquad J_{24}=0{,}015\\cdot2{.}500=37{,}50$$ $$\\text{Juros}=\\frac{(900+37{,}50)\\cdot24}{2}=<<jt>>$$ $$\\text{Total}=60{.}000+<<jt>>=<<tot>>.$$",
    jt=lx(total_j), tot=lx(60000 + total_j)),
  ("Custo total no SAC", "Total pago = dívida (soma das amortizações) + soma da PA dos juros.",
   "$$\\text{Total}=SD+\\frac{(J_1+J_n)\\cdot n}{2}$$", "Marcos: 24.000 + 1.560 = 25.560."))

a, j, p, s = sac(30000, 10, "0.02")
q(N, "Crédito empresarial",
  "Um empréstimo de R\\$ 30.000,00 pelo SAC tem 10 prestações a 2% ao mês. A 1ª é R\\$ 3.600,00 e a última é R\\$ 3.060,00. Qual é a **soma de todas as prestações**?",
  rs(sum(p)), [rs(36000), rs(30600), rs(3330), rs(66600)],
  T("As prestações formam uma PA de 10 termos: $$S_{10}=\\frac{(3{.}600+3{.}060)\\cdot10}{2}=<<s>>.$$", s=lx(sum(p))),
  ("Soma das prestações", "Use a soma da PA com o primeiro e o último termo.",
   "$$S_n=\\frac{(P_1+P_n)\\cdot n}{2}$$", "Marcos: $\\frac{(2.240+2.020)\\cdot12}{2}=25.560$."),
  pa=pa_visual("PRESTAÇÕES", p, -60))

a, j, p, s = sac(150000, 120, "0.009")
q(N, "Apartamento",
  "Um apartamento de R\\$ 150.000,00 foi financiado pelo SAC em 120 meses. Qual é o **saldo devedor após 45 pagamentos**?",
  rs(s[44]), [rs(56250), rs(105000), rs(148750), rs(90000)],
  T("$$A=\\frac{150{.}000}{120}=1{.}250\\qquad SD_{45}=1{.}250\\cdot(120-45)=<<s>>.$$", s=lx(s[44])),
  ("Termo geral dos saldos", "Multiplique a amortização pelas parcelas que ainda faltam.",
   "$$SD_k=A\\cdot(n-k)$$", "$A=500$, $n=60$, $k=20$: $SD_{20}=20.000$."),
  fonte=FONTE_DISSERTACAO)

a, j, p, s = sac(48000, 48, "0.01")
q(N, "Veículo",
  "Um veículo de R\\$ 48.000,00 foi financiado pelo SAC em 48 meses a 1% ao mês (1ª prestação de R\\$ 1.480,00). **Qual prestação** vale R\\$ 1.300,00?",
  "A 19ª prestação.", ["A 18ª prestação.", "A 20ª prestação.", "A 13ª prestação.", "A 30ª prestação."],
  "Com $A=1{.}000$, a razão é $r=-10$. Resolvendo o termo geral: $$1{.}300=1{.}480+(k-1)\\cdot(-10)\\;\\Rightarrow\\;k-1=18\\;\\Rightarrow\\;k=19.$$",
  ("Encontrar a posição de um termo", "Substitua o valor no termo geral e isole $k$.",
   "$$k=\\frac{P_k-P_1}{r}+1$$", "$P_1=500$, $r=-5$, $P_k=450$: $k=11$."),
  pa=pa_visual("PRESTAÇÕES", p, -10))

a, j, p, s = sac(18000, 18, "0.02")
q(N, "Motocicleta",
  "Uma moto de R\\$ 18.000,00 foi financiada pelo SAC em 18 meses a 2% ao mês. Use $P_k=A\\cdot[1+i\\cdot(n-k+1)]$ e calcule a **7ª prestação**.",
  rs(p[6]), [rs(1360), rs(1220), rs(1260), rs(1140)],
  T("$$A=1{.}000\\qquad P_7=1{.}000\\cdot[1+0{,}02\\cdot(18-7+1)]=1{.}000\\cdot1{,}24=<<p>>.$$", p=lx(p[6])),
  ("Fórmula da dissertação", "A prestação $k$ é a amortização mais os juros sobre $(n-k+1)$ amortizações.",
   "$$P_k=A\\cdot[1+i\\cdot(n-k+1)]$$", "$A=2.000$, $i=1\\%$, $n=12$, $k=1$: $P_1=2.000\\cdot1{,}12=2.240$."),
  pa=pa_visual("PRESTAÇÕES", p, -20), fonte=FONTE_DISSERTACAO)

q(N, "Casa própria",
  "No exemplo de Marcos (R\\$ 24.000,00, 12 meses, 1%), a prestação pode ser vista como uma **função afim** do número $k$ da parcela, definida para $k=1, 2, \\ldots, 12$. Qual é essa função?",
  "$P(k)=2{.}260-20k$",
  ["$P(k)=2{.}240-20k$", "$P(k)=2{.}000+20k$", "$P(k)=2{.}240\\cdot(0{,}99)^k$", "$P(k)=2{.}260+20k$"],
  "$$P(k)=A\\cdot[1+i\\cdot(n-k+1)]=2{.}000\\cdot[1+0{,}01\\cdot(13-k)]=2{.}260-20k.$$ Coeficiente angular $-20$ (a razão) em um domínio discreto.",
  ("PA como função afim", "Uma PA é uma função afim restrita aos números naturais: $a_k=a_1+(k-1)r=r\\cdot k+(a_1-r)$.",
   "$$P(k)=r\\cdot k+(P_1-r)$$", "PA 500; 490; 480: $P(k)=-10k+510$."),
  pa=pa_visual("PRESTAÇÕES DE MARCOS", P_M, -20), fonte=FONTE_DISSERTACAO)

a, j, p, s = sac(36000, 18, "0.015")
media = sum(p) / 18
q(N, "Reforma",
  "Uma reforma de R\\$ 36.000,00 foi financiada pelo SAC em 18 meses a 1,5% ao mês. Qual é o **valor médio** das prestações?",
  rs(media), [rs(2540), rs(2030), rs(2000), rs(2270)],
  T("$$P_1=2{.}000+540=2{.}540\\qquad P_{18}=2{.}000\\cdot1{,}015=2{.}030$$ Em uma PA, a média é a média do primeiro e do último termo: $$\\bar P=\\frac{2{.}540+2{.}030}{2}=<<m>>.$$", m=lx(media)),
  ("Média dos termos de uma PA", "Termos equidistantes dos extremos têm a mesma soma, então a média é $\\frac{a_1+a_n}{2}$.",
   "$$\\bar a=\\frac{a_1+a_n}{2}$$", "PA 300; 280; 260; 240: média $\\frac{300+240}{2}=270$."),
  pa=pa_visual("PRESTAÇÕES", p, -30))

a, j, p, s = sac(40000, 20, "0.01")
q(N, "Crédito empresarial",
  "Um crédito de R\\$ 40.000,00 pelo SAC tem 20 prestações a 1% ao mês. Quanto se paga de juros nas **5 primeiras prestações**?",
  rs(sum(j[:5])), [rs(2000), rs(1600), rs(1900), rs(4200)],
  T("$$J_1=400\\qquad r=-0{,}01\\cdot2{.}000=-20\\qquad J_5=400-4\\cdot20=320$$ $$S_5=\\frac{(400+320)\\cdot5}{2}=<<s>>.$$", s=lx(sum(j[:5]))),
  ("Soma parcial de uma PA", "Calcule o 5º termo e aplique a soma dos 5 primeiros termos.",
   "$$S_k=\\frac{(a_1+a_k)\\cdot k}{2}$$", "Juros 240; 220; 200: $S_3=660$."),
  pa=pa_visual("JUROS", j, -20))

q(N, "Terreno",
  "Em um financiamento SAC de um terreno, $P_1=\\text{R\\$ }3.200{,}00$, $P_2=\\text{R\\$ }3.180{,}00$ e a amortização é R\\$ 2.000,00. Qual é a **taxa mensal** de juros?",
  "1% ao mês.", ["2% ao mês.", "0,1% ao mês.", "10% ao mês.", "1,6% ao mês."],
  "A razão é $r=3{.}180-3{.}200=-20$. Como $r=-i\\cdot A$: $$i=\\frac{-r}{A}=\\frac{20}{2{.}000}=0{,}01=1\\%.$$",
  ("Da razão à taxa", "A razão da PA guarda a informação da taxa.",
   "$$i=\\frac{-r}{A}$$", "$r=-45$ e $A=3.000$: $i=1{,}5\\%$."))

a, j, p, s = sac(200000, 100, "0.009")
q(N, "Casa própria",
  "Uma casa de R\\$ 200.000,00 foi financiada pelo SAC em 100 meses a 0,9% ao mês. Após pagar **metade** das prestações, quanto será a 51ª prestação?",
  rs(p[50]), [rs(3800), rs(2000), rs(2918), rs(2450)],
  T("$$A=2{.}000\\qquad SD_{50}=2{.}000\\cdot50=100{.}000$$ $$P_{51}=A+i\\cdot SD_{50}=2{.}000+0{,}009\\cdot100{.}000=<<p>>.$$", p=lx(p[50])),
  ("Prestação a partir do saldo", "Os juros da parcela $k$ incidem sobre o saldo após $k-1$ pagamentos.",
   "$$P_k=A+i\\cdot SD_{k-1}$$", "$A=1.000$, $SD=30.000$, $i=1\\%$: $P=1.300$."))

a, j, p, s = sac(90000, 60, "0.01")
q(N, "Apartamento",
  "Um apartamento com saldo de R\\$ 90.000,00 foi financiado pelo SAC com amortização de R\\$ 1.500,00 e juros de 1% ao mês. Quantas prestações há e qual é a **última**?",
  T("60 prestações; a última é <<v>>.", v=rs(p[-1])),
  [T("60 prestações; a última é <<v>>.", v=rs(1500)), T("90 prestações; a última é <<v>>.", v=rs(1015)),
   T("60 prestações; a última é <<v>>.", v=rs(2400)), T("50 prestações; a última é <<v>>.", v=rs(1515))],
  T("$$n=\\frac{SD}{A}=\\frac{90{.}000}{1{.}500}=60\\qquad P_{60}=A\\cdot(1+i)=1{.}500\\cdot1{,}01=<<p>>.$$", p=lx(p[-1])),
  ("Número de termos e último termo", "O número de prestações é $\\frac{SD}{A}$; o último termo tem juros sobre uma só amortização.",
   "$$n=\\frac{SD}{A}\\qquad P_n=A\\cdot(1+i)$$", "$SD=24.000$, $A=2.000$: $n=12$ e $P_{12}=2.020$ (a 1%)."))

# ======================================================================
# DIFÍCIL — demonstração, comparação, limite e decisões
# ======================================================================
N = "Difícil"
q(N, "Casa própria",
  "Madalena financia R\\$ 100.000,00 pelo SAC a 1,5% ao mês. Hipoteticamente, o número de parcelas passa a ser $n=200$, $n=400$ e $n=1000$. Assinale a alternativa com as amortizações (em reais), o limite de $A_n=\\frac{SD}{n}$ quando $n\\to\\infty$ e sua interpretação.",
  alt(["A_{200}=500;\\;A_{400}=250;\\;A_{1000}=100", "\\lim_{n\\to\\infty}A_n=0", "P_1\\to" + lrs(1500)],
      "A amortização some e paga-se praticamente só juros."),
  [alt(["A_{200}=500;\\;A_{400}=250;\\;A_{1000}=100", "\\lim_{n\\to\\infty}A_n=0", "P_1\\to" + lrs(0)],
       "A primeira prestação também desaparece."),
   alt(["A_{200}=1{.}000;\\;A_{400}=500;\\;A_{1000}=200", "\\lim_{n\\to\\infty}A_n=100", "P_1\\to" + lrs(1600)],
       "Existe um piso para a amortização."),
   alt(["A_{200}=500;\\;A_{400}=250;\\;A_{1000}=100", "\\lim_{n\\to\\infty}A_n=0", "J_{total}\\to" + lrs(0)],
       "O custo com juros desaparece quando o prazo cresce."),
   alt(["A_{200}=500;\\;A_{400}=250;\\;A_{1000}=100", "\\lim_{n\\to\\infty}A_n=1{.}500", "P_1\\to" + lrs(3000)],
       "A amortização tende aos juros do primeiro mês.")],
  "$$A_{200}=\\frac{100{.}000}{200}=500\\qquad A_{400}=250\\qquad A_{1000}=100.$$ Como $\\frac{SD}{n}\\to0$: $$\\lim_{n\\to\\infty}A_n=0\\qquad P_1=A_n+i\\cdot SD\\to i\\cdot SD=1{.}500.$$ Com prazo muito longo, a dívida quase não diminui e paga-se basicamente juros (RODRIGUES, 2013, Ex. 4.10).",
  ("Prazo longo no SAC", "Aumentar indefinidamente o prazo faz a amortização tender a zero; a 1ª prestação tende aos juros sobre a dívida.",
   "$$\\lim_{n\\to\\infty}\\frac{SD}{n}=0\\qquad \\lim_{n\\to\\infty}P_1=i\\cdot SD$$",
   "R\\$ 50.000,00 a 1%: com $n$ enorme, $P_1\\approx500$, quase só juros."),
  fonte=FONTE_DISSERTACAO)

a, j, p, s = sac(80000, 40, "0.012")
q(N, "Apartamento",
  "Mostre que, no SAC, o total de juros é $J_{total}=\\frac{i\\cdot SD\\cdot(n+1)}{2}$ e aplique a um financiamento de R\\$ 80.000,00 em 40 meses a 1,2% ao mês.",
  alt(["J_{total}=\\frac{(i\\cdot SD+i\\cdot A)\\cdot n}{2}=\\frac{i\\cdot SD\\cdot(n+1)}{2}", "J_{total}=" + lrs(sum(j))],
      "Soma de uma PA de n termos, do 1º ao último juro."),
  [alt(["J_{total}=i\\cdot SD\\cdot n", "J_{total}=" + lrs(D("0.012") * 80000 * 40)],
       "O juro do 1º mês repetido em todos os meses."),
   alt(["J_{total}=\\frac{i\\cdot SD\\cdot n}{2}", "J_{total}=" + lrs(D("0.012") * 80000 * 20)],
       "Metade dos juros simples do período."),
   alt(["J_{total}=SD\\cdot[(1+i)^n-1]", "J_{total}=" + lrs(c(80000 * ((1 + D("0.012")) ** 40 - 1)))],
       "Juros compostos sobre a dívida inteira."),
   alt(["J_{total}=\\frac{i\\cdot SD\\cdot(n-1)}{2}", "J_{total}=" + lrs(D("0.012") * 80000 * 39 / 2)],
       "Soma de apenas n − 1 termos da PA.")],
  T("Os juros formam uma PA com $J_1=i\\cdot SD$ e $J_n=i\\cdot A=\\frac{i\\cdot SD}{n}$: $$J_{total}=\\frac{\\left(i\\cdot SD+\\frac{i\\cdot SD}{n}\\right)\\cdot n}{2}=\\frac{i\\cdot SD\\cdot(n+1)}{2}.$$ $$J_{total}=\\frac{0{,}012\\cdot80{.}000\\cdot41}{2}=<<v>>.$$", v=lx(sum(j))),
  ("Total de juros no SAC", "Some a PA dos juros usando o primeiro e o último termo.",
   "$$J_{total}=\\frac{i\\cdot SD\\cdot(n+1)}{2}$$", "Marcos: $\\frac{0{,}01\\cdot24.000\\cdot13}{2}=1.560$."),
  pa=pa_visual("JUROS", j, -D("0.012") * 2000))

pmt = c(D(24000) * D("0.01") / (1 - (1 + D("0.01")) ** -12))
jp = c(pmt * 12 - 24000)
q(N, "Casa própria",
  "Marcos compara SAC e PRICE para R\\$ 24.000,00 em 12 meses a 1% ao mês. No PRICE, $PMT\\approx\\text{R\\$ }2.132{,}37$. Assinale a comparação correta do **total de juros** e da **1ª prestação**.",
  alt(["J_{SAC}=" + lrs(1560), "J_{PRICE}\\approx" + lrs(jp), "P_1^{SAC}=" + lrs(2240)],
      "O SAC paga menos juros, mas começa com prestação maior que a do PRICE."),
  [alt(["J_{SAC}=" + lrs(1560), "J_{PRICE}\\approx" + lrs(1560), "P_1^{SAC}=" + lrs(2240)],
       "Os dois sistemas pagam os mesmos juros."),
   alt(["J_{SAC}=" + lrs(jp), "J_{PRICE}\\approx" + lrs(1560), "P_1^{SAC}=" + lrs(2020)],
       "O PRICE paga menos juros, e o SAC começa com prestação menor."),
   alt(["J_{SAC}=" + lrs(1560), "J_{PRICE}\\approx" + lrs(jp), "P_1^{SAC}=" + lrs(2000)],
       "O SAC paga menos juros e tem todas as prestações menores."),
   alt(["J_{SAC}=" + lrs(2880), "J_{PRICE}\\approx" + lrs(jp), "P_1^{SAC}=" + lrs(2240)],
       "O SAC paga mais juros porque a 1ª prestação é maior.")],
  T("SAC: $$J=\\frac{(240+20)\\cdot12}{2}=1{.}560.$$ PRICE: $$J=12\\cdot<<pmt>>-24{.}000\\approx<<jp>>.$$ No SAC a dívida cai mais depressa no início, por isso rende menos juros; em troca, $P_1=2{.}240>2{.}132{,}37$.",
    pmt=lx(pmt), jp=lx(jp)),
  ("SAC (PA) × PRICE (PG)", "No SAC as prestações formam uma PA decrescente; no PRICE são constantes e seus valores presentes formam uma PG.",
   "$$J_{SAC}=\\frac{i\\cdot SD\\cdot(n+1)}{2}\\qquad J_{PRICE}=n\\cdot PMT-SD$$",
   "Quanto maior o prazo, maior a diferença de juros a favor do SAC."),
  fonte=FONTE_DISSERTACAO)

q(N, "Casa própria",
  "Para R\\$ 24.000,00 em 12 meses a 1% ao mês, as prestações SAC são $P(k)=2{.}260-20k$ e a prestação PRICE é constante, $PMT\\approx\\text{R\\$ }2.132{,}37$. A partir de qual parcela a prestação SAC fica **menor** que a do PRICE?",
  "A partir da 7ª parcela.",
  ["A partir da 6ª parcela.", "A partir da 2ª parcela.", "A partir da 12ª parcela.", "Nunca: a SAC é sempre maior."],
  "Resolva a inequação da função afim: $$2{.}260-20k<2{.}132{,}37\\;\\Rightarrow\\;20k>127{,}63\\;\\Rightarrow\\;k>6{,}38.$$ Conferência: $P_6=2{.}140>2{.}132{,}37$ e $P_7=2{.}120<2{.}132{,}37$.",
  ("Inequação com a PA", "Escreva a prestação SAC como função afim de $k$ e compare com a constante do PRICE.",
   "$$P(k)=P_1+(k-1)\\cdot r<PMT$$", "Se $P(k)=1.100-10k$ e $PMT=1.040$, então $k>6$: a partir da 7ª."),
  pa=pa_visual("PRESTAÇÕES DE MARCOS", P_M, -20), fonte=FONTE_DISSERTACAO)

q(N, "Crédito empresarial",
  "Qual encadeamento demonstra corretamente a fórmula $J_k=i\\cdot A\\cdot(n-k+1)$ a partir do termo geral da PA dos juros?",
  alt(["J_1=i\\cdot SD=i\\cdot nA", "J_k=J_1+(k-1)\\cdot(-iA)", "J_k=i\\cdot A\\cdot(n-k+1)"],
      "Termo geral da PA dos juros, de razão −iA."),
  [alt(["J_1=i\\cdot SD", "J_k=J_1\\cdot(1-i)^{k-1}", "J_k=i\\cdot A\\cdot(n-k+1)"],
       "Os juros formariam uma PG."),
   alt(["J_1=i\\cdot SD", "J_k=J_1+k\\cdot(-iA)", "J_k=i\\cdot A\\cdot(n-k)"],
       "A razão é somada k vezes a partir do 1º termo."),
   alt(["SD_k=A\\cdot(n-k)", "J_k=i\\cdot SD_k", "J_k=i\\cdot A\\cdot(n-k)"],
       "Os juros incidem sobre o saldo após o pagamento."),
   alt(["J_1=i\\cdot SD", "J_k=J_1-(k-1)\\cdot A", "J_k=i\\cdot A\\cdot(n-k+1)"],
       "A razão dos juros seria −A.")],
  "Os juros formam PA com $J_1=i\\cdot SD=i\\cdot n\\cdot A$ e razão $r=-i\\cdot A$. Pelo termo geral: $$J_k=i\\cdot nA-(k-1)\\cdot iA=i\\cdot A\\cdot(n-k+1).$$ Para uma prova formal, usa-se indução sobre $k$ (RODRIGUES, 2013, seção 2.7).",
  ("Demonstrando com o termo geral", "Identifique o 1º termo e a razão da PA dos juros; substitua $SD=n\\cdot A$.",
   "$$J_k=J_1+(k-1)\\cdot r\\qquad J_1=i\\cdot nA\\qquad r=-iA$$",
   "Com $k=n$: $J_n=i\\cdot A\\cdot1=i\\cdot A$, os juros do último mês."),
  fonte=FONTE_DISSERTACAO)

a, j, p, s = sac(150000, 180, "0.008")
q(N, "Casa própria",
  "Uma casa de R\\$ 150.000,00 foi financiada pelo SAC em 180 meses a 0,8% ao mês. Qual é o **total desembolsado** ao longo do contrato?",
  alt(["\\text{Total}=SD\\cdot\\left[1+\\frac{i\\cdot(n+1)}{2}\\right]", "\\text{Total}=" + lrs(150000 + sum(j))]),
  [alt(["\\text{Total}=SD\\cdot(1+i\\cdot n)", "\\text{Total}=" + lrs(150000 * (1 + D("0.008") * 180))]),
   alt(["\\text{Total}=SD\\cdot\\frac{i\\cdot(n+1)}{2}", "\\text{Total}=" + lrs(sum(j))]),
   alt(["\\text{Total}=SD\\cdot(1+i)^n", "\\text{Total}=" + lrs(c(150000 * (1 + D("0.008")) ** 180))]),
   alt(["\\text{Total}=n\\cdot P_1", "\\text{Total}=" + lrs(180 * p[0])])],
  T("$$J_{total}=\\frac{0{,}008\\cdot150{.}000\\cdot181}{2}=<<j>>$$ $$\\text{Total}=150{.}000+<<j>>=<<t>>.$$", j=lx(sum(j)), t=lx(150000 + sum(j))),
  ("Custo total em contratos longos", "Some a dívida aos juros (soma da PA).",
   "$$\\text{Total}=SD\\cdot\\left[1+\\frac{i\\cdot(n+1)}{2}\\right]$$", "Marcos: $24.000\\cdot(1+0{,}065)=25.560$."))

q(N, "Veículo",
  "Em um financiamento SAC, a primeira prestação é R\\$ 3.500,00, a última é R\\$ 2.020,00 e as prestações caem R\\$ 20,00 por mês. Determine o número de prestações, a amortização, a taxa e o saldo financiado.",
  alt(["n=75", "A=" + lrs(2000), "i=1\\%\\text{ a.m.}", "SD=" + lrs(150000)]),
  [alt(["n=74", "A=" + lrs(2000), "i=1\\%\\text{ a.m.}", "SD=" + lrs(148000)]),
   alt(["n=75", "A=" + lrs(2020), "i=1\\%\\text{ a.m.}", "SD=" + lrs(151500)]),
   alt(["n=75", "A=" + lrs(1980), "i=2\\%\\text{ a.m.}", "SD=" + lrs(148500)]),
   alt(["n=76", "A=" + lrs(2000), "i=0{,}5\\%\\text{ a.m.}", "SD=" + lrs(152000)])],
  "Termo geral: $$2{.}020=3{.}500+(n-1)\\cdot(-20)\\;\\Rightarrow\\;n=75.$$ Como $r=-iA$ e $P_n=A+iA$: $$iA=20\\;\\Rightarrow\\;A=2{.}020-20=2{.}000\\;\\Rightarrow\\;i=\\frac{20}{2{.}000}=1\\%.$$ $$SD=n\\cdot A=75\\cdot2{.}000=150{.}000.$$",
  ("Reconstruindo o contrato pela PA", "O termo geral dá $n$; o último termo e a razão dão $A$ e $i$.",
   "$$n=\\frac{P_n-P_1}{r}+1\\qquad P_n=A+iA\\qquad r=-iA$$",
   "$P_1=1.300$, $P_n=1.010$, $r=-10$: $n=30$, $A=1.000$, $i=1\\%$."))

q(N, "Terreno",
  "O saldo devedor de um SAC de R\\$ 60.000,00 em 30 meses pode ser escrito como $SD(k)=60{.}000-2{.}000k$. Qual afirmação sobre essa função está correta?",
  alt(["k\\in\\{0,1,\\ldots,30\\}", "SD(30)=0"],
      "Função afim de domínio discreto: o gráfico são pontos alinhados, com inclinação −2.000."),
  [alt(["k\\in\\{0,1,\\ldots,30\\}", "SD(30)=0"],
       "Função exponencial: os pontos formam uma curva."),
   alt(["k\\in\\mathbb{R}", "SD(30)=2{.}000"],
       "Função afim contínua: o gráfico é uma reta inteira."),
   alt(["k\\in\\{0,1,\\ldots,30\\}", "SD(30)=0"],
       "Inclinação +2.000, pois o saldo cresce a cada mês."),
   alt(["k\\in\\{0,1,\\ldots,30\\}", "SD(k)=60{.}000"],
       "Função constante, pois a amortização é constante.")],
  "$SD(k)=SD-A\\cdot k$ é uma PA de razão $-A$: uma função afim cujo domínio são os meses $k=0,1,\\ldots,30$. $$SD(30)=60{.}000-2{.}000\\cdot30=0.$$ Os pontos $(k, SD(k))$ ficam alinhados, sem formar uma reta contínua (RODRIGUES, 2013, cap. 4).",
  ("Domínio discreto × contínuo", "Sequências são funções definidas nos naturais: o gráfico é formado por pontos.",
   "$$SD(k)=SD-A\\cdot k,\\quad k\\in\\{0,1,\\ldots,n\\}$$",
   "$f(x)=200+4x$ gera a PA 200; 204; 208; … (juros simples)."),
  fonte=FONTE_DISSERTACAO)

a, j, p, s = sac(60000, 24, "0.01")
jt_car = 3 * 600 + sum(j)
q(N, "Casa própria",
  "Um imóvel de R\\$ 60.000,00 tem **carência de 3 meses** em que se pagam apenas os juros de 1% ao mês; depois, o SAC é aplicado em 24 prestações. Qual é a 1ª prestação SAC e o total de juros do contrato?",
  alt(["P_1=" + lrs(p[0]), "J_{car}=" + lrs(1800), "J_{SAC}=" + lrs(sum(j)), "J_{total}=" + lrs(jt_car)],
      "Na carência pagam-se só os juros, e a dívida não muda."),
  [alt(["P_1=" + lrs(p[0]), "J_{car}=" + lrs(0), "J_{SAC}=" + lrs(sum(j)), "J_{total}=" + lrs(sum(j))],
       "A carência não gera juros."),
   alt(["P_1=" + lrs(2500), "J_{car}=" + lrs(1800), "J_{SAC}=" + lrs(sum(j)), "J_{total}=" + lrs(jt_car)],
       "A prestação SAC é só a amortização."),
   alt(["P_1=" + lrs(p[0]), "J_{car}=" + lrs(1800), "J_{SAC}=" + lrs(14400), "J_{total}=" + lrs(16200)],
       "No SAC paga-se i·SD em todos os meses."),
   alt(["P_1=" + lrs(p[0]), "J_{car}=" + lrs(600), "J_{SAC}=" + lrs(sum(j)), "J_{total}=" + lrs(8100)],
       "A carência cobra juros de um único mês.")],
  T("Carência: $3\\cdot0{,}01\\cdot60{.}000=1{.}800$ (a dívida não muda). SAC: $$A=\\frac{60{.}000}{24}=2{.}500\\qquad P_1=2{.}500+600=<<p>>$$ $$J_{SAC}=\\frac{0{,}01\\cdot60{.}000\\cdot25}{2}=<<js>>\\qquad J_{total}=1{.}800+<<js>>=<<t>>.$$",
    p=lx(p[0]), js=lx(sum(j)), t=lx(jt_car)),
  ("Carência com juros pagos", "Na carência, pagar os juros mantém o saldo; o SAC começa depois sobre a dívida original.",
   "$$J_{car}=m\\cdot i\\cdot SD\\qquad J_{SAC}=\\frac{i\\cdot SD\\cdot(n+1)}{2}$$",
   "2 meses de carência a 1% sobre 30.000: R\\$ 600,00 de juros."))

a, j, p, s = sac(240000, 240, "0.0075")
q(N, "Casa própria",
  "Uma casa de R\\$ 240.000,00 foi financiada pelo SAC em 240 meses a 0,75% ao mês. Quanto a família desembolsa no **primeiro ano** (12 prestações)?",
  rs(sum(p[:12])), [rs(12 * p[0]), rs(12 * 1000), rs(sum(p[:12]) - 1000), rs(21600)],
  T("$$A=1{.}000\\qquad P_1=1{.}000+1{.}800=2{.}800\\qquad r=-0{,}0075\\cdot1{.}000=-7{,}50$$ $$S_{12}=\\frac{12}{2}\\cdot[2\\cdot2{.}800+11\\cdot(-7{,}50)]=<<s>>.$$", s=lx(sum(p[:12]))),
  ("Soma dos k primeiros termos", "Sem calcular $P_{12}$, use a forma da soma com a razão.",
   "$$S_k=\\frac{k}{2}\\cdot[2P_1+(k-1)\\cdot r]$$", "$P_1=1.000$, $r=-10$: $S_4=\\frac{4}{2}(2.000-30)=3.940$."),
  pa=pa_visual("PRESTAÇÕES", p, D("-7.5")))

a, j, p, s = sac(120000, 150, "0.01")
q(N, "Apartamento",
  "Em um SAC de R\\$ 120.000,00 em 150 meses a 1% ao mês, em qual parcela os **juros ficam iguais à amortização** (a prestação vale $2A$)?",
  "Na 51ª parcela.", ["Na 50ª parcela.", "Na 100ª parcela.", "Na 75ª parcela.", "Na 1ª parcela."],
  "$$A=\\frac{120{.}000}{150}=800.$$ Impondo $J_k=A$: $$i\\cdot A\\cdot(n-k+1)=A\\;\\Rightarrow\\;n-k+1=\\frac{1}{i}=100\\;\\Rightarrow\\;k=51.$$ Conferência: $J_{51}=0{,}01\\cdot800\\cdot100=800$.",
  ("Equação com o termo geral", "Iguale o termo geral dos juros à amortização e isole $k$.",
   "$$J_k=i\\cdot A\\cdot(n-k+1)=A\\;\\Rightarrow\\;k=n+1-\\frac{1}{i}$$",
   "$n=60$, $i=2\\%$: $k=61-50=11$."),
  fonte=FONTE_DISSERTACAO)

j100 = D("0.01") * 100000 * 101 / 2
j200 = D("0.01") * 100000 * 201 / 2
q(N, "Casa própria",
  "Um imóvel de R\\$ 100.000,00 pelo SAC a 1% ao mês pode ser pago em 100 ou em 200 meses. Compare a 1ª prestação e o total de juros.",
  alt(["P_1^{(100)}=" + lrs(2000), "J^{(100)}=" + lrs(j100), "P_1^{(200)}=" + lrs(1500), "J^{(200)}=" + lrs(j200)],
      "Dobrar o prazo reduz a 1ª prestação em 25%, mas quase dobra os juros."),
  [alt(["P_1^{(100)}=" + lrs(2000), "J^{(100)}=" + lrs(j100), "P_1^{(200)}=" + lrs(1000), "J^{(200)}=" + lrs(j200)],
       "Dobrar o prazo reduz a 1ª prestação pela metade."),
   alt(["P_1^{(100)}=" + lrs(2000), "J^{(100)}=" + lrs(j100), "P_1^{(200)}=" + lrs(1500), "J^{(200)}=" + lrs(j100)],
       "Os juros não dependem do prazo."),
   alt(["P_1^{(100)}=" + lrs(2000), "J^{(100)}=" + lrs(j200), "P_1^{(200)}=" + lrs(1500), "J^{(200)}=" + lrs(j100)],
       "O prazo maior reduz os juros."),
   alt(["P_1^{(100)}=" + lrs(1000), "J^{(100)}=" + lrs(50000), "P_1^{(200)}=" + lrs(500), "J^{(200)}=" + lrs(100000)],
       "Dobrar o prazo dobra exatamente os juros.")],
  "$$P_1^{(100)}=1{.}000+1{.}000=2{.}000\\qquad P_1^{(200)}=500+1{.}000=1{.}500$$ $$J^{(100)}=\\frac{0{,}01\\cdot100{.}000\\cdot101}{2}=50{.}500\\qquad J^{(200)}=\\frac{0{,}01\\cdot100{.}000\\cdot201}{2}=100{.}500.$$",
  ("Efeito do prazo no SAC", "O prazo reduz só a amortização; os juros iniciais continuam $i\\cdot SD$ e a soma da PA cresce com $n+1$.",
   "$$P_1=\\frac{SD}{n}+i\\cdot SD\\qquad J_{total}=\\frac{i\\cdot SD\\cdot(n+1)}{2}$$",
   "Parcela menor não significa menor custo total."),
  fonte=FONTE_DISSERTACAO)

a, j, p, s = sac(12000, 12, "0.02")
soma_saldos = sum([D(12000)] + s[:-1])
q(N, "Notebook",
  "Em um SAC de R\\$ 12.000,00 em 12 meses a 2% ao mês, os saldos antes de cada pagamento são 12.000; 11.000; …; 1.000. Qual é a soma desses saldos e o total de juros?",
  alt(["\\sum SD_{k-1}=" + lrs(soma_saldos), "J_{total}=" + lrs(sum(j))], "Juros = taxa × soma dos saldos."),
  [alt(["\\sum SD_{k-1}=" + lrs(72000), "J_{total}=" + lrs(1440)], "Juros = taxa × soma dos saldos."),
   alt(["\\sum SD_{k-1}=" + lrs(78000), "J_{total}=" + lrs(2880)], "Juros = taxa × soma dos saldos, contada duas vezes."),
   alt(["\\sum SD_{k-1}=" + lrs(66000), "J_{total}=" + lrs(1320)], "Juros = taxa × soma dos saldos após os pagamentos."),
   alt(["\\sum SD_{k-1}=" + lrs(144000), "J_{total}=" + lrs(2880)], "Juros = taxa × 12 vezes o saldo inicial.")],
  T("Os saldos formam uma PA de 12 termos: $$\\sum SD_{k-1}=\\frac{(12{.}000+1{.}000)\\cdot12}{2}=<<s>>.$$ Como cada juro é $i\\cdot SD_{k-1}$: $$J_{total}=i\\cdot\\sum SD_{k-1}=0{,}02\\cdot<<s>>=<<j>>.$$", s=lx(soma_saldos), j=lx(sum(j))),
  ("Juros como taxa × soma dos saldos", "Colocar $i$ em evidência transforma o total de juros em uma soma de PA.",
   "$$J_{total}=i\\cdot\\sum_{k=1}^{n}SD_{k-1}=i\\cdot A\\cdot\\frac{n(n+1)}{2}$$",
   "Marcos: $0{,}01\\cdot2.000\\cdot\\frac{12\\cdot13}{2}=1.560$."),
  pa=pa_visual("SALDOS ANTES DE CADA PAGAMENTO", [D(12000)] + s[:-1], -1000))

a, j, p, s = sac(60000, 30, "0.01")
rest_sem = D("0.01") * 2000 * (20 * 21 / D(2))
rest_com = D("0.01") * 2000 * (15 * 16 / D(2))
q(N, "Reforma",
  "Uma reforma de R\\$ 60.000,00 pelo SAC tem 30 prestações a 1% ao mês. Após 10 pagamentos, a família faz uma amortização extra de R\\$ 10.000,00, mantendo $A=\\text{R\\$ }2.000{,}00$. Quantas prestações restam e quanto se economiza de juros?",
  alt(["m_{antes}=20", "m_{depois}=15", "\\text{economia}=" + lrs(rest_sem - rest_com)],
      "Menos termos na PA dos juros."),
  [alt(["m_{antes}=20", "m_{depois}=15", "\\text{economia}=" + lrs(10000)],
       "A economia é o próprio valor antecipado."),
   alt(["m_{antes}=20", "m_{depois}=20", "\\text{economia}=" + lrs(0)],
       "Antecipar não muda o contrato."),
   alt(["m_{antes}=20", "m_{depois}=16", "\\text{economia}=" + lrs(1500)],
       "Menos termos na PA dos juros."),
   alt(["m_{antes}=20", "m_{depois}=5", "\\text{economia}=" + lrs(rest_sem)],
       "Todos os juros restantes são eliminados.")],
  T("$$SD_{10}=2{.}000\\cdot20=40{.}000\\;\\to\\;40{.}000-10{.}000=30{.}000\\;\\Rightarrow\\;\\frac{30{.}000}{2{.}000}=15.$$ Juros restantes (PA): sem o extra $0{,}01\\cdot2{.}000\\cdot\\frac{20\\cdot21}{2}=<<a>>$; com o extra $0{,}01\\cdot2{.}000\\cdot\\frac{15\\cdot16}{2}=<<b>>$. Economia: $<<e>>$.",
    a=lx(rest_sem), b=lx(rest_com), e=lx(rest_sem - rest_com)),
  ("Amortização extraordinária", "Reduzir o saldo mantendo $A$ diminui o número de termos da PA de juros.",
   "$$J_{rest}=i\\cdot A\\cdot\\frac{m(m+1)}{2}\\quad(m=\\text{parcelas restantes})$$",
   "Com $A=1.000$ e $i=1\\%$: 10 parcelas restantes geram R\\$ 550,00 de juros."))

a, j, p, s = sac(160000, 40, "0.005")
q(N, "Casa própria",
  "Em um SAC a 0,5% ao mês, a 5ª prestação é R\\$ 4.720,00 e a 20ª é R\\$ 4.420,00. Determine o saldo financiado e o número de prestações.",
  alt(["SD=" + lrs(160000), "n=40"]),
  [alt(["SD=" + lrs(150000), "n=40"]), alt(["SD=" + lrs(160000), "n=36"]),
   alt(["SD=" + lrs(80000), "n=20"]), alt(["SD=" + lrs(189000), "n=45"])],
  "Razão: $$r=\\frac{P_{20}-P_5}{20-5}=\\frac{4{.}420-4{.}720}{15}=-20.$$ Como $r=-iA$: $A=\\frac{20}{0{,}005}=4{.}000$. Voltando 4 termos: $P_1=4{.}720+4\\cdot20=4{.}800$, logo $J_1=800$ e $$SD=\\frac{J_1}{i}=\\frac{800}{0{,}005}=160{.}000\\qquad n=\\frac{160{.}000}{4{.}000}=40.$$",
  ("Razão a partir de dois termos", "Entre os termos $p$ e $q$ há $(q-p)$ razões.",
   "$$r=\\frac{a_q-a_p}{q-p}$$", "$a_3=50$ e $a_8=35$: $r=\\frac{35-50}{5}=-3$."),
  pa=pa_visual("PRESTAÇÕES", p, -20))

# ---------------------------------------------------------------- saída
for nivel, total in contagem.items():
    if total != 15:
        raise SystemExit(f"{nivel}: {total} questões (esperado 15)")

dados = {
    "versao": 1,
    "atualizado_em": "2026-09-29",
    "observacao": (
        "Questões autorais do Sistema de Amortização Constante (SAC) com foco em "
        "Progressão Aritmética. Base: Rodrigues (2013), dissertação PROFMAT/UTFPR. "
        "Gerado por ferramentas/gerar_questoes_sac.py."
    ),
    "questoes": questoes,
}
DESTINO.write_text(json.dumps(dados, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
print(f"{len(questoes)} questões gravadas em {DESTINO}")
