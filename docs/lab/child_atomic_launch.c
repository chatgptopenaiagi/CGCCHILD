/* Nonroot atomic launch capability fixture. No cgroup, exec, or live controller. */
typedef unsigned long U;
typedef long L;
__attribute__((noinline,noclone)) static L call(U n,U a,U b,U c,U d,U e,U f) {
 register U r10 __asm__("r10")=d,r8 __asm__("r8")=e,r9 __asm__("r9")=f;L out;
 __asm__ volatile("syscall":"=a"(out):"a"(n),"D"(a),"S"(b),"d"(c),"r"(r10),"r"(r8),"r"(r9):"rcx","r11","memory");return out;
}
#define S(n,a,b,c,d,e,f) call(n,(U)(a),(U)(b),(U)(c),(U)(d),(U)(e),(U)(f))
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
 /* CLONE_PIDFD only; no shared VM, namespaces, threads, cgroup, or selected PID. */
 U args[11]={0x1000,(U)&pidfd,0,0,17,0,0,0,0,0,0};
 L pid=S(435,args,sizeof(args),0,0,0,0);
 if(pid<0){S(3,3,0,0,0,0,0);S(3,4,0,0,0,0,0);return pid==-38?77:pid==-1?78:79;}
 if(!pid){
  int code=0;char c=0;
  if(pidfd!=-1||S(3,4,0,0,0,0,0)||ready(3,2000)!=1||S(0,3,&c,1,0,0,0)!=1||c!='G')code=4;
  if(S(3,3,0,0,0,0,0))code=5;
  S(60,code,0,0,0,0,0);__builtin_unreachable();
 }
 if(pidfd!=5||S(72,5,1,0,0,0,0)!=1||ready(5,0)!=0||ready(63,0)!=-1)return 6;
 if(S(3,3,0,0,0,0,0))return 7;
 char c='G';if(S(1,4,&c,1,0,0,0)!=1||S(3,4,0,0,0,0,0)||ready(5,2000)!=1)return 8;
 int status=-1;if(S(61,pid,&status,0,0,0,0)!=pid||status||ready(5,0)!=1)return 9;
 if(S(3,5,0,0,0,0,0))return 10;
 for(int fd=3;fd<64;fd++)if(S(72,fd,1,0,0,0,0)!=-9)return 11;
 return 0;
}
void _start(void){int code=run();S(60,code,0,0,0,0,0);__builtin_unreachable();}
