"""Owned binary64 affine-contract checks; no target/native execution or native-bit equivalence.

Default: print JSON only. --out optionally writes the same result to an explicit path.
"""
import argparse,math,json,pathlib,random

def mm(a,b):return [[sum(a[i][k]*b[k][j] for k in range(4)) for j in range(4)] for i in range(4)]
def I():return [[float(i==j) for j in range(4)] for i in range(4)]
def T(v):
 a=I()
 for i in range(3):a[i][3]=v[i]
 return a

def S(v):
 a=I()
 for i in range(3):a[i][i]=v[i]
 return a

def R(axis,v):
 a=I();c=math.cos(v);s=math.sin(v);i=(axis+1)%3;j=(axis+2)%3;a[i][i]=a[j][j]=c;a[i][j]=-s;a[j][i]=s;return a

def native_columns(rot):
 x,y,z=rot;sx,cx=math.sin(x),math.cos(x);sy,cy=math.sin(y),math.cos(y);sz,cz=math.sin(z),math.cos(z)
 return [(cy*cz,cy*sz,-sy),(sx*sy*cz-cx*sz,sx*sy*sz+cx*cz,sx*cy),(cx*sy*cz+sx*sz,cx*sy*sz-sx*cz,cx*cy)]
def lifted(P,pos,pivot,rot,scale):
 cols=native_columns(rot);Q=I()
 for j in range(3):
  for i in range(4):Q[i][j]=scale[j]*sum(P[i][k]*cols[j][k] for k in range(3))
 t=(-pos[0]/16,pos[1]/16,pos[2]/16)
 for i in range(4):Q[i][3]=P[i][3]+sum(P[i][k]*t[k] for k in range(3))+sum(P[i][k]*pivot[k] for k in range(3))-sum(Q[i][k]*pivot[k] for k in range(3))
 return Q

def reference(P,pos,pivot,rot,scale):
 q=P
 for m in [T((-pos[0]/16,pos[1]/16,pos[2]/16)),T(pivot),R(2,rot[2]),R(1,rot[1]),R(0,rot[0]),S(scale),T(tuple(-x for x in pivot))]:q=mm(q,m)
 return q

def main():
 parser=argparse.ArgumentParser(description=__doc__)
 parser.add_argument("--out",type=pathlib.Path,help="Optional explicit JSON result path")
 args=parser.parse_args()
 rng=random.Random(265);worst=0
 for n in range(128):
  P=mm(T([rng.uniform(-3,3) for _ in range(3)]),mm(R(n%3,rng.uniform(-3,3)),S([rng.uniform(.2,3) for _ in range(3)])))
  pos=[rng.uniform(-32,32) for _ in range(3)];p=[rng.uniform(-2,2) for _ in range(3)];r=[rng.uniform(-3,3) for _ in range(3)];s=[rng.choice([-1,1])*rng.uniform(.2,3) for _ in range(3)]
  a,b=lifted(P,pos,p,r,s),reference(P,pos,p,r,s);err=max(abs(a[i][j]-b[i][j]) for i in range(4) for j in range(4));worst=max(worst,err);assert err<1e-12
 # Hand-check X position16 gives native translation-1; pivot stays fixed under local rotation.
 assert lifted(I(),(16,0,0),(0,0,0),(0,0,0),(1,1,1))[0][3]==-1
 p=(1,2,3);q=lifted(I(),(0,0,0),p,(.2,.3,.4),(2,3,4));v=[sum(q[i][k]*p[k] for k in range(3))+q[i][3] for i in range(3)];assert max(abs(v[i]-p[i]) for i in range(3))<1e-12
 # Parent rotation about Z maps child local+X to+Y; child local position is sign converted first.
 parent=lifted(I(),(0,0,0),(0,0,0),(0,0,math.pi/2),(1,1,1));child=lifted(parent,(-16,0,0),(0,0,0),(0,0,0),(1,1,1));assert abs(child[0][3])<1e-12 and abs(child[1][3]-1)<1e-12
 out=dict(status='PASS',random_algebra_comparisons=128,hand_contract_checks=3,max_absolute_error=worst,arithmetic='Python binary64; algebra consistency only, not native float32/trig-bit equivalence',target_executed=False)
 if args.out is not None:args.out.write_text(json.dumps(out,indent=2)+'\n')
 print(json.dumps(out))
if __name__=='__main__':main()
