"""Original illustrative instrument/legend art; no photographic pixels used."""
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path
import json, math, random
ROOT=Path(__file__).resolve().parent
OUT=ROOT/'textures'; OUT.mkdir(exist_ok=True)
font_path='C:/Windows/Fonts/consola.ttf'
def font(s): return ImageFont.truetype(font_path,s)
im=Image.new('RGB',(1536,512),(3,9,10)); d=ImageDraw.Draw(im)
green=(104,225,115); dim=(26,87,61); amber=(232,161,54); blue=(94,166,205)
# Left multifunction display: restrained flight/status page.
d.text((24,16),'SYSTEM STATUS',font=font(24),fill=green)
d.line((22,51,488,51),fill=dim,width=2)
rows=['FLIGHT CONTROL     NORM','NAV ALIGN          READY','FUEL TOTAL         5040','HYD 1 / 2          280','ELEC AC / DC       NORM','OXYGEN             NORM','CABIN PRESS        AUTO','DATA LINK          STBY']
for i,t in enumerate(rows): d.text((25,72+i*33),t,font=font(19),fill=green if i%3 else amber)
for i,t in enumerate(['FLIGHT','NAV','FUEL','SYS']): d.text((25+i*121,467),t,font=font(17),fill=green)
d.text((25,377),'ALT  18000   IAS  320',font=font(20),fill=blue)
d.text((25,414),'QNH  1013    HDG  045',font=font(20),fill=green)
# Middle display: authored schematic terrain/navigation page.
random.seed(8)
d.rectangle((530,48,1006,455),fill=(74,91,64))
for i in range(90):
 x=random.randrange(532,1000); y=random.randrange(50,450)
 d.polygon([(x,y),(x+random.randrange(12,75),y+12),(x+48,y+random.randrange(25,60)),(x-10,y+35)],fill=random.choice([(88,100,72),(101,111,76),(66,87,66),(117,116,82)]))
for i in range(7):
 y=68+i*58; pts=[(530+k*40,y+int(math.sin(k*.8+i)*20)) for k in range(13)]
 d.line(pts,fill=(155,155,110),width=2)
d.line([(550,425),(635,349),(680,245),(811,199),(868,97),(985,60)],fill=(93,146,165),width=10)
for i in range(5):d.line([(540,100+i*65),(650,140+i*49),(790,100+i*50),(1005,170+i*54)],fill=(190,177,135),width=3)
d.line([(646,389),(768,260),(889,165)],fill=(230,231,170),width=3)
d.polygon([(768,245),(756,274),(768,267),(780,274)],fill=(230,240,221))
d.ellipse((690,182,846,338),outline=(191,214,172),width=2)
d.text((537,13),'NAV   045       20 NM',font=font(22),fill=green)
d.text((537,469),'MAP    POS    DATA    MENU',font=font(19),fill=green)
# Right display: engine/system rings, original illustrative data.
d.text((1045,15),'ENGINE / FUEL',font=font(24),fill=green)
for row,(lab,v) in enumerate([('N1','87'),('TGT','640'),('FF','1840')]):
 for col in range(2):
  cx=1150+col*230; cy=115+row*135
  d.arc((cx-48,cy-48,cx+48,cy+48),-220,40,fill=blue,width=3)
  a=math.radians(-45+row*22); d.line((cx,cy,cx+math.cos(a)*41,cy+math.sin(a)*41),fill=green,width=3)
  d.text((cx-24,cy+16),v,font=font(19),fill=green)
  d.text((cx-20,cy-15),lab,font=font(17),fill=amber)
d.text((1048,467),'FUEL   ENG   HYD   ELEC',font=font(19),fill=green)
# User reference revision: subdued dark left display, map center, blue/brown
# attitude display on the right. These remain original illustrative graphics.
d.rectangle((1024,0,1535,511),fill=(6,13,21))
d.ellipse((1130,130,1470,470),fill=(36,118,168))
mask=Image.new('L',(1536,512),0);md=ImageDraw.Draw(mask);md.ellipse((1130,130,1470,470),fill=255)
brown=Image.new('RGB',(1536,512),(174,143,72));bm=Image.new('L',(1536,512),0);bd=ImageDraw.Draw(bm);bd.polygon([(1100,440),(1536,200),(1536,512),(1100,512)],fill=255)
from PIL import ImageChops
im.paste(brown,(0,0),ImageChops.multiply(mask,bm));d=ImageDraw.Draw(im)
d.line((1260,295,1340,295),fill=(220,225,199),width=2);d.line((1300,278,1300,311),fill=(220,225,199),width=2)
for k in range(5):
 yy=210+k*35;d.line((1285,yy,1315,yy),fill=(175,206,199),width=1)
d.text((1044,20),'ATT     HDG 045',font=font(20),fill=green)
d.text((1044,478),'NAV    ATT    HSI    SYS',font=font(16),fill=green)
im.save(OUT/'instruments.png')
# Separate low-brightness HUD control readout, authored from text primitives.
hud=Image.new('RGB',(512,256),(2,6,6));hd=ImageDraw.Draw(hud)
hd.text((20,16),'NAV READY',font=font(15),fill=(65,135,66))
hd.text((330,16),'ALIGN 00.0',font=font(14),fill=(65,135,66))
hd.text((22,221),'BRT 4',font=font(12),fill=(43,100,51))
hd.text((385,221),'MAN',font=font(12),fill=(43,100,51))
hud.save(OUT/'hud-controls.png')
# Alpha legends packed into a single atlas, authoring-only texture.
labels=['FUEL','NAV','SYS','ENG','MAP','DATA','MENU','COM','IFF','ALT','HDG','BRT','CONT','GAIN','OFF','ON','AUTO','STBY','RESET','TEST','FLIGHT CONTROL','COMMUNICATION','LIGHTING','ENGINE START','OXYGEN','ELECTRICAL','HYDRAULIC','FIRE','CANOPY','EMERGENCY','PULL','NO STEP','LOCK','FLIR','RDR','DCLT','HMD','HUD','MASTER','WARNING','CAUTION','BARO','1013','QNH','RADIO','UHF','VHF','VOL','DIM','EXT','INT','APU','BAT','GEN','L','R','1','2','3','4','5','6','7','8','9','0','CLR','ENT','NORM','ARM','SAFE','SECURE DATA','PARK BRAKE','GEAR','DOWN','UP','VOICE','TAC','IDENT','MAN','FWD','REV','PRESS TO RELEASE']
atlas=Image.new('RGBA',(2048,2048),(0,0,0,0)); a=ImageDraw.Draw(atlas); rect={}
for i,t in enumerate(labels):
 x=(i%4)*512; y=(i//4)*80
 f=font(34 if len(t)<14 else 28); b=a.textbbox((0,0),t,font=f); w=b[2];h=b[3]-b[1]
 a.text((x+8,y+12-b[1]),t,font=f,fill=((73,153,83,255) if t in ['LOCK','HMD','DCLT','RDR','FLIR'] else (203,215,201,255)))
 rect[t]=[x+5,y+8,x+w+12,y+h+17]
atlas.save(OUT/'legends.png'); (OUT/'legends.json').write_text(json.dumps(rect,indent=2))
# Small authored fabric maps: woven fibres rather than a smooth plastic seat.
for name,base in [('olive-weave',(77,82,44)),('harness-weave',(78,99,85))]:
 img=Image.new('RGB',(512,512)); px=img.load();random.seed(28)
 for y in range(512):
  for x in range(512):
   weave=(7 if (x%8)<3 else -4)+(5 if (y%8)<3 else -3)+random.randrange(-5,6)
   px[x,y]=tuple(max(0,min(255,c+weave)) for c in base)
 img.save(OUT/(name+'.png'))
