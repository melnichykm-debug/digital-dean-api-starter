import json,math
from pathlib import Path
from fastapi import APIRouter,HTTPException
router=APIRouter(prefix='/api/v1/lab/crypto',tags=['crypto-lab'])
REPORT_PATH=Path(__file__).resolve().parents[2]/'results/practice-02/report.json'
def load_benchmark_report(path):
    try:
        with Path(path).open('rb') as f: raw=f.read(1048577)
        if len(raw)>1048576: raise ValueError()
        def unique(pairs):
            d={}
            for k,v in pairs:
                if k in d: raise ValueError()
                d[k]=v
            return d
        d=json.loads(raw,object_pairs_hook=unique,parse_constant=lambda x: (_ for _ in ()).throw(ValueError()))
        expected={(b,a,s,o) for b in ('cryptography','pycryptodome') for a in ('AES-128-GCM','AES-256-GCM','ChaCha20-Poly1305') for s in (1024,65536,1048576) for o in ('encrypt','decrypt')}
        rows=d['results']; keys=[(x['backend'],x['algorithm'],x['payload_bytes'],x['operation']) for x in rows]
        if len(keys)!=36 or set(keys)!=expected: raise ValueError()
        for x in rows:
            if any(type(x[k]) not in (int,float) or not math.isfinite(x[k]) or x[k]<=0 for k in ('median_ns','throughput_mib_s')) or x['iqr_ns']<0: raise ValueError()
            if not math.isclose(x['throughput_mib_s'],x['payload_bytes']*1e9/(2**20*x['median_ns'])): raise ValueError()
        return d
    except FileNotFoundError: raise HTTPException(404,'Benchmark results unavailable') from None
    except (OSError,ValueError,KeyError,TypeError): raise HTTPException(500,'Benchmark results unavailable') from None
@router.get('/benchmark-results')
def results(): return load_benchmark_report(REPORT_PATH)
