"""Apply the reviewed whole-cockpit inspection camera without altering geometry."""
import json,math
from pathlib import Path
HERE=Path(__file__).parent
doc=json.loads((HERE/'camera-fit.json').read_text())
pose=json.loads((HERE/'camera-review/proposed-front.json').read_text())
old=doc['cameras']['front']
cfg={k:pose[k] for k in ['location_m','target_m','lens_mm','shift_x','shift_y','resolution']}
cfg.update({'scope':'Reviewed whole-cockpit inspection compromise; cushion and instruments visible; not calibrated', 'fit_method':'Manual camera review with rendered trials; 42mm perspective on horizontal 36mm sensor; old panel-only optimizer rejected', 'horizontal_fov_degrees':pose['horizontal_fov_degrees'],'review':'camera-review/proposed-front.json','supersedes':'Initial low 110mm instrument-only camera, archived under artifacts/initial-camera-fit','landmarks':old.get('landmarks',[])})
# Recompute diagnostic projections for the original anchor set, not an optimization objective.
loc=cfg['location_m'];target=cfg['target_m'];f=[target[i]-loc[i] for i in range(3)];d=math.sqrt(sum(x*x for x in f));f=[x/d for x in f]
r=[f[1],-f[0],0];d=math.sqrt(sum(x*x for x in r));r=[x/d for x in r];u=[r[1]*f[2]-r[2]*f[1],r[2]*f[0]-r[0]*f[2],r[0]*f[1]-r[1]*f[0]]
def dot(a,b):return sum(x*y for x,y in zip(a,b))
w,h=cfg['resolution']
for p in cfg['landmarks']:
 v=[p['world_m'][i]-loc[i] for i in range(3)];k=cfg['lens_mm']*w/(36*dot(v,f));q=[w*.5+dot(v,r)*k,h*.5-dot(v,u)*k+cfg['shift_y']*w]
 p['projected_px']=q;p['error_px']=math.dist(q,p['photo_px'])
cfg['anchor_rms_px']=math.sqrt(sum(p['weight']*p['error_px']**2 for p in cfg['landmarks'])/sum(p['weight'] for p in cfg['landmarks']))
doc['cameras']['front']=cfg
(HERE/'camera-fit.json').write_text(json.dumps(doc,indent=2))
print('Reviewed front camera applied; anchor RMS',cfg['anchor_rms_px'])
