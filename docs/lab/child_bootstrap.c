/* CGCCHILD unprivileged inert lab only. No cgroup or credential operations.
 * No argv, shell, transport, arbitrary attach or executable selection. */
typedef unsigned long U;
typedef long L;
struct ins { unsigned short code; unsigned char jt,jf; unsigned int k; };
struct prog { unsigned short len; struct ins *filter; };
__attribute__((noinline,noclone)) static L call(L n,U a,U b,U c,U d,U e,U f) {
 register U r10 __asm__("r10")=d, r8 __asm__("r8")=e, r9 __asm__("r9")=f;
 L out;
 __asm__ volatile("syscall":"=a"(out):"a"(n),"D"(a),"S"(b),"d"(c),"r"(r10),"r"(r8),"r"(r9):"rcx","r11","memory");
 return out;
}
#define S(n,a,b,c,d,e,f) call(n,(U)(a),(U)(b),(U)(c),(U)(d),(U)(e),(U)(f))
#include "child_filters.h"
static int install(struct prog *p) { return S(317,1,0,p,0,0,0)==0; }
static int child_inventory(void) {
 for(int fd=0;fd<64;fd++) {
  L flags=S(72,fd,1,0,0,0,0);
  int expected=fd<=2||fd==5||fd==8;
  if(expected ? flags<0 : flags!=-9)return 0;
 }
 return 1;
}
static int worker(void) {
 if(S(3,3,0,0,0,0,0)||S(3,4,0,0,0,0,0)||S(3,6,0,0,0,0,0)||S(3,7,0,0,0,0,0))return 31;
 if(!child_inventory()||!install(&w_filter))return 32;
 char value='R';
 if(S(1,8,&value,1,0,0,0)!=1)return 33;
 if(S(0,5,&value,1,0,0,0)!=1||value!='G')return 34;
 if(S(59,0,0,0,0,0,0)!=-1||S(41,1,1,0,0,0,0)!=-1||S(317,1,0,&w_filter,0,0,0)!=-1)return 35;
 if(S(3,5,0,0,0,0,0)||S(3,8,0,0,0,0,0))return 36;
 return 0;
}
static int run(void) {
 if(S(102,0,0,0,0,0,0)==0)return 1; /* refuse root */
 if(S(436,3,0xffffffffU,0,0,0,0))return 2;
 if(S(157,38,1,0,0,0,0)||S(157,4,0,0,0,0,0))return 3;
 if(S(83,"domain",0700,0,0,0,0))return 4;
 if(S(257,-100,"domain",0xb0000,0,0,0)!=3)return 5;
 if(S(257,3,"membership.inert",0xa00c2,0600,0,0)!=4)return 6;
 int gate[2],ready[2];
 if(S(293,gate,0x80000,0,0,0,0)||gate[0]!=5||gate[1]!=6)return 7;
 if(S(293,ready,0x80000,0,0,0,0)||ready[0]!=7||ready[1]!=8)return 8;
 L pid=S(57,0,0,0,0,0,0);
 if(pid<0)return 9;
 if(!pid){int code=worker();S(60,code,0,0,0,0,0);__builtin_unreachable();}
 if(S(3,5,0,0,0,0,0)||S(3,8,0,0,0,0,0))return 10;
 /* Exact child PID is substituted only into generated scalar comparison slots.
  * The child cannot exit/reuse PID unnoticed: it remains our unreaped child. */
 for(U i=0;i<sizeof(bindings)/sizeof(bindings[0]);i++)
  bindings[i].code[bindings[i].index].k=(unsigned int)pid;
 if(!install(&b_boot))return 11;
 if(S(434,pid,0,0,0,0,0)!=5)return 12;
 if(S(434,pid+1,0,0,0,0,0)!=-1)return 13;
 char value=0;
 if(S(0,7,&value,1,0,0,0)!=1||value!='R')return 14;
 char digits[20];U count=0,num=(U)pid;
 do{digits[count++]=(char)('0'+num%10);num/=10;}while(num);
 for(U i=0;i<count/2;i++){char c=digits[i];digits[i]=digits[count-1-i];digits[count-1-i]=c;}
 if(S(1,4,digits,count,0,0,0)!=(L)count)return 15;
 char observed[20];
 if(S(17,4,observed,count,0,0,0)!=(L)count)return 16;
 for(U i=0;i<count;i++)if(observed[i]!=digits[i])return 17;
 if(S(3,4,0,0,0,0,0)||!install(&b_sealed))return 18;
 if(S(1,4,digits,count,0,0,0)!=-1||S(257,3,"membership.inert",0,0,0,0)!=-1)return 19;
 if(S(434,pid,0,0,0,0,0)!=-1||S(317,1,0,&b_boot,0,0,0)!=-1)return 20;
 value='G';if(S(1,6,&value,1,0,0,0)!=1)return 21;
 int status=-1;
 if(S(61,pid+1,&status,0,0,0,0)!=-1)return 22;
 if(S(61,pid,&status,0,0,0,0)!=pid||status!=0)return 23;
 struct {int fd;short events,revents;} pollfd={5,1,0};
 if(S(7,&pollfd,1,0,0,0,0)!=1||!(pollfd.revents&1))return 24;
 if(S(3,3,0,0,0,0,0)||S(3,5,0,0,0,0,0)||S(3,6,0,0,0,0,0)||S(3,7,0,0,0,0,0))return 25;
 return 0;
}
void entry(void){S(60,run(),0,0,0,0,0);__builtin_unreachable();}
__asm__(".global _start\n_start:\nand $-16,%rsp\ncall entry\nud2\n");
