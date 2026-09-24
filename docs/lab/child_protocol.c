/* Fixed native CGC_LAB_PROTO_V1 payload mechanics only. No broker, IPC or authority. */
typedef unsigned long U;
struct cursor {const unsigned char *p; U n,i;};
struct message {int kind,op;char nonce[33],b[33],c[33],domain[33],lab[33],epoch[33];U seq;};
static const char *ops[]={"CREATE_OWN_DOMAIN","ATTACH_OWN_GATED_CHILD","SEAL","QUERY","REMOVE_OWN_EMPTY_DOMAIN"};
static int lit(struct cursor *r,const char *s) {
 U j=0;while(s[j]){if(j>=r->n-r->i||r->p[r->i+j]!=(unsigned char)s[j])return 0;j++;}
 r->i+=j;return 1;
}
static int hex(struct cursor *r,char *out) {
 if(r->n-r->i<32)return 0;
 for(U j=0;j<32;j++){unsigned char c=r->p[r->i+j];if(!((c>='0'&&c<='9')||(c>='a'&&c<='f')))return 0;out[j]=(char)c;}
 out[32]=0;r->i+=32;return 1;
}
static int number(struct cursor *r,U *out) {
 if(r->i==r->n||r->p[r->i]<'1'||r->p[r->i]>'9')return 0;
 U n=0,count=0;
 while(r->i<r->n&&r->p[r->i]>='0'&&r->p[r->i]<='9') {
  U d=r->p[r->i++]-'0';if(++count>20||n>(~(U)0-d)/10)return 0;n=n*10+d;
 }
 *out=n;return 1;
}
static int parse(const unsigned char *p,U n,struct message *m) {
 if(!n||n>1024)return 0;
 struct cursor r={p,n,0};
 if(lit(&r,"{\"NONCE\":\"")) {
  m->kind=1;
  return hex(&r,m->nonce)&&lit(&r,"\",\"TYPE\":\"READY\",\"VERSION\":1}")&&r.i==r.n;
 }
 r.i=0;m->kind=2;
 if(!lit(&r,"{\"BROKER_GENERATION\":\"")||!hex(&r,m->b)||
    !lit(&r,"\",\"CONTROLLER_GENERATION\":\"")||!hex(&r,m->c)||
    !lit(&r,"\",\"DOMAIN_ID\":\"")||!hex(&r,m->domain)||
    !lit(&r,"\",\"LAB_ID\":\"cgcq-")||!hex(&r,m->lab)||!lit(&r,"\",\"OP\":\""))return 0;
 U start=r.i;int found=0;
 for(int op=0;op<5;op++){r.i=start;if(lit(&r,ops[op])&&lit(&r,"\"")){m->op=op;found=1;break;}}
 if(!found||!lit(&r,",\"REQUEST_SEQUENCE\":")||!number(&r,&m->seq)||!lit(&r,",\"SEAL_EPOCH\":\""))return 0;
 if(lit(&r,"0\"")){m->epoch[0]='0';m->epoch[1]=0;}
 else if(!hex(&r,m->epoch)||!lit(&r,"\""))return 0;
 return lit(&r,"}")&&r.i==r.n;
}
static int same(const char *a,const char *b){for(U i=0;i<33;i++){if(a[i]!=b[i])return 0;if(!a[i])return 1;}return 0;}
static int match(const struct message *m,const struct message *e) {
 if(m->kind!=e->kind)return 0;
 if(m->kind==1)return same(m->nonce,e->nonce);
 return m->op==e->op&&m->seq==e->seq&&same(m->b,e->b)&&same(m->c,e->c)&&same(m->domain,e->domain)&&same(m->lab,e->lab)&&same(m->epoch,e->epoch);
}
struct writer {unsigned char *p;U n;int ok;};
static void put(struct writer *w,const char *s){for(U i=0;s[i];i++){if(w->n==1024){w->ok=0;return;}w->p[w->n++]=(unsigned char)s[i];}}
static U encode(const struct message *m,unsigned char *out) {
 struct writer w={out,0,1};
 if(m->kind==1){put(&w,"{\"NONCE\":\"");put(&w,m->nonce);put(&w,"\",\"TYPE\":\"READY\",\"VERSION\":1}");}
 else {
  put(&w,"{\"BROKER_GENERATION\":\"");put(&w,m->b);put(&w,"\",\"CONTROLLER_GENERATION\":\"");put(&w,m->c);
  put(&w,"\",\"DOMAIN_ID\":\"");put(&w,m->domain);put(&w,"\",\"LAB_ID\":\"cgcq-");put(&w,m->lab);
  put(&w,"\",\"OP\":\"");put(&w,ops[m->op]);put(&w,"\",\"REQUEST_SEQUENCE\":");
  char reversed[21],digits[21];U n=m->seq,k=0;do{reversed[k++]=(char)('0'+n%10);n/=10;}while(n);
  for(U i=0;i<k;i++){digits[i]=reversed[k-1-i];}
  digits[k]=0;put(&w,digits);
  put(&w,",\"SEAL_EPOCH\":\"");put(&w,m->epoch);put(&w,"\"}");
 }
 return w.ok?w.n:0;
}
/* Normalized ancillary facts are test inputs, NOT kernel credential authentication. */
static int accept(const unsigned char *raw,U n,const struct message *expected,const U *a) {
 if(a[0]!=1||a[1]||a[2]||a[3]||a[4]!=4242||a[5]!=62001||a[6]!=62001)return 0;
 struct message m;
 if(!parse(raw,n,&m)||!match(&m,expected))return 0;
 unsigned char encoded[1024];U count=encode(&m,encoded);
 if(count!=n)return 0;
 for(U i=0;i<n;i++)if(encoded[i]!=raw[i])return 0;
 return 1;
}
struct vector {const unsigned char *raw;U n;const struct message *expected;U ancillary[7];int good;};
#include "protocol_vectors.h"
__attribute__((noinline,noclone)) static long call(U nr,U a,U b,U c) {
 long out;__asm__ volatile("syscall":"=a"(out):"a"(nr),"D"(a),"S"(b),"d"(c):"rcx","r11","memory");return out;
}
static int run(void) {
 if(call(102,0,0,0)==0)return 2;
 for(U i=0;i<sizeof(vectors)/sizeof(vectors[0]);i++) {
  const struct vector *v=&vectors[i];
  if(accept(v->raw,v->n,v->expected,v->ancillary)!=v->good){unsigned int failed=(unsigned int)i;call(1,1,(U)&failed,4);return 1;}
 }
 return 0;
}
void entry(void){call(60,(U)run(),0,0);__builtin_unreachable();}
__asm__(".global _start\n_start:\nand $-16,%rsp\ncall entry\nud2\n");
