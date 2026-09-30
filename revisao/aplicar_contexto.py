"""Aplica a revisão de contexto e a troca "fórmula" -> "modelo matemático".

Aprovada pelo professor em 29/09/2026 (ver levantamento_contexto_e_modelo.html).
PRICE: edita dados/questoes_price.json. SAC: os textos vão para
ferramentas/gerar_questoes_sac.py (ENUNCIADOS_REVISADOS), que regenera o banco.
Pode ser executado mais de uma vez (cada troca confere o texto original).
"""

from __future__ import annotations

import json
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]

# ------------------------------------------------------------------ PRICE
PRICE_ENUNCIADOS = {
    "PRI001": "Lucas financiou um notebook pelo Sistema PRICE e recebeu o carnê com as 12 parcelas. Ao comparar os valores do carnê, o que ele observa?",
    "PRI002": "No contrato do smartphone de Lucas, a parcela mensal de R\\$ 409,21 aparece indicada como $PMT$. No modelo matemático do Sistema PRICE, o que $PMT$ representa?",
    "PRI003": "Júlia financiou um carro pelo Sistema PRICE e acompanha o extrato: a parcela é sempre a mesma. O que acontece com a parte de juros de cada parcela ao longo dos meses?",
    "PRI004": "No extrato do financiamento da geladeira de Ana (Sistema PRICE), o que acontece, mês a mês, com a parte da parcela que reduz a dívida (a amortização)?",
    "PRI005": "Pedro paga R\\$ 500,00 por mês pela lavadora, financiada pelo Sistema PRICE. Esse valor mensal é formado por quais duas partes?",
    "PRI006": "Para saber quanto valem hoje as parcelas de sua TV, Carla calculou $\\frac{PMT}{1+i},\\frac{PMT}{(1+i)^2},\\frac{PMT}{(1+i)^3},\\ldots$ Que tipo de sequência ela obteve?",
    "PRI007": "Carla quer trazer para a data da compra o valor da 1ª parcela da bicicleta, que vence em um mês. Qual é o primeiro termo da sequência dos valores presentes?",
    "PRI008": "Cada parcela da moto de Carla vence um mês depois da anterior. Por qual número se multiplica um valor presente para obter o seguinte (a razão da PG)?",
    "PRI009": "Bruno financiou um console. No dia da compra, a soma dos valores presentes de todas as parcelas deve ser igual a quê?",
    "PRI010": "A primeira parcela da câmera de Júlia, de valor $PMT$, vence daqui a um mês. Com taxa $i$ ao mês, quanto essa parcela vale hoje?",
    "PRI011": "Antes de assinar o contrato, Pedro quer calcular a parcela fixa do ar-condicionado financiado pelo Sistema PRICE. Qual modelo matemático ele deve usar?",
    "PRI012": "Lucas vai comprar um violão em 12 parcelas mensais iguais. No modelo matemático do Sistema PRICE, qual valor ele deve usar para $n$?",
    "PRI013": "No contrato do patinete de Ana aparece “$i=2\\%$ ao mês”. No modelo matemático do Sistema PRICE, o que o $i$ representa?",
    "PRI014": "Bruno pagou em dia a última parcela do robô aspirador. Qual deve ser, agora, o saldo devedor?",
    "PRI015": "Neste mês, o saldo devedor do micro-ondas de Carla é R\\$ 1.000,00 e a taxa é $1\\%$ ao mês. Como se calculam os juros desse mês?",
    "PRI016": "Lucas vai financiar um notebook a $2\\%$ ao mês. Qual valor decimal ele deve usar para $i$ no modelo matemático do Sistema PRICE?",
    "PRI017": "Ana financiou um smartphone a $1\\%$ ao mês e quer trazer as parcelas para a data da compra. Qual é a razão $q$ entre um valor presente e o anterior?",
    "PRI025": "Júlia quer financiar uma câmera de R\\$ 9.800,00 em 18 parcelas a $1{,}4\\%$ ao mês e saber o valor da parcela antes de ir à loja. Qual modelo matemático ela deve usar?",
    "PRI026": "Pedro vai financiar um ar-condicionado a $1{,}8\\%$ ao mês. Para comparar as parcelas com o preço à vista, ele as traz para a data da compra. Qual é a razão da PG desses valores?",
    "PRI027": "Lucas vai pagar o violão em 5 parcelas e trazer cada uma para a data da compra, para comparar com o preço à vista. Quantos valores presentes ele terá de somar?",
    "PRI028": "Ana vai somar os 8 valores presentes das parcelas do patinete, que formam uma PG de primeiro termo $a_1$ e razão $q$. Qual modelo matemático dá essa soma?",
    "PRI029": "Bruno recebeu duas propostas para o robô aspirador, com o mesmo valor financiado e o mesmo prazo: uma a $1{,}5\\%$ e outra a $2{,}5\\%$ ao mês. Qual terá a maior parcela?",
    "PRI030": "A loja ofereceu a Carla pagar o micro-ondas em 6 ou em 12 parcelas pelo Sistema PRICE, com a mesma taxa. Ao escolher 12 parcelas, o que geralmente acontece?",
}
PRICE_ALTERNATIVAS = {
    # índice da correta preservado (A, A e E, respectivamente)
    "PRI012": ["12", "1", "0,02", "2", "24"],
    "PRI027": ["5 valores", "4 valores", "6 valores", "1 valor", "10 valores"],
    "PRI029": ["A de 1,5% ao mês.", "As duas têm parcela zero.", "As duas têm a mesma parcela.",
               "Não é possível comparar.", "A de 2,5% ao mês."],
}
PRICE_EXPLICACOES = {
    "PRI012": "$n$ é o número de prestações do financiamento. Lucas pagará 12 parcelas, então $$n=12.$$",
    "PRI027": "Cada parcela gera um valor presente. Portanto, 5 parcelas formam uma PG com 5 termos: Lucas somará 5 valores.",
    "PRI029": "Com o mesmo saldo e o mesmo prazo, a taxa maior aumenta o custo financeiro. Por isso a proposta de $2{,}5\\%$ ao mês tem a maior parcela.",
}
PRICE_ESTUDO = {
    ("PRI011", "titulo"): ("Fórmula da prestação PRICE", "Modelo matemático da prestação PRICE"),
    ("PRI011", "texto"): ("A fórmula relaciona", "O modelo matemático relaciona"),
    ("PRI011", "exemplo"): ("Antes de usar a fórmula", "Antes de usar o modelo"),
    ("PRI016", "texto"): ("A fórmula PRICE utiliza", "O modelo matemático do Sistema PRICE utiliza"),
    ("PRI025", "texto"): ("A fórmula considera", "O modelo considera"),
    ("PRI028", "texto"): ("no expoente da fórmula da soma", "no expoente do modelo da soma da PG"),
}

# ------------------------------------------------------------------ SAC
SAC_ENUNCIADOS = {
    "SAC001": "Madalena financiou sua casa pelo SAC. Ao olhar o extrato, qual parte de cada parcela ela percebe que é sempre igual?",
    "SAC002": "O gerente do banco ofereceu a Madalena o “SAC” para financiar o apartamento. O que significa essa sigla?",
    "SAC003": "Pedro financiou um carro pelo SAC. Ao receber o carnê, como ele vê os valores das parcelas mês a mês?",
    "SAC004": "Lucas financiou um notebook de R\\$ 6.000,00 pelo SAC em 10 parcelas. Qual modelo matemático dá a parte da dívida que ele devolve em cada parcela (a amortização $A$)?",
    "SAC005": "Ana financiou uma geladeira pelo SAC. No extrato, os juros foram R\\$ 36,00; R\\$ 33,00; R\\$ 30,00; … Que tipo de sequência eles formam?",
    "SAC006": "Ana acompanha o saldo devedor do terreno financiado pelo SAC e percebe que ele cai sempre o mesmo valor por mês. Que valor é esse?",
    "SAC007": "As parcelas da TV de Ana, financiada pelo SAC, diminuem sempre R\\$ 15,00 por mês. Na PA formada pelas parcelas, como se chama esse valor constante?",
    "SAC008": "As parcelas da lavadora de Carla, financiada pelo SAC, começam em R\\$ 330,00 e caem R\\$ 3,00 por mês. Qual modelo matemático permite calcular a parcela de qualquer mês $n$?",
    "SAC009": "Pedro vai financiar um ar-condicionado pelo SAC e quer se preparar para o mês mais pesado. Qual parcela terá o maior valor?",
    "SAC010": "Carla anotou as parcelas da bicicleta, financiada pelo SAC: R\\$ 850,00; R\\$ 840,00; R\\$ 830,00; … A PA formada é decrescente porque sua razão $r$ é:",
    "SAC011": "Bruno anotou a amortização de cada mês do console financiado pelo SAC: R\\$ 800,00; R\\$ 800,00; R\\$ 800,00; … Qual é a razão dessa PA?",
    "SAC012": "No 5º mês do financiamento da câmera de Júlia pelo SAC, sobre qual valor são calculados os juros?",
    "SAC013": "Lucas percebeu que as parcelas do smartphone, financiado pelo SAC, ficam menores a cada mês. Por que isso acontece?",
    "SAC014": "Ao pesquisar financiamentos, Madalena viu que o SAC aparece com muita frequência em um tipo de crédito no Brasil. Qual?",
    "SAC015": "Madalena pagou a última parcela da casa financiada pelo SAC. Qual é, agora, o saldo devedor?",
    "SAC026": "Ana financiou a geladeira em 36 parcelas pelo SAC e anotou todas numa tabela, da 1ª à última. Quantos termos tem a PA das parcelas?",
    "SAC029": "Três amigos anotaram as primeiras parcelas de seus financiamentos. Qual das sequências pode ser a de quem escolheu o SAC?",
    "SAC050": "Bruno, microempreendedor, tomou crédito pelo SAC e quer entender de onde vêm os juros de cada mês, $J_k=i\\cdot A\\cdot(n-k+1)$. Qual raciocínio, a partir da PA dos juros, justifica esse modelo matemático?",
}
SAC_ESTUDO = {("SAC039", "titulo"): "Modelo da dissertação (Rodrigues, 2013)"}

JUROS_ESTUDO = {("JUR005", "texto"): ("antes de aplicar a fórmula", "antes de montar o modelo matemático")}

# ------------------------------------------------------------------ interface
INTERFACE = {
    "nivel_1_porcentagem.py": [
        ('"ORGANIZE A FÓRMULA"', '"MONTE O MODELO MATEMÁTICO"', None),
        ("f\"Fórmula. {estudo['formula']}. \"", "f\"Modelo matemático. {estudo['formula']}. \"", 1),
        ("Segundo, organize a fórmula.", "Segundo, monte o modelo matemático.", 1),
    ],
    "nivel_2_juros.py": [
        ('"ORGANIZE A FÓRMULA"', '"MONTE O MODELO MATEMÁTICO"', None),
        ("f\"Fórmula. {estudo['formula']}. \"", "f\"Modelo matemático. {estudo['formula']}. \"", 1),
        ("Segundo, organize a fórmula.", "Segundo, monte o modelo matemático.", 1),
        ("A fórmula é J igual a C vezes i vezes t.", "O modelo matemático é J igual a C vezes i vezes t.", 1),
        ("A fórmula é M igual a", "O modelo matemático é M igual a", 1),
        ("Identifique o regime antes de escolher a fórmula", "Identifique o regime antes de escolher o modelo matemático", 1),
        ("fórmulas e aplicações em empréstimos", "modelos matemáticos e aplicações em empréstimos", 1),
        ("conceitos, fórmulas e exemplos", "conceitos, modelos matemáticos e exemplos", 1),
    ],
    "nivel_3_price.py": [
        ('"ORGANIZE A FÓRMULA"', '"MONTE O MODELO MATEMÁTICO"', 1),
        ('"ESTRATÉGIA E FÓRMULA"', '"ESTRATÉGIA E MODELO MATEMÁTICO"', 1),
        ("Leia o conceito e observe a fórmula antes de avançar.", "Leia o conceito e observe o modelo matemático antes de avançar.", 1),
        ("f\"Fórmula. {estudo['formula']}. \"", "f\"Modelo matemático. {estudo['formula']}. \"", 1),
        ('"Estratégia e fórmula. "', '"Estratégia e modelo matemático. "', 1),
        ("f\"Fórmula. {estudo['formula']}.\"", "f\"Modelo matemático. {estudo['formula']}.\"", 1),
        ("com a fórmula do Sistema PRICE.", "com o modelo matemático do Sistema PRICE.", 1),
        ("A fórmula da prestação é PMT igual ao saldo", "O modelo matemático da prestação é PMT igual ao saldo", 1),
        ("Como a fórmula nasce da soma da PG", "Como o modelo matemático nasce da soma da PG", 1),
        ("obtém-se a fórmula da prestação PRICE.", "obtém-se o modelo matemático da prestação PRICE.", 1),
        ("permite justificar a fórmula, em vez de apenas ", "permite justificar o modelo, em vez de apenas ", 1),
        ('"memorizá-la, e ajuda', '"memorizá-lo, e ajuda', 1),
        ("obtemos a fórmula da prestação fixa.", "obtemos o modelo matemático da prestação fixa.", 1),
    ],
    "nivel_4_sac.py": [
        ('"ORGANIZE A FÓRMULA"', '"MONTE O MODELO MATEMÁTICO"', 1),
        ('"ESTRATÉGIA E FÓRMULA"', '"ESTRATÉGIA E MODELO MATEMÁTICO"', 1),
        ("Leia o conceito e observe a fórmula antes de avançar.", "Leia o conceito e observe o modelo matemático antes de avançar.", 1),
        ("f\"Fórmula. {estudo['formula']}. \"", "f\"Modelo matemático. {estudo['formula']}. \"", 1),
        ('"Estratégia e fórmula. "', '"Estratégia e modelo matemático. "', 1),
        ("f\"Fórmula. {estudo['formula']}.\"", "f\"Modelo matemático. {estudo['formula']}.\"", 1),
        ('"A fórmula vem do termo geral', '"O modelo vem do termo geral', 1),
        ("chega-se a uma fórmula direta.", "chega-se a um modelo matemático direto.", 1),
    ],
    "economia.py": [
        ('"Dica: fórmula e estratégia"', '"Dica: modelo matemático e estratégia"', 1),
    ],
}


def _trocar(texto: str, antigo: str, novo: str, vezes: int | None, onde: str) -> str:
    if novo in texto and antigo not in texto:
        return texto  # já aplicado
    n = texto.count(antigo)
    if n == 0 or (vezes is not None and n != vezes):
        raise SystemExit(f"{onde}: '{antigo[:60]}' encontrado {n} vez(es)")
    return texto.replace(antigo, novo)


def aplicar_banco(nome: str, enunciados: dict, alternativas: dict, explicacoes: dict, estudo: dict) -> None:
    caminho = BASE / "dados" / f"questoes_{nome}.json"
    dados = json.loads(caminho.read_text(encoding="utf-8"))
    por_id = {q["id"]: q for q in dados["questoes"]}
    for ident, texto in enunciados.items():
        por_id[ident]["enunciado"] = texto
    for ident, lista in alternativas.items():
        assert len(lista) == len(por_id[ident]["alternativas"]), ident
        por_id[ident]["alternativas"] = lista
    for ident, texto in explicacoes.items():
        por_id[ident]["explicacao"] = texto
    for (ident, campo), (antigo, novo) in estudo.items():
        por_id[ident]["estudo"][campo] = _trocar(por_id[ident]["estudo"][campo], antigo, novo, 1, ident)
    caminho.write_text(json.dumps(dados, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(f"{nome}: {len(enunciados)} enunciados, {len(estudo)} textos de estudo")


def aplicar_gerador_sac() -> None:
    caminho = BASE / "ferramentas" / "gerar_questoes_sac.py"
    t = caminho.read_text(encoding="utf-8")
    bloco = "# Revisão de contexto (29/09/2026): enunciados contextualizados e\n" \
            "# \"modelo matemático\" no lugar de \"fórmula\". Aplicados sobre o banco gerado.\n" \
            f"ENUNCIADOS_REVISADOS = {json.dumps(SAC_ENUNCIADOS, ensure_ascii=False, indent=4)}\n" \
            f"ESTUDO_REVISADO = {json.dumps({f'{i}|{c}': v for (i, c), v in SAC_ESTUDO.items()}, ensure_ascii=False, indent=4)}\n\n"
    marca = "# ---------------------------------------------------------------- saída"
    if "ENUNCIADOS_REVISADOS" in t:
        inicio = t.index("# Revisão de contexto (29/09/2026)")
        t = t[:inicio] + bloco + t[t.index(marca):]
    else:
        t = t.replace(marca, bloco + marca, 1)
        t = _trocar(t, '''dados = {
    "versao": 1,''', '''for _q in questoes:
    if _q["id"] in ENUNCIADOS_REVISADOS:
        _q["enunciado"] = ENUNCIADOS_REVISADOS[_q["id"]]
    for _chave, _valor in ESTUDO_REVISADO.items():
        _ident, _campo = _chave.split("|")
        if _q["id"] == _ident:
            _q["estudo"][_campo] = _valor

dados = {
    "versao": 1,''', 1, "gerador")
    caminho.write_text(t, encoding="utf-8", newline="\n")
    print(f"gerador SAC: {len(SAC_ENUNCIADOS)} enunciados revisados")


def aplicar_interface() -> None:
    for nome, trocas in INTERFACE.items():
        caminho = BASE / nome
        t = caminho.read_text(encoding="utf-8")
        for antigo, novo, vezes in trocas:
            t = _trocar(t, antigo, novo, vezes, nome)
        caminho.write_text(t, encoding="utf-8", newline="\n")
        print(f"{nome}: {len(trocas)} trocas")


if __name__ == "__main__":
    aplicar_banco("price", PRICE_ENUNCIADOS, PRICE_ALTERNATIVAS, PRICE_EXPLICACOES, PRICE_ESTUDO)
    aplicar_banco("juros", {}, {}, {}, JUROS_ESTUDO)
    aplicar_gerador_sac()
    aplicar_interface()
