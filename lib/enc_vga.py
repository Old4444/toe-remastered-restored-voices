import struct,sys,hcadec
def enc(d,sub=49920):
    ct,inv=hcadec.mk(0x71258D1CD37A52,sub)
    hs=struct.unpack('>H',d[6:8])[0]; h=bytearray(d[:hs]); p=8; fs=None
    while p<hs-2:
        t=bytes(h[p:p+4]).rstrip(b'\0')
        if t==b'fmt': p+=16
        elif t==b'comp': fs=struct.unpack('>H',h[p+4:p+6])[0]; p+=16
        elif t==b'ciph': h[p+4:p+6]=struct.pack('>H',56); h[p]|=0x80;h[p+1]|=0x80;h[p+2]|=0x80;h[p+3]|=0x80 if False else 0; p+=6
        elif t==b'pad': break
        else: raise Exception(t)
    # mask tags
    for tg in (b'fmt',b'comp',b'ciph'):
        i=bytes(h).find(tg)
        for k in range(len(tg)): h[i+k]|=0x80
    h[0]|=0x80;h[1]|=0x80;h[2]|=0x80
    h[4:6]=b"\x03\x00"
    h[hs-2:hs]=struct.pack('>H',hcadec.crc16(bytes(h[:hs-2])))
    out=bytearray(h)
    assert (len(d)-hs)%fs==0
    for q in range(hs,len(d),fs):
        fr=d[q:q+fs-2].translate(bytes(inv)); out+=fr+struct.pack('>H',hcadec.crc16(fr))
    return bytes(out)
if __name__=='__main__':
    o=enc(open(sys.argv[1],'rb').read()); open(sys.argv[2],'wb').write(o); print(o[:40].hex(),len(o))
