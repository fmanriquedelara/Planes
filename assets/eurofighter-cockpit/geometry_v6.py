from mathutils import Matrix
"""Geometry correction to the user's frontal and oblique cockpit photographs.
Executed by build_cockpit.py; dimensions are photo-informed fit estimates.
"""
def prism(name,outline,xfront,depth,m=graphite,edge=.002):
 if sum(a[0]*b[1]-b[0]*a[1] for a,b in zip(outline,outline[1:]+outline[:1]))<0:outline=list(reversed(outline))
 n=len(outline);v=[(xfront,y,z) for y,z in outline]+[(xfront+depth,y,z) for y,z in outline]
 f=[tuple(range(n-1,-1,-1)),tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
 return bevel(mesh(name,v,f,m),edge,3)
def smoothpath(name,pts,r,m=graphite):
 c=bpy.data.curves.new(name,'CURVE');c.dimensions='3D';c.resolution_u=10;c.bevel_depth=r;c.bevel_resolution=3
 sp=c.splines.new('BEZIER');sp.bezier_points.add(len(pts)-1)
 for b,p in zip(sp.bezier_points,pts):b.co=p;b.handle_left_type='AUTO';b.handle_right_type='AUTO'
 o=bpy.data.objects.new(name,c);scene.collection.objects.link(o);assign(o,m);return o
def top_prism(name,outline,z,height,m=panel,edge=.003):
 if sum(a[0]*b[1]-b[0]*a[1] for a,b in zip(outline,outline[1:]+outline[:1]))<0:outline=list(reversed(outline))
 n=len(outline);v=[(x,y,z) for x,y in outline]+[(x,y,z+height) for x,y in outline]
 f=[tuple(range(n-1,-1,-1)),tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
 return bevel(mesh(name,v,f,m),edge,3)
def soft_outline(name,outline,z,height,m=graphite):
 o=top_prism(name,outline,z,height,m,.02)
 return o
def hinge(x,y,z):
 cylinder('Canopy hinge trunnion',(x,y,z),.024,.045,panel,(0,1,0),40)
 cylinder('Canopy hinge end cap',(x,y+(.025 if y>0 else -.025),z),.017,.004,metal,(0,1,0),32)
def top_toggle(x,y,z,guard=False):
 cylinder('Switch locking nut',(x,y,z),.0055,.004,metal,vertices=6)
 smoothpath('Toggle lever',[(x,y,z+.002),(x+.006,y,z+.024)],.002,metal)
 if guard:
  box('Toggle guard cover',(x-.005,y,z+.018),(.025,.019,.010),red,.003)
def top_knob(x,y,z,r=.009):
 cylinder('Console rotary selector',(x,y,z+.010),r,.022,graphite,vertices=24)
 box('Console dial index',(x,y,z+.022),(.009,.0012,.0007),metal,0)
def front_plate(name,y,z,w,h,x=.827,m=panel):return box(name,(x,y,z),(.018,w,h),m,.003)
# Narrower, tapered shell and low side consoles. Source envelope retained.
box('Cockpit floor',(.1,0,-.97),(2.4,.94,.035),graphite,.012)
box('Deep front cockpit bulkhead',(1.17,0,-.76),(.045,.84,.66),rubber,.006)
for side in (-1,1):
 box('Closed lower cockpit side enclosure',(.30,side*.465,-.73),(1.80,.035,.52),graphite,.004)
 for z in (-.84,-.77,-.70):box('Footwell bulkhead stiffener',(1.138,side*.21,z),(.025,.18,.012),graphite,.003)
for side in (-1,1):
 # Faceted shell is outside the pilot-facing panels; rails slope and flare.
 vv=[(-1.0,side*.49,-.81),(-1.0,side*.47,-.43),(.35,side*.48,-.37),(1.10,side*.46,-.30),(1.10,side*.43,-.86)]
 o=mesh('Tub sidewall',vv,[(0,1,2,3,4)],graphite);o.modifiers.new('Tub thickness','SOLIDIFY').thickness=.025
 # Thin horizontal sills, not large elevated slab/guard rails.
 smoothpath('Canopy sill rubber seal',[(-.96,side*.47,-.42),(-.45,side*.475,-.40),(.20,side*.48,-.37),(.72,side*.48,-.32),(1.08,side*.46,-.30)],.008,rubber)
 o=top_prism('Canopy side sill',[(-1.0,side*.445),(-1.0,side*.50),(.65,side*.52),(1.1,side*.48),(1.1,side*.435),(.65,side*.455)],-.43,.025,panel,.005)
 # Width and console top height vary longitudinally.
 console_parts_before=set(scene.objects)
 outline=[(-.86,side*.47),(-.86,side*.26),(-.30,side*.26),(.12,side*.28),(.43,side*.32),(.55,side*.46)]
 base=top_prism('Console structural base',outline,-.79,.15,panel,.006)
 for vtx in base.data.vertices:
  if vtx.co.z>-.65:vtx.co.z+=max(0,vtx.co.x)*.12
 # Console panels are distinct asymmetric equipment groups.
 layouts=([(-.72,.24,.20,'COMMUNICATION'),(-.43,.26,.20,'LIGHTING'),(-.10,.29,.20,'ENGINE START'),(.23,.25,.17,'FUEL')] if side==1 else [(-.74,.18,.20,'SECURE DATA'),(-.50,.26,.21,'OXYGEN'),(-.18,.28,.20,'ELECTRICAL'),(.14,.19,.18,'HYDRAULIC'),(.36,.18,.15,'RADIO')])
 for j,(cx,dx,dy,title) in enumerate(layouts):
  cy=side*(.35 if cx<.1 else .385);z=-.64+max(0,cx)*.12
  pts=[(cx-dx/2,cy-dy/2),(cx+dx/2,cy-dy/2),(cx+dx/2,cy+dy/2),(cx-dx/2,cy+dy/2)]
  top_prism('Shaped '+title+' panel',pts,z,.012,panel if j%3!=1 else graphite,.003)
  for xx in (-dx*.42,dx*.42):
   for yy in (-dy*.42,dy*.42):screw(cx+xx,cy+yy,z+.014,(0,0,1),.0024)
  label(title,cx+dx*.36,cy,z+.014,.006,True)
  if side==1 and j==2:continue # occupied by throttle sector, intentionally sparse
  nr,nc=([(3,3),(2,3),(1,1),(3,2)] if side==1 else [(2,3),(3,4),(3,4),(2,3),(3,3)])[j]
  for rr in range(nr):
   for cc in range(nc):
    xx=cx-dx*.28+rr*dx*.45/max(1,nr-1); yy=cy-dy*.28+cc*dy*.56/max(1,nc-1)
    if (rr+cc+j)%3==0:top_knob(xx,yy,z+.015,.008+(j%2)*.002)
    else:top_toggle(xx,yy,z+.015,guard=(side==-1 and j==2 and cc==0 and rr==0))
    label('AUTO' if cc%2 else 'OFF',xx-.018,yy,z+.015,.0045,True)
  if side==-1 and j==1:
   box('Electrical guarded annunciator',(cx+.07,cy+.06,z+.027),(.033,.018,.018),red,.003)
  if j==3:
   box('Warning-striped switch plate',(cx,cy+.04,z+.015),(.037,.037,.002),yellow,.001)
   for kk in range(3):
    ob=box('Diagonal caution stripe',(cx-.012+kk*.012,cy+.04,z+.017),(.005,.036,.001),graphite,0);ob.rotation_euler.z=.4
   top_knob(cx,cy+.04,z+.019,.008)
 # Compact longitudinal equipment run while retaining dense varied groups.
 for ob in set(scene.objects)-console_parts_before:
  if ob.type=='MESH':
   ob.data.transform(ob.matrix_world);ob.matrix_world=Matrix.Identity(4)
   for vtx in ob.data.vertices:vtx.co.x=vtx.co.x*.60+.22
  elif ob.type=='CURVE':
   for sp in ob.data.splines:
    if sp.type=='BEZIER':
     for pt in sp.bezier_points:
      pt.co.x=pt.co.x*.60+.22;pt.handle_left.x=pt.handle_left.x*.60+.22;pt.handle_right.x=pt.handle_right.x*.60+.22
 # Front shoulder steeply drops from fascia to console; distinct side footwell.
 shoulder=[(side*.315,-.46),(side*.445,-.46),(side*.46,-.70),(side*.30,-.70)]
 ob=prism('Sloping forward side-console shoulder',shoulder,.54,.065,panel,.007)
 for vtx in ob.data.vertices:vtx.co.x+=-.02+1.1*(vtx.co.z+.70)
 cylinder('Shoulder circular ventilation cover',(.65,side*.385,-.56),.028,.011,graphite,(-1,0,0),48)
 for k in range(4):box('Vent grille',(.643,side*.385,-.573+k*.009),(.001,.039,.002),rubber,0)
 if side==1:
  for yy,zz in [(.352,-.51),(.406,-.51),(.352,-.61),(.406,-.61)]:
   xx=.52+1.1*(zz+.70)-.010
   knob(xx,yy,zz,.008)
   label('AUTO' if yy<.38 else 'OFF',xx-.015,yy,zz-.014,.0045)
  box('Left shoulder safety plate',(.68,.385,-.54),(.004,.037,.033),yellow,.001)
  knob(.672,.385,-.54,.008)
 else:
  for k in range(4):
   zz=-.495-k*.021;xx=.52+1.1*(zz+.70)-.010
   label(['FLIGHT CONTROL','NORM','AUTO','TEST'][k],xx,-.382,zz,.005)
  for yy in (-.35,-.41):knob(.612,yy,-.62,.008)
 for k in range(3):top_toggle(.39-k*.045,side*.36,-.600+k*.004)
 # Black inner walls form actual deep leg wells rather than flat black cards.
 box('Footwell outer wall',(.66,side*.315,-.76),(.35,.018,.29),graphite,.003)
 box('Rudder pedal',(.94,side*.215,-.87),(.11,.14,.019),metal,.003)
 for k in range(5):box('Pedal rib',(.90+k*.018,side*.215,-.858),(.005,.12,.005),rubber,.001)
# Continuous fascia: compact three-bezel row and true open lower leg bays.
instrument_parts_before=set(scene.objects)
outer=[(-.425,-.327),(-.404,-.271),(-.34,-.222),(-.27,-.18),(-.17,-.152),(-.11,-.16),(.11,-.16),(.17,-.152),(.27,-.18),(.34,-.222),(.404,-.271),(.425,-.327),(.414,-.548),(.35,-.586),(.13,-.586),(.095,-.626),(-.095,-.626),(-.13,-.586),(-.35,-.586),(-.414,-.548)]
prism('Continuous curved instrument fascia',outer,.851,.045,graphite,.004)
# Gray support flange follows the actual stepped lower row edge.
lower=[(-.358,-.492),(-.126,-.492),(-.112,-.546),(.112,-.546),(.126,-.492),(.358,-.492),(.358,-.574),(.125,-.574),(.100,-.625),(-.100,-.625),(-.125,-.574),(-.358,-.574)]
prism('Stepped grey instrument support fascia',lower,.828,.025,panel,.005)
# One smooth, low eyebrow over the curved panel contour. No floating tube rails.
curve=[(-.425,-.319),(-.392,-.264),(-.325,-.213),(-.24,-.171),(-.16,-.151),(0,-.160),(.16,-.151),(.24,-.171),(.325,-.213),(.392,-.264),(.425,-.319)]
v=[];f=[]
for j,(y,z) in enumerate(curve):
 for depth in [0,.05,.12,.21]:v.append((.842+depth,y,z+.012-.12*depth))
for j in range(len(curve)-1):
 for k in range(3):a=j*4+k;f.append((a,a+1,a+5,a+4))
o=mesh('Continuous curved glare shield skin',v,f,graphite);o.modifiers.new('Coaming padded thickness','SOLIDIFY').thickness=.012;bevel(o,.006,3)
for p in o.data.polygons:p.use_smooth=True
smoothpath('Fine rounded coaming front edge',[(.834,y,z+.008) for y,z in curve],.004,rubber)
# Thin cast MHDD plates, each 230x240mm. Center drops 53mm.
for i,(y,z) in enumerate([(.235,-.410),(0,-.463),(-.235,-.410)]):
 x=.816
 bevel(prism('Thin MHDD perimeter bezel',[(y-.115,z-.120),(y+.115,z-.120),(y+.115,z+.116),(y+.106,z+.120),(y-.106,z+.120),(y-.115,z+.116)],x,.025,panel,.002),.002,2)
 box('MHDD screen rebate',(x-.003,y,z+.008),(.006,.174,.179),rubber,.004)
 face('MHDD original display',x-.007,y,z+.008,.160,.165,display,[(i/3,0),((i+1)/3,0),((i+1)/3,1),(i/3,1)])
 for k in range(6):
  zz=z+.082-k*.031
  front_button(x-.004,y+.101,zz,.014,.021)
  front_button(x-.004,y-.101,zz,.014,.021)
 for k in range(6):front_button(x-.004,y+.076-k*.0304,z-.102,.022,.016)
 for yy in (-.104,.104):
  for zz in (-.11,.11):screw(x-.009,y+yy,z+zz,r=.0026)
 knob(x-.012,y+.098,z-.115,.007);knob(x-.012,y-.098,z-.115,.007)
 label('BRT',x-.015,y+.067,z-.115,.004);label('CONT',x-.015,y-.067,z-.115,.004)
# Glareshield keypad follows the curved left shoulder, not a separate huge box.
for row in range(5):
 for col in range(8):
  y=.12+col*.030;z=-.175-row*.022
  if z>-.151-.80*(y-.16):continue
  front_button(.843,y,z,.021,.013,['NAV','COM','IFF','ALT','HDG','SYS','MAP','DATA'][col])
# Narrow inclined outboard data entry panel.
de=prism('Outboard data entry housing',[(.365,-.319),(.414,-.279),(.440,-.349),(.437,-.529),(.369,-.529)],.820,.035,graphite,.004)
face('Data entry green screen',.814,.402,-.367,.046,.038,display,[(0,0),(.2,0),(.2,.1),(0,.1)])
for row in range(6):
 for col in range(3):front_button(.812,.381+col*.021,-.410-row*.020,.014,.013,str((row*3+col)%10))
# Standby attitude instrument, visible blue/brown face set into upper right.
box('Standby square surround',(.832,-.214,-.237),(.027,.087,.088),graphite,.004)
cylinder('Standby instrument ring',(.811,-.214,-.237),.033,.007,metal,(-1,0,0),64)
cylinder('Standby instrument dark face',(.806,-.214,-.237),.029,.003,rubber,(-1,0,0),64)
face('Standby blue brown attitude ball',.803,-.214,-.237,.052,.052,display,[(1130/1536,1-470/512),(1470/1536,1-470/512),(1470/1536,1-130/512),(1130/1536,1-130/512)])
for k in range(24):
 a=k*math.tau/24; yy=-.214+math.sin(a)*.026;zz=-.237+math.cos(a)*.026
 ob=box('Standby tick',(.803,yy,zz),(.0005,.001,.003 if k%6==0 else .0015),metal,0);ob.rotation_euler.x=-a
tube('Standby horizon line',[(.801,-.235,-.237),(.801,-.193,-.237)],.0007,metal,1)
for col in range(3):front_button(.842,-.28-col*.035,-.276,.018,.014)
# Compact hanging HUD assembly. Top button strip, inset central optical/control
# recess, tapering lower control fascia, separate open curved projector hood.
prism('HUD shallow five-window top bar',[(-.132,-.191),(.132,-.191),(.132,-.225),(-.132,-.225)],.724,.044,graphite,.003)
optics=mat('EF_ProjectorOptics',(.014,.023,.026),.18,.18)
hud_display=texmat('EF_HUDControlDisplay','hud-controls.png',emit=.12)
for i in range(5):
 yy=(2-i)*.038
 box('HUD fine key perimeter',(.719,yy,-.208),(.003,.031,.027),metal,.0012)
 box('HUD recessed key glazing',(.7165,yy,-.208),(.002,.0275,.0235),optics,.001)
 label(['LOCK','HMD','DCLT','RDR','FLIR'][i],.714,yy,-.208,.0045)
for yy in (-.120,.120):screw(.718,yy,-.208,r=.0021)
prism('HUD tapered hanging control fascia',[(-.121,-.222),(.121,-.222),(.112,-.288),(.088,-.338),(.062,-.354),(-.062,-.354),(-.088,-.338),(-.112,-.288)],.744,.046,graphite,.003)
box('HUD recessed central glass display',(.739,0,-.260),(.008,.112,.067),rubber,.002)
box('HUD inner display frame',(.735,0,-.260),(.002,.104,.059),metal,.001)
face('HUD faint control screen',.733,0,-.260,.099,.054,hud_display,[(0,0),(1,0),(1,1),(0,1)])
for side in (-1,1):
 for k in range(3):
  zz=-.241-k*.023
  box('HUD side key fine rim',(.736,side*.102,zz),(.003,.020,.010),metal,.0008)
  box('HUD inset side key',(.733,side*.102,zz),(.002,.017,.007),graphite,.0007)
  box('HUD side key cast step',(.746,side*.103,zz-.007),(.015,.024,.003),graphite,.0007)
 knob(.727,side*.069,-.323,.009)
 cylinder('HUD lower rotary',(.731,side*.032,-.344),.007,.011,graphite,(-1,0,0),24)
 label('BRT' if side==1 else 'CONT',.721,side*.064,-.309,.0045)
 for zz in (-.301,-.311,-.321):box('HUD lower casing vent slot',(.738,side*.102,zz),(.002,.013,.0022),rubber,.0004)
 screw(.736,side*.087,-.302,r=.0018)
# Thin mechanical side cheeks taper backwards around projector well.
for side in (-1,1):
 vv=[(.764,side*.122,-.215),(.922,side*.143,-.181),(.967,side*.127,-.238),(.862,side*.106,-.310),(.778,side*.101,-.295)]
 ob=mesh('HUD tapered side cheek',vv,[(0,1,2,3,4)],graphite);ob.modifiers.new('Cast cheek thickness','SOLIDIFY').thickness=.008;bevel(ob,.003,3)
 cylinder('HUD pivot outer housing',(.764,side*.143,-.211),.014,.024,graphite,(0,1,0),40)
 cylinder('HUD pivot machined cap',(.764,side*.157,-.211),.0105,.004,metal,(0,1,0),32)
 cylinder('HUD pivot central bolt',(.764,side*.160,-.211),.0045,.003,graphite,(0,1,0),8)
# Layered optical tray visible behind the five-window strip. The new close-up
# shows a shallow polygonal optic, cast lip, stepped rear housing and screws.
tray=[(.785,-.105),(.812,-.130),(.955,-.130),(1.015,-.085),(1.015,.085),(.955,.130),(.812,.130),(.785,.105)]
top_prism('HUD cast optical tray base',tray,-.194,.014,graphite,.003)
inner=[(.801,-.099),(.821,-.113),(.947,-.113),(.992,-.078),(.992,.078),(.947,.113),(.821,.113),(.801,.099)]
top_prism('HUD optical tray inset gasket',inner,-.180,.003,rubber,.001)
optic=[(.810,-.090),(.831,-.102),(.945,-.102),(.981,-.071),(.981,.071),(.945,.102),(.831,.102),(.810,.090)]
top_prism('HUD horizontal projector optic',optic,-.176,.002,optics,.001)
rim=[(x,y,-.176) for x,y in tray];tube('HUD raised optical tray perimeter',rim+[rim[0]],.0024,graphite,2)
# Short corner lips, stepped rear casting and inset front screw strip.
box('HUD optical tray front retaining strip',(.791,0,-.173),(.013,.183,.006),metal,.001)
for yy in [-.075,-.0375,0,.0375,.075]:screw(.790,yy,-.169,(0,0,1),.0019)
for j in range(3):box('HUD rear stepped optical casing',(.987+j*.011,0,-.177-j*.006),(.015,.157-j*.012,.012),graphite,.0015)
for side in (-1,1):
 box('HUD optical tray corner fastening lug',(.816,side*.119,-.171),(.024,.014,.010),graphite,.002)
 screw(.816,side*.119,-.165,(0,0,1),.0022)
 smoothpath('HUD short side cable',[ (.80,side*.128,-.181),(.845,side*.140,-.178),(.89,side*.139,-.187)],.0022,rubber)
# Revised by the user's day close-up: continuously curved oval upper contour,
# narrowing lower bowl, without the old flattened shield plateau.
def catmull_closed(points,steps=6):
 out=[];n=len(points)
 for i in range(n):
  p0,p1,p2,p3=[Vector(points[k%n]) for k in (i-1,i,i+1,i+2)]
  for j in range(steps):
   t=j/steps;out.append(tuple(.5*((2*p1)+(-p0+p2)*t+(2*p0-5*p1+4*p2-p3)*t*t+(-p0+3*p1-3*p2+p3)*t*t*t)))
 return out
hp=[]
for k in range(128):
 a=k*math.tau/128;y=.174*math.sin(a)*(1-.10*max(0,-math.cos(a)));z=-.017+.130*math.cos(a);hp.append((.924+.25*(z+.02),y,z))
mesh('HUD continuous oval optical combiner',hp,[tuple(range(len(hp)))],glass)
upper=[];lower=[]
for k in range(65):
 a=-math.pi/2+k*math.pi/64;y=.174*math.sin(a);z=-.017+.130*math.cos(a);upper.append((.924+.25*(z+.02),y,z))
 a=math.pi/2+k*math.pi/64;y=.174*math.sin(a)*(1-.10*max(0,-math.cos(a)));z=-.017+.130*math.cos(a);lower.append((.924+.25*(z+.02),y,z))
tube('HUD fine upper optical edge',upper,.00065,graphite,1)
tube('HUD thicker lower optical edge',lower,.0017,metal,2)
for side in (-1,1):
 path=[(.765,side*.132,-.208),(.785,side*.132,-.174),(.802,side*.137,-.153),(.839,side*.163,-.114),(.886,side*.182,-.049),(.929,side*.172,.014)]
 widths=[.014,.012,.010,.009,.010,.014];depths=[.016,.014,.012,.011,.012,.015];v=[];f=[];band=[]
 for i,p in enumerate(path):
  tangent=(Vector(path[min(len(path)-1,i+1)])-Vector(path[max(0,i-1)])).normalized();width_axis=tangent.cross(Vector((1,0,0))).normalized();depth_axis=width_axis.cross(tangent).normalized()
  if depth_axis.x<0:depth_axis=-depth_axis
  for w,d in [(-1,-1),(1,-1),(1,1),(-1,1)]:v.append(tuple(Vector(p)+width_axis*widths[i]*w*.5+depth_axis*depths[i]*d*.5))
  for w in (-1,1):band.append(tuple(Vector(p)+width_axis*widths[i]*w*.23-depth_axis*(depths[i]*.5+.0003)))
 for i in range(len(path)-1):
  for k in range(4):f.append((i*4+k,i*4+(k+1)%4,(i+1)*4+(k+1)%4,(i+1)*4+k))
 f.extend([(3,2,1,0),(20,21,22,23)]);bevel(mesh('HUD kinked tapered support bracket',v,f,graphite),.0011,3)
 mesh('HUD bracket lighter inner face',band,[(i*2,i*2+1,i*2+3,i*2+2) for i in range(len(path)-1)],panel)
 for finger in (-1,1):
  yy=side*.171+finger*.0045
  prism('HUD split upper optical clamp',[(yy-.003,-.010),(yy+.003,-.010),(yy+.004,.033),(yy-.004,.036)],.922,.019,graphite,.0015)
 box('HUD clamp upper bridge',(.932,side*.171,.033),(.019,.017,.008),graphite,.0015)
 screw(.919,side*.171,.025,r=.0017)
 screw(.755,side*.131,-.208,r=.0025)
# Smooth canopy arch and sculpted pivot feet. Keep overall envelope but no
# floating rectangular endpoints or heavy bolt spheres.
for ob in set(scene.objects)-instrument_parts_before:ob.location.z+=.10
canopy_bow_before=set(scene.objects)
arch=[];steps=100
control=[(.45,-.46),(.50,-.32),(.51,-.16),(.48,.02),(.38,.18),(.20,.28),(0,.315),(-.20,.28),(-.38,.18),(-.48,.02),(-.51,-.16),(-.50,-.32),(-.45,-.46)]
for i in range(steps+1):
 u=i/steps*(len(control)-1);seg=min(int(u),len(control)-2);t=u-seg
 p0,p1,p2,p3=[Vector(control[max(0,min(len(control)-1,k))]) for k in (seg-1,seg,seg+1,seg+2)]
 y,z=.5*((2*p1)+(-p0+p2)*t+(2*p0-5*p1+4*p2-p3)*t*t+(-p0+3*p1-3*p2+p3)*t*t*t)
 arch.append((.88+.05*max(0,min(1,(z+.46)/.46)),y,z))
v=[];f=[]
for i,(x,y,z) in enumerate(arch):
 delta=Vector(arch[min(steps,i+1)])-Vector(arch[max(0,i-1)])
 radial=Vector((0,delta.z,-delta.y)).normalized()
 for dx,rr in [(-.023,-.021),(.023,-.021),(.023,.021),(-.023,.021)]:v.append((x+dx,y+radial.y*rr,z+radial.z*rr))
for i in range(steps):
 for k in range(4):f.append((i*4+k,i*4+(k+1)%4,(i+1)*4+(k+1)%4,(i+1)*4+k))
f.extend([(3,2,1,0),(steps*4,steps*4+1,steps*4+2,steps*4+3)])
ob=bevel(mesh('Smooth windscreen structural bow',v,f,graphite),.003,3)
for p in ob.data.polygons:p.use_smooth=True
smoothpath('Canopy bow rubber lip',[(x-.019,y*.967,-.46+(z+.46)*.973) for x,y,z in arch],.0045,rubber)
for k in range(4,steps,5):x,y,z=arch[k];screw(x-.026,y,z,r=.0022)
for side in (-1,1):
 prism('Triangular canopy attachment lug',[(side*.425,-.478),(side*.49,-.478),(side*.508,-.400),(side*.474,-.378)],.845,.095,graphite,.009)
 hinge(.82,side*.46,-.455)
 # Inner side ledge slopes down towards the seat, with small latch handles.
 smoothpath('Canopy latch lever',[(.77,side*.455,-.37),(.72,side*.435,-.38),(.68,side*.43,-.405)],.007,metal)
prism('Canopy center triangular latch',[(-.045,.270),(.045,.270),(.020,.246),(-.020,.246)],.886,.02,panel,.006)
screw(.872,0,.260,r=.003)
# Keep the opaque frame separately addressable for the cockpit visibility option.
# Material copies retain the original exterior appearance and slot-zero contract.
bow_materials={}
for bow_part in set(scene.objects)-canopy_bow_before:
 for slot_index,original in enumerate(bow_part.data.materials):
  if original.name not in bow_materials:
   copied=original.copy();copied.name='EF_CanopyBow_'+original.name.removeprefix('EF_')
   bow_materials[original.name]=copied
  bow_part.data.materials[slot_index]=bow_materials[original.name]
# Front glazing follows smooth bow; thin clear material, no rear bubble claim.
v=[];f=[]
for j in range(9):
 t=j/8
 for i in range(49):
  a=i*math.pi/48;ax,ay,az=arch[round(i*steps/48)];v.append((ax+.01+t*.65,ay*(1-.52*t),az*(1-t)+(-.38+.04*math.sin(a))*t))
for j in range(8):
 for i in range(48):k=j*49+i;f.append((k,k+1,k+50,k+49))
ob=mesh('Front windscreen glazing',v,f,glass)
for p in ob.data.polygons:p.use_smooth=True
# Tapered center pedestal: broad control plate under display narrows at boot.
pedestal_parts_before=set(scene.objects)
prism('Center pedestal control fascia',[(-.110,-.602),(.110,-.602),(.082,-.773),(.055,-.806),(-.055,-.806),(-.082,-.773)],.660,.085,panel,.006)
for row in range(4):
 for col in range(3):front_button(.650,.050-col*.050,-.633-row*.034,.020,.017)
cylinder('Pedestal guarded rotary',(.644,-.065,-.626),.016,.009,metal,(-1,0,0),32)
for k in range(4):
 a=k*math.pi/2;box('Pedestal hazard corner',(.640,-.065+math.cos(a)*.023,-.626+math.sin(a)*.023),(.002,.012,.007),yellow,.0005)
for ob in set(scene.objects)-pedestal_parts_before:
 if ob.type=='MESH':
  ob.data.transform(ob.matrix_world);ob.matrix_world=Matrix.Identity(4)
  for vtx in ob.data.vertices:
   vtx.co.x+=.14+1.1*(vtx.co.z+.6)
   vtx.co.z+=.10
# Slender column extends to stick boot, leaving leg wells genuinely open.
top_prism('Pedestal tapered floor spine',[(.30,-.075),(.30,.075),(.67,.10),(.67,-.10)],-.89,.10,graphite,.008)
stick_parts_before=set(scene.objects)
box('Stick base plinth',(.19,0,-.805),(.19,.135,.075),panel,.011)
cylinder('Stick rubber boot',(.205,0,-.737),.050,.087,rubber,vertices=48)
for j in range(5):cylinder('Stick bellows',(.205,0,-.77+j*.014),.049-j*.001,.007,graphite,vertices=40)
smoothpath('Stick curved narrow neck',[(.205,0,-.702),(.190,0,-.654),(.177,0,-.607)],.017,graphite)
# Multi-section grip loft: broader palm/head, narrow waist, angled top.
sections=[(-.646,.187,.020,.022),(-.610,.177,.024,.025),(-.566,.167,.027,.026),(-.528,.155,.034,.032),(-.503,.151,.039,.043),(-.480,.158,.031,.037)]
v=[];f=[];ns=24
for z,cx,rx,ry in sections:
 for k in range(ns):a=k*math.tau/ns;v.append((cx+rx*math.cos(a),ry*math.sin(a),z))
for j in range(len(sections)-1):
 for k in range(ns):f.append((j*ns+k,j*ns+(k+1)%ns,(j+1)*ns+(k+1)%ns,(j+1)*ns+k))
f.extend([tuple(range(ns-1,-1,-1)),tuple(range((len(sections)-1)*ns,len(sections)*ns))])
ob=mesh('Anatomical control stick grip',v,f,graphite)
for p in ob.data.polygons:p.use_smooth=True
for j in range(3):ellipsoid('Finger scallop',(.140,.021,-.561-j*.023),(.008,.022,.010),rubber)
prism('Stick face plate',[(-.030,-.488),(.035,-.488),(.033,-.529),(.010,-.558),(-.022,-.554)],.117,.012,graphite,.007)
cylinder('Stick thumb hat',(.107,.018,-.509),.012,.009,metal,(-1,0,0),8)
for yy,zz in [(-.013,-.530),(.009,-.551)]:cylinder('Stick face button',(.105,yy,zz),.0055,.005,rubber,(-1,0,0),20)
box('Stick guarded red trigger',(.14,-.041,-.494),(.018,.012,.023),red,.003)
for ob in set(scene.objects)-stick_parts_before:ob.location.x+=.32
# Twin throttle handles follow a curved sector, not long rectangular rails.
throttle_parts_before=set(scene.objects)
top_prism('Throttle curved sector',[(-.24,.28),(-.24,.43),(.065,.43),(.11,.37),(.06,.29)],-.637,.037,graphite,.010)
for yy in (.327,.382):
 smoothpath('Throttle quadrant slot',[(-.23,yy,-.592),(-.12,yy,-.579),(.02,yy,-.590)],.004,rubber)
 smoothpath('Throttle lever shaft',[(-.11,yy,-.59),(-.09,yy,-.543),(-.10,yy,-.510)],.009,metal)
 ellipsoid('Throttle rounded handgrip',(-.105,yy,-.493),(.053,.029,.031),graphite)
 cylinder('Throttle side dial',(-.11,yy+.025,-.487),.014,.009,graphite,(0,1,0),24)
for k in range(3):top_knob(-.13+k*.033,.29,-.493,.004)
for ob in set(scene.objects)-throttle_parts_before:ob.location.x+=.25
# Broad U-notched protective seat cushion wraps the stick pedestal, as in BOTH
# user photos. It is not the long narrow olive rectangle from revision 5.
seat_parts_before=set(scene.objects)
cover=mat('EF_SeatCover',(.105,.115,.125),.86)
outline=[(-.78,-.255),(-.78,.255),(-.09,.255),(.11,.205),(.13,.078),(-.04,.078),(-.07,.055),(-.07,-.055),(-.04,-.078),(.13,-.078),(.11,-.205),(-.09,-.255)]
soft_outline('Wide U-notched seat cushion',outline,-.715,.090,cover)
# Very shallow cloth loft above the padded outline gives real surface relief.
def inside2d(x,y,poly):
 odd=False
 for a,b in zip(poly,poly[1:]+poly[:1]):
  if ((a[1]>y)!=(b[1]>y)) and x<(b[0]-a[0])*(y-a[1])/(b[1]-a[1])+a[0]:odd=not odd
 return odd
v=[];f=[];nx=49;ny=31
for ix in range(nx):
 x=-.765+ix*.88/(nx-1)
 for iy in range(ny):
  y=-.240+iy*.480/(ny-1)
  bulge=.010*max(0,1-(y/.255)**2)*math.sin(math.pi*(x+.78)/.91)
  wrinkle=.0023*math.sin(x*85+y*27)*math.exp(-min(abs(y-.245),abs(y+.245))*14)
  v.append((x,y,-.623+bulge+wrinkle))
for ix in range(nx-1):
 for iy in range(ny-1):
  ids=[ix*ny+iy,(ix+1)*ny+iy,(ix+1)*ny+iy+1,ix*ny+iy+1]
  if all(inside2d(v[k][0],v[k][1],outline) for k in ids):f.append(tuple(ids))
ob=mesh('Subtle protective seat cover cloth loft',v,f,cover)
for poly in ob.data.polygons:poly.use_smooth=True
top_prism('Seat bucket under cushion',[(-.81,-.27),(-.81,.27),(.10,.24),(.12,-.24)],-.79,.06,graphite,.018)
# A few restrained seam/crease lines trace cloth tension without polygon spikes.
smoothpath('Seat front seam',[(-.74,-.235),(-.74,.235)],.001,graphite) if False else None
for side in (-1,1):
 smoothpath('Seat cover stitched side seam',[(-.74,side*.238,-.620),(-.40,side*.237,-.618),(-.10,side*.229,-.618),(.08,side*.187,-.620)],.0007,harness)
 box('Seat side guide',(-.47,side*.277,-.665),(.58,.025,.065),graphite,.007)
 # Cloth straps lie over sides, leaving the broad center cover readable.
 ob=box('Seat lap harness',(-.58,side*.216,-.600),(.16,.048,.008),harness,.003);ob.rotation_euler.z=side*.24
 box('Seat harness buckle',(-.56,side*.216,-.592),(.038,.054,.006),metal,.003)
 box('Seat black side control paddle',(.06,side*.263,-.571),(.025,.014,.17),graphite,.010)
 label('PULL',.045,side*.263,-.53,.007)
box('Seat back cushion',(-.83,0,-.345),(.10,.46,.56),fabric,.028)
box('Seat headrest',(-.88,0,.015),(.17,.27,.22),graphite,.022)
for side in (-1,1):
 box('Seat back rail',(-.91,side*.25,-.31),(.05,.031,.81),metal,.004)
 ob=box('Rear shoulder harness',(-.773,side*.10,-.34),(.007,.042,.46),harness,.004)
 # Yellow ejection/canopy markings sit at side levers, not a conspicuous ring.
 box('Emergency side handle',(.22,side*.274,-.59),(.018,.014,.12),yellow,.002)
 for j in range(5):box('Emergency handle stripe',(.209,side*.274,-.635+j*.020),(.002,.015,.007),graphite,.0004)
for ob in set(scene.objects)-seat_parts_before:
 if ob.type=='MESH':
  ob.data.transform(ob.matrix_world);ob.matrix_world=Matrix.Identity(4)
  for vtx in ob.data.vertices:vtx.co.x=vtx.co.x*.714+.517
 elif ob.type=='CURVE':
  for sp in ob.data.splines:
   if sp.type=='BEZIER':
    for pt in sp.bezier_points:
     pt.co.x=pt.co.x*.714+.517
     pt.handle_left.x=pt.handle_left.x*.714+.517
     pt.handle_right.x=pt.handle_right.x*.714+.517
# Authoritative design ratios for correspondence checks (world ratios, photo
# projection differs with camera). Camera parameters are saved by main builder.
shape_metrics={'revision':6,'display_bezel_row_span_m':.700,'outer_screen_visible_width_m':.160,'display_center_spacing_m':.235,'center_display_drop_m':.053,'hud_top_bar_width_m':.264,'combiner_width_m':.348,'combiner_height_m':.260,'seat_width_m':.510,'ratios':{'hud_to_display_row':.264/.700,'combiner_to_display_row':.348/.700,'combiner_width_to_height':.348/.260,'seat_to_display_row':.510/.700,'display_center_spacing_to_visible_screen':.235/.160},'reference':'user/front.png + user/oblique.png; approximate manual perspective landmarks, not surveyed dimensions'}
shape_metrics['revision']=7
shape_metrics['hud_combiner_profile']='Continuous curved oval top and narrower lower bowl, corrected from the user day close-up; no flat plateau'
shape_metrics['hud_upper_edge_radius_m']=.00065
shape_metrics['hud_lower_edge_radius_m']=.0017
shape_metrics['detail_pass_reference']='user/detail-pass/hud-day.png, hud-night.png, oblique.png; simulator-secondary.png secondary only'
shape_metrics['instrument_cluster_raise_m']=.10
shape_metrics['seat_and_stick_forward_correction_m']=.32
shape_metrics['console_longitudinal_scale']=.60
shape_metrics['seat_length_m']=.91*.714
shape_metrics['comparison_camera_status']='estimated inspection poses, not a solved photo calibration'
(ROOT/'shape-metrics.json').write_text(json.dumps(shape_metrics,indent=2))
