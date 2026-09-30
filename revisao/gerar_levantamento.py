"""Gera revisao/levantamento_contexto_e_modelo.html (proposta para aprovação).

Lista (1) as questões sem contexto ou com contexto só decorativo, com a
reescrita proposta ao lado, e (2) todos os lugares em que o aluno vê a palavra
"fórmula", com a troca proposta por "modelo matemático".
Nada é alterado no jogo: é só o documento de revisão.
"""

from __future__ import annotations

import html
import json
import re
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
DESTINO = Path(__file__).resolve().parent / "levantamento_contexto_e_modelo.html"

# id: (tipo, enunciado proposto, observação sobre as alternativas)
#   tipo: "sem" = sem contexto; "decorativo" = produto citado só como enfeite;
#         "modelo" = já tem contexto, só troca "fórmula" por "modelo matemático".
PROPOSTAS: dict[str, tuple[str, str, str]] = {
    # ------------------------------------------------ PRICE — Super fácil
    "PRI001": ("decorativo", "Lucas financiou um notebook pelo Sistema PRICE e recebeu o carnê com as 12 parcelas. Ao comparar os valores do carnê, o que ele observa?", "Alternativas mantidas."),
    "PRI002": ("sem", "No contrato do notebook de Lucas, a parcela mensal de R$ 643,01 aparece indicada como PMT. No modelo matemático do Sistema PRICE, o que PMT representa?", "Alternativas mantidas."),
    "PRI003": ("sem", "Júlia financiou um carro pelo Sistema PRICE e acompanha o extrato: a parcela é sempre a mesma. O que acontece com a parte de juros de cada parcela ao longo dos meses?", "Alternativas mantidas."),
    "PRI004": ("sem", "No extrato do financiamento da geladeira de Ana (Sistema PRICE), o que acontece, mês a mês, com a parte da parcela que reduz a dívida (a amortização)?", "Alternativas mantidas."),
    "PRI005": ("sem", "Pedro paga R$ 500,00 por mês pela lavadora, financiada pelo Sistema PRICE. Esse valor mensal é formado por quais duas partes?", "Alternativas mantidas."),
    "PRI006": ("sem", "Para saber quanto valem hoje as parcelas de sua TV, Carla calculou PMT/(1+i), PMT/(1+i)², PMT/(1+i)³, … Que tipo de sequência ela obteve?", "Alternativas mantidas."),
    "PRI007": ("sem", "Carla quer trazer para a data da compra o valor da 1ª parcela da bicicleta, que vence em um mês. Qual é o primeiro termo da sequência dos valores presentes?", "Alternativas mantidas."),
    "PRI008": ("sem", "Cada parcela da bicicleta de Carla vence um mês depois da anterior. Por qual número se multiplica um valor presente para obter o seguinte (a razão da PG)?", "Alternativas mantidas."),
    "PRI009": ("sem", "Bruno financiou um console. No dia da compra, a soma dos valores presentes de todas as parcelas deve ser igual a quê?", "Alternativas mantidas."),
    "PRI010": ("sem", "A primeira parcela da câmera de Júlia, de valor PMT, vence daqui a um mês. Com taxa i ao mês, quanto essa parcela vale hoje?", "Alternativas mantidas."),
    "PRI011": ("sem", "Antes de assinar o contrato, Pedro quer calcular a parcela fixa do ar-condicionado financiado pelo Sistema PRICE. Qual modelo matemático ele deve usar?", "Alternativas mantidas."),
    "PRI012": ("sem", "Lucas vai comprar um violão em 12 parcelas mensais iguais. No modelo matemático do Sistema PRICE, qual valor ele deve usar para n?", "NOVAS alternativas numéricas (sua sugestão): 12 (correta); 1; 0,02; 2; 24."),
    "PRI013": ("sem", "No contrato do patinete de Ana aparece “i = 2% ao mês”. No modelo matemático do Sistema PRICE, o que o i representa?", "Alternativas mantidas."),
    "PRI014": ("sem", "Bruno pagou em dia a última parcela do robô aspirador. Qual deve ser, agora, o saldo devedor?", "Alternativas mantidas."),
    "PRI015": ("sem", "Neste mês, o saldo devedor do micro-ondas de Carla é R$ 1.000,00 e a taxa é 1% ao mês. Como se calculam os juros desse mês?", "Alternativas mantidas."),
    # ------------------------------------------------ PRICE — Fácil
    "PRI016": ("modelo", "Lucas vai financiar um notebook a 2% ao mês. Qual valor decimal ele deve usar para i no modelo matemático do Sistema PRICE?", "Alternativas mantidas."),
    "PRI017": ("decorativo", "Ana financiou um smartphone a 1% ao mês e quer trazer as parcelas para a data da compra. Qual é a razão q entre um valor presente e o anterior?", "Alternativas mantidas."),
    "PRI025": ("decorativo", "Júlia quer financiar uma câmera de R$ 9.800,00 em 18 parcelas a 1,4% ao mês e saber o valor da parcela antes de ir à loja. Qual modelo matemático ela deve usar?", "Alternativas mantidas."),
    "PRI026": ("decorativo", "Pedro vai financiar um ar-condicionado a 1,8% ao mês. Para comparar as parcelas com o preço à vista, ele as traz para a data da compra. Qual é a razão da PG desses valores?", "Alternativas mantidas."),
    "PRI027": ("decorativo", "Lucas vai pagar o violão em 5 parcelas e trazer cada uma para a data da compra, para comparar com o preço à vista. Quantos valores presentes ele terá de somar?", "Mesmas alternativas, trocando “termos” por “valores” (5 valores = correta)."),
    "PRI028": ("decorativo", "Ana vai somar os 8 valores presentes das parcelas do patinete, que formam uma PG de primeiro termo a₁ e razão q. Qual modelo matemático dá essa soma?", "Alternativas mantidas."),
    "PRI029": ("decorativo", "Bruno recebeu duas propostas para o robô aspirador, com o mesmo valor financiado e o mesmo prazo: uma a 1,5% e outra a 2,5% ao mês. Qual terá a maior parcela?", "Alternativas ajustadas aos números: “A de 2,5% ao mês” (correta), “A de 1,5% ao mês”, “As duas iguais”…"),
    "PRI030": ("decorativo", "A loja ofereceu a Carla pagar o micro-ondas em 6 ou em 12 parcelas pelo Sistema PRICE, com a mesma taxa. Ao escolher 12 parcelas, o que geralmente acontece?", "Alternativas mantidas."),
    # ------------------------------------------------ SAC — Super fácil
    "SAC001": ("decorativo", "Madalena financiou sua casa pelo SAC. Ao olhar o extrato, qual parte de cada parcela ela percebe que é sempre igual?", "Alternativas mantidas."),
    "SAC002": ("sem", "O gerente do banco ofereceu a Madalena o “SAC” para financiar a casa. O que significa essa sigla?", "Alternativas mantidas."),
    "SAC003": ("sem", "Marcos financiou um carro pelo SAC. Ao receber o carnê, como ele vê os valores das parcelas mês a mês?", "Alternativas mantidas."),
    "SAC004": ("sem", "Marcos financiou R$ 24.000,00 pelo SAC em 12 parcelas. Qual modelo matemático dá a parte da dívida que ele devolve em cada parcela (a amortização)?", "Alternativas mantidas."),
    "SAC005": ("sem", "No extrato do SAC de Marcos, os juros foram R$ 240, R$ 220, R$ 200, … Que tipo de sequência eles formam?", "Alternativas mantidas."),
    "SAC006": ("sem", "Ana acompanha o saldo devedor do terreno financiado pelo SAC e percebe que ele cai sempre o mesmo valor por mês. Que valor é esse?", "Alternativas mantidas."),
    "SAC007": ("sem", "As parcelas de Ana diminuem sempre R$ 15,00 por mês. Na PA formada pelas parcelas, como se chama esse valor constante?", "Alternativas mantidas."),
    "SAC008": ("sem", "As parcelas do SAC de Marcos começam em R$ 2.240,00 e caem R$ 20,00 por mês. Qual modelo matemático permite calcular a parcela de qualquer mês n?", "Alternativas mantidas."),
    "SAC009": ("sem", "Pedro vai financiar um ar-condicionado pelo SAC e quer se preparar para o mês mais pesado. Qual parcela terá o maior valor?", "Alternativas mantidas."),
    "SAC010": ("sem", "Carla anotou as parcelas da bicicleta: R$ 850, R$ 840, R$ 830, … A PA formada é decrescente porque sua razão é:", "Alternativas mantidas."),
    "SAC011": ("sem", "Bruno anotou a amortização de cada mês do console financiado pelo SAC: R$ 800, R$ 800, R$ 800, … Qual é a razão dessa PA?", "Alternativas mantidas."),
    "SAC012": ("sem", "No 5º mês do financiamento da câmera de Júlia pelo SAC, sobre qual valor são calculados os juros?", "Alternativas mantidas."),
    "SAC013": ("sem", "Lucas percebeu que as parcelas do smartphone, financiado pelo SAC, ficam menores a cada mês. Por que isso acontece?", "Alternativas mantidas."),
    "SAC014": ("sem", "Ao pesquisar financiamentos, Madalena viu que o SAC aparece com muita frequência em um tipo de crédito no Brasil. Qual?", "Alternativas mantidas."),
    "SAC015": ("sem", "Madalena pagou a última parcela da casa financiada pelo SAC. Qual é, agora, o saldo devedor?", "Alternativas mantidas."),
    # ------------------------------------------------ SAC — Fácil e Difícil
    "SAC026": ("decorativo", "Ana financiou a geladeira em 36 parcelas pelo SAC e anotou todas numa tabela, da 1ª à última. Quantos termos tem a PA das parcelas?", "Alternativas mantidas."),
    "SAC029": ("decorativo", "Três amigos anotaram as primeiras parcelas de seus financiamentos. Qual das sequências pode ser a de quem escolheu o SAC?", "Alternativas mantidas."),
    "SAC050": ("sem", "Bruno, microempreendedor, tomou crédito pelo SAC e quer entender de onde vêm os juros de cada mês, Jₖ = i·A·(n − k + 1). Qual raciocínio, a partir da PA dos juros, justifica esse modelo matemático?", "Alternativas mantidas."),
}

# Campos de estudo com a palavra "fórmula" (id, campo, proposta).
ESTUDO: list[tuple[str, str, str]] = [
    ("JUR005", "estudo.texto", "Quando a taxa está ao ano, mantenha o tempo em anos antes de montar o modelo matemático."),
    ("PRI011", "estudo.titulo", "Modelo matemático da prestação PRICE"),
    ("PRI011", "estudo.texto", "O modelo matemático relaciona o saldo financiado, a taxa por período e o número de prestações."),
    ("PRI011", "estudo.exemplo", "Antes de usar o modelo, escreva a taxa na forma decimal."),
    ("PRI016", "estudo.texto", "O modelo matemático do Sistema PRICE utiliza a taxa escrita na forma decimal."),
    ("PRI025", "estudo.texto", "O modelo considera simultaneamente saldo, taxa e prazo."),
    ("PRI028", "estudo.texto", "Substitua o número de termos no expoente do modelo da soma da PG."),
    ("SAC039", "estudo.titulo", "Modelo da dissertação (Rodrigues, 2013)"),
]

# Textos da interface (código) que o aluno vê ou ouve.
INTERFACE: list[tuple[str, str, str]] = [
    ("Todos os módulos — passo 2 do estudo", "ORGANIZE A FÓRMULA", "MONTE O MODELO MATEMÁTICO"),
    ("PRICE e SAC — título do estudo", "ESTRATÉGIA E FÓRMULA", "ESTRATÉGIA E MODELO MATEMÁTICO"),
    ("PRICE e SAC — estudo, página 1", "Leia o conceito e observe a fórmula antes de avançar.", "Leia o conceito e observe o modelo matemático antes de avançar."),
    ("Todos os módulos — narração do estudo", "“Fórmula. …” / “Segundo, organize a fórmula.”", "“Modelo matemático. …” / “Segundo, monte o modelo matemático.”"),
    ("PRICE — descrição do nível Médio", "Cálculo da prestação fixa com a fórmula do Sistema PRICE.", "Cálculo da prestação fixa com o modelo matemático do Sistema PRICE."),
    ("PRICE — teoria, parte 1 (narração)", "A fórmula da prestação é PMT igual ao…", "O modelo matemático da prestação é PMT igual ao…"),
    ("PRICE — teoria, parte 2 (título do exemplo)", "Como a fórmula nasce da soma da PG", "Como o modelo matemático nasce da soma da PG"),
    ("PRICE — teoria, parte 2 (passo 3)", "…obtém-se a fórmula da prestação PRICE.", "…obtém-se o modelo matemático da prestação PRICE."),
    ("PRICE — teoria, parte 2 (aplicação)", "…permite justificar a fórmula, em vez de apenas memorizá-la…", "…permite justificar o modelo, em vez de apenas memorizá-lo…"),
    ("PRICE — teoria, parte 2 (narração)", "Isolando PMT, obtemos a fórmula da prestação fixa.", "Isolando PMT, obtemos o modelo matemático da prestação fixa."),
    ("SAC — teoria, parte 3", "A fórmula vem do termo geral…", "O modelo vem do termo geral…"),
    ("SAC — teoria, parte 5", "…chega-se a uma fórmula direta.", "…chega-se a um modelo matemático direto."),
    ("Juros — teoria, partes 1 e 2 (narração)", "A fórmula é J igual a C vezes i vezes t… / A fórmula é M igual a…", "O modelo matemático é J igual a C vezes i vezes t… / O modelo é M igual a…"),
    ("Juros — teoria, parte 3 (subtítulo)", "Identifique o regime antes de escolher a fórmula", "Identifique o regime antes de escolher o modelo matemático"),
    ("Juros — revisão (texto e narração)", "…conceitos, fórmulas e aplicações…", "…conceitos, modelos matemáticos e aplicações…"),
    ("Modo economia — ajuda", "Dica: fórmula e estratégia", "Dica: modelo matemático e estratégia"),
]


def sem_latex(texto: str) -> str:
    """Versão legível do enunciado original (sem comandos LaTeX)."""
    t = texto.replace("R\\$", "R$")
    t = re.sub(r"\\frac\{([^{}]*)\}\{([^{}]*)\}", r"(\1)/(\2)", t)
    t = t.replace("\\cdot", "·").replace("\\ldots", "…").replace("\\cdots", "⋯")
    t = t.replace("{,}", ",").replace("{.}", ".").replace("$", "").replace("**", "")
    t = re.sub(r"\\text\{([^{}]*)\}", r"\1", t)
    return t.replace("\\", "")


def main() -> None:
    questoes: dict[str, dict] = {}
    for nome in ("porcentagem", "juros", "price", "sac"):
        for q in json.loads((BASE / "dados" / f"questoes_{nome}.json").read_text(encoding="utf-8"))["questoes"]:
            questoes[q["id"]] = q

    rotulo = {"sem": "Sem contexto", "decorativo": "Contexto só decorativo", "modelo": "Troca “fórmula”"}
    linhas = []
    for ident, (tipo, proposta, obs) in PROPOSTAS.items():
        q = questoes[ident]
        correta = sem_latex(q["alternativas"][q["correta"]])
        linhas.append(
            f"<tr><td class='id'>{ident}<br><span class='nivel'>{html.escape(q.get('nivel', ''))}</span></td>"
            f"<td><span class='tag {tipo}'>{rotulo[tipo]}</span><p>{html.escape(sem_latex(q['enunciado']))}</p>"
            f"<p class='resp'>Resposta: {html.escape(correta)}</p></td>"
            f"<td><p class='novo'>{html.escape(proposta)}</p><p class='obs'>{html.escape(obs)}</p></td></tr>"
        )
    estudo = "".join(
        f"<tr><td class='id'>{i}</td><td>{html.escape(c)}</td><td><p>{html.escape(sem_latex(_campo(questoes[i], c)))}</p></td>"
        f"<td><p class='novo'>{html.escape(n)}</p></td></tr>"
        for i, c, n in ESTUDO
    )
    interface = "".join(
        f"<tr><td>{html.escape(o)}</td><td><p>{html.escape(a)}</p></td><td><p class='novo'>{html.escape(n)}</p></td></tr>"
        for o, a, n in INTERFACE
    )
    cont = {t: sum(1 for v in PROPOSTAS.values() if v[0] == t) for t in rotulo}
    DESTINO.write_text(MODELO.format(
        linhas="".join(linhas), estudo=estudo, interface=interface,
        sem=cont["sem"], deco=cont["decorativo"], modelo=cont["modelo"],
        total=len(PROPOSTAS), n_estudo=len(ESTUDO), n_interface=len(INTERFACE),
    ), encoding="utf-8")
    print(f"{DESTINO} gerado: {len(PROPOSTAS)} questões, {len(ESTUDO)} campos de estudo, {len(INTERFACE)} textos da interface")


def _campo(q: dict, caminho: str) -> str:
    grupo, _, chave = caminho.partition(".")
    return str(q[grupo][chave]) if chave else str(q[grupo])


MODELO = """<!doctype html>
<html lang="pt-BR"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Levantamento de contexto</title>
<style>
:root {{ --fundo:#f6f8fb; --cartao:#ffffff; --texto:#1b2433; --suave:#5a6678; --linha:#dfe5ee;
  --sem:#b42318; --sem-f:#fde8e7; --deco:#9a5b00; --deco-f:#fff3dd; --mod:#1f5fbf; --mod-f:#e6f0ff; --novo:#0f6b45; }}
@media (prefers-color-scheme: dark) {{ :root:not([data-theme="light"]) {{
  --fundo:#0f1623; --cartao:#172133; --texto:#e8edf5; --suave:#9fb0c7; --linha:#2a3850;
  --sem:#ff8a80; --sem-f:#3a1d1f; --deco:#ffc266; --deco-f:#3a2c14; --mod:#8ab4ff; --mod-f:#18284a; --novo:#6fdca8; }} }}
:root[data-theme="dark"] {{ --fundo:#0f1623; --cartao:#172133; --texto:#e8edf5; --suave:#9fb0c7; --linha:#2a3850;
  --sem:#ff8a80; --sem-f:#3a1d1f; --deco:#ffc266; --deco-f:#3a2c14; --mod:#8ab4ff; --mod-f:#18284a; --novo:#6fdca8; }}
body {{ margin:0; background:var(--fundo); color:var(--texto); font:16px/1.5 system-ui, "Segoe UI", sans-serif; }}
main {{ max-width:1180px; margin:0 auto; padding:24px 16px 60px; }}
h1 {{ font-size:1.7rem; margin:0 0 4px; }} h2 {{ margin-top:36px; font-size:1.25rem; }}
.sub {{ color:var(--suave); margin:0 0 20px; }}
.resumo {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(170px,1fr)); gap:10px; }}
.resumo div {{ background:var(--cartao); border:1px solid var(--linha); border-radius:12px; padding:12px; }}
.resumo b {{ display:block; font-size:1.6rem; }}
.tabela {{ overflow-x:auto; }}
table {{ width:100%; border-collapse:collapse; background:var(--cartao); border:1px solid var(--linha); border-radius:12px; overflow:hidden; }}
th, td {{ text-align:left; vertical-align:top; padding:10px 12px; border-bottom:1px solid var(--linha); }}
th {{ font-size:.8rem; text-transform:uppercase; letter-spacing:.04em; color:var(--suave); }}
td p {{ margin:4px 0; }} .id {{ font-weight:700; white-space:nowrap; }} .nivel {{ font-weight:400; color:var(--suave); font-size:.85rem; }}
.resp {{ color:var(--suave); font-size:.9rem; }} .novo {{ color:var(--novo); font-weight:600; }} .obs {{ color:var(--suave); font-size:.88rem; }}
.tag {{ display:inline-block; font-size:.75rem; font-weight:700; padding:2px 8px; border-radius:999px; }}
.tag.sem {{ color:var(--sem); background:var(--sem-f); }} .tag.decorativo {{ color:var(--deco); background:var(--deco-f); }}
.tag.modelo {{ color:var(--mod); background:var(--mod-f); }}
.nota {{ background:var(--cartao); border-left:4px solid var(--mod); padding:10px 14px; border-radius:8px; }}
@media (max-width:700px) {{ th, td {{ padding:8px; font-size:.92rem; }} }}
</style></head><body><main>
<h1>Levantamento: contexto das questões e a palavra “fórmula”</h1>
<p class="sub">Responda ou Estuda — proposta para aprovação. Nada foi alterado no jogo ainda.</p>

<div class="resumo">
  <div><b>{total}</b>questões a reescrever</div>
  <div><b>{sem}</b>sem contexto</div>
  <div><b>{deco}</b>contexto só decorativo</div>
  <div><b>{modelo}</b>já contextualizada: só troca “fórmula”</div>
  <div><b>{n_estudo}</b>campos de estudo com “fórmula”</div>
  <div><b>{n_interface}</b>textos da interface com “fórmula”</div>
</div>

<p class="nota"><b>Porcentagem e Juros:</b> as 40 questões já partem de uma situação real (produto, empréstimo ou aplicação) e não precisam de reescrita; em Juros só um texto de estudo usa “fórmula”.
<br><b>Critério das reescritas:</b> situação real com personagem → dado concreto → interpretação ou decisão. O conceito cobrado, a dificuldade e a resposta correta ficam os mesmos (exceto onde indicado). Personagens: Marcos e Madalena (dissertação), Lucas, Ana, Júlia, Pedro, Carla e Bruno.
<br><b>Pesquisa:</b> sugiro dar novo ID às questões reescritas (ex.: PRI002 → PRI002b) para os relatórios não misturarem versões.</p>

<h2>1. Questões: original × proposta</h2>
<div class="tabela"><table><thead><tr><th>ID</th><th>Original</th><th>Proposta</th></tr></thead>
<tbody>{linhas}</tbody></table></div>

<h2>2. Estudo das questões: “fórmula” → “modelo matemático”</h2>
<div class="tabela"><table><thead><tr><th>ID</th><th>Campo</th><th>Original</th><th>Proposta</th></tr></thead>
<tbody>{estudo}</tbody></table></div>

<h2>3. Textos da interface e da narração</h2>
<div class="tabela"><table><thead><tr><th>Onde aparece</th><th>Hoje</th><th>Proposta</th></tr></thead>
<tbody>{interface}</tbody></table></div>
</main></body></html>
"""

if __name__ == "__main__":
    main()
