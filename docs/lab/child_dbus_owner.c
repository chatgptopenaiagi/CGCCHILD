/* Request correlation and bus-owner MODEL, never a live generation authority. */
#include "decoder.h"
enum {NEW,HELLO_BOUND,OWNER_BOUND,INVALID};
struct model {U generation,next,count,pending_serial;int phase,pending;char client[256],owner[256];};
static int refuse(struct model *m){m->phase=INVALID;m->pending=0;return 0;}
static int unique(struct span s) {
 if(s.n<4||s.n>255||s.p[0]!=':')return 0;
 int digit=0,dot=0;
 for(U i=1;i<s.n;i++) {
  unsigned char c=s.p[i];
  if(c=='.'){if(!digit)return 0;digit=0;dot=1;}
  else if(c>='0'&&c<='9')digit=1;
  else return 0;
 }
 return digit&&dot;
}
static void copy(char *out,struct span s){for(U i=0;i<s.n;i++)out[i]=(char)s.p[i];out[s.n]=0;}
static U issue(struct model *m,int operation,U generation) {
 if(m->phase==INVALID||generation!=m->generation||!generation||m->pending||m->count>=8||!m->next||m->next>=0xffffffffUL)return (U)refuse(m);
 if(!((operation==1&&m->phase==NEW)||(operation==2&&m->phase==HELLO_BOUND)||(operation==3&&m->phase==OWNER_BOUND)))return (U)refuse(m);
 m->pending=operation;m->pending_serial=m->next++;m->count++;return m->pending_serial;
}
static int incoming(struct model *m,const unsigned char *raw,U n,U generation) {
 if(m->phase==INVALID||generation!=m->generation||!generation||n<16)return refuse(m);
 struct decoded d;
 if(raw[1]==4) {
  struct context ctx={"org.freedesktop.DBus","",0,0,0};
  if(m->phase!=OWNER_BOUND||!decode(raw,n,&ctx,&d)||d.kind!=4||!eq(d.text[1],m->owner))return refuse(m);
  return 1;
 }
 if(!m->pending)return refuse(m);
 struct context ctx={m->pending==3?m->owner:"org.freedesktop.DBus",m->pending==3?"v":"s",
                     (unsigned int)m->pending_serial,m->pending==3?4U:0U,0};
 if(!decode(raw,n,&ctx,&d)||d.kind!=2)return refuse(m);
 if(m->pending==1) {
  if(!unique(d.text[0]))return refuse(m);
  copy(m->client,d.text[0]);m->phase=HELLO_BOUND;
 } else if(m->pending==2) {
  if(!unique(d.text[0])||eq(d.text[0],m->client))return refuse(m);
  copy(m->owner,d.text[0]);m->phase=OWNER_BOUND;
 }
 m->pending=0;return 1;
}
struct step {int kind,operation;U generation;const unsigned char *raw;U n;int accepted,phase,pending;};
struct scenario {const struct step *steps;U n,next;};
#include "owner_vectors.h"
__attribute__((noinline,noclone)) static long call(U nr,U a,U b,U c) {
 long out;__asm__ volatile("syscall":"=a"(out):"a"(nr),"D"(a),"S"(b),"d"(c):"rcx","r11","memory");return out;
}
static int run(void) {
 if(call(102,0,0,0)==0)return 2;
 for(U i=0;i<sizeof(scenarios)/sizeof(scenarios[0]);i++) {
  const struct scenario *s=&scenarios[i];struct model m;m.generation=7;m.next=s->next;m.count=0;m.pending_serial=0;m.phase=NEW;m.pending=0;m.client[0]=0;m.owner[0]=0;
  for(U j=0;j<s->n;j++) {
   const struct step *v=&s->steps[j];int okay;
   if(v->kind==1)okay=issue(&m,v->operation,v->generation)!=0;
   else if(v->kind==2) {
    unsigned char scratch[1024];if(v->n>sizeof(scratch))return 3;
    for(U k=0;k<v->n;k++)scratch[k]=v->raw[k];
    okay=incoming(&m,scratch,v->n,v->generation);
    /* Stored owner/client must not alias the consumed frame buffer. */
    for(U k=0;k<v->n;k++)((volatile unsigned char *)scratch)[k]=0;
   } else {okay=refuse(&m);}
   if(okay!=v->accepted||m.phase!=v->phase||m.pending!=v->pending) {
    unsigned int failed[2]={(unsigned int)i,(unsigned int)j};call(1,1,(U)failed,8);return 1;
   }
  }
 }
 return 0;
}
void entry(void){call(60,(U)run(),0,0);__builtin_unreachable();}
__asm__(".global _start\n_start:\nand $-16,%rsp\ncall entry\nud2\n");
