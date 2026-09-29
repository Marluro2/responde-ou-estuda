RESPONDA OU ESTUDA - EDIÇÃO EM JANELA EXCLUSIVA
Jogo de educação financeira em Python 3.14 e Flet 0.86.3

IMPORTANTE

Esta edição abre o jogo em uma janela própria, sem abas, barra de endereço ou
menus do navegador. Internamente, ela utiliza o mecanismo do Microsoft Edge ou
do Google Chrome em modo aplicativo. Assim, o flet.exe bloqueado pelo Controle
Inteligente de Aplicativos do Windows não é executado.

O jogo e o servidor Python continuam funcionando somente neste computador. O
endereço local não é publicado na internet.

Depois da instalação das dependências, todas as imagens, ilustrações, sons e
arquivos do mascote são carregados da pasta assets. Nenhum módulo depende de
imagens HTTP ou HTTPS durante a execução.

As fórmulas matemáticas são exibidas por ft.Markdown com LaTeX. Frações aparecem
empilhadas, com o numerador acima do denominador, nas teorias, nos enunciados e
alternativas que contêm expressões, nos exemplos e no painel ESTUDAR.

COMO INSTALAR NO WINDOWS

1. Extraia todo o conteúdo do ZIP para uma pasta.
2. Abra o PowerShell dentro da pasta extraída.
3. Instale as dependências:

   py -3.14 -m pip install -r requirements.txt

4. Clique duas vezes em INICIAR_JOGO.bat.

O aplicativo abrirá em uma janela exclusiva. A pequena janela de comando do
iniciador fecha automaticamente e não precisa permanecer visível. Para encerrar
o programa, feche normalmente a janela do jogo.

Se a janela não abrir, execute INICIAR_COM_DIAGNOSTICO.bat. O diagnóstico
mostra as mensagens técnicas e também grava o arquivo:

   dados\iniciador_janela_app.log

O Microsoft Edge é utilizado de preferência. Se ele não estiver disponível, o
iniciador tenta usar o Google Chrome. Pelo menos um dos dois precisa estar
instalado.

Não retire os arquivos Python de dentro da pasta. O programa precisa encontrar
as pastas assets e dados.

RECURSOS DE JOGO (VERSÃO DE 28/09/2026)

• Ao responder, a alternativa escolhida fica verde (acerto) ou vermelha
  (erro) e a correta é destacada por cerca de 1 segundo antes da resolução.
• O saldo no placar "rola" até o novo valor.
• Efeitos sonoros de acerto, erro e conquista; nos últimos 10 segundos o
  cronômetro pulsa e faz tique. Os efeitos têm botão próprio, EFEITOS
  (na tela inicial é o ícone de mão ao lado de ATIVAR SOM), separado da
  música: ATIVAR SOM liga só a música de fundo. Os efeitos vêm ligados e a
  escolha fica salva. Para recriá-los: py -3.14 ferramentas\gerar_efeitos.py
• Todo botão faz um "clique" ao ser pressionado (em todas as telas).
• Ao ACERTAR: fanfarra de vitória com aplausos da plateia, e o cartão da
  alternativa correta vibra (a vibração some com "Sem animações").
  Volumes e duração dos aplausos: início de ferramentas\gerar_efeitos.py.
• Transição suave entre as telas.
• Sequência de acertos: a partir de 2 acertos seguidos aparece a faixa
  "🔥 N acertos seguidos!". É só um reconhecimento visual: a pontuação
  (+100, −200, +50) não muda.
• Resultado com pódio animado e conquistas da partida: Mais preciso, Maior
  sequência, Mais rápido e Mais estudioso.
• Atalhos de teclado: R responder · E estudar · A–E ou 1–5 alternativas ·
  Enter ou Espaço passar a vez.

ACESSIBILIDADE

O botão ACESSIBILIDADE, no topo da tela inicial, abre as opções (ficam
salvas para as próximas partidas):
• Tempo para cada questão: 60 s, 90 s, 120 s ou sem limite (o cronômetro
  mostra ∞ e não marca erro por tempo).
• Sem animações: desliga transições, pulsos do cronômetro, saldo animado e
  crescimento dos cartões; os sons continuam no botão ATIVAR SOM.
• Tema de alto contraste: preto, branco, amarelo e ciano (também aparece na
  lista "Tema" como "Alto contraste").
Sempre ativos: acerto e erro marcados com cor, ícone e palavra
("✓ CORRETA" / "✗ SUA ESCOLHA"), LUPA, leitura em voz e atalhos de teclado.

Para a pesquisa, dados\respostas.csv registra em cada jogada o tempo
limite, se as animações estavam desligadas e o tema usado.
O botão de importar música virou só um ícone (nota musical) ao lado de
Música, para a barra do topo caber em uma linha.

LUPA (ACESSIBILIDADE)

O botão LUPA, no topo da tela inicial e de cada módulo, liga a Lupa do
Windows no modo lente: um retângulo ampliado acompanha o mouse. Clique de
novo (LUPA LIGADA) para desligar.
Atalhos da própria Lupa do Windows:
   Windows + "+"   aumenta o zoom (e liga a lupa)
   Windows + "−"   diminui o zoom
   Windows + Esc   desliga a lupa
Neste computador o zoom inicial da Lupa foi definido em 300%. Em outro
computador, se o zoom estiver em 100%, pressione Windows + "+" para ampliar;
o Windows lembra o nível escolhido.

TELAS SEM ROLAGEM

As telas foram ajustadas para caber inteiras na janela do jogo em uma tela
1920 x 1080 com zoom de 125% (área útil de cerca de 1536 x 786), sem rolar:
• O estudo de Porcentagem e de Juros tem duas páginas, como no PRICE:
  1) conceito, fórmula e exemplos; 2) resolução passo a passo e o botão
  CONCLUIR ESTUDO E PASSAR A VEZ. Enter avança a página.
• O resultado mostra, lado a lado, a classificação e o pódio.
• No modo administrador a barra ocupa uma só linha (o gabarito completo
  aparece ao passar o mouse) e o placar de saldos de teste fica oculto.
Em telas menores a barra de rolagem aparece automaticamente.

DADOS PARA A PESQUISA

Cada jogada é registrada automaticamente (abre no Excel):

   dados\respostas.csv
       Uma linha por jogada: data e hora, sessão, módulo, nível, questão,
       jogador, resultado (acerto, erro, tempo_esgotado ou estudo),
       alternativa escolhida, alternativa correta e tempo de resposta.
   dados\relatorio_por_questao.csv
       Tentativas, acertos, erros, tempo esgotado, estudos, % de acerto e
       tempo médio de cada questão (as mais difíceis aparecem primeiro).
   dados\relatorio_por_jogador.csv
       Resumo de cada jogador por módulo.

A tela RANKING mostra as 5 questões com menor índice de acerto da turma.
No modo administrador os arquivos recebem o sufixo _admin e não se misturam
aos dados dos estudantes.

Atenção (ética em pesquisa): os arquivos contêm os nomes digitados pelos
jogadores. Se o protocolo da pesquisa exigir anonimato, cadastre apelidos ou
códigos (ex.: A01, A02) no lugar dos nomes.

NOVA TURMA

O botão NOVA TURMA, no topo da tela inicial, guarda jogadores, saldos,
ranking e respostas da turma atual em dados\turmas\<data e hora> e recomeça
o jogo do zero, mantendo tema e músicas. Nada é apagado.

MODO ADMINISTRADOR (PARA O PROFESSOR)

Clique duas vezes em INICIAR_ADMIN.bat para conferir o conteúdo sem precisar
jogar cada rodada. Nos módulos aparece uma barra amarela com:

• lista com todas as questões do módulo, na ordem do banco;
• setas para a questão anterior e a próxima;
• botões SITUAÇÃO, ALTERNATIVAS, ESTUDO e RESOLUÇÃO, que abrem direto
  cada tela da questão escolhida;
• gabarito da questão (letra e alternativa correta).

No modo administrador o cronômetro fica desligado e as questões não são
sorteadas. Os saldos de teste ficam em dados\estado_admin.json: os saldos dos
jogadores reais (dados\estado_jogo.json) e o ranking (dados\ranking.xlsx) não
são alterados. O modo administrador pode ficar aberto junto com o jogo normal.

REGRAS DO JOGO

• Cadastre de 2 a 4 jogadores na tela inicial.
• Cada jogador pode escolher uma foto ou imagem opcional.
• A cada rodada, o jogador escolhe RESPONDER ou ESTUDAR.
• Resposta correta: ganha R$ 100,00.
• Resposta incorreta: perde R$ 200,00.
• O saldo pode ficar negativo.
• Ao estudar, ganha R$ 50,00 e o conteúdo da questão é apresentado.
• Cada questão possui um cronômetro regressivo de 60 segundos.
• Se o tempo terminar, a questão é registrada automaticamente como erro.
• A narração da questão é opcional e utiliza a voz nativa do computador.
• O controle de velocidade oferece 0,75x, 1,0x, 1,5x e 2,0x.
• No módulo de Juros, a narração acompanha a revisão, o enunciado, as
  alternativas ou a resolução que estiver visível.
• Depois de acerto, erro ou estudo, a vez passa obrigatoriamente ao próximo
  jogador.
• Porcentagem e Juros usam 20 situações cada; PRICE usa 60 situações.
• O saldo fica acumulado ao voltar à tela inicial ou jogar novamente.
• A pontuação obtida em Porcentagem e Juros permanece ao iniciar PRICE.
• Os dados continuam salvos ao fechar e reabrir o programa na mesma pasta.

PERSONALIZAÇÃO

Durante o jogo é possível escolher:

• 5 temas de cores, selecionados na tela inicial ou durante a etapa.
• 10 trilhas sonoras.
• Música escolhida pelo jogador no computador.
• Som ligado ou desligado.
• Narração da questão ligada ou desligada.

MASCOTE DO MÓDULO DE PORCENTAGEM

O espaço do mascote usa inicialmente:

   assets/mascote_financeiro.webp

Para trocar a imagem, coloque o novo arquivo em assets e altere a constante
CAMINHO_MASCOTE no início de nivel_1_porcentagem.py.

MÓDULO DE JUROS SIMPLES E COMPOSTOS

Na tela inicial, escolha JUROS. Antes das questões, o módulo pergunta se o
jogador deseja rever o assunto ou ir direto ao quiz.

A revisão inclui:

• definição de juros simples;
• definição de juros compostos;
• fórmulas de juros e montante;
• exemplos de empréstimos, financiamentos e investimentos;
• imagens financeiras armazenadas localmente no aplicativo.

O conteúdo é dividido em três partes: Juros Simples, Juros Compostos e
Comparação/Aplicações. Use VOLTAR e AVANÇAR dentro da revisão para mudar de
parte sem precisar percorrer um texto único muito extenso.

NAVEGAÇÃO DO MÓDULO DE JUROS

Todas as telas apresentam dois controles no cabeçalho:

• TELA ANTERIOR: retorna à tela interna de onde o jogador veio;
• INÍCIO: encerra o fluxo atual e volta diretamente ao menu principal.

O histórico é mantido dentro do próprio módulo para não acumular Views nem
duplicar controles na página principal. Ao concluir uma rodada, o histórico da
questão é encerrado para impedir uma segunda pontuação na mesma situação.

O espaço do mascote continua usando:

   assets/mascote_financeiro.webp

As imagens da teoria e das questões são configuradas em:

   nivel_2_juros.py
   dados/questoes_juros.json

Os respectivos arquivos ficam em:

   assets/imagens/juros/

Não é necessária conexão com a internet para exibir essas imagens.

MÓDULO DO SISTEMA PRICE / SAF

Na tela inicial, escolha SISTEMA PRICE. Antes das questões, o módulo pergunta
se o jogador deseja rever o assunto ou ir direto ao quiz.

A revisão está dividida em quatro partes:

• definição do Sistema de Amortização Francês e prestação fixa PMT;
• relação entre os valores presentes das prestações e Progressão Geométrica;
• juros decrescentes, amortização crescente e tabela PRICE demonstrativa;
• custo total, CET e tomada de decisão financeira.

O módulo contém 60 questões com cinco alternativas, distribuídas nos níveis
Super fácil, Fácil, Médio e Difícil. As imagens são locais e ficam em:

   assets/imagens/price/

Todas as telas mantêm TELA ANTERIOR e INÍCIO. A narração acompanha a revisão,
o enunciado, as cinco alternativas ou a resolução aberta em ESTUDAR.

RANKING

O botão RANKING mostra a classificação dentro do programa. A planilha:

   dados/ranking.xlsx

é atualizada automaticamente quando nomes, saldos ou resultados mudam.
Se a planilha estiver aberta no Excel durante uma jogada, feche-a para permitir
que o programa grave a atualização seguinte.

CONTEÚDO DAS PASTAS

assets/imagens/produtos/
    20 imagens ilustrativas de produtos reais comercializados no Brasil.

assets/imagens/juros/
    Imagens locais usadas na teoria e nas questões de juros.

assets/imagens/price/
    Imagens locais dos produtos usados na teoria e nas 60 questões PRICE.

assets/sons/
    10 trilhas instrumentais leves, próprias para o jogo.

assets/perfis/
    Fotos e imagens opcionais escolhidas pelos jogadores.

assets/sons_personalizados/
    Músicas escolhidas pelo usuário.

dados/questoes_porcentagem.json
    Banco externo com enunciados, alternativas, respostas, explicações,
    conteúdos de estudo, preços, datas e fontes.

dados/questoes_juros.json
    Banco com 20 questões autorais de juros simples e compostos, alternativas,
    respostas, explicações e resolução passo a passo.

dados/questoes_price.json
    Banco com 60 questões do Sistema PRICE / SAF, cinco alternativas,
    gabarito comentado e memória de cálculo.

dados/estado_jogo.json
    Jogadores, saldos acumulados, estatísticas e preferências.

dados/ranking.xlsx
    Planilha automática de classificação.

ferramentas/validar_conteudo.py
    Confere questões, LaTeX, imagens locais, assets_dir e sons.

ferramentas/testar_telas.py
    Monta as 100 questões e todas as páginas teóricas em Flet 0.86.3 para
    verificar os componentes Markdown e as frações empilhadas.

ferramentas/gerar_sons.py
    Recria as dez trilhas, caso seja necessário.

TESTE RÁPIDO DO MÓDULO DE PORCENTAGEM

Também é possível abrir somente o jogo de porcentagem:

   py -3.14 nivel_1_porcentagem.py

TESTE RÁPIDO DO MÓDULO DE JUROS

   py -3.14 nivel_2_juros.py

TESTE RÁPIDO DO MÓDULO PRICE / SAF

   py -3.14 nivel_3_price.py

OBSERVAÇÃO SOBRE OS PREÇOS

Os preços foram consultados em 27/07/2026. Promoções e preços podem mudar.
Antes de uma nova aplicação com estudantes, confira as fontes registradas no
arquivo JSON e atualize os valores e a data da consulta.
