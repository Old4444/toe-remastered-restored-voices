import struct
TYPES={0:('B',1),1:('b',1),2:('>H',2),3:('>h',2),4:('>I',4),5:('>i',4),6:('>Q',8),7:('>q',8),8:('>f',4),9:('>d',8)}
class UTF:
    pass
def parse(buf):
    assert buf[:4]==b'@UTF', buf[:4]
    size,=struct.unpack('>I',buf[4:8]); b=buf[8:8+size]
    ver,rows_off,str_off,data_off,name_off,fc,rsz,rc=struct.unpack('>HHIIIHHI',b[:24])
    t=UTF(); t.ver=ver; t.rsz=rsz
    strings=b[str_off:data_off]; t.strings=strings
    def S(o): return strings[o:strings.index(b'\0',o)].decode('utf8')
    t.name=S(name_off); t.name_off=name_off
    p=24; fields=[]
    for _ in range(fc):
        fl=b[p]; p+=1
        noff,=struct.unpack('>I',b[p:p+4]); p+=4
        st=fl&0xF0; ty=fl&0x0F; const=None
        if st==0x30:
            const,p=rdval(b,p,ty,strings,data_off)
        fields.append(dict(flags=fl,st=st,ty=ty,name=S(noff),noff=noff,const=const))
    t.fields=fields
    rows=[]; p=rows_off
    for _ in range(rc):
        r={}
        for f in fields:
            if f['st']==0x50: r[f['name']],p=rdval(b,p,f['ty'],strings,data_off)
            elif f['st']==0x30: r[f['name']]=f['const']
            else: r[f['name']]=None
        rows.append(r)
    t.rows=rows; t.datapool=b[data_off:]
    return t
def rdval(b,p,ty,strings,data_off):
    if ty in TYPES:
        fmt,n=TYPES[ty]; return struct.unpack(fmt,b[p:p+n])[0],p+n
    if ty==0xA:
        o,=struct.unpack('>I',b[p:p+4]); return ('S',o),p+4
    if ty==0xB:
        o,s=struct.unpack('>II',b[p:p+8]); return ('D',bytes(b[data_off+o:data_off+o+s]),o),p+8
    raise ValueError(ty)
def wrval(v,ty,pool):
    if ty in TYPES: return struct.pack(TYPES[ty][0],v)
    if ty==0xA: return struct.pack('>I',v[1])
    if ty==0xB:
        data=v[1]
        if len(data)==0 and len(v)>2: return struct.pack('>II',v[2],0)
        o=len(pool[0]); pool[0]+=data
        # keep 8-byte alignment between blobs like CRI tools usually do
        pad=(-len(pool[0]))%8
        pool[0]+=b'\0'*pad if False else b''
        return struct.pack('>II',o,len(data))
def build(t):
    pool=[b'']
    schema=b''
    for f in t.fields:
        schema+=bytes([f['flags']])+struct.pack('>I',f['noff'])
        if f['st']==0x30: schema+=wrval(f['const'],f['ty'],pool)
    rows=b''
    for r in t.rows:
        for f in t.fields:
            if f['st']==0x50: rows+=wrval(r[f['name']],f['ty'],pool)
    rows_off=24+len(schema)
    str_off=rows_off+len(rows)
    data_off=str_off+len(t.strings)
    # strings pool length must keep alignment so datapool starts aligned to 8 like originals
    body=schema+rows+t.strings+pool[0]
    hdr=struct.pack('>HHIIIHHI',t.ver,rows_off,str_off,data_off,t.name_off,len(t.fields),t.rsz,len(t.rows))
    body=hdr+body
    pad=(-len(body))%8
    body+=b'\0'*pad
    return b'@UTF'+struct.pack('>I',len(body))+body

def sget(t,v):
    o=v[1]; return t.strings[o:t.strings.index(b'\0',o)].decode('utf8')
