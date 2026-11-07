"""Approximate rigid pinhole camera fits. Manual landmarks; no mesh deformation."""
import math,json,random
from pathlib import Path
HERE=Path(__file__).parent
def dot(a,b):return sum(x*y for x,y in zip(a,b))
def basis(v):
 y,p,r=v[3:6];f=(math.cos(p)*math.cos(y),math.cos(p)*math.sin(y),math.sin(p));rr=(math.sin(y),-math.cos(y),0);u=(-math.sin(p)*math.cos(y),-math.sin(p)*math.sin(y),math.cos(p))
 return f,tuple(rr[i]*math.cos(r)+u[i]*math.sin(r) for i in range(3)),tuple(u[i]*math.cos(r)-rr[i]*math.sin(r) for i in range(3))
def project(v,pt,w,h,cx):
 f,r,u=basis(v);d=tuple(pt[i]-v[i] for i in range(3));z=dot(f,d)
 if z<.02:return(1e5,1e5)
 k=v[6]*w/36/z
 return(cx+dot(r,d)*k,h/2-dot(u,d)*k)
def fit(name,w,h,cx,pts,start):
 bounds=[(-10,.5),(-4,4),(-.2,6),(-1.3,1.3),(-1.4,.3),(-.7,.7),(12,300)]
 if name=='front':bounds=[(-3,-.2),(-.12,.12),(.30,2),(-.12,.12),(-1,-.15),(-.04,.04),(18,110)]
 def loss(v):
  if any(not a<=x<=b for x,(a,b) in zip(v,bounds)):return 1e14+sum(x*x for x in v)
  return sum(weight*sum((a-b)**2 for a,b in zip(project(v,p,w,h,cx),q)) for _,p,q,weight in pts)
 def nm(v):
  steps=[.15,.10,.12,.08,.08,.04,8];ss=[v]+[[x+(steps[j] if i==j else 0) for i,x in enumerate(v)] for j in range(7)]
  for it in range(1800):
   ss.sort(key=loss);lo,hi=loss(ss[0]),loss(ss[-1]);c=[sum(s[i] for s in ss[:-1])/7 for i in range(7)]
   ref=[2*c[i]-ss[-1][i] for i in range(7)];lr=loss(ref)
   if lr<lo:
    ex=[c[i]+2*(ref[i]-c[i]) for i in range(7)];ss[-1]=ex if loss(ex)<lr else ref
   elif lr<loss(ss[-2]):ss[-1]=ref
   else:
    co=[c[i]+.5*((ref if lr<hi else ss[-1])[i]-c[i]) for i in range(7)]
    if loss(co)<min(lr,hi):ss[-1]=co
    else:ss=[ss[0]]+[[ss[0][i]+.5*(s[i]-ss[0][i]) for i in range(7)] for s in ss[1:]]
   if hi-lo<1e-6:break
  return min(ss,key=loss)
 random.seed(43);best=nm(start)
 for t in range(10):
  trial=[best[i]+random.uniform(-1,1)*[.3,.15,.2,.08,.10,.03,15][i] for i in range(7)];v=nm(trial)
  if loss(v)<loss(best):best=v
 f,r,u=basis(best)
 # Matrix columns are camera local X(right),Y(up),Z(-forward). Blender Euler via later conversion.
 result={'location_m':best[:3],'target_m':[best[i]+f[i] for i in range(3)],'camera_matrix_columns':[r,u,[-x for x in f]],'lens_mm':best[6],'shift_x':(.5-cx/w),'shift_y':0,'resolution':[w,h], 'roll_rad':best[5], 'fit_method':'Rigid pinhole, manually estimated landmarks; no geometry changes; fixed principal point estimate; lens distortion unmodeled', 'landmarks':[]}
 for label,p,q,weight in pts:
  pred=project(best,p,w,h,cx);result['landmarks'].append({'name':label,'world_m':p,'photo_px':q,'projected_px':pred,'error_px':math.dist(q,pred),'weight':weight})
 result['weighted_rms_px']=math.sqrt(loss(best)/sum(p[3] for p in pts))
 print(name,round(result['weighted_rms_px'],2),best,flush=True)
 return result
def point(n,p,q,wt=1):return(n,p,q,wt)
# Screen opening centers and corners constrain the panel plane. HUD bar adds depth.
front=[point('left_screen',(.809,.235,-.302),(157,252),2),point('right_screen',(.809,-.235,-.302),(345,252),2),point('center_screen',(.809,0,-.355),(249,279),2),point('left_top_left',(.809,.315,-.2195),(125,222)),point('left_bottom_right',(.809,.155,-.3845),(190,280)),point('right_top_right',(.809,-.315,-.2195),(380,223)),point('right_bottom_left',(.809,-.155,-.3845),(314,280)),point('hud_bar_left',(.724,.132,-.108),(197,161)),point('hud_bar_right',(.724,-.132,-.108),(298,161))]
oblique=[point('left_top_left',(.809,.315,-.2195),(477,412)),point('left_top_right',(.809,.155,-.2195),(612,461)),point('left_bottom_left',(.809,.315,-.3845),(475,547)),point('left_bottom_right',(.809,.155,-.3845),(610,588)),point('center_screen',(.809,0,-.355),(744,618),2),point('right_top_left',(.809,-.155,-.2195),(899,567)),point('right_top_right',(.809,-.315,-.2195),(1055,624)),point('right_bottom_left',(.809,-.155,-.3845),(875,695)),point('right_bottom_right',(.809,-.315,-.3845),(1030,750)),point('hud_bar_left',(.724,.132,-.108),(538,366)),point('hud_bar_right',(.724,-.132,-.108),(727,401))]
day=[point('bar_left',(.724,.132,-.108),(433,842)),point('bar_right',(.724,-.132,-.108),(963,842)),point('lens_top',(.95725,0,.213),(704,73)),point('lens_left',(.92475,.174,.083),(369,320)),point('lens_right',(.92475,-.174,.083),(1054,320)),point('lens_bottom',(.89225,0,-.047),(707,598)),point('center_screen',(.809,0,-.355),(694,1088),.3)]
cameras={'front':fit('front',499,615,249.5,front,[-.8,0,.8,0,-.7,0,40]),'oblique':fit('oblique',1125,1500,562.5,oblique,[-.6,-.5,.9,.35,-.65,-.1,40]),'hud-day':fit('hud-day',1237,1178,700,day,[-.2,0,.2,0,-.2,0,35])}
for n,c in cameras.items():
 c['scope']='Local HUD comparison; fit uses lens anchors, so lens agreement is not independent validation' if n=='hud-day' else 'Instrument-cluster fit; other geometry is an independent visual comparison'
(HERE/'camera-fit.json').write_text(json.dumps({'cameras':cameras},indent=2))
if (HERE/'camera-review/proposed-front.json').exists():
 import runpy
 runpy.run_path(str(HERE/'apply_reviewed_front.py'))
