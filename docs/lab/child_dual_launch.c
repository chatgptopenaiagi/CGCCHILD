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
static int child_run(int gate,int had_peer_pidfd,struct prog *filter) {
 if(!install(filter))return 20;
 for(int fd=3;fd<=7;fd++)if(fd!=gate&&(fd<=6||had_peer_pidfd)&&S(3,fd,0,0,0,0,0))return 21;
 for(int fd=3;fd<64;fd++){
  L flags=S(72,fd,1,0,0,0,0);
  if(fd==gate?flags!=1:flags!=-9)return 22;
 }
 int output=-1;
 if(S(56,0x1011,0,&output,0,0,0)!=-1||S(317,1,0,&boot,0,0,0)!=-1)return 23;
 char c=0;if(ready(gate,2000)!=1||S(0,gate,&c,1,0,0,0)!=1||c!='G')return 24;
 return S(3,gate,0,0,0,0,0)?25:0;
}
static int reap(int fd,L pid) {
 int info[32];for(int i=0;i<32;i++)info[i]=0;
 return S(247,3,fd,info,4,0,0)==0&&info[0]==17&&info[2]==1&&info[4]==pid&&info[6]==0;
}
static int run(void) {
 if(!S(102,0,0,0,0,0,0)||S(436,3,0xffffffffU,0,0,0,0))return 1;
 if(S(157,38,1,0,0,0,0)||S(157,4,0,0,0,0,0))return 2;
 int cg[2],wg[2];
 if(S(293,cg,0x80000,0,0,0,0)||cg[0]!=3||cg[1]!=4||S(293,wg,0x80000,0,0,0,0)||wg[0]!=5||wg[1]!=6)return 3;
 if(!install(&boot))return 4;
 int cfd=-1,wfd=-1;
 L cp=S(56,0x1011,0,&cfd,0,0,0);if(cp<0)return 5;
 if(!cp){int code=child_run(3,0,&controller);S(60,code,0,0,0,0,0);__builtin_unreachable();}
 if(cfd!=7||S(72,7,1,0,0,0,0)!=1||ready(7,0)!=0)return 6;
 L wp=S(56,0x1011,0,&wfd,0,0,0);if(wp<0)return 7;
 if(!wp){int code=child_run(5,1,&worker);S(60,code,0,0,0,0,0);__builtin_unreachable();}
 if(wfd!=8||wp==cp||S(72,8,1,0,0,0,0)!=1||ready(7,0)!=0||ready(8,0)!=0)return 8;
 if(!install(&parent)||S(56,0x1011,0,&wfd,0,0,0)!=-1||S(317,1,0,&boot,0,0,0)!=-1)return 9;
 if(S(3,3,0,0,0,0,0)||S(3,5,0,0,0,0,0))return 10;
 const int first=RELEASE_FIRST;
 int firstfd=first?8:7,secondfd=first?7:8;
 int firstgate=first?6:4,secondgate=first?4:6;
 L firstpid=first?wp:cp,secondpid=first?cp:wp;
 char g='G';
 if(S(1,firstgate,&g,1,0,0,0)!=1||ready(firstfd,2000)!=1||ready(secondfd,0)!=0||!reap(firstfd,firstpid))return 11;
 if(S(1,secondgate,&g,1,0,0,0)!=1||ready(secondfd,2000)!=1||!reap(secondfd,secondpid))return 12;
 for(int fd=4;fd<=8;fd++)if(fd!=5&&S(3,fd,0,0,0,0,0))return 13;
 for(int fd=3;fd<64;fd++)if(S(72,fd,1,0,0,0,0)!=-9)return 14;
 return 0;
}
__attribute__((used,noinline)) static void entry(void){int code=run();S(60,code,0,0,0,0,0);__builtin_unreachable();}
__attribute__((naked,noreturn)) void _start(void){__asm__ volatile("andq $-16,%rsp\ncall entry\nud2");}
