from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageFilter
import numpy as np
import math, random, functools, subprocess, wave, json, sys, os, shutil
from pathlib import Path

ROOT=Path(__file__).resolve().parent
WORK=ROOT/'work'; OUT=ROOT/'outputs'
WORK.mkdir(parents=True, exist_ok=True)
OUT.mkdir(parents=True, exist_ok=True)
W,H,FPS,DURATION=1920,1080,30,30
INK=(17,21,18); CREAM=(239,235,218); AMBER=(232,188,78); MUTED=(136,148,128)
PAPER=(241,239,231); BLUE=(176,218,230)
def find_font(env_name, candidates, fallback=None):
 override=os.environ.get(env_name)
 if override:
  if not Path(override).is_file():raise FileNotFoundError(f"{env_name} 指定的字体不存在：{override}")
  return override
 for candidate in candidates:
  if Path(candidate).is_file():return candidate
 if fallback:return fallback
 raise FileNotFoundError("未找到中文字体，请通过 CJK_FONT 环境变量指定 .ttf/.ttc/.otf 字体文件。")
CN=find_font('CJK_FONT', ['/System/Library/Fonts/STHeiti Medium.ttc','/System/Library/Fonts/PingFang.ttc','C:/Windows/Fonts/msyh.ttc','/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'])
LATIN=find_font('LATIN_FONT', ['/System/Library/Fonts/Avenir Next.ttc','C:/Windows/Fonts/arial.ttf','/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'],CN)
CONDENSED=find_font('DISPLAY_FONT', ['/System/Library/Fonts/Avenir Next Condensed.ttc','C:/Windows/Fonts/arialbd.ttf','/usr/share/fonts/truetype/dejavu/DejaVuSansCondensed-Bold.ttf'],LATIN)
MONO=find_font('MONO_FONT', ['/System/Library/Fonts/Menlo.ttc','C:/Windows/Fonts/consola.ttf','/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf'],LATIN)
@functools.lru_cache(maxsize=180)
def font(size,face=CN):return ImageFont.truetype(face,size)
def ease(x):x=max(0,min(1,x));return 1-(1-x)**3
def clamp(x):return max(0,min(1,x))
def text(im,xy,txt,size=30,color=CREAM,face=CN,anchor='lt'):
 for i,part in enumerate(txt.split('\n')):ImageDraw.Draw(im).text((xy[0],xy[1]+i*int(size*1.4)),part,font=font(size,face),fill=color,anchor=anchor,stroke_width=0)
def tracked(im,xy,txt,size=18,color=MUTED,spacing=4):
 x,y=xy;d=ImageDraw.Draw(im);f=font(size,MONO)
 for c in txt:d.text((x,y),c,font=f,fill=color,anchor='lt');x+=d.textlength(c,font=f)+spacing
def line(im,xy,color=(68,76,63),width=1):ImageDraw.Draw(im).line(xy,fill=color,width=width)
def rr(im,box,r,fill,outline=None,width=1):ImageDraw.Draw(im).rounded_rectangle(box,r,fill=fill,outline=outline,width=width)
def smooth_text(im,xy,txt,size,color,progress,face=CN):
 layer=Image.new('RGBA',(W,H));text(layer,(xy[0],xy[1]+int(24*(1-ease(progress)))),txt,size,color,face)
 layer.putalpha(layer.getchannel('A').point(lambda a:int(a*ease(progress))));im.paste(layer,(0,0),layer)

def make_bg(light=False):
 y,x=np.mgrid[0:H,0:W];dist=((x-W*.52)/(W*.8))**2+((y-H*.48)/(H*.9))**2
 rng=np.random.default_rng(31);grain=rng.normal(0,.6,(H,W))
 base=np.array(PAPER if light else INK);glow=1.5 if light else 8
 a=np.clip(base[None,None,:]+(glow*(1-np.minimum(1,dist))+grain)[:,:,None],0,255).astype('uint8')
 return Image.fromarray(a)
DARK_BG=make_bg();LIGHT_BG=make_bg(True)

def brand(im,light=False):
 c=(39,47,36) if light else CREAM;d=ImageDraw.Draw(im)
 for i in range(4):
  x=90+(i%2)*16;y=58+(i//2)*20;rr(im,(x,y,x+11,y+15),2,AMBER if i==3 else c)
 text(im,(140,59),'候机楼',26,c);tracked(im,(140,96),'THE FLAP TERMINAL',11,(119,130,109) if light else MUTED,2)
def topmeta(im,word,light=False):tracked(im,(1420,66),word,13,(117,126,106) if light else MUTED,2)
def footer(im,t,light=False):
 c=(182,189,171) if light else (58,68,53);d=ImageDraw.Draw(im)
 d.line((90,1018,1830,1018),fill=c,width=1)
 d.line((90,1018,90+int(1740*t/DURATION),1018),fill=(128,141,103) if light else AMBER,width=2)
 tracked(im,(90,1039),'MECHANICAL DISPLAY / 001',12,(123,134,110) if light else MUTED,2)
 text(im,(1830,1040),f'{int(t):02d} / 30',14,(123,134,110) if light else MUTED,MONO,'rt')

PALETTES={'warm':(CREAM,(34,39,33),(41,47,39)), 'amber':(AMBER,(38,40,29),(45,48,34)), 'cool':(BLUE,(34,45,48),(40,54,57))}
@functools.lru_cache(maxsize=16000)
def tile(char,w,h,palette='warm',accent=False):
 fg,top,bottom=PALETTES[palette];fg=AMBER if accent and palette=='warm' else fg
 im=Image.new('RGB',(w,h),(10,14,10));d=ImageDraw.Draw(im)
 d.rounded_rectangle((0,0,w-1,h-2),radius=max(2,w//13),fill=top)
 d.rounded_rectangle((0,h//2,w-1,h-2),radius=max(2,w//13),fill=bottom)
 d.rectangle((0,h//2,w-1,h//2+2),fill=bottom)
 chinese=any(ord(c)>255 for c in char)
 f=font(int(w*(.82 if chinese else 1.10)), CN if chinese else CONDENSED)
 d.text((w/2,h/2-1),char,font=f,fill=fg,anchor='mm')
 for yy in range(h//2-6,h//2):
  layer=Image.new('RGBA',(w,1),(0,0,0,int(20*(yy-(h//2-6))/6)));im.paste(layer,(0,yy),layer)
 d.line((1,0,w-2,0),fill=tuple(min(255,c+9) for c in top))
 return im

def flap(im,x,y,w,h,old,new,phase,palette='warm',accent=False):
 a=tile(old,w,h,palette,accent);b=tile(new,w,h,palette,accent);half=h//2
 if phase<=0 or old==new:im.paste(a,(x,y))
 elif phase>=1:im.paste(b,(x,y))
 else:
  im.paste(b.crop((0,0,w,half)),(x,y));im.paste(a.crop((0,half,w,h)),(x,y+half))
  if phase<.5:
   height=max(1,round(half*math.cos(math.pi*phase)))
   leaf=a.crop((0,0,w,half)).resize((w,height),Image.Resampling.BILINEAR)
   leaf=ImageEnhance.Brightness(leaf).enhance(1-.5*math.sin(math.pi*phase))
   im.paste(leaf,(x,y+half-height))
  else:
   height=max(1,round((h-half)*math.sin(math.pi*(phase-.5))))
   leaf=b.crop((0,half,w,h)).resize((w,height),Image.Resampling.BILINEAR)
   leaf=ImageEnhance.Brightness(leaf).enhance(.5+.5*math.sin(math.pi*(phase-.5)))
   im.paste(leaf,(x,y+half))
 d=ImageDraw.Draw(im);d.line((x,y+half,x+w-1,y+half),fill=(5,9,6),width=max(1,h//100))
 d.line((x+1,y+half-1,x+1,y+half+2),fill=(3,7,4),width=2);d.line((x+w-2,y+half-1,x+w-2,y+half+2),fill=(3,7,4),width=2)

POOL='ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-+/'
def random_char(seed,index,cycle):
 n=(seed*214013+(index+3)*2531011+(cycle+7)*1103515245)&0x7fffffff
 n=(n^(n>>13))*1274126177
 return POOL[n%len(POOL)]
def animated_char(old,new,t,start,index,seed,steps=9,speed=.08,stagger=.009,force=False):
 if old==new and not force:return old,new,1
 elapsed=t-start-index*stagger
 if elapsed<0:return old,old,0
 cycle=int(elapsed/speed);phase=(elapsed/speed)%1
 if cycle>=steps:return new,new,1
 a=old if cycle==0 else random_char(seed,index,cycle-1)
 b=new if cycle==steps-1 else random_char(seed,index,cycle)
 return a,b,phase
def row(im,txt,x,y,w,h,gap,t,start,seed=1,old=None,palette='warm',steps=10,speed=.08,stagger=.01,force=False,flight=False):
 old=old if old is not None else ' '*len(txt)
 for i,c in enumerate(txt):
  if flight and i in (5,12,25,30):continue
  a,b,p=animated_char(old[i] if i<len(old) else ' ',c,t,start,i,seed,steps,speed,stagger,force)
  flap(im,x+i*(w+gap),y,w,h,a,b,p,palette,flight and i>=31)

def fit(s,n):return s[:n].ljust(n)
def flightline(time,code,city,gate,status):return ' '.join(fit(s,n) for s,n in zip([time,code,city,gate,status],[5,6,12,4,8]))
FLIGHTS=[flightline('09:25','MU5101','SHANGHAI','A12','检票中'),flightline('09:40','CA1831','BEIJING','B06','准点'),flightline('10:05','JL0820','TOKYO','A08','准点'),flightline('10:20','SQ0833','SINGAPORE','C03','延误'),flightline('10:45','CX0365','HONG KONG','B11','检票中')]
NEW_FLIGHT=flightline('11:30','QF0288','SYDNEY','C16','准点')
def plane(im,x,y,color=AMBER):
 d=ImageDraw.Draw(im);d.polygon([(x+2,y+20),(x+25,y+16),(x+40,y+2),(x+45,y+4),(x+32,y+21),(x+34,y+40),(x+29,y+43),(x+24,y+26),(x+7,y+29)],fill=color)
def airport_board(im,t):
 x,y,bw,bh=150,320,1620,600
 rr(im,(x,y,x+bw,y+bh),18,(13,17,13),(58,66,51),2)
 rr(im,(x+33,y+30,x+98,y+95),7,(27,34,24),(67,77,58));plane(im,x+43,y+40)
 text(im,(x+119,y+33),'出发航班',32);tracked(im,(x+121,y+79),'DEPARTURES / TERMINAL 01',13,MUTED,2)
 text(im,(x+bw-34,y+37),'09:21:08',29,CREAM,MONO,'rt');text(im,(x+bw-34,y+82),'模拟航班 · 加速演示',16,MUTED,CN,'rt')
 w,h,gap=35,59,4;left=x+50;ty=y+136
 for title,col in [('时间 TIME',0),('航班 FLIGHT',6),('目的地 DESTINATION',13),('登机口',26),('状态 STATUS',31)]:text(im,(left+col*(w+gap),ty),title,14,MUTED)
 for r,base in enumerate(FLIGHTS):
  tt=t;old=None;target=base;start=.05+r*.055;seed=20+r
  if r==0:
   closed=flightline('09:25','MU5101','SHANGHAI','A12','停止检票')
   if tt>=2.0:old=base;target=closed;start=2.0;seed=101
   if tt>=3.65:old=closed;target=' '*39;start=3.65;seed=102
   if tt>=5.6:old=' '*39;target=NEW_FLIGHT;start=5.6;seed=103
  if r==3 and tt>=5.8:old=base;target=flightline('10:20','SQ0833','SINGAPORE','C03','检票中');start=5.8;seed=105
  row(im,target,left,y+174+r*75,w,h,gap,tt,start,seed,old,steps=9,speed=.067,stagger=.005,flight=True)
 line(im,(x+35,y+553,x+bw-35,y+553),(49,58,43))
 rr(im,(x+38,y+575,x+46,y+583),4,AMBER)
 text(im,(x+59,y+571),'自动运行 · 无需手动切换',17,MUTED)
 text(im,(x+bw-36,y+572),'05 ROWS × 39 FLAPS',15,MUTED,MONO,'rt')

def chip(im,x,y,label,on=False):
 w=int(ImageDraw.Draw(im).textlength(label,font=font(21)))+44
 rr(im,(x,y,x+w,y+48),24,(40,49,32) if on else (229,231,218),None)
 text(im,(x+22,y+13),label,21,CREAM if on else (92,106,76));return w

def scene_intro(t):
 im=DARK_BG.copy();brand(im);topmeta(im,'A LITTLE NOSTALGIA')
 smooth_text(im,(90,179),'听，文字正在抵达。',64,CREAM,t/.8)
 tracked(im,(94,272),'SOME THINGS DESERVE A LITTLE MOTION.',18,MUTED,3)
 s='NEXT STOP';w,h,gap=148,226,12;total=len(s)*(w+gap)-gap;x=(W-total)//2
 rr(im,(x-35,364,x+total+35,670),16,(13,17,13),(57,64,49))
 row(im,s,x,402,w,h,gap,t,.25,88,steps=13,speed=.075,stagger=.028)
 text(im,(W//2,775),'把机场里的机械浪漫，带回你的屏幕。',30,MUTED,anchor='mt')
 footer(im,t);return im

def scene_airport(t):
 im=DARK_BG.copy();brand(im);topmeta(im,'01 / ALWAYS IN MOTION')
 smooth_text(im,(90,165),'下一班，自动抵达。',62,CREAM,t/.6)
 text(im,(94,258),'随机检票 · 延误恢复 · 离场换新',25,MUTED)
 airport_board(im,t)
 footer(im,t+3.5);return im

def scene_custom(t):
 im=LIGHT_BG.copy();brand(im,True);topmeta(im,'02 / MAKE IT YOURS',True)
 smooth_text(im,(90,165),'你的文字，就是下一站。',62,(36,46,30),t/.6)
 text(im,(94,257),'中文、字母、数字与符号，都有自己的出场方式。',25,(117,130,102))
 x,y,bw,bh=150,330,1620,506;rr(im,(x,y,x+bw,y+bh),16,(18,24,17),(59,69,49),2)
 text(im,(x+44,y+30),'自由文字',24,CREAM);tracked(im,(x+bw-475,y+34),'YOUR WORDS. YOUR RULES.',14,MUTED,2)
 palette='warm' if t<2.3 else 'amber' if t<4.45 else 'cool'
 targets=['MAKE IT YOURS'.center(22),'下一站，自由'.center(22),'HELLO, WORLD'.center(22)]
 for i,s in enumerate(targets):row(im,s,x+151,y+99+i*118,55,91,5,t,.12+i*.16,200+i,palette=palette,steps=12,speed=.072,stagger=.014)
 chips=['自定义字符集','60–220 ms 翻动速度','三种配色','机械音效']
 xx=346
 for i,c in enumerate(chips):xx+=chip(im,xx,884,c,i==int(t/1.75)%4)+15
 footer(im,t+12,True);return im

rng=random.Random(9482);CITIES=['SHANGHAI','BEIJING','TOKYO','SINGAPORE','LONDON','PARIS','SEOUL','SYDNEY','DUBAI','BANGKOK']
BIG_ROWS=[flightline(f'{9+i//4:02d}:{(i%4)*15:02d}',rng.choice(['MU','SQ','CA','JL','QF'])+str(rng.randint(1000,9999)),rng.choice(CITIES),rng.choice('ABC')+str(rng.randint(1,24)).zfill(2),rng.choice(['准点','检票中','延误','停止检票'])) for i in range(50)]
def scene_fifty(t):
 im=DARK_BG.copy();brand(im);topmeta(im,'03 / ROOM TO IMAGINE')
 text(im,(90,220),'不止一行灵感。',49,CREAM)
 text(im,(80,316),'50',230,AMBER,CONDENSED)
 text(im,(345,475),'行',46,CREAM)
 text(im,(96,620),'让整个世界，\n一起翻动。',43,CREAM)
 text(im,(96,770),'航班与文字模式\n最多 50 行自由排布',27,MUTED)
 vx,vy,vw,vh=640,174,1190,770
 panel=Image.new('RGB',(vw,vh),(16,21,15));d=ImageDraw.Draw(panel)
 tracked(panel,(34,24),'50 ROWS / UNLIMITED DESTINATIONS',14,MUTED,1)
 head=88;stride=61;scroll=ease(t/5)*1450
 first=int(scroll//stride);offset=int(scroll%stride)
 for r in range(first,min(50,first+14)):
  yy=head+(r-first)*stride-offset
  row(panel,BIG_ROWS[r],36,yy,25,44,3,t,0,r+500,old=BIG_ROWS[r],steps=1,flight=True)
 d.rectangle((0,0,vw,head-8),fill=(16,21,15));tracked(panel,(34,24),'50 ROWS / 39 FLAPS',15,MUTED,2)
 text(panel,(vw-36,26),'↕ 自由滚动',17,MUTED,anchor='rt')
 rr(panel,(vw-14,90,vw-9,vh-20),3,(54,64,47));bar_y=94+int((vh-240)*clamp(t/5));rr(panel,(vw-14,bar_y,vw-9,bar_y+125),3,(166,179,142))
 im.paste(panel,(vx,vy));rr(im,(vx,vy,vx+vw,vy+vh),12,None,(66,78,55),2)
 footer(im,t+19);return im

def scene_outro(t):
 im=DARK_BG.copy();brand(im);topmeta(im,'READY WHEN YOU ARE')
 smooth_text(im,(W//2-152,211),'候机楼',100,CREAM,t/.7)
 text(im,(W//2,344),'机械翻牌显示器',30,MUTED,anchor='mt')
 s='LET WORDS FLY';w,h,gap=101,156,8;total=len(s)*(w+gap)-gap;x=(W-total)//2
 row(im,s,x,445,w,h,gap,t,.15,999,steps=15,speed=.066,stagger=.022,palette='amber')
 text(im,(W//2,681),'一个 HTML   /   双击打开   /   离线可用',31,CREAM,anchor='mt')
 text(im,(W//2,772),'把下一站，交给想象。',31,MUTED,anchor='mt')
 footer(im,t+24);return im

def frame(t):
 if t<3.5:im=scene_intro(t)
 elif t<12:im=scene_airport(t-3.5)
 elif t<19:im=scene_custom(t-12)
 elif t<24:im=scene_fifty(t-19)
 else:im=scene_outro(t-24)
 # Short dip transitions keep typography readable and give the mechanical cuts weight.
 boundaries=[3.5,12,19,24]
 for cut in boundaries:
  dist=abs(t-cut)
  if dist<.16:im=ImageEnhance.Brightness(im).enhance(.20+.80*dist/.16)
 if t<.3:im=ImageEnhance.Brightness(im).enhance(.25+.75*ease(t/.3))
 if t>29.5:im=ImageEnhance.Brightness(im).enhance(1-.65*ease((t-29.5)/.5))
 return im

def audio():
 sr=48000;n=int(sr*DURATION);result=np.zeros((n,2),dtype=np.float64);tt=np.arange(n)/sr
 # Original, restrained ambient bed: no licensed or third-party audio.
 chords=[(0,7.5,[146.832,220,293.665,349.228]),(7.5,7.5,[130.813,195.998,261.626,329.628]),(15,7.5,[174.614,261.626,349.228,440]),(22.5,7.5,[146.832,220,293.665,440])]
 for start,dur,notes in chords:
  a=int(start*sr);b=min(n,int((start+dur)*sr));t=np.arange(b-a)/sr
  env=np.minimum(1,t/1.5)*np.minimum(1,(dur-t)/1.5)
  for j,f in enumerate(notes):
   tone=np.sin(2*np.pi*f*t+.3*j)+.17*np.sin(2*np.pi*2*f*t)
   pan=.35+.3*(j%2);gain=.016*env
   result[a:b,0]+=tone*gain*(1-pan);result[a:b,1]+=tone*gain*pan
 rng=np.random.default_rng(9823)
 def click(pos,volume=.14,pan=.5):
  a=int(pos*sr);size=int(.028*sr);b=min(n,a+size)
  if a<0 or a>=n:return
  t=np.arange(b-a)/sr;noise=rng.uniform(-1,1,len(t));sig=(noise*.65+np.sin(2*np.pi*1850*t)*.35)*np.exp(-t/0.0038)*volume
  result[a:b,0]+=sig*math.sqrt(1-pan);result[a:b,1]+=sig*math.sqrt(pan)
 # Flap bursts follow the animated shots and lifecycle changes.
 for start,end in [(.25,2.0),(3.65,4.8),(5.5,6.5),(7.15,8.25),(9.1,10.3),(12.12,14.0),(24.15,25.9)]:
  for pos in np.arange(start,end,.039):click(float(pos),float(rng.uniform(.10,.21)),float(rng.uniform(.15,.85)))
 for cut in [3.5,12,19,24]:
  a=int(cut*sr);size=int(.4*sr);t=np.arange(size)/sr
  sig=np.sin(2*np.pi*(65*t-22*t*t))*np.exp(-t/0.08)*.20
  result[a:a+size]+=sig[:,None]
 for pos in np.arange(0,DURATION,.75):
  a=int(pos*sr);size=int(.11*sr);b=min(n,a+size);t=np.arange(b-a)/sr
  sig=np.sin(2*np.pi*880*t)*np.exp(-t/.025)*.009
  result[a:b,0]+=sig;result[a:b,1]+=sig
 env=np.minimum(1,tt/.4)*np.minimum(1,(DURATION-tt)/.7);result*=env[:,None]
 peak=np.max(np.abs(result));result*=.78/max(peak,.01)
 with wave.open(str(WORK/'soundtrack.wav'),'wb') as f:f.setnchannels(2);f.setsampwidth(2);f.setframerate(sr);f.writeframes((np.clip(result,-1,1)*32767).astype('<i2').tobytes())

def previews():
 times=[1.8,4.9,6.65,8.9,10.9,13.9,17.5,21.5,27]
 thumbs=[]
 for t in times:
  im=frame(t);im.save(WORK/f'frame-{t}.jpg',quality=92)
  thumb=im.resize((640,360),Image.Resampling.LANCZOS);thumb=thumb.copy();rr(thumb,(10,10,82,40),5,(0,0,0));text(thumb,(20,18),f'{t:.1f}s',16,CREAM,MONO);thumbs.append(thumb)
 sheet=Image.new('RGB',(1920,1080));
 for i,img in enumerate(thumbs):sheet.paste(img,((i%3)*640,(i//3)*360))
 sheet.save(WORK/'contact-sheet.jpg',quality=94)
 frame(27).save(OUT/'候机楼-宣传片封面.jpg',quality=95)

def render():
 ffmpeg=os.environ.get('FFMPEG_BIN') or shutil.which('ffmpeg')
 if not ffmpeg:raise RuntimeError('未找到 FFmpeg，请安装并加入 PATH，或设置 FFMPEG_BIN 为完整路径。')
 audio()
 target=OUT/'候机楼-30秒宣传片.mp4'
 cmd=[ffmpeg,'-y','-hide_banner','-loglevel','warning','-f','rawvideo','-vcodec','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',str(FPS),'-i','pipe:0','-i',str(WORK/'soundtrack.wav'),'-c:v','libx264','-preset','fast','-crf','18','-pix_fmt','yuv420p','-c:a','aac','-b:a','192k','-movflags','+faststart','-shortest',str(target)]
 p=subprocess.Popen(cmd,stdin=subprocess.PIPE)
 for i in range(FPS*DURATION):
  p.stdin.write(frame(i/FPS).tobytes())
  if i%90==0:print(f'Rendered {i//FPS:02d}/{DURATION}s',flush=True)
 p.stdin.close();assert p.wait()==0
 print(str(target),flush=True)

if __name__=='__main__':
 if '--preview' in sys.argv:previews()
 else:render()
