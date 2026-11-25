import json,urllib.request,os,hashlib,sys
D='assets-polyhaven/';os.makedirs(D,exist_ok=True);tot=0
def get(u,dst,md5=None):
    global tot
    if os.path.exists(dst): return
    os.makedirs(os.path.dirname(dst),exist_ok=True)
    assert u.startswith('https://dl.polyhaven.org/')
    d=urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':'asset-fetch/1.0'}),timeout=120).read()
    if md5: assert hashlib.md5(d).hexdigest()==md5,u
    open(dst,'wb').write(d);tot+=len(d)
def api(n): return json.load(urllib.request.urlopen(urllib.request.Request('https://api.polyhaven.com/files/'+n,headers={'User-Agent':'asset-fetch/1.0'}),timeout=60))
for n in sys.argv[1].split(','):
    if not n: continue
    try:
        f=api(n)['blend'];r='1k' if '1k' in f else sorted(f)[0];b=f[r]['blend'];get(b['url'],D+n+'/'+n+'.blend',b['md5'])
        for p,q in b.get('include',{}).items(): get(q['url'],D+n+'/'+p,q['md5'])
        print(n,r,tot>>20)
    except Exception as e: print(n,'ERR',e)
for n in sys.argv[2].split(','):
    if not n: continue
    try:
        f=api(n)
        for k in ('Diffuse','Rough','nor_gl'):
            if k in f: q=f[k]['2k']['jpg'];get(q['url'],D+'tex/'+n+'_'+k+'.jpg',q['md5'])
        print(n,tot>>20)
    except Exception as e: print(n,'ERR',e)
