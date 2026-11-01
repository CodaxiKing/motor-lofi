"""Planejamento de produção e execução opt-in, com trilha de auditoria."""
import json
from pathlib import Path
from .autodirect import write_episode
from .asset_plan import write_asset_manifest
from .providers import synthesize, ProviderError

def prepare(story_path, output_path, *, profile='horror_illustrated', actor='roberta', scene='apartamento', duration=None):
    ep=write_episode(story_path,output_path,visual_profile=profile,actor=actor,scene=scene,duration=duration)
    manifest_path=Path(output_path).with_suffix('.assets.json')
    manifest=write_asset_manifest(ep,manifest_path)
    return {'episode':str(output_path),'manifest':str(manifest_path),'shots':len(ep['shots']), 'visual_assets':manifest}

def generate_narration(story_path, output_path, *, provider='piper', model=None, voice=None):
    text=Path(story_path).read_text(encoding='utf-8')
    return str(synthesize(text,output_path,provider=provider,model=model,voice=voice))

def status(story_path, episode_path):
    ep=Path(episode_path)
    data=json.loads(ep.read_text(encoding='utf-8'))
    voices={k: str((ep.parent/v).resolve()) for k,v in data.get('voices',{}).items()}
    return {'episode_exists':True,'shots':len(data.get('shots',[])),
            'voices':{k:Path(v).is_file() for k,v in voices.items()},
            'render_ready':bool(data.get('shots')),
            'audio_synced':bool(data.get('clips') and data.get('subs')),
            'warning':'JSON pronto não significa vídeo final nem áudio sincronizado.'}
