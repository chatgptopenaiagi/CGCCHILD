/* Inert EXTERNAL transcript codec. ENCODED never means bytes were sent. */
typedef unsigned long U;
enum {NEW,AUTH_ENCODED,GUID_PARSED,BEGIN_ENCODED,INVALID};
struct auth {int state;U received;unsigned char guid[32];};
static int invalid(struct auth *a){a->state=INVALID;return 0;}
static U auth_encode(struct auth *a,U uid,unsigned char *out,U cap) {
 if(a->state!=NEW||uid>=0xffffffffUL){invalid(a);return 0;}
 unsigned char digits[10];U count=0,value=uid;
 do{digits[count++]=(unsigned char)('0'+value%10);value/=10;}while(value);
 U size=1+14+2*count+2;if(cap<size){invalid(a);return 0;}
 static const char prefix[]="AUTH EXTERNAL ";static const char hex[]="0123456789abcdef";
 U i=0;out[i++]=0;for(U j=0;j<14;j++)out[i++]=(unsigned char)prefix[j];
 for(U j=count;j>0;j--){unsigned char c=digits[j-1];out[i++]=hex[c>>4];out[i++]=hex[c&15];}
 out[i++]='\r';out[i++]='\n';a->state=AUTH_ENCODED;return i;
}
static int feed(struct auth *a,const unsigned char *raw,U n) {
 if(a->state!=AUTH_ENCODED||!n||n>64||a->received>37||n>37-a->received)return invalid(a);
 for(U i=0;i<n;i++) {
  U at=a->received;unsigned char c=raw[i];
  if(at<3){static const char prefix[]="OK ";if(c!=(unsigned char)prefix[at])return invalid(a);}
  else if(at<35){if(!((c>='0'&&c<='9')||(c>='a'&&c<='f')||(c>='A'&&c<='F')))return invalid(a);a->guid[at-3]=c;}
  else if(c!=(at==35?'\r':'\n'))return invalid(a);
  a->received++;
 }
 if(a->received==37)a->state=GUID_PARSED;
 return 1;
}
static U begin_encode(struct auth *a,unsigned char *out,U cap) {
 if(a->state!=GUID_PARSED||cap<7){invalid(a);return 0;}
 static const char begin[]="BEGIN\r\n";for(U i=0;i<7;i++)out[i]=(unsigned char)begin[i];
 a->state=BEGIN_ENCODED;return 7;
}
struct uid_vector {U uid;const unsigned char *raw;U n;};
struct line_vector {const unsigned char *raw;U n;int good;};
#include "auth_vectors.h"
__attribute__((noinline,noclone)) static long call(U nr,U a,U b,U c) {
 long out;__asm__ volatile("syscall":"=a"(out):"a"(nr),"D"(a),"S"(b),"d"(c):"rcx","r11","memory");return out;
}
static int run(void) {
 if(call(102,0,0,0)==0)return 2;
 unsigned char out[66];
 for(U i=0;i<sizeof(uids)/sizeof(uids[0]);i++) {
  const struct uid_vector *v=&uids[i];
  for(U cap=0;cap<=v->n;cap++) {
   struct auth a={0};for(U j=0;j<66;j++)out[j]=165;
   U n=auth_encode(&a,v->uid,out+1,cap);
   if(n!=(cap==v->n?v->n:0)||a.state!=(n?AUTH_ENCODED:INVALID))return 10;
   for(U j=0;j<66;j++)if(out[j]!=(n&&j>=1&&j<=n?v->raw[j-1]:165))return 11;
  }
 }
 struct auth bad={0};if(auth_encode(&bad,0xffffffffUL,out,64)||bad.state!=INVALID)return 12;
 for(U i=0;i<sizeof(lines)/sizeof(lines[0]);i++) {
  const struct line_vector *v=&lines[i];
  for(U split=0;split<=v->n;split++) {
   struct auth a={0};if(!auth_encode(&a,62001,out,64))return 13;
   if(split)feed(&a,v->raw,split);
   if(split<v->n)feed(&a,v->raw+split,v->n-split);
   int good=a.state==GUID_PARSED;
   if(good!=v->good)return 14;
   if(!good){invalid(&a);if(begin_encode(&a,out,64))return 15;}
   else {
    for(U j=0;j<32;j++)if(a.guid[j]!=v->raw[j+3])return 16;
    for(U cap=0;cap<7;cap++){struct auth copy=a;if(begin_encode(&copy,out,cap)||copy.state!=INVALID)return 17;}
    if(begin_encode(&a,out,64)!=7||a.state!=BEGIN_ENCODED)return 18;
    static const char expected[]="BEGIN\r\n";for(U j=0;j<7;j++)if(out[j]!=(unsigned char)expected[j])return 19;
    if(feed(&a,v->raw,v->n)||a.state!=INVALID)return 20;
   }
  }
 }
 struct auth a={0};if(!auth_encode(&a,1,out,64))return 21;
 for(U i=0;i<lines[0].n;i++)if(!feed(&a,lines[0].raw+i,1))return 22;
 if(a.state!=GUID_PARSED)return 23;
 struct auth twice={0};if(!auth_encode(&twice,1,out,64)||auth_encode(&twice,1,out,64)||twice.state!=INVALID)return 24;
 struct auth early={0};if(begin_encode(&early,out,64)||early.state!=INVALID)return 25;
 struct auth zero={0};if(!auth_encode(&zero,1,out,64)||feed(&zero,out,0)||zero.state!=INVALID)return 26;
 return 0;
}
void entry(void){call(60,(U)run(),0,0);__builtin_unreachable();}
__asm__(".global _start\n_start:\nand $-16,%rsp\ncall entry\nud2\n");
