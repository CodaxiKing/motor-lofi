"""Gestos com intenção, preparação e acomodação; movimentos locais por pins."""
import copy
import math

PERFIS={
 'perguntar':{'cabeca':2.5,'mao_d':[-.008,-.012]},
 'negar':{'cabeca':-3,'mao_d':[.012,-.006]},
 'afirmar':{'cabeca':1.8,'mao_d':[-.004,-.008]},
 'alertar':{'cabeca':-1.5,'mao_d':[-.015,-.025]},
 'esconder':{'cabeca':-2,'mao_e':[.008,-.01]},
 'provocar':{'cabeca':3,'mao_d':[.012,-.012]},
 'ouvir':{'cabeca':1.2},
}


def envoltoria(t,start,end,antecipacao=.18,acomodacao=.28):
    def ease(x):x=max(0,min(1,x));return x*x*(3-2*x)
    if t<start-antecipacao or t>end+acomodacao:return 0
    return ease((t-start+antecipacao)/max(.001,antecipacao)) if t<start else 1-ease((t-end)/max(.001,acomodacao)) if t>end else 1


def aplicar(rig,eventos,t):
    out=copy.deepcopy(rig)
    for e in eventos or []:
        peso=envoltoria(t,e['start'],e['end'])
        if not peso:continue
        perfil=PERFIS.get(e.get('intencao','afirmar'),PERFIS['afirmar'])
        # Pulso na fala evita segurar um gesto rígido durante toda a frase.
        pulso=.6+.4*math.sin(math.pi*min(1,max(0,(t-e['start'])/max(.1,e['end']-e['start']))))
        for nome,delta in perfil.items():
            if nome=='cabeca':
                for grupo in out.get('grupos_rigidos',[]):
                    grupo['offset_graus']=grupo.get('offset_graus',0)+delta*peso*pulso
            elif nome in out['pins'] and not out['pins'][nome].get('fixo'):
                pin=out['pins'][nome];old=pin.get('offset',[0,0])
                pin['offset']=[old[i]+delta[i]*peso*pulso for i in range(2)]
    return out
