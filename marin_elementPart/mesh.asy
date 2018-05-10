import three;
import palette;
pen[] allPens=Wheel();
pen[] materialPens = new pen[0];
for(int i=0;i< 0;++i)
  {
   int iPen = round(i*allPens.length/0);
   materialPens[i] = allPens[iPen];
  }
currentprojection=FrontView;
unitsize(4.0 inches/3.220000);
size(5 inches);
real Lx=3.220000;
real Ly=1.000000;
real Lz=1.000000;
real offset=.0125Lx;
real x=0.000000;
real y=0.000000;
real z=0.000000;
triple p0=(x,y,z);
triple p1=(x,y+Ly,z);
triple p2=(x+Lx,y+Ly,z);
triple p3=(x+Lx,y,z);
triple p4=(x,y,z+Lz);
triple p5=(x,y+Ly,z+Lz);
triple p6=(x+Lx,y+Ly,z+Lz);
triple p7=(x+Lx,y,z+Lz);
string strx="$3.22\mbox{m}$";
string stry="$1.00\mbox{m}$";
string strz="$1.00\mbox{m}$";
draw(strx,(x,y-offset,z-offset)--(x+Lx,y-offset,z-offset),-(Y+Z),black,Bars3(Z),Arrows3);
draw(stry,(x-offset,y,z-offset)--(x-offset,y+Ly,z-offset),-(X+Z),black,Bars3(Z),Arrows3);
draw(strz,(x-offset,y-offset,z)--(x-offset,y-offset,z+Lz),-(X+Y),black,Bars3(X),Arrows3);
pen[] allPens=Wheel();
pen[] myPens = new pen[0];
for(int i=0;i< 0;++i)
  {
   int iPen = round(i*allPens.length/0);
   myPens[i] = allPens[iPen];
  }
surface s; path3 p;p = ((0.000000,0.000000,0.000000)--(3.220000,0.000000,0.000000)--(3.220000,1.000000,0.000000)--(0.000000,1.000000,0.000000)--cycle);
s.append(surface(p,planar=true));
p = ((2.395500,0.298500,0.000000)--(2.556500,0.298500,0.000000)--(2.556500,0.701500,0.000000)--(2.395500,0.701500,0.000000)--cycle);
s.append(surface(p,planar=true));
surface s; path3 p;p = ((0.000000,0.000000,0.000000)--(3.220000,0.000000,0.000000)--(3.220000,0.000000,1.000000)--(0.000000,0.000000,1.000000)--cycle);
s.append(surface(p,planar=true));
surface s; path3 p;p = ((3.220000,0.000000,0.000000)--(3.220000,1.000000,0.000000)--(3.220000,1.000000,1.000000)--(3.220000,0.000000,1.000000)--cycle);
s.append(surface(p,planar=true));
surface s; path3 p;p = ((3.220000,1.000000,0.000000)--(0.000000,1.000000,0.000000)--(0.000000,1.000000,1.000000)--(3.220000,1.000000,1.000000)--cycle);
s.append(surface(p,planar=true));
surface s; path3 p;p = ((0.000000,1.000000,0.000000)--(0.000000,0.000000,0.000000)--(0.000000,0.000000,1.000000)--(0.000000,1.000000,1.000000)--cycle);
s.append(surface(p,planar=true));
surface s; path3 p;p = ((0.000000,0.000000,1.000000)--(3.220000,0.000000,1.000000)--(3.220000,1.000000,1.000000)--(0.000000,1.000000,1.000000)--cycle);
s.append(surface(p,planar=true));
surface s; path3 p;p = ((2.395500,0.298500,0.000000)--(2.556500,0.298500,0.000000)--(2.556500,0.298500,0.161000)--(2.395500,0.298500,0.161000)--cycle);
s.append(surface(p,planar=true));
surface s; path3 p;p = ((2.556500,0.298500,0.000000)--(2.556500,0.701500,0.000000)--(2.556500,0.701500,0.161000)--(2.556500,0.298500,0.161000)--cycle);
s.append(surface(p,planar=true));
surface s; path3 p;p = ((2.556500,0.701500,0.000000)--(2.395500,0.701500,0.000000)--(2.395500,0.701500,0.161000)--(2.556500,0.701500,0.161000)--cycle);
s.append(surface(p,planar=true));
surface s; path3 p;p = ((2.395500,0.701500,0.000000)--(2.395500,0.298500,0.000000)--(2.395500,0.298500,0.161000)--(2.395500,0.701500,0.161000)--cycle);
s.append(surface(p,planar=true));
surface s; path3 p;p = ((2.395500,0.298500,0.161000)--(2.556500,0.298500,0.161000)--(2.556500,0.701500,0.161000)--(2.395500,0.701500,0.161000)--cycle);
s.append(surface(p,planar=true));
