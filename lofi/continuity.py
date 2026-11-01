"""Verificações adicionais de continuidade, sem modificar fichas travadas."""
import json
from pathlib import Path

def validate_episode(path):
    path=Path(path); spec=json.loads(path.read_text(encoding='utf-8'))
    issues=[]
    for folder in (path.parent,path.parent.parent):
        file=folder/'personagens.json'
        if file.is_file():
            locked=json.loads(file.read_text(encoding='utf-8'))
            for name, override in spec.get('characters',{}).items():
                if name in locked and override != locked[name]:
                    issues.append(f'{name}: ficha local difere da ficha travada; a ficha travada prevalece')
            break
    shots=spec.get('shots',[])
    for i,shot in enumerate(shots):
        if float(shot.get('end',0))<=float(shot.get('start',0)):
            issues.append(f'plano {i}: intervalo inválido')
        for layer in shot.get('layers',[]):
            if not (path.parent/layer.get('path','')).is_file():
                issues.append(f'plano {i}: asset não encontrado: {layer.get("path")}')
    return issues
