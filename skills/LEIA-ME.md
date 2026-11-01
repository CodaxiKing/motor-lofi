# Skills da série lo-fi interativa

Cópia das 8 skills usadas com o motor. Para usar em outra conta do Claude, adicione cada uma nas configurações de skills
da conta (envie o arquivo `.zip` de cada pasta ou o `SKILL.md`).

| Skill | Para que serve |
|---|---|
| `serie-lofi-interativa` | Manual base: estilo, recursos do motor e formato do roteiro (instale primeiro) |
| `serie-planejar` | `/serie-planejar` — cria uma série nova e a bíblia |
| `serie-roteiro` | `/serie-roteiro` — roteiro do próximo episódio, voto por toque |
| `serie-continuar` | `/serie-continuar 2 B` — registra o voto e gera o próximo roteiro |
| `serie-montar` | `/serie-montar` + áudios — monta o vídeo, teaser, capa e legenda |
| `motor-lofi-studio` | Skill principal do Studio 4.0: orquestra as outras, da história ao roteiro técnico e à revisão (`tools/studio.py`) |
| `serie-producao-ia` | Produção híbrida: planejamento automático, assets, narração local (Piper) ou ElevenLabs só com autorização, revisão e render |
| `serie-comentarios` | `/serie-comentarios` + comentários (texto ou print) → roteiro de respostas; com os áudios → vídeo |

## Requisitos na outra conta
- Acesso a este repositório no GitHub (`CodaxiKing/motor-lofi`): conecte o GitHub na outra conta. Se o repositório for privado,
  a conta conectada precisa ter permissão nele (convide-a como colaboradora ou deixe o repositório público).
- As skills apontam para `https://github.com/CodaxiKing/motor-lofi`. Se você copiar o repositório para outro lugar,
  troque esse endereço dentro dos arquivos `SKILL.md`.
