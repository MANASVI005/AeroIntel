#!/usr/bin/env python3
"""Generate AeroIntel Dataset E: synthetic longitudinal AeroMemory data.

Run from the AeroIntel repository root:
    python tools/generate_aeromemory_dataset.py

Requirements:
    pip install pillow numpy

Dataset E is NOT a YOLO training dataset.
It uses existing images from datasets/master_dataset_ABC as read-only base
panel context and renders deterministic synthetic defect progression.
"""

from __future__ import annotations
import hashlib
import json
import math
import random
import shutil
from datetime import date, timedelta
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageOps

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "datasets" / "master_dataset_ABC"
OUT = ROOT / "datasets" / "dataset_E_aeromemory"
SEED = 42
SIZE = (1024, 1024)
PX_PER_MM = 10.0
INTERVAL_DAYS = 30
CLASSES = {0: "Crack", 1: "Corrosion", 2: "Dent", 3: "Missing Fastener"}

SCENARIOS = [
    ("AI-001", "crack_progression", "PNL-07", "R-03", "crack_growth"),
    ("AI-002", "crack_progression_fast", "PNL-11", "R-02", "crack_fast"),
    ("AI-003", "stable_crack", "PNL-04", "R-05", "crack_stable"),
    ("AI-004", "corrosion_progression", "PNL-09", "R-01", "corr_growth"),
    ("AI-005", "corrosion_accelerating", "PNL-14", "R-04", "corr_fast"),
    ("AI-006", "stable_corrosion", "PNL-03", "R-02", "corr_stable"),
    ("AI-007", "dent_depth_progression", "PNL-12", "R-03", "dent_depth"),
    ("AI-008", "dent_dimension_progression", "PNL-05", "R-06", "dent_size"),
    ("AI-009", "stable_dent", "PNL-02", "R-04", "dent_stable"),
    ("AI-010", "missing_fastener_appearance", "PNL-18", "R-02", "fastener"),
    ("AI-011", "new_crack_then_progression", "PNL-08", "R-05", "new_crack"),
    ("AI-012", "mixed_defects_and_repair", "PNL-21", "R-01", "mixed"),
]

def write_json(p, obj):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, indent=2), encoding="utf-8")

def sha256(p):
    h = hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda: f.read(1024 * 1024), b""):
            h.update(b)
    return h.hexdigest()

def severity(kind, value):
    if kind == "crack":
        return "Low" if value < 10 else "Medium" if value <= 20 else "High"
    if kind == "corrosion":
        return "Low" if value < 20 else "Medium" if value <= 40 else "High"
    if kind == "dent":
        return "Low" if value < 1.5 else "Medium" if value <= 2.5 else "High"
    return "High"

def decision(sev):
    return {
        "Low": ("Monitor", "LOW"),
        "Medium": ("Engineer Review", "MEDIUM"),
        "High": ("Immediate Engineer Attention", "HIGH"),
    }[sev]

def bbox(cx, cy, w, h):
    x1, y1 = max(0, cx-w/2), max(0, cy-h/2)
    x2, y2 = min(SIZE[0], cx+w/2), min(SIZE[1], cy+h/2)
    return [round(x1, 3), round(y1, 3), round(x2, 3), round(y2, 3)]

def iou(a, b):
    x1, y1 = max(a[0],b[0]), max(a[1],b[1])
    x2, y2 = min(a[2],b[2]), min(a[3],b[3])
    inter = max(0,x2-x1)*max(0,y2-y1)
    aa=(a[2]-a[0])*(a[3]-a[1]); bb=(b[2]-b[0])*(b[3]-b[1])
    return inter/(aa+bb-inter) if aa+bb-inter else 0

def measurements(kind, i):
    tables = {
        "crack_growth":[8,11,15,20,27],
        "crack_fast":[6,12,19,28,38],
        "crack_stable":[10,10.2,10.1,10.3,10.2],
        "corr_growth":[12,19,27,39,54],
        "corr_fast":[8,14,24,39,62],
        "corr_stable":[100,102,101,103,102],
        "dent_depth":[(30,20,1.2),(31,21,1.5),(34,23,1.9),(38,25,2.4),(42,27,3.0)],
        "dent_size":[(22,16,1.0),(26,18,1.2),(30,20,1.4),(35,23,1.8),(42,27,2.2)],
        "dent_stable":[(32,22,1.8),(32,22,1.8),(33,22,1.8),(32,23,1.9),(33,22,1.8)],
    }
    return tables[kind][i]

def make_states(scenario, i):
    aid, _, panel, region, kind = scenario
    # Stable physical locations for each aircraft/region.
    h = hashlib.sha256(f"{aid}|{panel}|{region}".encode()).digest()
    cx = 420 + int.from_bytes(h[:2],"big") % 220
    cy = 420 + int.from_bytes(h[2:4],"big") % 220
    out = []

    def add(did, cid, typ, b, status, prog, sev, **m):
        out.append({
            "defect_id": did, "class_id": cid, "defect_type": typ,
            "status": status, "progression_status": prog,
            "bbox_px": b, "severity": sev, **m
        })

    if kind in ("crack_growth","crack_fast","crack_stable"):
        v = measurements(kind,i); add(f"DEF-{aid}-D01",0,"Crack",
            bbox(cx,cy,max(50,v*PX_PER_MM),30),"active",
            "stable" if kind=="crack_stable" else ("stable" if i==0 else "increased"),
            severity("crack",v), length_mm=v, width_mm=.8)
    elif kind in ("corr_growth","corr_fast","corr_stable"):
        v=measurements(kind,i); s=math.sqrt(v)
        add(f"DEF-{aid}-D01",1,"Corrosion",bbox(cx,cy,max(60,s*15),max(45,s*10)),
            "active","stable" if kind=="corr_stable" else ("stable" if i==0 else "increased"),
            severity("corrosion",v), area_mm2=v)
    elif kind in ("dent_depth","dent_size","dent_stable"):
        w,h,d=measurements(kind,i)
        add(f"DEF-{aid}-D01",2,"Dent",bbox(cx,cy,w*PX_PER_MM,h*PX_PER_MM),
            "active","stable" if kind=="dent_stable" else ("stable" if i==0 else "increased"),
            severity("dent",d), length_mm=w, width_mm=h, depth_mm=d)
    elif kind=="fastener":
        active=i>=3
        add(f"DEF-{aid}-D01",3,"Missing Fastener",bbox(cx,cy,42,42),
            "active" if active else "not_present",
            "new" if i==3 else ("stable" if i>3 else "not_present"),
            "High" if active else "Low")
    elif kind=="new_crack":
        v=[0,0,6,11,17][i]
        if v: add(f"DEF-{aid}-D01",0,"Crack",bbox(cx,cy,max(50,v*PX_PER_MM),30),
            "active","new" if i==2 else "increased",
            severity("crack",v),length_mm=v,width_mm=.8)
    elif kind=="mixed":
        # Crack grows then is repaired.
        if i<3:
            v=[18,21,25][i]
            add(f"DEF-{aid}-D01",0,"Crack",bbox(cx,cy,max(60,v*PX_PER_MM),30),
                "active","stable" if i==0 else "increased",severity("crack",v),
                length_mm=v,width_mm=.8)
        # Dent is present alongside the crack until repair inspection.
        if i<3:
            w,h,d=[(26,18,1.4),(28,19,1.6),(30,20,1.8)][i]
            add(f"DEF-{aid}-D02",2,"Dent",bbox(cx+180,cy+80,w*PX_PER_MM,h*PX_PER_MM),
                "active","stable" if i==0 else "increased",severity("dent",d),
                length_mm=w,width_mm=h,depth_mm=d)
        # Fastener becomes missing at inspection 4 and remains missing.
        if i>=3:
            add(f"DEF-{aid}-D03",3,"Missing Fastener",bbox(cx-170,cy-80,42,42),
                "active","new" if i==3 else "stable","High")
    return out

def render(base, states, seed):
    img=base.copy()
    # Tiny deterministic inspection noise so images are not byte-identical.
    arr=np.asarray(img).astype(np.int16)
    rng=np.random.default_rng(seed)
    arr=np.clip(arr+rng.normal(0,.7,arr.shape[:2]+(1,)),0,255).astype(np.uint8)
    img=Image.fromarray(arr,"RGB")
    for j,s in enumerate(states):
        ov=Image.new("RGBA",img.size,(0,0,0,0)); d=ImageDraw.Draw(ov)
        x1,y1,x2,y2=s["bbox_px"]; cx=(x1+x2)/2; cy=(y1+y2)/2
        if s["class_id"]==0:
            L=s["length_mm"]; span=max(35,L*PX_PER_MM)
            pts=[(cx-span/2,cy)]
            rng2=random.Random(seed+j*17)
            for k in range(1,8):
                t=k/7; pts.append((cx-span/2+span*t,cy+math.sin(t*9)*6+rng2.uniform(-2,2)))
            d.line(pts,fill=(235,235,235,90),width=5,joint="curve")
            d.line(pts,fill=(25,27,29,220),width=2,joint="curve")
        elif s["class_id"]==1:
            area=s["area_mm2"]; r=max(18,math.sqrt(area)*5)
            rng2=random.Random(seed+j*31)
            for _ in range(int(15+area/2)):
                ox=rng2.gauss(0,r*.35); oy=rng2.gauss(0,r*.3); rr=rng2.uniform(2,7)
                d.ellipse((cx+ox-rr,cy+oy-rr,cx+ox+rr,cy+oy+rr),
                          fill=rng2.choice([(120,75,35,90),(150,90,40,75),(80,60,40,80)]))
        elif s["class_id"]==2:
            depth=s["depth_mm"]; rx=(x2-x1)/2; ry=(y2-y1)/2
            for scale in np.linspace(1,.35,8):
                a=int(18+35*(1-scale))
                d.ellipse((cx-rx*scale,cy-ry*scale,cx+rx*scale,cy+ry*scale),
                          fill=(35,40,45,a))
            d.ellipse((cx-rx*.35,cy-ry*.25,cx+rx*.05,cy+ry*.15),
                      fill=(240,242,244,min(80,int(35+depth*12))))
        elif s["class_id"]==3:
            r=min(x2-x1,y2-y1)/2
            d.ellipse((cx-r,cy-r,cx+r,cy+r),fill=(40,42,45,215),
                      outline=(205,210,215,190),width=max(2,int(r*.12)))
            d.ellipse((cx-r*.55,cy-r*.55,cx+r*.55,cy+r*.55),fill=(15,17,19,230))
        img=Image.alpha_composite(img.convert("RGBA"),ov.filter(ImageFilter.GaussianBlur(.2))).convert("RGB")
    return img

def compare(prev, cur):
    p={x["defect_id"]:x for x in prev}; c={x["defect_id"]:x for x in cur}
    def val(x):
        if x["class_id"]==0:return x["length_mm"]
        if x["class_id"]==1:return x["area_mm2"]
        if x["class_id"]==2:return x["depth_mm"]
        return 1 if x["status"]=="active" else 0
    matched=[]; new=[]; resolved=[]
    for did,x in c.items():
        if did in p:
            y=p[did]; delta=val(x)-val(y)
            matched.append({"defect_id":did,"match_status":"matched",
                "previous_value":val(y),"current_value":val(x),"change":round(delta,3),
                "progression":"stable" if abs(delta)<.5 else ("increased" if delta>0 else "decreased"),
                "bbox_iou_ground_truth":round(iou(y["bbox_px"],x["bbox_px"]),6)})
        else:new.append({"defect_id":did,"match_status":"new","current_value":val(x)})
    for did,x in p.items():
        if did not in c: resolved.append({"defect_id":did,"match_status":"resolved","previous_value":val(x),"current_value":0})
    return {"matched_defects":matched,"new_defects":new,"resolved_defects":resolved}

def main():
    if not SOURCE.exists():
        raise SystemExit(f"Missing source dataset: {SOURCE}")
    sources=sorted([p for split in ("train","valid","test")
                    for p in (SOURCE/split/"images").rglob("*")
                    if p.is_file() and p.suffix.lower() in {".jpg",".jpeg",".png",".bmp",".webp"}],
                   key=lambda p:p.as_posix().lower())
    if len(sources)<12: raise SystemExit(f"Need >=12 source images; found {len(sources)}")
    rng=random.Random(SEED); rng.shuffle(sources)
    chosen=sources[:12]

    if OUT.exists(): shutil.rmtree(OUT)
    OUT.mkdir(parents=True)

    all_records=[]; source_info=[]
    for ai,scenario in enumerate(SCENARIOS):
        aid,scenario_name,panel,region,kind=scenario
        src=chosen[ai]
        with Image.open(src) as im:
            base=ImageOps.exif_transpose(im).convert("RGB").resize(SIZE,Image.Resampling.LANCZOS)
        source_info.append({"aircraft_id":aid,"source_image":src.as_posix(),"source_sha256":sha256(src)})
        previous=[]
        for i in range(5):
            iid=f"INS-{i+1:03d}"
            states=make_states(scenario,i)
            rel=Path("aircraft")/aid/iid/"image.png"
            folder=OUT/rel.parent; folder.mkdir(parents=True,exist_ok=True)
            render(base,states,SEED+ai*100+i*17).save(OUT/rel,"PNG",optimize=True)
            prev_id=f"INS-{i:03d}" if i else None
            next_id=f"INS-{i+2:03d}" if i<4 else None
            active=[x for x in states if x["status"]=="active"]
            order={"Low":0,"Medium":1,"High":2}
            sev=max([x["severity"] for x in active],key=lambda x:order[x],default="Low")
            cat,priority=decision(sev)
            meta={
                "dataset":{"name":"AeroMemory Synthetic Longitudinal Dataset","version":"1.0","not_for_yolo_training":True},
                "aircraft_id":aid,"inspection_id":iid,"inspection_index":i+1,
                "inspection_date":(date(2026,1,15)+timedelta(days=i*INTERVAL_DAYS)).isoformat(),
                "previous_inspection_id":prev_id,"next_inspection_id":next_id,
                "scenario":scenario_name,"panel_id":panel,"region_id":region,
                "image":{"path":rel.as_posix(),"source_image":src.as_posix(),"width":SIZE[0],"height":SIZE[1],"format":"PNG"},
                "calibration":{"pixels_per_mm":PX_PER_MM,"note":"Synthetic validation calibration only."},
                "defects":states,
                "comparison_ground_truth":compare(previous,states) if i else None,
                "decision_support_ground_truth":{"severity":sev,"category":cat,"priority":priority,
                    "note":"Prototype synthetic rule; final maintenance decisions require engineer verification."}
            }
            write_json(OUT/rel.with_suffix(".json"),meta)
            all_records.append(meta); previous=states

    index={"dataset":"AeroMemory Synthetic Longitudinal Dataset","version":"1.0","seed":SEED,
           "aircraft_count":12,"inspections_per_aircraft":5,"image_count":60,
           "image_size":SIZE,"pixels_per_mm":PX_PER_MM,"classes":CLASSES,"source_images":source_info}
    write_json(OUT/"index.json",index)
    cases=[]
    for aid,scenario_name,panel,region,_ in SCENARIOS:
        rs=sorted([r for r in all_records if r["aircraft_id"]==aid],key=lambda x:x["inspection_index"])
        cases.append({"aircraft_id":aid,"scenario":scenario_name,"panel_id":panel,"region_id":region,
                      "comparisons":[{"previous_inspection_id":r["previous_inspection_id"],
                                      "current_inspection_id":r["inspection_id"],
                                      "ground_truth":r["comparison_ground_truth"]} for r in rs[1:]]})
    write_json(OUT/"progression_cases.json",{"cases":cases})
    write_json(OUT/"generation_config.json",{"seed":SEED,"version":"1.0","image_width":1024,
        "image_height":1024,"pixels_per_mm":PX_PER_MM,"inspection_interval_days":INTERVAL_DAYS,
        "aircraft_count":12,"inspections_per_aircraft":5,"source_root":SOURCE.as_posix(),"classes":CLASSES})

    errors=[]
    if len(all_records)!=60: errors.append(f"Expected 60 images, got {len(all_records)}")
    for r in all_records:
        p=OUT/r["image"]["path"]
        if not p.exists(): errors.append(f"Missing image: {p}")
        for d in r["defects"]:
            x1,y1,x2,y2=d["bbox_px"]
            if not (0<=x1<x2<=1024 and 0<=y1<y2<=1024): errors.append(f"Invalid bbox in {p}")
            if d["class_id"] not in CLASSES: errors.append(f"Invalid class in {p}")
    status="PASS" if not errors else "FAIL"
    report=[
        "DATASET E — AEROMEMORY SYNTHETIC LONGITUDINAL DATASET","="*60,
        f"Version: 1.0",f"Seed: {SEED}","Aircraft: 12","Inspections: 60",
        "Image size: 1024x1024","Pixels/mm: 10","", "NOT FOR YOLO TRAINING.",
        "Synthetic decision/severity rules are prototype rules, not maintenance limits.",
        "", "VALIDATION",f"Status: {status}"
    ] + ([f"- {e}" for e in errors] if errors else ["- 0 errors"])
    (OUT/"dataset_E_report.txt").write_text("\n".join(report)+"\n",encoding="utf-8")
    print(f"Dataset E created: {OUT}")
    print("Aircraft: 12")
    print("Inspection images: 60")
    print(f"Validation: {status}")
    if errors:
        raise SystemExit(1)

if __name__=="__main__":
    main()
