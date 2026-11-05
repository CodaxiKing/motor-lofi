"""Planejamento de produção e execução opt-in, com trilha de auditoria."""
import json
from pathlib import Path
from .autodirect import write_episode
from .asset_plan import write_asset_manifest
from .providers import synthesize, ProviderError

def prepare(story_path, output_path, *, profile='horror_illustrated', actor='roberta', scene='apartamento', duration=None, duration_profile=None, opening=None, elenco=None, world_state=None):
    ep=write_episode(story_path,output_path,visual_profile=profile,actor=actor,scene=scene,duration=duration, duration_profile=duration_profile, opening=opening, elenco=elenco, world_state=world_state)
    manifest_path=Path(output_path).with_suffix('.assets.json')
    manifest=write_asset_manifest(ep,manifest_path)
    from .studio import quality_report
    report_path = Path(output_path).with_suffix('.quality.json')
    report_path.write_text(json.dumps(quality_report(ep), ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    return {'episode':str(output_path),'manifest':str(manifest_path),'quality':str(report_path),'shots':len(ep['shots']), 'visual_assets':manifest}

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
