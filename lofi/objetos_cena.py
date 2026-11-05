"""Objetos deixados no cenário: desenhos nativos que respeitam câmera e oclusão frontal."""
from PIL import ImageDraw


def desenhar(imagem, shot, rel, cam, camx, depth, xo=0):
    from .mapa import marcas
    z, x0, y0 = cam
    d = ImageDraw.Draw(imagem)
    for objeto in shot.get('ground_objects', []):
        if rel < objeto.get('visible_after', 0) or rel >= objeto.get('visible_until', float('inf')):
            continue
        mk = marcas(shot['scene']).get(objeto.get('mark'), {'x': 540, 'y': 1700})
        x = (objeto.get('x', mk['x']) + xo - camx * depth - x0) * z
        y = (objeto.get('y', mk['y']) - y0) * z
        def caixa(a, b, c, e): return [x+a*z, y+b*z, x+c*z, y+e*z]
        tipo = objeto['id']
        d.ellipse(caixa(-38, -7, 38, 6), fill=(25, 25, 30))
        if tipo == 'key':
            d.ellipse(caixa(-25, -21, -3, 1), outline=(235, 191, 65), width=max(1, int(5*z)))
            d.line([(x-3*z, y-10*z), (x+27*z, y-10*z), (x+27*z, y-3*z)], fill=(235, 191, 65), width=max(1, int(5*z)))
        elif tipo == 'bag':
            d.rounded_rectangle(caixa(-34, -65, 34, 0), 12*z, fill=(205, 163, 65), outline=(30, 30, 35), width=max(1, int(3*z)))
            d.rectangle(caixa(-22, -30, 22, -8), outline=(70, 60, 40), width=max(1, int(3*z)))
        elif tipo == 'phone':
            d.rounded_rectangle(caixa(-24, -37, 24, -1), 5*z, fill=(40, 42, 50))
            d.rectangle(caixa(-19, -32, 19, -7), fill=(116, 165, 180))
        elif tipo == 'flashlight':
            d.rectangle(caixa(-25, -18, 15, -5), fill=(80, 85, 92))
            d.ellipse(caixa(10, -24, 30, 0), fill=(232, 221, 160))
        elif tipo == 'radio':
            d.rounded_rectangle(caixa(-30, -35, 30, 0), 6*z, fill=(120, 80, 54))
            d.line([(x+20*z, y-35*z), (x+30*z, y-66*z)], fill=(170, 170, 175), width=max(1, int(3*z)))
