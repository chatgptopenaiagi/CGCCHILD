/* Fixed incoming D-Bus decoder fixture. No transport, allocation or authority. */
typedef unsigned long U;
struct span {const unsigned char *p;U n;};
struct cursor {const unsigned char *p;U n,i;};
struct context {const char *sender,*signature;unsigned int reply,property,test;};
struct decoded {unsigned int kind,error,variant;struct span text[3];U number;struct span bytes;};
static int take(struct cursor *r,U n,struct span *s) {
 if(r->i>r->n||n>r->n-r->i)return 0;
 s->p=r->p+r->i;s->n=n;r->i+=n;return 1;
}
static int pad(struct cursor *r,U a) {
 struct span s;if(!take(r,(-r->i)&(a-1),&s))return 0;
 for(U i=0;i<s.n;i++){if(s.p[i])return 0;}return 1;
}
static int scalar(struct cursor *r,U bytes,U *v) {
 struct span s;if(!pad(r,bytes)||!take(r,bytes,&s))return 0;
 *v=0;for(U i=0;i<bytes;i++){*v|=(U)s.p[i]<<(8*i);}return 1;
}
static int eq(struct span s,const char *text) {
 U i=0;while(text[i]){if(i>=s.n||s.p[i]!=(unsigned char)text[i])return 0;i++;}return i==s.n;
}
static int equal(struct span a,struct span b) {
 if(a.n!=b.n){return 0;}for(U i=0;i<a.n;i++){if(a.p[i]!=b.p[i])return 0;}return 1;
}
static int string(struct cursor *r,int type,struct span *s) {
 U n;struct span zero;
 if(!scalar(r,type=='g'?1:4,&n)||n>4096||!take(r,n,s)||!take(r,1,&zero)||zero.p[0])return 0;
 for(U i=0;i<n;i++){if(!s->p[i]||s->p[i]>127)return 0;}
 if(type=='o') {
  if(!n||s->p[0]!='/')return 0;
  for(U i=1;i<n;i++) {
   unsigned char c=s->p[i];
   if(c=='/'){if(s->p[i-1]=='/'||i==n-1)return 0;}
   else if(!((c>='a'&&c<='z')||(c>='A'&&c<='Z')||(c>='0'&&c<='9')||c=='_'))return 0;
  }
 }
 return 1;
}
static int decode(const unsigned char *raw,U n,const struct context *ctx,struct decoded *out) {
 *out=(struct decoded){0};
 if(n<16||n>65536||raw[0]!=108||raw[3]!=1||raw[1]<2||raw[1]>4||(raw[2]&~3))return 0;
 struct cursor r={raw,n,4};U blen,serial,hlen;
 if(!scalar(&r,4,&blen)||!scalar(&r,4,&serial)||!scalar(&r,4,&hlen)||!serial||blen>65536||hlen>4096||hlen>n-16)return 0;
 U end=16+hlen,start=(end+7)&~7UL;
 if(start>n||blen!=n-start)return 0;
 struct span f[9]={{0}};U seen=0,reply=0;r.n=end;
 static const char types[]=" osssussg";
 while(r.i<r.n) {
  U key;struct span type;
  if(!pad(&r,8)||!scalar(&r,1,&key)||key<1||key>8||(seen&(1UL<<key))||!string(&r,'g',&type))return 0;
  if(type.n!=1||type.p[0]!=(unsigned char)types[key])return 0;
  seen|=1UL<<key;
  if(key==5){if(!scalar(&r,4,&reply))return 0;}
  else if(!string(&r,types[key],&f[key]))return 0;
 }
 r.n=n;if(!pad(&r,8)||r.i!=start||!eq(f[7],ctx->sender))return 0;
 U kind=raw[1],allowed=kind==2?((1UL<<5)|(1UL<<6)|(1UL<<7)|(1UL<<8)):
  kind==3?((1UL<<4)|(1UL<<5)|(1UL<<6)|(1UL<<7)|(1UL<<8)):
  ((1UL<<1)|(1UL<<2)|(1UL<<3)|(1UL<<6)|(1UL<<7)|(1UL<<8));
 if(seen&~allowed)return 0;
 if(kind!=4&&(!(seen&(1UL<<5))||reply!=ctx->reply))return 0;
 if(kind==2&&!eq(f[8],ctx->signature))return 0;
 out->kind=(unsigned int)kind;
 if(kind==3) {
  if(!eq(f[8],"s")||!string(&r,'s',&out->text[0])||r.i!=n||ctx->test<7||ctx->test>8)return 0;
  out->text[0]=(struct span){0}; /* Remote error text is never retained. */
  if(eq(f[4],"org.freedesktop.DBus.Error.AccessDenied"))out->error=1;
  else if(eq(f[4],"org.freedesktop.DBus.Error.InteractiveAuthorizationRequired"))out->error=2;
  else return 0;
  return 1;
 }
 if(kind==4) {
  if(!eq(f[1],"/org/freedesktop/DBus")||!eq(f[2],"org.freedesktop.DBus")||!eq(f[3],"NameOwnerChanged")||!eq(f[8],"sss"))return 0;
  for(U i=0;i<3;i++){if(!string(&r,'s',&out->text[i]))return 0;}
  return r.i==n&&eq(out->text[0],"org.freedesktop.systemd1")&&equal(out->text[1],out->text[2]);
 }
 if(eq(f[8],""))return r.i==n;
 if(eq(f[8],"s")||eq(f[8],"o"))return string(&r,f[8].p[0],&out->text[0])&&r.i==n;
 if(!eq(f[8],"v")||ctx->property<1||ctx->property>5)return 0;
 struct span variant;if(!string(&r,'g',&variant))return 0;
 if(ctx->property==2) {
  U length;
  if(!eq(variant,"ay")||!scalar(&r,4,&length)||length!=16||!take(&r,length,&out->bytes))return 0;
  out->variant=2;
 } else if(ctx->property==3) {
  if(!eq(variant,"u")||!scalar(&r,4,&out->number))return 0;
  out->variant=3;
 } else {
  if(!eq(variant,"s")||!string(&r,'s',&out->text[0]))return 0;
  out->variant=1;
 }
 return r.i==n;
}
struct vector {const unsigned char *raw;U n;struct context ctx;int good;struct decoded expected;};
#include "dbus_vectors.h"
__attribute__((noinline,noclone)) static long call(U nr,U a,U b,U c) {
 long out;__asm__ volatile("syscall":"=a"(out):"a"(nr),"D"(a),"S"(b),"d"(c):"rcx","r11","memory");return out;
}
static int run(void) {
 if(call(102,0,0,0)==0)return 2;
 for(U i=0;i<sizeof(vectors)/sizeof(vectors[0]);i++) {
  const struct vector *v=&vectors[i];struct decoded d;int good=decode(v->raw,v->n,&v->ctx,&d),same=good==v->good;
  if(good&&same) {
   same=d.kind==v->expected.kind&&d.error==v->expected.error&&d.variant==v->expected.variant&&d.number==v->expected.number&&equal(d.bytes,v->expected.bytes);
   for(U j=0;j<3;j++){if(!equal(d.text[j],v->expected.text[j]))same=0;}
  }
  if(!same){unsigned int failed=(unsigned int)i;call(1,1,(U)&failed,4);return 1;}
 }
 return 0;
}
void entry(void){call(60,(U)run(),0,0);__builtin_unreachable();}
__asm__(".global _start\n_start:\nand $-16,%rsp\ncall entry\nud2\n");
