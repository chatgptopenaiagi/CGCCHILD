/* Scalar atomic launch and monotonic fixture filters; no production authority. */
typedef unsigned long U;
typedef long L;
__attribute__((noinline,noclone)) static L call(U n,U a,U b,U c,U d,U e,U f) {
 register U r10 __asm__("r10")=d,r8 __asm__("r8")=e,r9 __asm__("r9")=f;L out;
 __asm__ volatile("syscall":"=a"(out):"a"(n),"D"(a),"S"(b),"d"(c),"r"(r10),"r"(r8),"r"(r9):"rcx","r11","memory");return out;
}
#define S(n,a,b,c,d,e,f) call(n,(U)(a),(U)(b),(U)(c),(U)(d),(U)(e),(U)(f))
struct ins {unsigned short code;unsigned char jt,jf;unsigned int k;};
struct prog {unsigned short len;struct ins *filter;};
#include "filters.h"
static int install(struct prog *p){return S(317,1,0,p,0,0,0)==0;}
static int ready(int fd,int timeout) {
 struct {int fd;short events,revents;} p={fd,1,0};
 L n=S(7,&p,1,timeout,0,0,0);
 if(!n)return 0;
 return n==1&&(p.revents&1)&&!(p.revents&40)?1:-1;
}
static int run(void) {
 if(!S(102,0,0,0,0,0,0)||S(436,3,0xffffffffU,0,0,0,0))return 1;
 if(S(157,38,1,0,0,0,0)||S(157,4,0,0,0,0,0))return 2;
 int gate[2];if(S(293,gate,0x80000,0,0,0,0)||gate[0]!=3||gate[1]!=4)return 3;
 int pidfd=-1;
 if(!install(&boot))return 12;
 if(S(435,0,0,0,0,0,0)!=-1||S(56,17,0,&pidfd,0,0,0)!=-1||
    S(56,0x1111,0,&pidfd,0,0,0)!=-1||S(56,0x1011,1,&pidfd,0,0,0)!=-1)return 13;
 L pid=S(56,0x1011,0,&pidfd,0,0,0);
 if(pid<0){S(3,3,0,0,0,0,0);S(3,4,0,0,0,0,0);return pid==-38?77:pid==-1?78:79;}
 if(!pid){
  int code=0;char c=0;
  if(!install(&child)||S(56,0x1011,0,&pidfd,0,0,0)!=-1||S(317,1,0,&boot,0,0,0)!=-1)return 14;
  if(pidfd!=-1||S(3,4,0,0,0,0,0)||ready(3,2000)!=1||S(0,3,&c,1,0,0,0)!=1||c!='G')code=4;
  if(S(3,3,0,0,0,0,0))code=5;
  S(60,code,0,0,0,0,0);__builtin_unreachable();
 }
 if(!install(&parent)||S(56,0x1011,0,&pidfd,0,0,0)!=-1||S(317,1,0,&boot,0,0,0)!=-1)return 15;
 if(S(59,0,0,0,0,0,0)!=-1||S(41,1,1,0,0,0,0)!=-1||S(434,pid,0,0,0,0,0)!=-1)return 16;
 if(pidfd!=5||S(72,5,1,0,0,0,0)!=1||ready(5,0)!=0||ready(63,0)!=-1)return 6;
 if(S(3,3,0,0,0,0,0))return 7;
 char c='G';if(S(1,4,&c,1,0,0,0)!=1||S(3,4,0,0,0,0,0)||ready(5,2000)!=1)return 8;
 int info[32];for(int i=0;i<32;i++)info[i]=0;
 if(S(247,3,5,info,4,0,0)||info[0]!=17||info[2]!=1||info[4]!=pid||info[6]!=0||ready(5,0)!=1)return 9;
 if(S(3,5,0,0,0,0,0))return 10;
 for(int fd=3;fd<64;fd++)if(S(72,fd,1,0,0,0,0)!=-9)return 11;
 return 0;
}
void _start(void){int code=run();S(60,code,0,0,0,0,0);__builtin_unreachable();}
