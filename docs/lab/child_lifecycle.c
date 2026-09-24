/* Native admission MODEL only: effects are counters, never broker operations. */
#include "payload.h"
enum {NEW,CREATED,ATTACHED,SEALED,CLOSED,INVALIDATED};
struct lab {int state;U next,count;int creates,attaches,removes;};
static const char seal_epoch[]="55555555555555555555555555555555";
static const struct message binding={.kind=2,.b="11111111111111111111111111111111",
 .c="22222222222222222222222222222222",.domain="33333333333333333333333333333333",
 .lab="00000000000000000000000000000001",.epoch="0"};
static U result_position(const unsigned char *raw,U n,const char *marker) {
 for(U i=0;i<n;i++){struct cursor r={raw,n,i};if(lit(&r,marker))return i;}
 return n;
}
static U reply_encode(const struct message *m,int invalid,unsigned char *out) {
 unsigned char request[1024];U n=encode(m,request);
 U pos=result_position(request,n,",\"SEAL_EPOCH\":");
 const char *result=invalid?",\"RESULT\":\"INVALIDATED\"":",\"RESULT\":\"OK\"";
 struct writer w={out,0,1};
 for(U i=0;i<pos;i++){out[w.n++]=request[i];}
 put(&w,result);
 if(!w.ok||n-pos>1024-w.n)return 0;
 for(U i=pos;i<n;i++){out[w.n++]=request[i];}
 return w.n;
}
static int reply_parse(const unsigned char *raw,U n,struct message *m,int *invalid) {
 if(!n||n>1024)return 0;
 U pos=result_position(raw,n,",\"RESULT\":");if(pos==n)return 0;
 struct cursor r={raw,n,pos};
 if(lit(&r,",\"RESULT\":\"OK\""))*invalid=0;
 else if(lit(&r,",\"RESULT\":\"INVALIDATED\""))*invalid=1;
 else return 0;
 unsigned char request[1024];U size=0;
 for(U i=0;i<pos;i++){request[size++]=raw[i];}
 for(U i=r.i;i<n;i++){request[size++]=raw[i];}
 if(!parse(request,size,m)||m->kind!=2)return 0;
 unsigned char canonical[1024];U length=reply_encode(m,*invalid,canonical);
 if(length!=n)return 0;
 for(U i=0;i<n;i++){if(canonical[i]!=raw[i])return 0;}
 return 1;
}
static int refuse(struct lab *l){l->state=INVALIDATED;return 0;}
static int dispatch(struct lab *l,const unsigned char *raw,U n,int authenticated,int continuity,int empty,unsigned char *reply,U *reply_size) {
 *reply_size=0;
 if(l->state==CLOSED||l->state==INVALIDATED)return 0;
 if(!authenticated||!continuity||l->count>=8||l->next==~(U)0)return refuse(l);
 struct message m;if(!parse(raw,n,&m)||m.kind!=2)return refuse(l);
 struct message expected_message=binding;
 expected_message.op=m.op;expected_message.seq=l->next;
 if(l->state==SEALED){for(U i=0;i<33;i++){expected_message.epoch[i]=seal_epoch[i];}}
 U ancillary[7]={1,0,0,0,4242,62001,62001};
 if(!accept(raw,n,&expected_message,ancillary))return refuse(l);
 switch(m.op) {
  case 0:if(l->state!=NEW)return refuse(l);l->state=CREATED;l->creates++;break;
  case 1:if(l->state!=CREATED)return refuse(l);l->state=ATTACHED;l->attaches++;break;
  case 2:
   if(l->state!=ATTACHED)return refuse(l);
   l->state=SEALED;for(U i=0;i<33;i++){m.epoch[i]=seal_epoch[i];}break;
  case 3:if(l->state!=CREATED&&l->state!=ATTACHED&&l->state!=SEALED)return refuse(l);break;
  case 4:if(l->state!=SEALED||empty!=1)return refuse(l);l->state=CLOSED;l->removes++;break;
  default:return refuse(l);
 }
 l->next++;l->count++;*reply_size=reply_encode(&m,0,reply);
 if(!*reply_size)return refuse(l);
 return 1;
}
struct step {const unsigned char *raw;U size;int auth,continuity,empty,accepted,state;const unsigned char *reply;U reply_size;};
struct scenario {const struct step *steps;U count,next;int creates,attaches,removes;};
struct reply_vector {const unsigned char *raw;U n;int good,invalid;};
#include "lifecycle_vectors.h"
__attribute__((noinline,noclone)) static long call(U nr,U a,U b,U c) {
 long out;__asm__ volatile("syscall":"=a"(out):"a"(nr),"D"(a),"S"(b),"d"(c):"rcx","r11","memory");return out;
}
static int run(void) {
 if(call(102,0,0,0)==0)return 2;
 for(U i=0;i<sizeof(scenarios)/sizeof(scenarios[0]);i++) {
  const struct scenario *s=&scenarios[i];struct lab lab={NEW,s->next,0,0,0,0};
  for(U j=0;j<s->count;j++) {
   const struct step *t=&s->steps[j];unsigned char reply[1024];U size;
   int okay=dispatch(&lab,t->raw,t->size,t->auth,t->continuity,t->empty,reply,&size);
   if(okay!=t->accepted||lab.state!=t->state||size!=t->reply_size)return 10;
   for(U k=0;k<size;k++){if(reply[k]!=t->reply[k])return 11;}
   if(okay){struct message m;int invalid;if(!reply_parse(reply,size,&m,&invalid)||invalid)return 12;}
  }
  if(lab.creates!=s->creates||lab.attaches!=s->attaches||lab.removes!=s->removes)return 13;
 }
 for(U i=0;i<sizeof(reply_vectors)/sizeof(reply_vectors[0]);i++) {
  struct message m;int invalid=-1;const struct reply_vector *v=&reply_vectors[i];
  int good=reply_parse(v->raw,v->n,&m,&invalid);
  if(good!=v->good||(good&&invalid!=v->invalid))return 14;
 }
 return 0;
}
void entry(void){call(60,(U)run(),0,0);__builtin_unreachable();}
__asm__(".global _start\n_start:\nand $-16,%rsp\ncall entry\nud2\n");
