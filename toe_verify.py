import struct,zlib,sys,hashlib
class CSO:
    def __init__(s,p):
        s.f=open(p,'rb');h=s.f.read(24)
        assert h[:4]==b'CISO',"not a CSO file"
        s.hs,s.total,s.bs,s.ver,s.align=struct.unpack('<IQIBB',h[4:22])
        s.n=s.total//s.bs
        s.idx=struct.unpack('<%dI'%(s.n+1),s.f.read(4*(s.n+1)))
    def block(s,i):
        a=s.idx[i];b=s.idx[i+1];plain=a&0x80000000;a&=0x7fffffff;b&=0x7fffffff
        a<<=s.align;b<<=s.align;s.f.seek(a);d=s.f.read(b-a)
        return d if plain else zlib.decompress(d,-15)
    def read(s,off,n):
        out=b'';
        while n>0:
            i=off//s.bs;o=off%s.bs;d=s.block(i)[o:o+n];out+=d;off+=len(d);n-=len(d)
            if not d:break
        return out

import struct,hashlib,os
class RAW:
    def __init__(s,p):s.f=open(p,'rb')
    def read(s,o,n):s.f.seek(o);return s.f.read(n)
S=2048
# ---- ACCEPTED HASH LIST (sha256). Generated from the original European disc (TRSI/CSO). ----
# BLOCKS: if any of these differ, the installation does NOT proceed.
OBRIGATORIOS={
 'PSP_GAME/USRDIR/dat/b_us.v':['25e471d88f5571ce91b3a61fae8d76d58422c702f55638689d339ca02fc34b8d'],
 'PSP_GAME/USRDIR/dat/s_us.v':['0db0caec59094ffd0e11e2ed051fd1f02903abef7f9780953ac8351a614c48e7'],
 'PSP_GAME/USRDIR/dat/fc_us.v':['359e81021fe40d4af36ade157cb05e859efe6fd87cb8102e22822895225446b1'],
}
# INFORMATIVE ONLY (does not block): helps classify the disc variant.
INFORMATIVOS={
 'PSP_GAME/USRDIR/dat/fc_us.d':{'140aeb1bc2dd7dc5171310e6d015aad08ed4cde409f615d48db406962a4abfa6':'original'},
 'PSP_GAME/USRDIR/dat/m_us.d':{'e1a9fbebdc183df1fc621ef18d89d160f3bd344c19811521b5ac0b8102e11ce9':'original','c88281a2289fd94af669fc4ac8439cc8121749c92cb80dbc10047073bfbb667c':'translated variant (PT-BR?)'},
 'PSP_GAME/USRDIR/movie/op.pmf':{'8217c1f8af5024cceb3e7dc5a98b75219bd9fc92bc243c2761b9dd5bf75039aa':'original','8ea13f5e87f55dadc3632e5d90ea8556c02eb8ca5ece009e8b9e71a0ea81bbc9':'undub variant'},
 'PSP_GAME/USRDIR/sndadd/S00.see':{'2f13b97108decd2ddf955adb4fc2d731340169955689c1e131e03a21c7521291':'original','8bca8c7146bd27f0dbba0c4dca430928dbf6cd9cf0665c77cb7fecc4bdca1883':'undub variant'},
 'PSP_GAME/SYSDIR/EBOOT.BIN':{'85368d25c24959993fa5f7df78b9d03d307a0f88dbad8f33244c4589961b29f9':'original','46721838849b3da42f05be884dbcda750f9b2a06289ad570e2f18bb6b86b9c84':'undub variant','c54154e1026b6ee1e7bdbd3d1fa99ca1439704ea2fc06c6fee1f237d2988eb1d':'translated variant (PT-BR?)'},
}
def ls(c,lba,ln):
    d=c.read(lba*S,ln);o=0;r=[]
    while o<len(d):
        l=d[o]
        if l==0:o=(o//S+1)*S;continue
        lb=struct.unpack('<I',d[o+2:o+6])[0];sz=struct.unpack('<I',d[o+10:o+14])[0];fl=d[o+25];nl=d[o+32]
        nm=d[o+33:o+33+nl].decode('latin1').split(';')[0]
        if nm not in('\x00','\x01'):r.append((nm,lb,sz,bool(fl&2)))
        o+=l
    return r
def walk(c,lba,ln,pre=''):
    for nm,lb,sz,isd in ls(c,lba,ln):
        if isd:yield from walk(c,lb,sz,pre+nm+'/')
        else:yield pre+nm,lb,sz
def sha(c,lb,sz):
    h=hashlib.sha256();off=lb*S;left=sz
    while left>0:
        d=c.read(off,min(left,1<<20))
        if not d:break
        h.update(d);off+=len(d);left-=len(d)
    return h.hexdigest()
def verificar(p):
    with open(p,'rb') as f:magic=f.read(4)
    c=CSO(p) if magic==b'CISO' else RAW(p)
    pvd=c.read(16*S,S)
    if pvd[1:6]!=b'CD001':return False,['This file does not look like a valid PSP ISO/CSO.']
    root=struct.unpack('<I',pvd[158:162])[0];rlen=struct.unpack('<I',pvd[166:170])[0]
    files={n:(lb,sz) for n,lb,sz in walk(c,root,rlen)}
    msgs=[];ok=True
    if 'PSP_GAME/PARAM.SFO' in files:
        lb,sz=files['PSP_GAME/PARAM.SFO'];d=c.read(lb*S,sz)
        i=d.find(b'ULES');msgs.append('DISC_ID: '+(d[i:i+9].decode('latin1') if i>=0 else '?'))
    for n,hs in OBRIGATORIOS.items():
        if n not in files:ok=False;msgs.append('MISSING: '+n);continue
        h=sha(c,*files[n])
        if h in hs:msgs.append('OK        '+n)
        else:ok=False;msgs.append('MISMATCH  %s  (sha256 %s)'%(n,h))
    for n,m in INFORMATIVOS.items():
        if n in files:
            h=sha(c,*files[n]);msgs.append('info      %s -> %s'%(n,m.get(h,'UNKNOWN '+h[:16])))
    return ok,msgs
if __name__=='__main__':
    if len(sys.argv)<2:
        print('Usage: python toe_verify.py "path\\to\\game.iso or .cso"');sys.exit(2)
    p=sys.argv[1]
    print('Verifying (may take a few seconds)...')
    ok,msgs=verificar(p)
    print('\n'.join(msgs));print()
    if ok:print('RESULT: DISC ACCEPTED. The original English voices (b_us/s_us/fc_us) match.');sys.exit(0)
    print('RESULT: DISC REJECTED. This file does not contain the original English voices (it may be an undub, a hack or an altered/corrupted dump). Installation blocked.');sys.exit(1)
