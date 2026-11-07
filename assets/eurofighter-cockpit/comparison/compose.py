"""Plain image composition; reference pixels, UI and watermarks are retained."""
from pathlib import Path
from PIL import Image
HERE=Path(__file__).resolve().parent
REPO=HERE.parent.parent.parent
refs={'front':'front.png','oblique':'oblique.png','hud-day':'detail-pass/hud-day.png'}
for name,relative in refs.items():
    photo=Image.open(REPO/'references/eurofighter-cockpit/user'/relative).convert('RGBA')
    model=Image.open(HERE/(name+'-model.png')).convert('RGBA')
    assert model.size==photo.size,(name,model.size,photo.size)
    photo.save(HERE/(name+'-reference.png'))
    model.putalpha(model.getchannel('A').point(lambda a:round(a*.35)))
    Image.alpha_composite(photo,model).convert('RGB').save(HERE/(name+'-overlay.png'))
