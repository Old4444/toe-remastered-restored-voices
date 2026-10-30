import struct
def build_afs2(a,payloads):
    cnt=a['cnt']; al=a['al']; osz=a['osz']; idsz=a['idsz']
    pos=a['hdr_end']; offs=[]; chunks=[]
    for i in range(cnt):
        offs.append(pos)
        start=(pos+al-1)//al*al
        chunks.append((start,payloads[i])); pos=start+len(payloads[i])
    offs.append(pos)
    hdr=bytearray(a['hdr'][:16])
    for i in a['ids']: hdr+=int(i).to_bytes(idsz,'little')
    for o in offs: hdr+=int(o).to_bytes(osz,'little')
    assert len(hdr)==a['hdr_end']
    out=bytearray(hdr)
    for start,p in chunks:
        out+=b'\0'*(start-len(out)); out+=p
    return bytes(out)
