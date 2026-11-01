"""Adapters opcionais: offline (Piper) e HTTP (ElevenLabs/ComfyUI).
Nenhuma chamada remota ocorre sem escolha explícita do provedor.
"""
import json
import os
import shutil
import subprocess
import urllib.request
import urllib.error
from pathlib import Path

class ProviderError(RuntimeError): pass

def synthesize(text, destination, *, provider='piper', voice=None, model=None, base_url=None):
    if not isinstance(text, str) or not text.strip(): raise ValueError('Texto vazio')
    dest = Path(destination)
    if dest.suffix.lower() not in ('.wav', '.mp3'): raise ValueError('Saída deve ser WAV ou MP3')
    dest.parent.mkdir(parents=True, exist_ok=True)
    if provider == 'piper':
        if dest.suffix.lower() != '.wav': raise ValueError('Piper gera WAV')
        exe = shutil.which('piper')
        if not exe: raise ProviderError('Piper não instalado. Instale o executável e o modelo de voz.')
        voice_model = model or os.getenv('LOFI_PIPER_MODEL')
        if not voice_model or not Path(voice_model).is_file(): raise ProviderError('Configure --model com um arquivo .onnx existente')
        cmd = [exe, '--model', str(voice_model), '--output_file', str(dest)]
        result = subprocess.run(cmd, input=text, text=True, capture_output=True, timeout=180)
        if result.returncode != 0: raise ProviderError('Piper falhou: '+result.stderr[-600:])
    elif provider == 'elevenlabs':
        if dest.suffix.lower() != '.mp3': raise ValueError('ElevenLabs gera MP3')
        key = os.getenv('ELEVENLABS_API_KEY')
        voice_id = voice or os.getenv('LOFI_ELEVENLABS_VOICE_ID')
        if not key or not voice_id: raise ProviderError('Configure ELEVENLABS_API_KEY e --voice')
        if not all(c.isalnum() or c in '_-' for c in voice_id): raise ValueError('ID de voz inválido')
        url = 'https://api.elevenlabs.io/v1/text-to-speech/'+voice_id
        data = json.dumps({'text':text,'model_id':model or 'eleven_multilingual_v2'}).encode()
        req=urllib.request.Request(url,data=data,headers={'xi-api-key':key,'Content-Type':'application/json','Accept':'audio/mpeg'},method='POST')
        try:
            with urllib.request.urlopen(req,timeout=120) as resp: dest.write_bytes(resp.read())
        except urllib.error.HTTPError as e: raise ProviderError(f'ElevenLabs HTTP {e.code}: {e.read(300)!r}') from e
    else: raise ValueError('Provedor de voz não suportado: '+provider)
    if not dest.exists() or dest.stat().st_size == 0: raise ProviderError('Arquivo de voz não gerado')
    return dest

def comfyui_image(prompt, destination, *, workflow_path, base_url='http://127.0.0.1:8188', timeout=240):
    """Submete workflow exportado do ComfyUI; NÃO baixa nem presume imagens prontas.

    O workflow deve ser API JSON e conter o marcador __PROMPT__ em campos de texto.
    Retorna prompt_id para consulta; não afirma que a imagem foi criada.
    """
    from urllib.parse import urlparse
    u=urlparse(base_url)
    if u.scheme!='http' or u.hostname not in ('127.0.0.1','localhost','::1'):
        raise ValueError('Por segurança ComfyUI deve ser local (localhost)')
    wf=Path(workflow_path).read_text(encoding='utf-8')
    if '__PROMPT__' not in wf: raise ValueError('Workflow deve conter marcador __PROMPT__')
    workflow=json.loads(wf.replace('__PROMPT__',json.dumps(prompt)[1:-1]))
    req=urllib.request.Request(base_url.rstrip('/')+'/prompt',data=json.dumps({'prompt':workflow}).encode(),headers={'Content-Type':'application/json'})
    try:
        with urllib.request.urlopen(req,timeout=timeout) as r: result=json.load(r)
    except (urllib.error.URLError,TimeoutError) as e: raise ProviderError('ComfyUI indisponível: '+str(e)) from e
    return {'prompt_id':result.get('prompt_id'),'status':'queued','requested_destination':str(destination)}
