"""Exemplo editorial original; não interpreta briefs nem invoca geração de texto."""


def rascunho(titulo=None, ideia=None, duracao=120):
    from .perfis_duracao import planejar
    planejar('curto',duracao)
    situacao='Mara se esconde num abrigo enquanto um rádio anuncia resgate na torre.'
    premissa='Antes de seguir uma luz na mata, ela precisa confirmar o sinal de duas piscadas.'
    textos=[
        situacao+' '+premissa+' É sábado, a energia acabou e ela tem água para uma noite. A transmissão promete uma saída, mas manda conferir o sinal antes de abandonar o abrigo.',
        'O rádio repete: quinta-feira, equipe na torre depois do escuro. Mara guarda a instrução que vem em seguida: duas piscadas curtas. Uma luz parada não confirma a presença de ninguém. O chiado cobre o fim da mensagem.',
        'Ela quer encontrar ajuda antes que a água termine. Mas deixar a porta protegida por uma promessa sem confirmação pode custar o único teto disponível. Mara decide observar da trilha, mantendo o caminho de volta na memória.',
        'Da clareira, a torre aparece entre as árvores. Nenhuma janela está acesa. A mensagem parecia próxima; a construção, agora diante dela, parece abandonada. Mara espera o tempo de uma nova chamada sem avançar pela escada.',
        'Nada pisca na cabine. Mais abaixo, porém, um brilho amarelo atravessa os galhos. Ela poderia chamar por socorro, mas o sinal combinado ainda não apareceu. Segue apenas até a curva de onde consegue identificar aquela luz.',
        'O brilho vem de um posto vazio. Uma lâmpada presa à cobertura ilumina o asfalto molhado. Não há veículo de resgate nem sinal na janela da loja. A luz é abrigo possível, mas não é a resposta prometida pelo rádio.',
        'A lâmpada permanece acesa, sem uma única piscada. Mara percebe que quase trocou uma instrução verificável pela vontade de acreditar em qualquer luz. Recusa aquela pista e retorna ao abrigo pela mesma trilha.',
        'De volta, o rádio repete a chamada inteira. Quinta-feira. Só agora Mara junta a data da mensagem ao sábado que marcou antes de sair. A transmissão está atrasada. A confirmação evitou que ela passasse a noite esperando um resgate antigo.',
        'Ela ganhou uma resposta, mas continua com pouca água. A torre pode alcançar outros sobreviventes se ainda tiver equipamento; o mercado visto da estrada pode guardar suprimentos. Mara precisa escolher entre tentar contato e procurar o que beber antes de amanhecer.'
    ]
    locais=['abrigo_radio']*3+['floresta_torre']*2+['posto_estrada']*2+['abrigo_radio']*2
    batidas=['estabelecer','detalhe','sustentar','estabelecer','detalhe','estabelecer','detalhe','detalhe','reacao']
    eventos=['A transmissão oferece uma rota de resgate','A data e o sinal são apresentados',
             'Mara decide conferir sem abandonar o retorno','A torre não mostra atividade',
             'Outra luz chama a atenção','O posto explica a origem da luz',
             'A luz falha no teste combinado','A data revela que a mensagem é antiga',
             'Mara decide o próximo objetivo']
    cenas=[]
    for i,(texto,local,batida) in enumerate(zip(textos,locais,batidas)):
        cena={'n':i+1,'cenario':local,'narracao':texto,'acontecimento':eventos[i],
              'consequencia':eventos[min(i+1,8)],'batida_visual':batida,'personagens':[]}
        if i:cena['causa']={'cena':i,'texto':eventos[i-1]+' motiva a próxima observação'}
        if i in (0,2,8):
            cena['personagens']=[{'id':'mara','pose':'neutro','pos':.57,'altura':.48,'chao':.94,
                                 'orientacao':'manual','respirar':0,'balanco_corpo':0}]
        if i in (1,7):cena['camera']={'plano':'detalhe','zoom':[1.65,1.7],'cx':.12,'cy':.46}
        if i==4:cena['camera']={'plano':'detalhe','zoom':[1.45,1.5],'cx':.27,'cy':.27}
        if i==6:cena['camera']={'plano':'detalhe','zoom':[1.6,1.65],'cx':.35,'cy':.34}
        cenas.append(cena)
    cenas[0]['conflito_pessoal']={'personagem':'mara','desejo':'Encontrar ajuda e água','custo':'Deixar o abrigo sem confirmar o resgate'}
    cenas[1]['planta']=[{'id':'data_chamada','texto':'O rádio diz quinta-feira, mas é sábado'},
                        {'id':'duas_piscadas','texto':'Somente duas piscadas confirmam a equipe'}]
    cenas[6]['paga']=[{'id':'duas_piscadas','texto':'A luz fixa do posto não é tratada como resgate'}]
    cenas[7]['revela']=[{'id':'data_chamada','texto':'A chamada está desatualizada'}]
    cenas[7]['resolve']=[{'id':'resgate','texto':'A mensagem antiga não confirma resgate presente'}]
    return {'version':1,'biblioteca':'cronicas','titulo':titulo or 'A luz que não respondeu',
            'perfil':'curto','duracao':duracao,'producao':{'etapa':'previa_visual'},
            'ideia_do_usuario':ideia,'metodo':'Exemplo editorial fixo e editável; o brief fica registrado, sem interpretação automática.',
            'abertura':{'situacao':situacao,'premissa':premissa},'cenas':cenas,
            'interface':{'relogio':{'dia':'SÁB','inicio':'23:00'}},
            'pendencias':['Gravar e sincronizar narração e transmissão do rádio',
                          'Arte de deslocamento e confirmação dos contatos antes de animar Mara',
                          'Revisar duração com a voz final; não preencher sobras com silêncio'],
            'escolhas':{'A':{'label':'SUBIR À TORRE','texto':'Procurar equipamento na torre',
                             'ganha':'chance de pedir ajuda','perde':'tempo e proteção do abrigo','motivo':'A instalação pode estar sem energia'},
                         'B':{'label':'IR AO MERCADO','texto':'Buscar água no mercado',
                             'ganha':'chance de repor suprimentos','perde':'oportunidade de contato antes do amanhecer','motivo':'O estoque pode ter acabado'}}}
