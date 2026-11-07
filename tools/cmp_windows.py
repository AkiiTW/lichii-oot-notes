"""Compare Lichii logs inside their test windows (Nx2TestWindow lines): back zones, draws/s, frame ms.
Usage: python cmp_windows.py before.txt after.txt"""
import re,sys,statistics as st
def windows(fn):
    start=end=None; rows=[]
    for line in open(fn,errors='replace'):
        m=re.match(r'\[\s*([\d.]+)\]',line)
        if not m: continue
        t=float(m.group(1))
        if 'recording starts' in line: start=t
        if 'recording ends' in line: end=t
        if 'GPU back thread per second:' in line and start and (end is None or t<=end+1) and t>start+5:
            z={k:(float(a),int(b)) for k,a,b in re.findall(r'\| ([a-z /]+) ([\d.]+) ms \((\d+)/s\)',line)}
            busy=float(re.search(r'host_cpu_busy_ms_per_s=([\d.]+)',line).group(1))
            rows.append((t,z,busy))
        if 'Host pacing on' in line and start and t>start+5 and (end is None or t<=end+1):
            pass
    return rows
def frames(fn):
    start=end=None; out=[]
    for line in open(fn,errors='replace'):
        m=re.match(r'\[\s*([\d.]+)\]',line)
        if not m: continue
        t=float(m.group(1))
        if 'recording starts' in line: start=t
        if 'recording ends' in line: end=t
        if 'last 600 presents' in line and start and t>start and (end is None or t<=end+15):
            out.append(int(re.search(r'frame (\d+) us',line).group(1)))
    return out
keys=['storage binds','ubo bank','ubo fast','ubo classic','bind stage buffers','update buffers','texture upload','method','other','draw','clear','split wait']
res={}
for fn in sys.argv[1:]:
    rows=windows(fn)
    d={k:st.mean([r[1].get(k,(0,0))[0] for r in rows]) for k in keys}
    d['draws']=st.mean([r[1].get('draw',(0,0))[1] for r in rows])
    fr=frames(fn); d['frame_ms']=st.mean(fr)/1000 if fr else 0
    d['n']=len(rows); res[fn]=d
print('metric'.ljust(20),*[f.ljust(10) for f in sys.argv[1:]])
for k in ['n','frame_ms','draws']+keys:
    print(k.ljust(20),*[f"{res[f][k]:10.1f}" for f in sys.argv[1:]])
