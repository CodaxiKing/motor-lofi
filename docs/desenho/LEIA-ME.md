# Modo DESENHO no motor-lofi

Já instalado neste repositório (os módulos estão em `lofi/` e o gancho em `Episode.scene_frame`); não é preciso rodar o
`install_into_motor.py` citado nos READMEs abaixo. Exemplos em `examples/desenho/`, testes em `tests/test_v4.py`,
`tests/test_v5.py`, `tests/test_drawing_mode.py`, `tests/test_animation_engines.py` e `tests/test_visual_assets.py`.

Correção na integração: o gancho original importava `W, H` dentro de `scene_frame`, o que quebrava todos os planos normais
(UnboundLocalError); agora usa os `W, H` do módulo (funciona em pé e na versão deitada).
