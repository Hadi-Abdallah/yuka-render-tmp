import cv2,numpy as np,json
B='bk/'
H=1000
def rect(im,q,w=None):
    q=np.float32(q);wa=(np.linalg.norm(q[1]-q[0])+np.linalg.norm(q[2]-q[3]))/2;ha=(np.linalg.norm(q[3]-q[0])+np.linalg.norm(q[2]-q[1]))/2
    w=w or int(round(wa*H/ha));M=cv2.getPerspectiveTransform(q,np.float32([[0,0],[w,0],[w,H],[0,H]]));return cv2.warpPerspective(im,M,(w,H),flags=cv2.INTER_LANCZOS4,borderMode=cv2.BORDER_REPLICATE)
S={}
im8=cv2.imread(B+'8.png');k=1600/2400
A8=[[(44,70),(172,66),(297,1100),(190,1104)],[(194,76),(306,74),(400,1095),(298,1100)],[(314,80),(403,80),(471,1095),(402,1097)],[(406,88),(484,86),(547,1088),(477,1090)],[(486,90),(598,88),(647,1090),(551,1092)],[(601,96),(723,98),(761,1085),(649,1090)],[(727,102),(866,102),(889,1080),(765,1083)],[(874,102),(954,104),(971,1075),(894,1078)],[(958,110),(1055,112),(1063,1072),(975,1074)],[(1057,114),(1200,120),(1200,1068),(1067,1072)]]
B8=[[(3,120),(101,120),(98,1068),(5,1070)],[(104,122),(214,122),(200,1066),(100,1068)],[(218,128),(331,126),(311,1060),(202,1064)],[(334,128),(439,124),(405,1058),(314,1060)],[(442,126),(567,128),(529,1056),(409,1058)],[(579,134),(686,132),(643,1050),(533,1054)],[(693,142),(831,140),(769,1046),(647,1050)],[(844,140),(965,138),(876,1042),(779,1046)],[(969,138),(1079,140),(991,1040),(899,1042)],[(1079,152),(1187,154),(1092,1035),(999,1038)]]
S['fatawa']=[rect(im8,[((x)*k,(y+120)*k) for x,y in q]) for q in A8]+[rect(im8,[((x+1200)*k,(y+120)*k) for x,y in q]) for q in B8]
im3=cv2.imread(B+'3.png');F=[[(184,8),(367,8),(331,1172),(167,1165)],[(370,8),(534,8),(499,1180),(335,1172)],[(537,6),(694,6),(639,1190),(503,1185)],[(697,4),(867,4),(807,1200),(643,1195)],[(870,2),(1089,2),(1017,1215),(811,1208)],[(1092,2),(1261,2),(1179,1225),(1021,1220)],[(1264,2),(1417,2),(1327,1232),(1183,1230)],[(1420,2),(1604,2),(1499,1240),(1331,1236)],[(1607,2),(1754,2),(1641,1250),(1503,1245)]]
S['fath']=[rect(im3,[(400+x/3,10+y/3) for x,y in q]) for q in F]
im5=cv2.imread(B+'5.png');K=[[(34,38),(134,30),(144,1468),(43,1476)],[(138,28),(254,34),(249,1412),(148,1448)]]
S['khallal']=[rect(im5,[(690+.9286*x,80+.9267*y) for x,y in q],w) for q,w in zip(K,(150,160))]
im4=cv2.imread(B+'4.png');Q=[[(60,12),(203,36),(200,1420),(58,1466)],[(206,36),(338,66),(334,1370),(203,1420)]]
S['sunna']=[rect(im4,[(600+.606*x,50+.6067*y) for x,y in q],w) for q,w in zip(Q,(205,205))]
im2=cv2.imread(B+'2.png');S['bukhari']=[rect(im2,[(427,8),(587,8),(587,590),(427,590)],245)]
im9=cv2.imread(B+'9.png');xs=[227,270,316.5,363.5,414.5,466];tp=[31,29,27,25,23,22];bt=[300,302,303,304,305,305]
S['umda']=[rect(im9,[(xs[i]+1,tp[i]),(xs[i+1]-1,tp[i+1]),(xs[i+1]-1,bt[i+1]),(xs[i]+1,bt[i])],w) for i,w in enumerate((165,165,168,170,172))]
# bukhari volumes: repaint the numeral
from PIL import Image,ImageDraw,ImageFont
f=ImageFont.truetype('C:/Windows/Fonts/arabtype.ttf',54);b0=S['bukhari'][0];out=[]
g=cv2.cvtColor(b0,cv2.COLOR_BGR2RGB)
for d in '١٢٣٤٥':
    p=Image.fromarray(g.copy());dr=ImageDraw.Draw(p);cx,cy=b0.shape[1]*.505,94
    if d!='١': dr.ellipse((cx-13,cy-13,cx+13,cy+13),fill=(18,17,18));dr.text((cx,cy-2),d,font=f,fill=(225,205,160),anchor='mm')
    out.append(cv2.cvtColor(np.array(p),cv2.COLOR_RGB2BGR))
S['bukhari']=out
meta={};col=[];x=0
for n,l in S.items():
    meta[n]=[]
    for s in l:
        # the photo's own light: flatten the side falloff a little, keep the print
        s=s.astype('f4');lum=s.mean(2);c=cv2.GaussianBlur(lum.mean(0,keepdims=True).repeat(5,0),(0,0),max(3,s.shape[1]*.12))[2];gain=np.clip(np.median(c)/np.maximum(c,8),.8,1.35);s=np.clip(s*gain[None,:,None],0,255).astype('u1')
        if n in('umda','fath','bukhari','fatawa'): s=cv2.addWeighted(s,1.35,cv2.GaussianBlur(s,(0,0),1.6),-.35,0)
        meta[n].append([x,s.shape[1]]);col.append(s);x+=s.shape[1]
atlas=np.hstack(col);hsv=cv2.cvtColor(atlas,cv2.COLOR_BGR2HSV).astype('f4')
gold=np.clip((hsv[...,2]-95)/70,0,1)*(np.clip((34-abs(hsv[...,0]-22))/14,0,1)*np.clip((hsv[...,1]-35)/50,0,1)+np.clip((40-hsv[...,1])/30,0,1)*np.clip((hsv[...,2]-150)/60,0,1)).clip(0,1)
cv2.imwrite(B+'atlas.png',atlas);cv2.imwrite(B+'gold.png',(gold*255).astype('u1'));json.dump({'W':atlas.shape[1],'H':H,'s':meta},open(B+'meta.json','w'))
print(atlas.shape,{n:len(l) for n,l in S.items()});cv2.imwrite(B+'av.png',cv2.resize(atlas,(2000,int(2000*H/atlas.shape[1]))))
t=meta['fath'][0][0];cv2.imwrite(B+'av2.png',atlas[:,t:])
