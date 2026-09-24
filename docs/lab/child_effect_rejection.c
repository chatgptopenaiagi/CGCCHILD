/* Malformed/stale packet rejection before owned inert effects, never live authority. */
#include "lifecycle.h"
typedef long L;
struct ins {unsigned short code;unsigned char jt,jf;unsigned int k;};
struct prog {unsigned short len;struct ins *filter;};
__attribute__((noinline,noclone)) static L call(U n,U a,U b,U c,U d,U e,U f) {
 register U r10 __asm__("r10")=d,r8 __asm__("r8")=e,r9 __asm__("r9")=f;L out;
 __asm__ volatile("syscall":"=a"(out):"a"(n),"D"(a),"S"(b),"d"(c),"r"(r10),"r"(r8),"r"(r9):"rcx","r11","memory");return out;
}
#define S(n,a,b,c,d,e,f) call(n,(U)(a),(U)(b),(U)(c),(U)(d),(U)(e),(U)(f))
#include "effect_filters.h"
struct packet_vector {const unsigned char *request,*reply;U request_size,reply_size;};
struct rejection {const unsigned char *raw;U n;int after_create;};
#include "effect_vectors.h"
static int install(struct prog *p){return S(317,1,0,p,0,0,0)==0;}
static int poll_state(int fd,int timeout) {
 struct {int fd;short events,revents;} p={fd,1,0};
 L result=S(7,&p,1,timeout,0,0,0);
 if(result==0)return 0;
 if(result!=1||(p.revents&40))return -1;
 return (p.revents&1)?1:-1;
}
static int worker(void) {
 if(S(3,3,0,0,0,0,0)||S(3,4,0,0,0,0,0)||S(3,6,0,0,0,0,0)||S(3,7,0,0,0,0,0))return 31;
 for(int fd=3;fd<64;fd++){L x=S(72,fd,1,0,0,0,0);if((fd==5||fd==8)?x<0:x!=-9)return 32;}
 if(!install(&w_filter))return 33;
 char c='R';if(S(1,8,&c,1,0,0,0)!=1||poll_state(5,2000)!=1||S(0,5,&c,1,0,0,0)!=1||c!='G')return 34;
 if(S(59,0,0,0,0,0,0)!=-1||S(41,1,1,0,0,0,0)!=-1||S(317,1,0,&w_filter,0,0,0)!=-1)return 35;
 if(S(3,5,0,0,0,0,0)||S(3,8,0,0,0,0,0))return 36;
 return 0;
}
static struct lab lab={NEW,1,0,0,0,0};
static U acks;
static int prepare_raw(const unsigned char *raw,U size,int empty,struct lab *candidate,unsigned char *reply,U *n) {
 *candidate=lab;
 if(!dispatch(candidate,raw,size,1,1,empty,reply,n)){refuse(&lab);return 0;}
 return 1;
}
static int prepare(U index,int empty,struct lab *candidate,unsigned char *reply,U *n) {
 const struct packet_vector *p=&packets[index];
 return prepare_raw(p->request,p->request_size,empty,candidate,reply,n);
}
static int commit(U index,const struct lab *candidate,const unsigned char *reply,U n) {
 const struct packet_vector *p=&packets[index];struct message m;int invalid;
 if(n!=p->reply_size||!reply_parse(reply,n,&m,&invalid)||invalid)return 0;
 for(U i=0;i<n;i++)if(reply[i]!=p->reply[i])return 0;
 lab=*candidate;acks++;return 1;
}
static int release_reap(L pid) {
 char c='G';int status=-1;
 return S(1,6,&c,1,0,0,0)==1&&S(61,pid,&status,0,0,0,0)==pid&&status==0&&poll_state(5,0)==1;
}
static int remove_owned(void) {
 if(S(263,3,"membership.inert",0,0,0,0)||S(3,3,0,0,0,0,0)||S(84,"domain",0,0,0,0,0))return 0;
 for(int fd=5;fd<=7;fd++)if(S(3,fd,0,0,0,0,0))return 0;
 return 1;
}
static int rejected(U index) {
 const struct rejection *v=&rejections[index];struct lab candidate;unsigned char reply[1024];U n=0;
 if(v->after_create) {
  if(!prepare(0,0,&candidate,reply,&n)||S(83,"domain",0700,0,0,0,0)||
     S(257,-100,"domain",0xb0000,0,0,0)!=3||S(257,3,"membership.inert",0xa00c2,0600,0,0)!=4||
     !commit(0,&candidate,reply,n))return 40;
 }
 if(prepare_raw(v->raw,v->n,0,&candidate,reply,&n)||n||lab.state!=INVALIDATED||
    acks!=(U)v->after_create||lab.count!=(U)v->after_create||lab.creates!=v->after_create||lab.attaches)return 41;
 /* A later correct packet must not reopen invalidated admission. */
 if(prepare(v->after_create?1:0,0,&candidate,reply,&n)||n||lab.state!=INVALIDATED)return 42;
 if(v->after_create) {
  char byte=0;
  if(S(17,4,&byte,1,0,0,0)!=0||S(3,4,0,0,0,0,0)||S(263,3,"membership.inert",0,0,0,0)||
     S(3,3,0,0,0,0,0)||S(84,"domain",0,0,0,0,0))return 43;
 }
 return 0;
}
static int run(U selector) {
 if(!S(102,0,0,0,0,0,0)||S(436,3,0xffffffffU,0,0,0,0))return 1;
 if(S(157,38,1,0,0,0,0)||S(157,4,0,0,0,0,0))return 2;
 if(selector>=3)return rejected(selector-3);
 struct lab next;unsigned char reply[1024];U n=0;
 if(!prepare(0,0,&next,reply,&n))return 3;
 L created=S(83,"domain",0700,0,0,0,0);
 if(selector==1) {
  n=0;refuse(&lab);
  return created==-17&&lab.state==INVALIDATED&&lab.count==0&&acks==0?0:4;
 }
 if(created||S(257,-100,"domain",0xb0000,0,0,0)!=3||S(257,3,"membership.inert",0xa00c2,0600,0,0)!=4)return 5;
 if(!commit(0,&next,reply,n)||!prepare(1,0,&next,reply,&n))return 6;
 int gate[2],notice[2];
 if(S(293,gate,0x80000,0,0,0,0)||gate[0]!=5||gate[1]!=6||S(293,notice,0x80000,0,0,0,0)||notice[0]!=7||notice[1]!=8)return 7;
 L pid=S(57,0,0,0,0,0,0);if(pid<0)return 8;
 if(!pid){int code=worker();S(60,code,0,0,0,0,0);__builtin_unreachable();}
 if(S(3,5,0,0,0,0,0)||S(3,8,0,0,0,0,0))return 9;
 for(U i=0;i<sizeof(bindings)/sizeof(bindings[0]);i++)bindings[i].code[bindings[i].index].k=(unsigned int)pid;
 if(!install(&b_boot)||S(434,pid,0,0,0,0,0)!=5||S(434,pid+1,0,0,0,0,0)!=-1)return 10;
 char c=0;if(poll_state(7,2000)!=1||S(0,7,&c,1,0,0,0)!=1||c!='R'||poll_state(5,0)!=0||poll_state(63,0)!=-1)return 11;
 char digits[20];U count=0,num=(U)pid;
 do{digits[count++]=(char)('0'+num%10);num/=10;}while(num);
 for(U i=0;i<count/2;i++){char ch=digits[i];digits[i]=digits[count-1-i];digits[count-1-i]=ch;}
 if(selector==2&&S(3,4,0,0,0,0,0))return 12;
 L written=S(1,4,digits,count,0,0,0);
 if(selector==2) {
  n=0;refuse(&lab);
  if(written!=-9||acks!=1||lab.count!=1||lab.attaches||!release_reap(pid)||!install(&b_sealed)||!remove_owned())return 13;
  return 0;
 }
 if(written!=(L)count)return 14;
 char observed[20];if(S(17,4,observed,count,0,0,0)!=(L)count)return 15;
 for(U i=0;i<count;i++)if(observed[i]!=digits[i])return 16;
 if(!commit(1,&next,reply,n)||!prepare(2,0,&next,reply,&n))return 17;
 if(S(3,4,0,0,0,0,0)||!install(&b_sealed))return 18;
 if(S(1,4,digits,count,0,0,0)!=-1||S(257,3,"membership.inert",0,0,0,0)!=-1||S(317,1,0,&b_boot,0,0,0)!=-1)return 19;
 if(!commit(2,&next,reply,n)||!prepare(3,0,&next,reply,&n)||poll_state(5,0)!=0||!commit(3,&next,reply,n))return 20;
 if(!release_reap(pid)||!prepare(4,1,&next,reply,&n)||!remove_owned()||!commit(4,&next,reply,n))return 21;
 return lab.state==CLOSED&&acks==5&&lab.creates==1&&lab.attaches==1&&lab.removes==1?0:22;
}
void entry(U *stack) {
 int code=2;
 if(stack[0]==2){
  const char *arg=(const char *)stack[2];U selector=99;
  if(arg[0]>='0'&&arg[0]<='9'&&!arg[1])selector=(U)(arg[0]-'0');
  else if(arg[0]=='1'&&arg[1]>='0'&&arg[1]<='9'&&!arg[2])selector=10+(U)(arg[1]-'0');
  if(selector<3+sizeof(rejections)/sizeof(rejections[0]))code=run(selector);
 }
 S(60,code,0,0,0,0,0);__builtin_unreachable();
}
__asm__(".global _start\n_start:\nmov %rsp,%rdi\nand $-16,%rsp\ncall entry\nud2\n");
