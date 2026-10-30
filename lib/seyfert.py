import numpy as np
from PIL import Image
S_DEF,DY_DEF=0.62,-55
def _remap(reg,cx,cy,R,T,s,dy):
    h,w=reg.shape[:2];Rs=R*s
    X=np.arange(w,dtype=np.float32);u=X-cx;au=np.abs(u)
    xo=np.where(au<=Rs,au/s,np.where(au<=T,R+(au-Rs)*(T-R)/max(T-Rs,1e-3),au))
    xs=cx+np.sign(u)*xo
    Y=np.arange(h,dtype=np.float32);ys=cy+(Y-cy-dy)/s
    def idx(c,n):
        c0=np.floor(c).astype(int);f=(c-c0).astype(np.float32);c1=c0+1
        ok0=(c0>=0)&(c0<n);ok1=(c1>=0)&(c1<n);return np.clip(c0,0,n-1),np.clip(c1,0,n-1),f,ok0.astype(np.float32),ok1.astype(np.float32)
    x0,x1,fx,mx0,mx1=idx(xs,w);y0,y1,fy,my0,my1=idx(ys,h)
    def g(yy,xx):return reg[yy[:,None],xx[None,:]]
    wx0=((1-fx)*mx0)[None,:,None];wx1=(fx*mx1)[None,:,None];wy0=((1-fy)*my0)[:,None,None];wy1=(fy*my1)[:,None,None]
    return g(y0,x0)*wy0*wx0+g(y0,x1)*wy0*wx1+g(y1,x0)*wy1*wx0+g(y1,x1)*wy1*wx1
def transform(img,s=S_DEF,dy=DY_DEF):
    a=np.array(img.convert("RGBA")).astype(np.float32);al=a[...,3:4]/255;a[...,:3]*=al
    out=a.copy()
    # peca de cima: bola + pontas
    reg=a[0:511];out[0:511]=_remap(reg,1023,256,222,753,s,dy)
    # 9 celulas 512x512 (centros y 767,1279,1791; x 256,768,1280,1792)
    for cyc in(767,1279,1791):
        for cxc in(256,768,1280,1792):
            if cyc==1791 and cxc>256:continue
            y0,y1=cyc-256,cyc+256;x0,x1=cxc-256,cxc+256
            out[y0:y1,x0:x1]=_remap(a[y0:y1,x0:x1],256,256,222,256,s,dy)
    al2=np.clip(out[...,3:4]/255,1e-4,1);out[...,:3]=np.clip(out[...,:3]/al2,0,255)
    return Image.fromarray(np.clip(out,0,255).astype(np.uint8),"RGBA")
if __name__=="__main__":
    src='/mnt/user-data/uploads/TOE_Projeto/Logo_Titulo/PNG_LOGO2/residenttexture_texture_assets_0x08010058_0db815bcf8d4__ToE_logo_seyfert.png'
    im=Image.open(src);t=transform(im)
    bg=Image.new("RGBA",t.size,(40,60,40,255));bg.alpha_composite(t);bg.convert("RGB").resize((1024,1024)).save("/tmp/lg/seyfert_depois.png")
