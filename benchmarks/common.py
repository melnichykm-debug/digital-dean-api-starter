import csv,json,platform,subprocess,statistics
from datetime import datetime,timezone
from pathlib import Path
from time import perf_counter_ns,get_clock_info
ROOT=Path(__file__).resolve().parents[1]
def stamp(): return datetime.now(timezone.utc).isoformat().replace('+00:00','Z')
def commit():
    import shutil

    git = shutil.which("git")
    if git is None:
        return "unavailable-source-archive"

    try:
        return subprocess.check_output(
            [git, "rev-parse", "HEAD"],
            cwd=ROOT,
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except (subprocess.CalledProcessError, OSError):
        return "unavailable-source-archive"
def stats(samples):
    q1,_,q3=statistics.quantiles(samples,n=4,method='inclusive')
    return float(statistics.median(samples)),float(q3-q1)
def write(directory,report,rows,avalanche=None):
    p=ROOT/directory;p.mkdir(parents=True,exist_ok=True)
    (p/'report.json').write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
    for name,values in [('raw.csv',rows),('avalanche.csv',avalanche)]:
        if values:
            with (p/name).open('w',newline='') as f:
                writer=csv.DictWriter(f,fieldnames=list(values[0]));writer.writeheader();writer.writerows(values)
def crypto_environment():
    import cryptography
    from cryptography.hazmat.backends.openssl.backend import backend
    return dict(python=platform.python_version(),cryptography=cryptography.__version__,openssl=backend.openssl_version_text(),os=platform.platform(),cpu=platform.processor() or platform.machine())
