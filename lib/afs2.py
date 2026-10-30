import struct
def parse_afs2(awb):
    assert awb[:4]==b'AFS2'
    ver=awb[4]; osz=awb[5]; idsz=awb[6]
    cnt,=struct.unpack('<I',awb[8:12]); al,sub=struct.unpack('<HH',awb[12:16])
    p=16
    ids=[int.from_bytes(awb[p+i*idsz:p+(i+1)*idsz],'little') for i in range(cnt)]; p+=idsz*cnt
    offs=[int.from_bytes(awb[p+i*osz:p+(i+1)*osz],'little') for i in range(cnt+1)]; p+=osz*(cnt+1)
    hdr_end=p
    ents=[]
    for i in range(cnt):
        s=offs[i]; s=(s+al-1)//al*al
        e=offs[i+1]
        ents.append((s,e))
    return dict(ver=ver,osz=osz,idsz=idsz,cnt=cnt,al=al,sub=sub,ids=ids,offs=offs,ents=ents,hdr_end=hdr_end,hdr=awb[:hdr_end])
def build_afs2(info,payloads,orig_awb):
    # payloads: list of bytes in entry order; reuse header layout
    cnt=info['cnt']; al=info['al']; osz=info['osz']; idsz=info['idsz']
    hdr=bytearray(info['hdr'][:16])
    body=b''; offs=[]
    pos=info['hdr_end']
    out=bytearray()
    for i in range(cnt):
        start=(pos+al-1)//al*al
        offs.append(pos)         # stored offset = running (unaligned) position, like original (verified by round trip)
        out+=b'\0'*(start-pos-0) if False else b''
        pos=start+len(payloads[i])
    offs.append(pos)
    return offs
