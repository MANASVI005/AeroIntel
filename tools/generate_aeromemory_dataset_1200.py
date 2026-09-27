#!/usr/bin/env python3
from __future__ import annotations

import hashlib, json, math, random, shutil
from datetime import date, timedelta
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageOps

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'datasets' / 'master_dataset_ABC'
OUT = ROOT / 'datasets' / 'dataset_E_aeromemory'

SEED = 42
NUM_AIRCRAFT = 200
INSPECTIONS_PER_AIRCRAFT = 6
EXPECTED_IMAGES = 1200
IMAGE_SIZE = (1024, 1024)
PX_PER_MM = 10.0
INTERVAL_DAYS = 30

CLASSES = {0: 'Crack', 1: 'Corrosion', 2: 'Dent', 3: 'Missing Fastener'}
SCENARIOS = [
    'crack_slow_progression','crack_fast_progression','crack_stable','crack_branching','crack_new','crack_resolved',
    'corrosion_slow_progression','corrosion_accelerating','corrosion_stable','corrosion_new','corrosion_resolved',
    'dent_size_progression','dent_depth_progression','dent_stable','dent_repair',
    'missing_fastener_new','missing_fastener_stable','missing_fastener_repaired',
    'mixed_progression','mixed_new_defects','multi_defect_stable','multi_defect_progression',
    'camera_variation','nearby_decoy_region'
]

def stable_seed(*parts):
    return int(hashlib.sha256('|'.join(map(str, parts)).encode()).hexdigest()[:16], 16) % (2**32)

def clamp(v, lo, hi): return max(lo, min(hi, v))

def bbox(cx, cy, w, h):
    x1=int(clamp(cx-w/2,0,1022)); y1=int(clamp(cy-h/2,0,1022))
    x2=int(clamp(cx+w/2,x1+1,1023)); y2=int(clamp(cy+h/2,y1+1,1023))
    return [x1,y1,x2,y2]

def yolo(b):
    x1,y1,x2,y2=b
    return [round((x1+x2)/2/1024,6),round((y1+y2)/2/1024,6),round((x2-x1)/1024,6),round((y2-y1)/1024,6)]

def add(ds,did,cid,state,**m):
    ds.append({'defect_id':did,'class_id':cid,'defect_type':CLASSES[cid],'status':'active','progression_status':state,'measurements':m})

def scenario(s,i):
    d=[]
    if s=='crack_slow_progression': add(d,'D01',0,'increased',length_mm=12+1.5*i,width_mm=.8+.03*i)
    elif s=='crack_fast_progression': add(d,'D01',0,'increased',length_mm=8+4*i,width_mm=.7+.08*i)
    elif s=='crack_stable': add(d,'D01',0,'stable',length_mm=18,width_mm=1)
    elif s=='crack_branching':
        add(d,'D01',0,'increased',length_mm=10+2*i,width_mm=.8)
        if i>=3: add(d,'D02',0,'new' if i==3 else 'stable',length_mm=5+i-3,width_mm=.6)
    elif s=='crack_new':
        if i>=2: add(d,'D01',0,'new' if i==2 else 'stable',length_mm=7+1.2*(i-2),width_mm=.7)
    elif s=='crack_resolved':
        if i<4: add(d,'D01',0,'stable',length_mm=16,width_mm=.9)
    elif s=='corrosion_slow_progression': add(d,'D01',1,'increased',area_mm2=80+18*i,severity_index=.35+.04*i)
    elif s=='corrosion_accelerating': add(d,'D01',1,'increased',area_mm2=60+8*i*i,severity_index=.30+.06*i)
    elif s=='corrosion_stable': add(d,'D01',1,'stable',area_mm2=120,severity_index=.55)
    elif s=='corrosion_new':
        if i>=3: add(d,'D01',1,'new' if i==3 else 'increased',area_mm2=55+15*(i-3),severity_index=.30+.05*(i-3))
    elif s=='corrosion_resolved':
        if i<4: add(d,'D01',1,'stable',area_mm2=100,severity_index=.45)
    elif s=='dent_size_progression': add(d,'D01',2,'increased',width_mm=18+2*i,height_mm=14+1.5*i,depth_mm=2)
    elif s=='dent_depth_progression': add(d,'D01',2,'increased',width_mm=24,height_mm=18,depth_mm=1.5+.7*i)
    elif s=='dent_stable': add(d,'D01',2,'stable',width_mm=22,height_mm=17,depth_mm=2.5)
    elif s=='dent_repair':
        if i<4: add(d,'D01',2,'stable',width_mm=28,height_mm=20,depth_mm=3)
        elif i==4: add(d,'D01',2,'decreased',width_mm=18,height_mm=13,depth_mm=1.4)
    elif s=='missing_fastener_new':
        if i>=2: add(d,'D01',3,'new' if i==2 else 'stable',diameter_mm=6)
    elif s=='missing_fastener_stable': add(d,'D01',3,'stable',diameter_mm=6)
    elif s=='missing_fastener_repaired':
        if i<5: add(d,'D01',3,'stable',diameter_mm=6)
    elif s=='mixed_progression':
        add(d,'D01',0,'increased',length_mm=10+2*i,width_mm=.8); add(d,'D02',1,'stable',area_mm2=90,severity_index=.4)
        if i>=3: add(d,'D03',3,'new' if i==3 else 'stable',diameter_mm=6)
    elif s=='mixed_new_defects':
        if i>=1: add(d,'D01',0,'new' if i==1 else 'stable',length_mm=9,width_mm=.7)
        if i>=3: add(d,'D02',2,'new' if i==3 else 'stable',width_mm=20,height_mm=15,depth_mm=2)
        if i>=5: add(d,'D03',3,'new',diameter_mm=6)
    elif s=='multi_defect_stable':
        add(d,'D01',0,'stable',length_mm=14,width_mm=.9); add(d,'D02',1,'stable',area_mm2=110,severity_index=.45)
        add(d,'D03',2,'stable',width_mm=20,height_mm=15,depth_mm=2); add(d,'D04',3,'stable',diameter_mm=6)
    elif s=='multi_defect_progression':
        add(d,'D01',0,'increased',length_mm=8+2.5*i,width_mm=.7); add(d,'D02',1,'increased',area_mm2=60+20*i,severity_index=.30+.05*i)
        add(d,'D03',2,'stable',width_mm=21,height_mm=16,depth_mm=2)
        if i>=4: add(d,'D04',3,'new',diameter_mm=6)
    elif s=='camera_variation': add(d,'D01',0,'increased',length_mm=11+1.8*i,width_mm=.8)
    elif s=='nearby_decoy_region':
        add(d,'D01',0,'stable',length_mm=15,width_mm=.9)
        if i>=3: add(d,'D02',0,'new',length_mm=5,width_mm=.5)
    return d

def find_sources():
    if not SOURCE.exists(): raise FileNotFoundError(f'Source dataset not found: {SOURCE}')
    files=[]
    for split in ('train','valid','test'):
        f=SOURCE/split/'images'
        if f.exists(): files += [p for p in f.iterdir() if p.is_file() and p.suffix.lower() in {'.jpg','.jpeg','.png','.bmp','.webp'}]
    files.sort(key=lambda p:p.as_posix().lower()); random.Random(SEED).shuffle(files)
    if len(files)<NUM_AIRCRAFT: raise RuntimeError(f'Need {NUM_AIRCRAFT} source images; found {len(files)}')
    return files[:NUM_AIRCRAFT]

def loc(a,d):
    r=random.Random(stable_seed(a,d,'loc')); return r.uniform(220,800),r.uniform(220,800)

def make_bbox(spec,a,i):
    cx,cy=loc(a,spec['defect_id']); r=random.Random(stable_seed(a,spec['defect_id'],i,'cam')); cx+=r.uniform(-7,7); cy+=r.uniform(-7,7)
    m=spec['measurements']; cid=spec['class_id']
    if cid==0: w=max(25,m['length_mm']*PX_PER_MM); h=max(12,m['width_mm']*PX_PER_MM*2)
    elif cid==1: w=math.sqrt(m['area_mm2'])*PX_PER_MM; h=w*.75
    elif cid==2: w=max(30,m['width_mm']*PX_PER_MM); h=max(25,m['height_mm']*PX_PER_MM)
    else: w=h=max(15,m['diameter_mm']*PX_PER_MM)
    return bbox(cx,cy,w,h)

def render(img,spec,b,seed,branch=False):
    ov=Image.new('RGBA',img.size,(0,0,0,0)); dr=ImageDraw.Draw(ov); cid=spec['class_id']; x1,y1,x2,y2=b
    if cid==0:
        r=random.Random(seed); pts=[]
        for j in range(20):
            t=j/19; pts.append((x1+t*(x2-x1),(y1+y2)/2+math.sin(t*math.pi*2.3)*(y2-y1)*.35+r.uniform(-2.5,2.5)))
        dr.line(pts,fill=(35,25,25),width=max(2,int((y2-y1)/5)))
        if branch:
            m=pts[10]; dr.line([m,(m[0]+(x2-x1)*.12,m[1]-(y2-y1)*1.5),(m[0]+(x2-x1)*.22,m[1]-(y2-y1)*.8)],fill=(40,25,25),width=2)
    elif cid==1:
        r=random.Random(seed)
        for _ in range(100):
            x=r.uniform(x1,x2); y=r.uniform(y1,y2); rr=r.uniform(1.5,max(2,min(x2-x1,y2-y1)*.035)); q=r.randint(70,145); dr.ellipse((x-rr,y-rr,x+rr,y+rr),fill=(q,max(0,q-15),max(0,q-25)))
    elif cid==2:
        dr.ellipse((x1,y1,x2,y2),fill=(115,115,115),outline=(55,55,55),width=3); dx=(x2-x1)*.12; dy=(y2-y1)*.12; dr.ellipse((x1+dx,y1+dy,x2-dx,y2-dy),fill=(82,82,82))
    else:
        dr.ellipse((x1,y1,x2,y2),fill=(28,28,28),outline=(180,180,180),width=3); cx=(x1+x2)/2; cy=(y1+y2)/2; dx=(x2-x1)*.28; dy=(y2-y1)*.28; dr.ellipse((cx-dx,cy-dy,cx+dx,cy+dy),fill=(8,8,8))
    if cid in (1,2): ov=ov.filter(ImageFilter.GaussianBlur(.7))
    return Image.alpha_composite(img.convert('RGBA'),ov).convert('RGB')

def measure(spec):
    for k in ('length_mm','area_mm2','depth_mm','width_mm','diameter_mm'):
        if k in spec['measurements']: return float(spec['measurements'][k])
    return 0.0

def compare(prev,cur):
    pm={x['defect_id']:x for x in prev}; cm={x['defect_id']:x for x in cur}; out=[]
    for did,c in cm.items():
        if did not in pm: out.append({'defect_id':did,'state':'new','measurement_change':None}); continue
        old,new=measure(pm[did]),measure(c); state='increased' if new>old*1.08 else 'decreased' if new<old*.92 else 'stable'
        out.append({'defect_id':did,'state':state,'previous_measurement':round(old,3),'current_measurement':round(new,3),'measurement_change':round(new-old,3)})
    for did in pm:
        if did not in cm: out.append({'defect_id':did,'state':'resolved','measurement_change':None})
    return out

def severity(spec,c):
    v=measure(spec); st=c['state']; cid=spec['class_id']
    if cid==3: return 'High' if st in ('new','increased') else 'Medium'
    if st in ('new','increased'):
        if cid==0 and v>=22 or cid==1 and v>=140 or cid==2 and v>=30: return 'High'
        return 'Medium'
    return 'Medium' if st=='stable' else 'Low'

def decision(st,sev):
    if st=='resolved': return 'Verify repair/resolution during engineer review'
    if sev=='High': return 'Prioritize engineer inspection and verification'
    if st=='increased': return 'Schedule engineer review and monitor progression'
    if st=='new': return 'Create inspection finding and verify defect'
    return 'Continue monitoring and retain historical record'

def validate():
    ims=sorted(OUT.glob('aircraft/**/INS-*.png')); js=sorted(OUT.glob('aircraft/**/INS-*.json'))
    if len(ims)!=EXPECTED_IMAGES or len(js)!=EXPECTED_IMAGES: raise RuntimeError(f'Count validation failed: images={len(ims)}, json={len(js)}, expected={EXPECTED_IMAGES}')
    for p in ims:
        with Image.open(p) as im:
            if im.size!=IMAGE_SIZE: raise RuntimeError(f'Bad image size: {p}')
    for p in js:
        d=json.loads(p.read_text());
        for x in d['defects']:
            if x['class_id'] not in CLASSES: raise RuntimeError(f'Bad class: {p}')
            x1,y1,x2,y2=x['bbox_px'];
            if not (0<=x1<x2<=1024 and 0<=y1<y2<=1024): raise RuntimeError(f'Bad bbox: {p}')
            if not all(0<=v<=1 for v in x['bbox_yolo']): raise RuntimeError(f'Bad YOLO bbox: {p}')
    return len(ims)

def main():
    if OUT.exists(): shutil.rmtree(OUT)
    (OUT/'aircraft').mkdir(parents=True)
    sources=find_sources(); idx=[]; cases=[]; counts={i:0 for i in CLASSES}; scount={s:0 for s in SCENARIOS}; total=0
    base=date(2026,1,1)
    for a in range(NUM_AIRCRAFT):
        aid=f'AI-{a+1:03d}'; s=SCENARIOS[a%len(SCENARIOS)]; scount[s]+=1; src=sources[a]; baseimg=ImageOps.fit(Image.open(src).convert('RGB'),IMAGE_SIZE,method=Image.Resampling.LANCZOS); ad=OUT/'aircraft'/aid; ad.mkdir()
        prev=[]; hist=[]
        for i in range(INSPECTIONS_PER_AIRCRAFT):
            iid=f'INS-{i+1:03d}'; specs=scenario(s,i); img=baseimg.copy()
            if s in ('camera_variation','nearby_decoy_region'):
                r=random.Random(stable_seed(aid,i,s,'view')); img=img.rotate(r.uniform(-1.4,1.4),resample=Image.Resampling.BICUBIC,fillcolor=(95,95,95)); img=ImageEnhance.Brightness(img).enhance(r.uniform(.94,1.06)); img=ImageEnhance.Contrast(img).enhance(r.uniform(.96,1.05))
            comps=compare(prev,specs); cmap={x['defect_id']:x for x in comps}; defs=[]
            for sp in specs:
                b=make_bbox(sp,aid,i); img=render(img,sp,b,stable_seed(aid,i,sp['defect_id']),s=='crack_branching' and sp['defect_id']=='D01' and i>=3); c=cmap.get(sp['defect_id'],{'defect_id':sp['defect_id'],'state':'new','measurement_change':None}); sev=severity(sp,c)
                defs.append({'defect_id':sp['defect_id'],'class_id':sp['class_id'],'defect_type':sp['defect_type'],'bbox_px':b,'bbox_yolo':yolo(b),'status':sp['status'],'progression_status':sp['progression_status'],'measurements':sp['measurements'],'matched_previous_defect':sp['defect_id'] in {x['defect_id'] for x in prev},'comparison':c,'severity':sev,'decision_support':decision(c['state'],sev)})
                counts[sp['class_id']]+=1; total+=1
            folder=ad/iid; folder.mkdir(); ip=folder/f'{iid}.png'; jp=folder/f'{iid}.json'; arr=np.asarray(img).astype(np.int16); rng=np.random.default_rng(stable_seed(aid,i,'noise')); img=Image.fromarray(np.clip(arr+rng.normal(0,1.15,arr.shape[:2]+(1,)),0,255).astype(np.uint8)); img.save(ip,'PNG',optimize=True)
            meta={'dataset':'AeroIntel Dataset E','version':'2.0','synthetic':True,'not_for_yolo_training':True,'aircraft_id':aid,'component_id':f'COMP-{a%10+1:02d}','panel_id':f'PANEL-{a%20+1:02d}','region_id':f'REGION-{a%40+1:03d}','inspection_id':iid,'inspection_index':i+1,'date':(base+timedelta(days=i*INTERVAL_DAYS)).isoformat(),'previous_inspection_id':f'INS-{i:03d}' if i else None,'next_inspection_id':f'INS-{i+2:03d}' if i<5 else None,'scenario':s,'source_panel_image':str(src.relative_to(ROOT)),'image_path':str(ip.relative_to(ROOT)),'image_size_px':list(IMAGE_SIZE),'calibration':{'pixels_per_mm':PX_PER_MM,'synthetic':True},'defects':defs,'resolved_from_previous':[x for x in comps if x['state']=='resolved'],'comparison_ground_truth':comps,'notes':['Synthetic AeroMemory validation data.','Measurements are synthetic.','Severity is synthetic.','Decision support is prototype logic.','Not aircraft maintenance limits.','Engineer verification remains required.']}; jp.write_text(json.dumps(meta,indent=2)); idx.append({'aircraft_id':aid,'inspection_id':iid,'date':meta['date'],'scenario':s,'image_path':str(ip.relative_to(ROOT)),'metadata_path':str(jp.relative_to(ROOT)),'defect_count':len(defs)}); hist.append(meta); prev=specs
        cases.append({'aircraft_id':aid,'scenario':s,'inspection_count':6,'inspection_ids':[h['inspection_id'] for h in hist],'ground_truth_states':[h['comparison_ground_truth'] for h in hist]})
    (OUT/'index.json').write_text(json.dumps(idx,indent=2)); (OUT/'progression_cases.json').write_text(json.dumps(cases,indent=2)); (OUT/'generation_config.json').write_text(json.dumps({'dataset':'AeroIntel Dataset E','version':'2.0','seed':SEED,'aircraft_histories':NUM_AIRCRAFT,'inspections_per_aircraft':6,'expected_images':EXPECTED_IMAGES,'image_size':list(IMAGE_SIZE),'pixels_per_mm':PX_PER_MM,'inspection_interval_days':INTERVAL_DAYS,'classes':CLASSES,'scenarios':SCENARIOS,'source_dataset':str(SOURCE.relative_to(ROOT)),'source_read_only':True,'not_for_yolo_training':True},indent=2)); actual=validate()
    report=['AeroIntel Dataset E v2 - AeroMemory Synthetic Dataset','='*58,'',f'Aircraft histories: {NUM_AIRCRAFT}',f'Inspections per aircraft: {INSPECTIONS_PER_AIRCRAFT}',f'Expected images: {EXPECTED_IMAGES}',f'Generated images: {actual}',f'Total defect instances: {total}','', 'CLASS COUNTS']+[f'{i}: {CLASSES[i]}: {counts[i]}' for i in CLASSES]+['','SCENARIO COVERAGE']+[f'{s}: {scount[s]} aircraft' for s in SCENARIOS]+['','VALIDATION: PASS','Exact image count: PASS','Image dimensions: PASS','Bounding boxes: PASS','Normalized coordinates: PASS','Class IDs: PASS','','Source master_dataset_ABC was read only.','No external dataset was downloaded.','No web scraping was performed.','Synthetic measurements/severity/decision support are not aircraft maintenance limits.','Engineer verification remains required.']; (OUT/'dataset_E_report.txt').write_text('\n'.join(report)+'\n')
    print('='*60); print('AeroIntel Dataset E v2 COMPLETE'); print('='*60); print(f'Generated images: {actual}/{EXPECTED_IMAGES}'); print(f'Total defect instances: {total}'); print('\nClass counts:'); [print(f'  {i}: {CLASSES[i]}: {counts[i]}') for i in CLASSES]; print('\nVALIDATION: PASS')

if __name__=='__main__': main()
