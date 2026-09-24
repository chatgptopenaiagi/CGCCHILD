/* Closed selector encoder fixture: dummy immutable targets, never a bus client. */
typedef unsigned long U;
struct writer {unsigned char *p;U n,cap;int ok;};
static U length(const char *s){U n=0;while(s[n])n++;return n;}
static void byte(struct writer *w,unsigned char v) {
 if(!w->ok||w->n>=w->cap){w->ok=0;return;}w->p[w->n++]=v;
}
static void pad(struct writer *w,U a){while(w->ok&&(w->n&(a-1)))byte(w,0);}
static void scalar(struct writer *w,U width,U v) {
 pad(w,width);for(U i=0;i<width;i++)byte(w,(unsigned char)(v>>(8*i)));
}
static void patch(struct writer *w,U at,U v) {
 if(at>w->n||w->n-at<4){w->ok=0;return;}
 for(U i=0;i<4;i++)w->p[at+i]=(unsigned char)(v>>(8*i));
}
static void text(struct writer *w,int signature,const char *s) {
 U n=length(s);if(n>(signature?255UL:4096UL)){w->ok=0;return;}
 scalar(w,signature?1:4,n);for(U i=0;i<n;i++)byte(w,(unsigned char)s[i]);byte(w,0);
}
static U array(struct writer *w,U alignment) {pad(w,4);U at=w->n;scalar(w,4,0);pad(w,alignment);return at;}
static void end_array(struct writer *w,U at,U start){patch(w,at,w->n-start);}
static void field(struct writer *w,U key,const char *type,const char *s) {
 pad(w,8);byte(w,(unsigned char)key);text(w,1,type);text(w,type[0]=='g',s);
}
static void prop(struct writer *w,const char *name,const char *type) {
 pad(w,8);text(w,0,name);text(w,1,type);
}
static void ps(struct writer *w,const char *name,const char *value){prop(w,name,"s");text(w,0,value);}
static void pn(struct writer *w,const char *name,const char *type,U width,U value){prop(w,name,type);scalar(w,width,value);}
static const char unit[]="cgcq-00000000000000000000000000000001.service";
static const char peer[]="cgcq-00000000000000000000000000000001-peer.service";
static const char image[]="/run/cgc-quiescence/cgcq-00000000000000000000000000000001/bin/cgc-lab";
static const char manifest[]="/run/cgc-quiescence/cgcq-00000000000000000000000000000001/manifest.json";
static const char bus[]="org.freedesktop.DBus";
static const char manager[]="org.freedesktop.systemd1";
static const char manager_interface[]="org.freedesktop.systemd1.Manager";
static const char bus_path[]="/org/freedesktop/DBus";
static const char manager_path[]="/org/freedesktop/systemd1";
static const char unit_path[]="/org/freedesktop/systemd1/unit/cgcq_2d00000000000000000000000000000001_2eservice";
static void exec_property(struct writer *w) {
 prop(w,"ExecStart","a(sasb)");U at=array(w,8),start=w->n;
 pad(w,8);text(w,0,image);
 U args=array(w,4),args_start=w->n;text(w,0,image);text(w,0,"--manifest");text(w,0,manifest);
 end_array(w,args,args_start);scalar(w,4,0);end_array(w,at,start);
}
static void launch(struct writer *w,int is_peer) {
 text(w,0,is_peer?peer:unit);text(w,0,"fail");
 U at=array(w,8),start=w->n;
 if(is_peer){exec_property(w);ps(w,"Type","exec");}
 else {
  pn(w,"Delegate","b",4,1);
  prop(w,"Environment","as");U env=array(w,4),env_start=w->n;text(w,0,"LANG=C");text(w,0,"LC_ALL=C");end_array(w,env,env_start);
  exec_property(w);ps(w,"ExitType","cgroup");ps(w,"Group","0");ps(w,"KillMode","process");
  pn(w,"LimitCORE","t",8,0);pn(w,"LimitCORESoft","t",8,0);
  pn(w,"LimitNOFILE","t",8,64);pn(w,"LimitNOFILESoft","t",8,64);
  ps(w,"Restart","no");pn(w,"RuntimeMaxUSec","t",8,~0UL);
  pn(w,"SendSIGHUP","b",4,0);pn(w,"SendSIGKILL","b",4,0);ps(w,"Slice","system.slice");
  prop(w,"SupplementaryGroups","as");U groups=array(w,4);end_array(w,groups,w->n);
  pn(w,"TasksMax","t",8,16);ps(w,"Type","exec");pn(w,"UMask","u",4,63);
  ps(w,"User","0");pn(w,"WatchdogUSec","t",8,0);ps(w,"WorkingDirectory","/");
 }
 end_array(w,at,start);U aux=array(w,8);end_array(w,aux,w->n);
}
static U encode(U selector,unsigned char *out,U capacity) {
 if(selector<1||selector>11)return 0;
 unsigned char body[4096],header[4096];struct writer b={body,0,sizeof(body),1},h={header,0,sizeof(header),1};
 static const char *const members[]={"","Hello","GetNameOwner","GetUnit","Get","StartTransientUnit",
  "AttachProcessesToUnit","SetUnitProperties","AttachProcesses","AddMatch","Subscribe","StartTransientUnit"};
 static const char *const signatures[]={"","","s","s","ss","ssa(sv)a(sa(sv))","ssau","sba(sv)","sau","s","","ssa(sv)a(sa(sv))"};
 int is_bus=selector==1||selector==2||selector==9;
 const char *path=is_bus?bus_path:(selector==4||selector==8?unit_path:manager_path);
 const char *iface=is_bus?bus:selector==4?"org.freedesktop.DBus.Properties":selector==8?"org.freedesktop.systemd1.Service":manager_interface;
 switch(selector) {
 case 1:case 10:break;
 case 2:text(&b,0,manager);break;
 case 3:text(&b,0,unit);break;
 case 4:text(&b,0,"org.freedesktop.systemd1.Unit");text(&b,0,"ControlGroup");break;
 case 5:case 11:launch(&b,selector==11);break;
 case 6:case 8: {
  if(selector==6)text(&b,0,unit);
  text(&b,0,"workers");U at=array(&b,4),start=b.n;scalar(&b,4,4242);end_array(&b,at,start);break;
 }
 case 7: {
  text(&b,0,unit);scalar(&b,4,1);U at=array(&b,8),start=b.n;
  ps(&b,"Description","CGC lab unauthorized probe");end_array(&b,at,start);break;
 }
 case 9:text(&b,0,"type='signal',sender='org.freedesktop.DBus',interface='org.freedesktop.DBus',member='NameOwnerChanged',arg0='org.freedesktop.systemd1'");break;
 }
 byte(&h,108);byte(&h,1);byte(&h,2);byte(&h,1);scalar(&h,4,b.n);scalar(&h,4,selector);scalar(&h,4,0);
 field(&h,1,"o",path);field(&h,2,"s",iface);field(&h,3,"s",members[selector]);field(&h,6,"s",is_bus?bus:manager);
 if(signatures[selector][0])field(&h,8,"g",signatures[selector]);
 patch(&h,12,h.n-16);pad(&h,8);
 if(!h.ok||!b.ok||h.n>capacity||b.n>capacity-h.n)return 0;
 for(U i=0;i<h.n;i++)out[i]=header[i];
 for(U i=0;i<b.n;i++)out[h.n+i]=body[i];
 return h.n+b.n;
}
struct vector {const unsigned char *raw;U n;};
#include "encode_vectors.h"
__attribute__((noinline,noclone)) static long call(U nr,U a,U b,U c) {
 long out;__asm__ volatile("syscall":"=a"(out):"a"(nr),"D"(a),"S"(b),"d"(c):"rcx","r11","memory");return out;
}
static int run(void) {
 if(call(102,0,0,0)==0)return 2;
 unsigned char out[4098];
 for(U i=0;i<11;i++) {
  const struct vector *v=&vectors[i];
  for(U cap=0;cap<=v->n;cap++) {
   for(U j=0;j<sizeof(out);j++)out[j]=165;
   U n=encode(i+1,out+1,cap);
   if(n!=(cap==v->n?v->n:0))return (int)(10+i);
   for(U j=0;j<sizeof(out);j++) {
    unsigned char expected=n&&j>=1&&j<=n?v->raw[j-1]:165;
    if(out[j]!=expected)return (int)(30+i);
   }
  }
 }
 if(encode(0,out,sizeof(out))||encode(12,out,sizeof(out))||encode(~0UL,out,sizeof(out)))return 50;
 return 0;
}
void entry(void){call(60,(U)run(),0,0);__builtin_unreachable();}
__asm__(".global _start\n_start:\nand $-16,%rsp\ncall entry\nud2\n");
