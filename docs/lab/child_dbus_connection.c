/* Composed inert AUTH/framing/request-owner model. No bus or authority. */
#include "owner.h"
#define NEW A_NEW
#define INVALID A_INVALID
#define feed auth_feed
#include "auth.h"
#undef feed
#undef INVALID
#undef NEW
struct connection {struct auth auth;struct model model;unsigned char bytes[65536];U used,need,total,count;int invalid,finished;};
static void reset(struct connection *s) {
 s->auth.state=A_NEW;s->auth.received=0;
 s->model.generation=7;s->model.next=1;s->model.count=0;s->model.pending_serial=0;
 s->model.phase=NEW;s->model.pending=0;s->model.client[0]=s->model.owner[0]=0;
 s->used=s->total=s->count=0;s->need=16;s->invalid=s->finished=0;
}
static int stop(struct connection *s) {s->invalid=1;invalid(&s->auth);refuse(&s->model);return 0;}
static int wire_feed(struct connection *s,const unsigned char *raw,U n,U generation) {
 if(s->invalid||s->finished||s->auth.state!=BEGIN_ENCODED||generation!=s->model.generation||!n||n>65536||n>1048576-s->total)return stop(s);
 s->total+=n;
 for(U i=0;i<n;i++) {
  if(s->count>=16||s->used>=65536)return stop(s);
  s->bytes[s->used++]=raw[i];
  if(s->used==16) {
   const unsigned char *b=s->bytes;
   if(b[0]!=108||b[3]!=1||b[1]<2||b[1]>4||(b[2]&~3))return stop(s);
   struct cursor r={b,16,4};U body,serial,header;
   if(!scalar(&r,4,&body)||!scalar(&r,4,&serial)||!scalar(&r,4,&header)||!serial||header>4096||body>65536)return stop(s);
   U start=(16+header+7)&~7UL;if(body>65536-start)return stop(s);
   s->need=start+body;
  }
  if(s->used==s->need) {
   if(!incoming(&s->model,s->bytes,s->used,generation))return stop(s);
   for(U j=0;j<s->used;j++)((volatile unsigned char *)s->bytes)[j]=0;
   s->used=0;s->need=16;s->count++;
  }
 }
 return 1;
}
static int operation(struct connection *s,int kind,int op,const unsigned char *raw,U n,U generation) {
 unsigned char out[64];
 if(s->invalid||s->finished)return stop(s);
 if(kind==1) {if(!auth_encode(&s->auth,62001,out,sizeof(out)))return stop(s);return 1;}
 if(kind==2) {if(!auth_feed(&s->auth,raw,n))return stop(s);return 1;}
 if(kind==3) {if(!begin_encode(&s->auth,out,sizeof(out)))return stop(s);return 1;}
 if(kind==4) {
  if(s->auth.state!=BEGIN_ENCODED||s->used||!issue(&s->model,op,generation))return stop(s);
  return 1;
 }
 if(kind==5)return wire_feed(s,raw,n,generation);
 if(kind==6) {
  if(s->auth.state!=BEGIN_ENCODED||s->used||s->model.pending||s->model.phase!=OWNER_BOUND||s->count<3)return stop(s);
  s->finished=1;return 1;
 }
 return stop(s);
}
struct step {int kind,op;const unsigned char *raw;U n,generation;int good;};
struct scenario {const struct step *steps;U n;int good;};
#include "connection_vectors.h"
static struct connection s;
__attribute__((noinline,noclone)) static long call(U nr,U a,U b,U c) {
 long out;__asm__ volatile("syscall":"=a"(out):"a"(nr),"D"(a),"S"(b),"d"(c):"rcx","r11","memory");return out;
}
static int run(void) {
 if(call(102,0,0,0)==0)return 2;
 for(U chunk_index=0;chunk_index<3;chunk_index++) {
  U chunk=chunk_index==0?1:(chunk_index==1?17:65536);
  for(U i=0;i<sizeof(scenarios)/sizeof(scenarios[0]);i++) {
   reset(&s);const struct scenario *v=&scenarios[i];
   for(U j=0;j<v->n;j++) {
    const struct step *st=&v->steps[j];int okay=1;
    if((st->kind==2||st->kind==5)&&st->n) {
     for(U at=0;at<st->n;) {
      U n=st->n-at<chunk?st->n-at:chunk;
      okay=operation(&s,st->kind,st->op,st->raw+at,n,st->generation);at+=n;
      if(!okay)break;
     }
    } else okay=operation(&s,st->kind,st->op,st->raw,st->n,st->generation);
    if(okay!=st->good){unsigned int failed[3]={(unsigned int)i,(unsigned int)j,(unsigned int)chunk_index};call(1,1,(U)failed,12);return 10;}
   }
   if(v->good) {
    if(!s.finished||s.invalid||s.model.pending||s.used||!eq((struct span){(unsigned char *)s.model.owner,5},":1.42"))return 11;
   } else if(!s.invalid||s.auth.state!=A_INVALID||s.model.phase!=INVALID)return 12;
   if(operation(&s,4,1,0,0,7)||!s.invalid)return 13;
  }
 }
 return 0;
}
void entry(void){call(60,(U)run(),0,0);__builtin_unreachable();}
__asm__(".global _start\n_start:\nand $-16,%rsp\ncall entry\nud2\n");
