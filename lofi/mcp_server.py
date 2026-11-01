"""Servidor MCP opcional: pip install mcp; python -m lofi.mcp_server.
Ferramentas sem cobrança automática; voz é operação explícita.
"""
def main():
    try: from mcp.server.fastmcp import FastMCP
    except ImportError as e: raise SystemExit('Instale a dependência opcional: pip install mcp') from e
    from .production import prepare, status, generate_narration
    app=FastMCP('motor-lofi-skill')
    @app.tool()
    def preparar_episodio(roteiro_txt:str,episodio_json:str,perfil:str='horror_illustrated')->dict:
        """Cria roteiro técnico e manifesto, sem consumir créditos de API."""
        return prepare(roteiro_txt,episodio_json,profile=perfil)
    @app.tool()
    def consultar_episodio(roteiro_txt:str,episodio_json:str)->dict:
        """Consulta arquivos e status de preparação."""
        return status(roteiro_txt,episodio_json)
    @app.tool()
    def gerar_voz_local(roteiro_txt:str,saida_wav:str,modelo_onnx:str)->str:
        """Executa Piper local com modelo já instalado, sem serviço pago."""
        return generate_narration(roteiro_txt,saida_wav,provider='piper',model=modelo_onnx)
    app.run(transport='stdio')
if __name__=='__main__':main()
