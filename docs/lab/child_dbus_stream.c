/* Bounded inert stream accumulation; no transport or authority. */
#include "decoder.h"
struct vector {const unsigned char *raw;U n;struct context ctx;int good;struct decoded expected;};
#include "dbus_vectors.h"
static const unsigned char stream_bytes[]={
#include "stream_bytes.h"
};
struct stream {unsigned char bytes[65536];U used,need,count,total,max;const struct vector *contexts;int invalid,finished,mismatch;};
static void init(struct stream *s,const struct vector *contexts,U max) {
 s->used=s->count=s->total=0;s->need=16;s->max=max;s->contexts=contexts;s->invalid=max>16||!max;s->finished=s->mismatch=0;
}
static int refuse(struct stream *s){s->invalid=1;return 0;}
static int result_equal(const struct decoded *a,const struct decoded *b) {
 if(a->kind!=b->kind||a->error!=b->error||a->variant!=b->variant||a->number!=b->number||!equal(a->bytes,b->bytes))return 0;
 for(U j=0;j<3;j++)if(!equal(a->text[j],b->text[j]))return 0;
 return 1;
}
static int feed(struct stream *s,const unsigned char *raw,U n) {
 if(s->invalid||s->finished||!n||n>65536||n>1048576-s->total)return refuse(s);
 s->total+=n;
 for(U i=0;i<n;i++) {
  if(s->count>=s->max||s->used>=65536)return refuse(s);
  s->bytes[s->used++]=raw[i];
  if(s->used==16) {
   const unsigned char *b=s->bytes;
   if(b[0]!=108||b[3]!=1||b[1]<2||b[1]>4||(b[2]&~3))return refuse(s);
   struct cursor r={b,16,4};U body,serial,header;
   if(!scalar(&r,4,&body)||!scalar(&r,4,&serial)||!scalar(&r,4,&header)||!serial||header>4096||body>65536)return refuse(s);
   U start=(16+header+7)&~7UL;if(body>65536-start)return refuse(s);
   s->need=start+body;
  }
  if(s->used==s->need) {
   const struct vector *v=&s->contexts[s->count];struct decoded decoded;
   if(!decode(s->bytes,s->used,&v->ctx,&decoded))return refuse(s);
   /* Test comparison only; mismatch never turns an accepted frame into a refusal. */
   if(!result_equal(&decoded,&v->expected))s->mismatch=1;
   s->count++;s->used=0;s->need=16;
  }
 }
 return 1;
}
static int finish(struct stream *s) {
 if(s->invalid||s->finished||s->used||s->count!=s->max)return refuse(s);
 s->finished=1;return 1;
}
static struct stream s;
__attribute__((noinline,noclone)) static long call(U nr,U a,U b,U c) {
 long out;__asm__ volatile("syscall":"=a"(out):"a"(nr),"D"(a),"S"(b),"d"(c):"rcx","r11","memory");return out;
}
static int run(void) {
 if(call(102,0,0,0)==0)return 2;
 U size=sizeof(stream_bytes);
 for(U split=0;split<=size;split++) {
  init(&s,vectors,12);
  if(split&&!feed(&s,stream_bytes,split))return 10;
  if(split<size&&!feed(&s,stream_bytes+split,size-split))return 11;
  if(!finish(&s)||s.mismatch)return 12;
  if(feed(&s,stream_bytes,1)||!s.invalid)return 13;
 }
 for(U chunk=1;chunk<=17;chunk+=16) {
  init(&s,vectors,12);
  for(U at=0;at<size;) {U n=size-at<chunk?size-at:chunk;if(!feed(&s,stream_bytes+at,n))return 14;at+=n;}
  if(!finish(&s)||s.mismatch)return 15;
 }
 for(U end=0;end<size;end++) {
  init(&s,vectors,12);if(end)feed(&s,stream_bytes,end);
  if(finish(&s)||!s.invalid)return 16;
 }
 for(U i=12;i<sizeof(vectors)/sizeof(vectors[0]);i++) {
  const struct vector *v=&vectors[i];if(v->good)return 17;
  init(&s,v,1);if(v->n)feed(&s,v->raw,v->n);
  if(finish(&s)||!s.invalid)return 18;
 }
 init(&s,vectors,12);if(!feed(&s,stream_bytes,size)||feed(&s,stream_bytes,1)||!s.invalid)return 19;
 init(&s,vectors,12);if(feed(&s,stream_bytes,0)||!s.invalid)return 20;
 init(&s,vectors,17);if(!s.invalid)return 21;
 return 0;
}
void entry(void){call(60,(U)run(),0,0);__builtin_unreachable();}
__asm__(".global _start\n_start:\nand $-16,%rsp\ncall entry\nud2\n");
