/* Model-derived query binding, no socket, manager or live authority. */
#include "owner.h"
extern U model_query_encode(U selector,U serial,const char *owner,unsigned char *out,U capacity);
static U bounded(const char *s){U n=0;while(n<256&&s[n])n++;return n;}
static U bound_query(struct model *m,U generation,unsigned char *out,U capacity) {
 U n=bounded(m->owner),client_n=bounded(m->client);
 if(m->phase!=OWNER_BOUND||m->pending!=3||!generation||generation!=m->generation||
    !m->pending_serial||m->pending_serial>=0xffffffffUL||m->next!=m->pending_serial+1||
    m->count<3||m->count>8||m->pending_serial!=m->count||!unique((struct span){(const unsigned char *)m->owner,n})||
    !unique((struct span){(const unsigned char *)m->client,client_n})||
    eq((struct span){(const unsigned char *)m->owner,n},m->client))return (U)refuse(m);
 return model_query_encode(3,m->pending_serial,m->owner,out,capacity);
}
struct packet {const unsigned char *p;U n;};
struct fixture {struct packet hello,owner,request[6],reply[6];};
#include "binding_vectors.h"
static void init(struct model *m) {
 m->generation=7;m->next=1;m->count=0;m->pending_serial=0;
 m->phase=NEW;m->pending=0;
 for(U i=0;i<256;i++)m->client[i]=m->owner[i]=0;
}
static int prepare(struct model *m,const struct fixture *v) {
 init(m);
 return issue(m,1,7)==1&&incoming(m,v->hello.p,v->hello.n,7)&&
        issue(m,2,7)==2&&incoming(m,v->owner.p,v->owner.n,7);
}
static int run(void) {
 unsigned char out[1026];
 if(model_query_encode(0,0,"",out,sizeof(out)))return 2;
 for(U i=0;i<sizeof(fixtures)/sizeof(fixtures[0]);i++) {
  const struct fixture *v=&fixtures[i];struct model m;
  if(!prepare(&m,v))return 3;
  for(U j=0;j<6;j++) {
   if(issue(&m,3,7)!=j+3)return 4;
   for(U k=0;k<sizeof(out);k++)out[k]=165;
   for(U cap=0;cap<v->request[j].n;cap++) {
    if(bound_query(&m,7,out+1,cap)||m.phase!=OWNER_BOUND||m.pending!=3||m.next!=j+4)return 5;
    for(U k=0;k<sizeof(out);k++)if(out[k]!=165)return 6;
   }
   U n=bound_query(&m,7,out+1,v->request[j].n);
   if(n!=v->request[j].n||out[0]!=165||out[n+1]!=165)return 7;
   for(U k=0;k<n;k++)if(out[k+1]!=v->request[j].p[k])return 8;
   if(!incoming(&m,v->reply[j].p,v->reply[j].n,7)||m.pending)return 9;
  }
  if(issue(&m,3,7)||m.phase!=INVALID)return 10;
 }
 for(U which=0;which<18;which++) {
  struct model m;U generation=7;if(!prepare(&m,&fixtures[0])||issue(&m,3,7)!=3)return 11;
  switch(which) {
   case 0:m.phase=NEW;break;case 1:m.pending=0;break;case 2:m.pending=2;break;
   case 3:generation=0;break;case 4:generation=8;break;case 5:m.generation=8;break;
   case 6:m.pending_serial=0;break;case 7:m.pending_serial=0xffffffffUL;break;
   case 8:m.next=9;break;case 9:m.count=2;break;case 10:m.count=9;break;
   case 11:m.owner[0]='x';break;case 12:m.owner[0]=0;break;
   case 13:for(U k=0;k<256;k++)m.owner[k]='1';break;
   case 14:for(U k=0;k<256;k++)m.owner[k]=m.client[k];break;
   case 15:m.client[0]='x';break;case 16:m.phase=INVALID;break;
   case 17:m.pending_serial=99;m.next=100;break;
  }
  for(U k=0;k<sizeof(out);k++)out[k]=165;
  if(bound_query(&m,generation,out,sizeof(out))||m.phase!=INVALID||m.pending)return 12;
  for(U k=0;k<sizeof(out);k++)if(out[k]!=165)return 13;
  if(bound_query(&m,7,out,sizeof(out)))return 14;
 }
 return 0;
}
__attribute__((noinline,noclone)) static long call(U nr,U a,U b,U c) {
 long out;__asm__ volatile("syscall":"=a"(out):"a"(nr),"D"(a),"S"(b),"d"(c):"rcx","r11","memory");return out;
}
void entry(void){int code=call(102,0,0,0)==0?2:run();call(60,(U)code,0,0);__builtin_unreachable();}
__asm__(".global _start\n_start:\nand $-16,%rsp\ncall entry\nud2\n");
