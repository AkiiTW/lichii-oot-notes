"""Lichii log: one line per 10 s profile window (EDEN_NX2_GPU_PROFILE, EDEN_NX2_THREAD_USAGE).
Usage: python profile_windows.py eden_log.txt [more logs]"""
import re,sys
for fn in sys.argv[1:]:
    print("=====",fn)
    rows={}
    for line in open(fn,errors='replace'):
        m=re.match(r'\[\s*([\d.]+)\]',line)
        if not m: continue
        t=int(float(m.group(1))//10)*10
        r=rows.setdefault(t,{})
        if 'GPU back thread per second:' in line:
            r['draws']=int(re.search(r'\| draw [\d.]+ ms \((\d+)/s\)',line).group(1)) if '| draw ' in line else 0
            mm=re.search(r'split wait ([\d.]+) ms',line); r['bwait']=float(mm.group(1)) if mm else 0.0
            for z in ['bind stage buffers','texture upload','fill image views','pipeline lookup','method','update buffers','fence']:
                mm=re.search(r'\| '+z+r' ([\d.]+) ms',line)
                if mm: r[z]=float(mm.group(1))
        elif 'GPU thread per second:' in line:
            r['fidle']=float(re.search(r'idle ([\d.]+) ms',line).group(1))
            mm=re.search(r'split drain ([\d.]+) ms',line); r['drain']=float(mm.group(1)) if mm else 0
            mm=re.search(r'\| macro ([\d.]+) ms \((\d+)/s',line); r['macro']=float(mm.group(1)) if mm else 0
            mm=re.search(r'MME DMA reads (\d+) KiB',line); r['dma']=int(mm.group(1)) if mm else 0
        elif 'Thread CPU last' in line:
            for k,pat in [('cGPU',r'\| GPU (\d+)%'),('cBack',r'GPUBack (\d+)%'),('cCore',r'CPUCore_\d (\d+)%')]:
                mm=re.search(pat,line); 
                if mm: r[k]=int(mm.group(1))
        elif 'Host pacing on' in line:
            mm=re.search(r'Host pacing on: (\d+) frames',line); r['frames']=int(mm.group(1))
        elif 'Scheduler per second' in line:
            mm=re.search(r'(\d+) render passes',line); r['rp']=int(mm.group(1))
    for t in sorted(rows):
        r=rows[t]
        if r.get('draws',0)<1000: continue
        print(f"t={t:4d} draws/s={r.get('draws',0):6d} backbusy={1000-r.get('bwait',1000):5.0f} frontbusy={1000-r.get('fidle',1000):5.0f} drain={r.get('drain',0):5.0f} cpuGPU={r.get('cGPU','-')} cpuBack={r.get('cBack','-')} RP={r.get('rp','-')} pacer={r.get('frames','-')} bind={r.get('bind stage buffers',0):.0f} meth={r.get('method',0):.0f}")
