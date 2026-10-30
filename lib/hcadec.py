import struct,subprocess,os
def crc16(b):
    t=[]
    for i in range(256):
        c=i<<8
        for _ in range(8): c=((c<<1)^0x8005) if c&0x8000 else c<<1
        t.append(c&0xFFFF)
    c=0
    for x in b: c=((c<<8)&0xFFFF)^t[(c>>8)^x]
    return c
def tbl(key):
    mul=((key&1)<<3)|5; add=(key&14)|1; key>>=4; r=[]
    for i in range(16):
        key=(key*mul+add)&0xF; r.append(key)
    return r
def mk(keycode,subkey):
    if subkey: keycode=(keycode*(((subkey<<16)|((~subkey+2)&0xFFFF))))&0xFFFFFFFFFFFFFFFF
    keycode-=1
    kc=[(keycode>>(8*i))&0xFF for i in range(7)]
    seed=[kc[1],kc[1]^kc[6],kc[2]^kc[3],kc[2],kc[2]^kc[1],kc[3]^kc[4],kc[3],kc[3]^kc[2],kc[4]^kc[5],kc[4],kc[4]^kc[3],kc[5]^kc[6],kc[5],kc[5]^kc[4],kc[6]^kc[1],kc[6]]
    br=tbl(kc[0]); base=[0]*256
    for r in range(16):
        bc=tbl(seed[r]); nb=br[r]<<4
        for c in range(16): base[r*16+c]=nb|bc[c]
    ct=[0]*256; x=0; pos=1
    for i in range(256):
        x=(x+17)&0xFF
        if base[x]!=0 and base[x]!=0xFF: ct[pos]=base[x]; pos+=1
    ct[0]=0; ct[255]=255
    inv=[0]*256
    for i in range(256): inv[ct[i]]=i
    return ct,inv
def decrypt(data,key=0x71258D1CD37A52,subkey=49920):
    ct,inv=mk(key,subkey)
    hs=struct.unpack('>H',data[6:8])[0]
    h=bytearray(data[:hs]); 
    # find ciph and comp
    p=8; fs=None
    while p<hs-2:
        tag=bytes(h[p:p+4]); t=bytes(b&0x7f for b in tag)
        if t==b'fmt\0': p+=16
        elif t==b'comp': fs=struct.unpack('>H',h[p+4:p+6])[0]; p+=16
        elif t==b'dec\0': 
            fs=fs; p+=12
        elif t==b'ciph': h[p+4:p+6]=b'\0\0'; p+=6
        elif t in (b'vbr\0',): p+=8
        elif t==b'ath\0': p+=6
        elif t==b'loop': p+=16
        elif t==b'rva\0': p+=8
        elif t==b'comm': p+=5
        elif t==b'pad\0': break
        else: break
    # unmask tags
    h=bytearray(h)
    q=8
    # header may be masked; unmask 4-byte tags handled by ffmpeg? clear high bits of known tags
    for tg in (b'fmt',b'comp',b'dec',b'ciph',b'ath',b'loop',b'vbr',b'rva',b'comm',b'pad'):
        pass
    h[:3]=b'HCA'
    h[hs-2:hs]=struct.pack('>H',crc16(bytes(h[:hs-2])))
    out=bytearray(h)
    for i in range(hs,len(data),fs):
        fr=bytearray(data[i:i+fs])
        for j in range(fs-2): fr[j]=inv[fr[j]] if False else ct[fr[j]]
        fr[fs-2:fs]=struct.pack('>H',crc16(bytes(fr[:fs-2])))
        out+=fr
    return bytes(out)
