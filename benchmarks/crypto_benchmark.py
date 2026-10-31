import argparse,random,secrets,time
from pathlib import Path
from benchmarks.common import *
from app.security.adapters import seal_bytes,open_bytes
from app.security.profiles import KEY_BYTES,BACKENDS
from app.security.nonce import NonceSequence
SIZES_BYTES=(1024,65536,1048576)
WARMUP=10
SERIES=5
OPERATIONS_PER_SERIES=100
BENCHMARK_AAD=b'digital-dean-practice-02-benchmark'.ljust(64,b'.')
def measure_batch(operation,arguments):
    start=perf_counter_ns()
    for args in arguments: operation(*args)
    return (perf_counter_ns()-start)/len(arguments)
def summarize(samples,size):
    median,iqr=stats(samples)
    return dict(median_ns=median,iqr_ns=iqr,throughput_mib_s=size*1e9/(2**20*median))
def run_benchmark(output_dir):
    combinations=[(b,a,s,o) for b in BACKENDS for a in KEY_BYTES for s in SIZES_BYTES for o in ('encrypt','decrypt')]
    keys={(b,a):(secrets.token_bytes(n),NonceSequence()) for b in BACKENDS for a,n in KEY_BYTES.items()}
    samples={c:[] for c in combinations};rows=[]
    rng=random.Random(15)
    for series in range(5):
        order=combinations.copy();rng.shuffle(order)
        for b,a,size,op in order:
            key,seq=keys[b,a];data=b'D'*size
            def args():
                nonce=seq.next()
                if op=='encrypt': return b,a,key,nonce,data,BENCHMARK_AAD
                ct,tag=seal_bytes(b,a,key,nonce,data,BENCHMARK_AAD)
                assert open_bytes(b,a,key,nonce,ct,tag,BENCHMARK_AAD)==data
                return b,a,key,nonce,ct,tag,BENCHMARK_AAD
            function=seal_bytes if op=='encrypt' else open_bytes
            if series==0:
                for _ in range(10): function(*args())
            arguments=[args() for _ in range(100)]
            mean=measure_batch(function,arguments);samples[b,a,size,op].append(mean)
            rows.append(dict(backend=b,algorithm=a,payload_bytes=size,operation=op,series_index=series+1,operations=100,elapsed_ns=mean*100,ns_per_operation=mean))
    results=[dict(backend=b,algorithm=a,payload_bytes=s,operation=o,**summarize(samples[b,a,s,o],s)) for b,a,s,o in combinations]
    report=dict(schema_version=1,environment={**crypto_environment(),'pycryptodome':__import__('Crypto').__version__},experiment=dict(series=5,operations_per_series=100,warmup=10,aad_bytes=64,cipher_creation_included=True,clock_resolution=time.get_clock_info('perf_counter').resolution,source_commit=commit(),created_at_utc=stamp()),results=results)
    write(str(output_dir),report,rows)
    print('Practice 02: 180 raw rows, 36 aggregates')
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--output-dir',type=Path,default=Path('results/practice-02'));run_benchmark(parser.parse_args().output_dir)

