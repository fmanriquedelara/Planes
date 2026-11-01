export const atmosphereGLSL = /* glsl */ `
uniform vec3 sunDirection;
uniform vec3 skyZenith;
uniform vec3 skyHorizon;
uniform vec3 sunTint;
uniform float hazeDensity;
vec3 atmosphere(vec3 ray) {
  // C1-smooth angular falloff keeps the horizon continuous while the upper
  // sky reaches a substantially deeper blue instead of retaining milky haze.
  float elevation=max(ray.y,0.0);
  float height = 1.0-exp(-elevation*elevation*32.0);
  vec3 sky = mix(skyHorizon, skyZenith, height);
  vec2 azimuth = ray.xz / max(length(ray.xz), 0.0001);
  float sunFacing = max(dot(azimuth, normalize(sunDirection.xz)), 0.0);
  float horizonGlow = exp(-ray.y*ray.y*45.0) * pow(sunFacing, 5.0);
  sky = mix(sky, sunTint * 0.65, horizonGlow * 0.65);
  float alignment = max(dot(ray, sunDirection), 0.0);
  sky += sunTint * pow(alignment, 180.0) * 0.42;
  sky += sunTint * smoothstep(0.99991, 0.99997, alignment) * 5.0;
  return sky;
}
`;

export const noiseGLSL = /* glsl */ `
float hash21(vec2 p) { return fract(sin(dot(p, vec2(127.1,311.7))) * 43758.5453); }
float noise2(vec2 p) {
  vec2 i=floor(p), f=fract(p); f=f*f*(3.0-2.0*f);
  return mix(mix(hash21(i),hash21(i+vec2(1,0)),f.x),mix(hash21(i+vec2(0,1)),hash21(i+vec2(1,1)),f.x),f.y);
}
float fbm2(vec2 p) {
  return noise2(p)*.53+noise2(p*2.03+11.3)*.27+noise2(p*4.09+21.7)*.13+noise2(p*8.13)*.07;
}
float hash31(vec3 p) { p=fract(p*.1031);p+=dot(p,p.yzx+33.33);return fract((p.x+p.y)*p.z); }
float noise3(vec3 p) {
  vec3 i=floor(p),f=fract(p); f=f*f*(3.0-2.0*f);
  return mix(mix(mix(hash31(i),hash31(i+vec3(1,0,0)),f.x),mix(hash31(i+vec3(0,1,0)),hash31(i+vec3(1,1,0)),f.x),f.y),mix(mix(hash31(i+vec3(0,0,1)),hash31(i+vec3(1,0,1)),f.x),mix(hash31(i+vec3(0,1,1)),hash31(i+vec3(1,1,1)),f.x),f.y),f.z);
}
float fbm3(vec3 p) { return noise3(p)*.57+noise3(p*2.07+17.3)*.28+noise3(p*4.13+31.7)*.15; }
`;

export const terrainVertex = /* glsl */ `
varying vec3 worldPosition;
varying vec3 worldNormal;
void main() {
  worldPosition=(modelMatrix*vec4(position,1.0)).xyz;
  worldNormal=normalize(mat3(modelMatrix)*normal);
  gl_Position=projectionMatrix*viewMatrix*vec4(worldPosition,1.0);
}
`;

export const terrainFragment = /* glsl */ `
${atmosphereGLSL}
${noiseGLSL}
varying vec3 worldPosition;
varying vec3 worldNormal;
uniform vec4 cloudShadows[12];
float riverX(float z) { return 2300.0+sin(z*.00019)*2500.0+sin(z*.00061)*420.0; }
void main() {
  vec2 p=worldPosition.xz;
  vec2 farm=mat2(.94,-.342,.342,.94)*p;
  farm+=vec2(fbm2(p*.0007),fbm2(p*.0007+7.3))*640.0;
  vec2 grid=floor(farm/430.0), field=grid;
  float nearest=10.0, second=10.0;
  for(int j=-1;j<=1;j++)for(int i=-1;i<=1;i++){
    vec2 cell=grid+vec2(float(i),float(j));
    vec2 centre=(cell+vec2(hash21(cell),hash21(cell+21.7))*.8+.1)*430.0;
    float d=length((farm-centre)/430.0);
    if(d<nearest){second=nearest;nearest=d;field=cell;}else{second=min(second,d);}
  }
  float crop=hash21(field);
  vec3 green=mix(vec3(.022,.065,.014),vec3(.10,.17,.035),crop);
  vec3 earth=mix(vec3(.13,.067,.018),vec3(.30,.20,.065),hash21(field+8.4));
  vec3 colour=mix(green,earth,smoothstep(.46,.68,crop));
  float soilFilter=1.0-smoothstep(.45,1.6,length(fwidth(p*.018)));
  float fineFilter=1.0-smoothstep(.4,1.4,length(fwidth(p*.075)));
  float soil=fbm2(p*.018+crop*13.0);
  float growth=fbm2(p*.003+vec2(crop*7.0));
  colour*=mix(.78,1.22,growth)*mix(1.0,.76+soil*.48,soilFilter);
  colour*=1.0+(noise2(p*.075)-.5)*.16*fineFilter;
  float ridge=1.0-normalize(worldNormal).y;
  float forest=smoothstep(.47,.64,fbm2(p*.00065)+ridge*.8);
  float canopyFilter=1.0-smoothstep(.5,2.0,length(fwidth(p*.055)));
  float canopy=mix(.5,noise2(p*.055),canopyFilter);
  colour=mix(colour,vec3(.012,.041,.013)*(.65+canopy*.7),forest);
  float border=(second-nearest)*430.0;
  float borderAA=max(fwidth(border),1.0);
  float hedgeWidth=2.0+hash21(field+31.9)*4.0;
  colour=mix(vec3(.021,.047,.014),colour,smoothstep(.6,hedgeWidth+borderAA,border));
  float cropDirection=crop*6.283;
  float cropPhase=dot(farm,vec2(cos(cropDirection),sin(cropDirection)))*.14;
  float aa=max(fwidth(cropPhase),.15);
  float furrow=sin(cropPhase)*.5+.5;
  colour*=1.0+(furrow-.5)*.09*(1.0-smoothstep(.2,1.5,aa));
  float road=abs(p.x+1500.0+sin(p.y*.00027)*1100.0);
  float road2=abs(p.y+8500.0+sin(p.x*.00033)*1300.0);
  float roadMask=1.0-smoothstep(7.0,15.0+fwidth(road),min(road,road2));
  colour=mix(colour,vec3(.26,.22,.16),roadMask);
  float riverDistance=abs(p.x-riverX(p.y));
  float riverWidth=95.0+45.0*sin(p.y*.0004);
  float river=1.0-smoothstep(riverWidth,riverWidth+30.0,riverDistance);
  vec3 viewDirection=normalize(cameraPosition-worldPosition);
  vec2 canopySlope=vec2(noise2(p*.055+vec2(.4,0))-canopy,noise2(p*.055+vec2(0,.4))-canopy);
  vec3 normal=normalize(worldNormal+vec3(-canopySlope.x,0.0,-canopySlope.y)*forest*.9*canopyFilter);
  float diffuse=max(dot(normal,sunDirection),0.0);
  float shadow=1.0-forest*(1.0-canopy)*.30;
  vec2 shadowAxis=normalize(sunDirection.xz);
  float cloudShade=0.0;
  float shadowBreakup=.85+noise2(p*.00065)*.15;
  for(int i=0;i<12;i++){
    vec2 q=(p-cloudShadows[i].xy)/cloudShadows[i].z;
    vec2 stretched=vec2(dot(q,shadowAxis)*.65,dot(q,vec2(-shadowAxis.y,shadowAxis.x)));
    float bankShadow=(1.0-smoothstep(.45,1.4,length(stretched)))*cloudShadows[i].w*shadowBreakup;
    cloudShade=max(cloudShade,bankShadow);
  }
  vec3 light=vec3(.13,.18,.22)+sunTint*(diffuse*1.3)*shadow*(1.0-cloudShade);
  colour*=light;
  colour=mix(colour,colour*vec3(.94,.98,1.035),cloudShade);
  vec3 reflection=atmosphere(reflect(-viewDirection,vec3(0,1,0)));
  float fresnel=.035+.965*pow(1.0-max(viewDirection.y,0.0),5.0);
  vec3 water=mix(vec3(.025,.095,.105),reflection,fresnel*.85+.12);
  float glint=pow(max(dot(normalize(viewDirection+sunDirection),vec3(0,1,0)),0.0),220.0);
  water+=sunTint*glint*1.8;
  colour=mix(colour,water,river);
  float distanceToEye=distance(cameraPosition,worldPosition);
  float haze=1.0-exp(-max(distanceToEye-1500.0,0.0)*hazeDensity);
  haze=max(haze,smoothstep(33000.0,54000.0,distanceToEye));
  colour=mix(colour,atmosphere(normalize(worldPosition-cameraPosition)),haze);
  gl_FragColor=vec4(colour,1.0);
  #include <tonemapping_fragment>
  #include <colorspace_fragment>
}
`;

export const oceanFragment = /* glsl */ `
${atmosphereGLSL}
varying vec3 worldPosition;
varying vec3 worldNormal;
uniform float time;
void main(){
  vec2 p=worldPosition.xz;
  vec3 viewDirection=normalize(cameraPosition-worldPosition);
  float eyeDistance=distance(cameraPosition,worldPosition);
  float phase=dot(p,vec2(.023,.017))+sin(p.x*.0008)*2.0+time*.7;
  float waveFilter=1.0-smoothstep(.4,1.6,fwidth(phase));
  vec3 normal=normalize(vec3(cos(phase)*.025*waveFilter,1.0,sin(phase*.73)*.018*waveFilter));
  vec3 reflection=atmosphere(reflect(-viewDirection,normal));
  float fresnel=.035+.965*pow(1.0-max(dot(viewDirection,normal),0.0),5.0);
  vec3 colour=mix(vec3(.018,.075,.092),reflection,.15+fresnel*.8);
  float glint=pow(max(dot(normal,normalize(viewDirection+sunDirection)),0.0),320.0);
  colour+=sunTint*glint*2.3;
  float haze=max(1.0-exp(-max(eyeDistance-1500.0,0.0)*hazeDensity),smoothstep(33000.0,54000.0,eyeDistance));
  colour=mix(colour,atmosphere(normalize(worldPosition-cameraPosition)),haze);
  gl_FragColor=vec4(colour,1.0);
  #include <tonemapping_fragment>
  #include <colorspace_fragment>
}
`;

export const cloudVertex = /* glsl */ `
varying vec3 worldPosition;
void main(){ worldPosition=(modelMatrix*vec4(position,1.0)).xyz;gl_Position=projectionMatrix*viewMatrix*vec4(worldPosition,1.0); }
`;

export const cloudFragment = /* glsl */ `
${atmosphereGLSL}
${noiseGLSL}
varying vec3 worldPosition;
uniform vec3 boxCentre;
uniform vec3 boxHalfSize;
uniform vec4 lobes[7];
uniform float time;
uniform float marchSteps;
uniform float coverStrength;
uniform float sampleQuality;
float density(vec3 world){
  vec3 p=world-boxCentre;
  p.x+=time*4.0;
  vec3 warp=vec3(noise3(p*.0015),noise3(p*.0015+17.0),noise3(p*.0015+41.0));
  p+=(warp-.5)*380.0;
  float shape=-1.0;
  for(int i=0;i<7;i++){
    float seed=hash31(lobes[i].xyz*.003);
    vec3 aspect=vec3(.72+seed*.48,.42+hash31(lobes[i].xyz*.007)*.38,.64+hash31(lobes[i].xyz*.011)*.5);
    vec3 q=(p-lobes[i].xyz)/(lobes[i].w*aspect);
    shape=max(shape,1.0-length(q));
  }
  if(shape<=0.0)return 0.0;
  float erosion=fbm3(p*.0018)*.16;
  if(sampleQuality<.5){
    // Preserve mean cloud mass while dropping fine erosion noise octaves.
    erosion+=.1125;
  }else{
    erosion+=fbm3(p*.004)*.17+noise3(p*.012)*.055;
  }
  return smoothstep(.0,.4,shape-erosion);
}
void main(){
  vec3 ray=normalize(worldPosition-cameraPosition);
  vec3 inverseRay=sign(ray+vec3(.000001))/max(abs(ray),vec3(.000001));
  vec3 a=(boxCentre-boxHalfSize-cameraPosition)*inverseRay;
  vec3 b=(boxCentre+boxHalfSize-cameraPosition)*inverseRay;
  vec3 nearT=min(a,b),farT=max(a,b);
  float entry=max(max(nearT.x,nearT.y),max(nearT.z,0.0));
  float end=min(min(farT.x,farT.y),farT.z);
  if(end<=entry)discard;
  float stepSize=(end-entry)/marchSteps;
  float transmittance=1.0;
  vec3 accumulated=vec3(0);
  for(int i=0;i<80;i++){
    if(float(i)>=marchSteps)break;
    float t=entry+(float(i)+.5)*stepSize;
    vec3 p=cameraPosition+ray*t;
    float d=density(p)*coverStrength;
    if(d>.003){
      float optical;
      if(sampleQuality<.5){
        optical=density(p+sunDirection*350.0)*2.3;
      }else if(sampleQuality<.8){
        optical=density(p+sunDirection*150.0)*.7+density(p+sunDirection*600.0)*1.7;
      }else{
        optical=density(p+sunDirection*110.0)*.45+density(p+sunDirection*350.0)+density(p+sunDirection*750.0)*1.5;
      }
      float sunLight=exp(-optical*2.1);
      float height=clamp((p.y-boxCentre.y+boxHalfSize.y)/(boxHalfSize.y*2.0),0.0,1.0);
      vec3 ambient=mix(vec3(.16,.21,.28),vec3(.27,.32,.39),height);
      float multipleScatter=exp(-optical*.35)*.17;
      vec3 lit=ambient+sunTint*(sunLight*.73+multipleScatter+.09);
      lit=mix(lit,atmosphere(ray),1.0-exp(-t*hazeDensity));
      float alpha=1.0-exp(-d*stepSize*.005);
      accumulated+=transmittance*alpha*lit;
      transmittance*=1.0-alpha;
    }
    if(transmittance<.015)break;
  }
  float alpha=1.0-transmittance;
  if(alpha<.005)discard;
  gl_FragColor=vec4(accumulated/max(alpha,.0001),alpha);
  #include <tonemapping_fragment>
  #include <colorspace_fragment>
}
`;
