/* Model-bound encoding over a filtered private socketpair; no bus connection. */
#include "connection.h"
#include "binding.h"
struct fixture {const unsigned char *owner_reply;U owner_n;const unsigned char *query;U query_n;const unsigned char *reply;U n;int accepted,eof;};
#include "socket_vectors.h"
__attribute__((noinline,noclone)) static long call(U n,U a,U b,U c,U d,U e,U f) {
 register U r10 __asm__("r10")=d,r8 __asm__("r8")=e,r9 __asm__("r9")=f;long out;
 __asm__ volatile("syscall":"=a"(out):"a"(n),"D"(a),"S"(b),"d"(c),"r"(r10),"r"(r8),"r"(r9):"rcx","r11","memory");return out;
}
#define S(n,a,b,c,d,e,f) call(n,(U)(a),(U)(b),(U)(c),(U)(d),(U)(e),(U)(f))
struct ins {unsigned short code;unsigned char jt,jf;unsigned int k;};
struct prog {unsigned short len;struct ins *filter;};
#include "io_filter.h"
static int install(void) {
 if(S(157,38,1,0,0,0,0)||S(317,1,0,&io_filter,0,0,0))return 0;
 unsigned char byte=0;
 if(S(0,0,&byte,1,0,0,0)!=-1||S(0,3,&byte,18,0,0,0)!=-1)return 0;
 if(S(44,3,&byte,1,0,0,0)!=-1||S(44,1,&byte,1,0x4000,0,0)!=-1)return 0;
 if(S(44,3,&byte,1,0x4000,1,1)!=-1||S(3,0,0,0,0,0,0)!=-1)return 0;
 if(S(72,3,2,0,0,0,0)!=-1||S(317,1,0,&io_filter,0,0,0)!=-1)return 0;
 static const U denied[]={41,53,57,59,101,157,272,322,435,436};
 for(U i=0;i<sizeof(denied)/sizeof(denied[0]);i++)if(S(denied[i],0,0,0,0,0,0)!=-1)return 0;
 return 1;
}
static struct connection s;
static U emit_query(U selector,unsigned char *out,U capacity) {
 if(selector==3)return bound_query(&s.model,7,out,capacity);
 return model_query_encode(selector,0,"",out,capacity);
}
static U calls;
/* Return -1 for I/O mismatch,0 for model refusal,1 for complete delivery. */
static int transfer(int from,int to,const unsigned char *raw,U n,int kind,U fragment) {
 if(!n||n>4096||!fragment||fragment>17)return -1;
 unsigned char input[17];
 for(U at=0;at<n;) {
  U count=n-at<fragment?n-at:fragment,sent=0;
  while(sent<count) {
   if(++calls>8192)return -1;
   long wrote=S(44,from,raw+at+sent,count-sent,0x4000,0,0);
   if(wrote<=0||(U)wrote>count-sent)return -1;
   sent+=(U)wrote;
  }
  U received=0;
  while(received<count) {
   if(++calls>8192)return -1;
   long got=S(0,to,input,count-received,0,0,0);
   if(got<=0||(U)got>count-received)return -1;
   for(U j=0;j<(U)got;j++)if(input[j]!=raw[at+received+j])return -1;
   if(kind&&!operation(&s,kind,0,input,(U)got,7))return 0;
   received+=(U)got;
  }
  at+=count;
 }
 return 1;
}
static int exchange(const struct fixture *v,U fragment) {
 int fd[2];unsigned char out[64];reset(&s);calls=0;
 if(S(53,1,0x80801,0,fd,0,0)||fd[0]!=3||fd[1]!=4)return 10;
 if(!install())return 27;
 if(emit_query(0,out,sizeof(out))||emit_query(4,out,sizeof(out))||emit_query(~0UL,out,sizeof(out)))return 32;
 for(int i=0;i<2;i++)if(S(72,fd[i],1,0,0,0,0)!=1||(S(72,fd[i],3,0,0,0,0)&0x800)!=0x800)return 11;
 if(S(0,3,out,1,0,0,0)!=-11)return 26; /* Empty nonblocking endpoint must report EAGAIN. */
 U n=auth_encode(&s.auth,62001,out,sizeof(out));
 if(n!=sizeof(auth_request))return 12;
 for(U i=0;i<n;i++)if(out[i]!=auth_request[i])return 13;
 if(transfer(3,4,out,n,0,fragment)!=1||transfer(4,3,auth_reply,sizeof(auth_reply),2,fragment)!=1)return 14;
 n=begin_encode(&s.auth,out,sizeof(out));if(n!=7||transfer(3,4,out,n,0,fragment)!=1)return 15;
 const unsigned char *requests[]={request_hello,request_owner,v->query};
 U sizes[]={sizeof(request_hello),sizeof(request_owner),v->query_n};
 for(int i=0;i<3;i++) {
  if(!operation(&s,4,i+1,0,0,7))return 33;
  unsigned char encoded[4098];
  for(U j=0;j<sizeof(encoded);j++)encoded[j]=165;
  for(U cap=0;cap<sizes[i];cap++) {
   if(emit_query(i+1,encoded+1,cap))return 28;
   for(U j=0;j<sizeof(encoded);j++)if(encoded[j]!=165)return 29;
  }
  U size_out=emit_query(i+1,encoded+1,sizes[i]);
  if(size_out!=sizes[i]||encoded[0]!=165||encoded[size_out+1]!=165)return 30;
  for(U j=0;j<size_out;j++)if(encoded[j+1]!=requests[i][j])return 31;
  if(transfer(3,4,encoded+1,size_out,0,fragment)!=1)return 16;
  const unsigned char *reply=i==0?reply_hello:i==1?v->owner_reply:v->reply;
  U size=i==0?sizeof(reply_hello):i==1?v->owner_n:v->n;
  int received=transfer(4,3,reply,size,5,fragment);
  if(i<2&&received!=1)return 17;
  if(i==2) {
   if(received<0||received!=v->accepted)return 18;
   if(v->eof) {
    if(S(3,4,0,0,0,0,0))return 19;
    if(S(0,3,out,1,0,0,0)!=0||stop(&s)||!s.invalid)return 20;
   } else if(v->accepted) {
    if(!operation(&s,6,0,0,0,7)||!s.finished||s.invalid)return 21;
   } else if(!s.invalid||s.model.phase!=INVALID)return 22;
  }
 }
 if(S(3,3,0,0,0,0,0))return 23;
 if(!v->eof&&S(3,4,0,0,0,0,0))return 24;
 for(int i=3;i<64;i++)if(S(72,i,1,0,0,0,0)!=-9)return 25;
 return 0;
}
static int run(U selector) {
 if(S(102,0,0,0,0,0,0)==0)return 2;
 if(S(436,3,~0U,0,0,0,0))return 3;
 return exchange(&fixtures[selector/2],selector%2?17:1);
}
void entry(U *stack) {
 int code=2;
 if(stack[0]==2) {
  const unsigned char *arg=(const unsigned char *)stack[2];U selector=99;
  if(arg[0]>='0'&&arg[0]<='9'&&!arg[1])selector=arg[0]-'0';
  else if(arg[0]>='1'&&arg[0]<='5'&&arg[1]>='0'&&arg[1]<='9'&&!arg[2])selector=(arg[0]-'0')*10+arg[1]-'0';
  if(selector<56)code=run(selector);
 }
 S(60,code,0,0,0,0,0);__builtin_unreachable();
}
__asm__(".global _start\n_start:\nmov %rsp,%rdi\nand $-16,%rsp\ncall entry\nud2\n");
