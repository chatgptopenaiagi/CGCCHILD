/* Filtered owned sender composition. No protected UID or broker authority. */
#include "payload.h"
#include "receive.h"
#include <sys/stat.h>
_Static_assert(sizeof(struct stat)==144,"installed native x86-64 stat ABI");
struct fd_identity {U dev,ino,mode,uid,gid,rdev;long flags;int bound;};
static struct fd_identity ids[7];
static int capture_fd(int fd) {
 struct stat st;long flags=S(72,fd,3,0,0,0,0);
 if(S(5,fd,&st,0,0,0,0)||flags<0||S(72,fd,1,0,0,0,0)!=1)return 0;
 ids[fd]=(struct fd_identity){st.st_dev,st.st_ino,st.st_mode,st.st_uid,st.st_gid,st.st_rdev,flags,1};return 1;
}
static int same_fd(int fd) {
 struct stat st;struct fd_identity *x=&ids[fd];
 return x->bound&&S(5,fd,&st,0,0,0,0)==0&&S(72,fd,1,0,0,0,0)==1&&
 S(72,fd,3,0,0,0,0)==x->flags&&st.st_dev==x->dev&&st.st_ino==x->ino&&
 st.st_mode==x->mode&&st.st_uid==x->uid&&st.st_gid==x->gid&&st.st_rdev==x->rdev;
}
static int setup_inventory(void) {
 for(int fd=3;fd<64;fd++) {
  long f=S(72,fd,1,0,0,0,0);
  if(fd<=6?!same_fd(fd):f!=-9)return 0;
 }
 return 1;
}
static int substitution_checks(void) {
 for(int fd=3;fd<=6;fd++)if(!capture_fd(fd))return 0;
 if((ids[3].mode&0170000)!=0140000||(ids[4].mode&0170000)!=0140000||
    (ids[5].mode&0170000)!=0010000||(ids[6].mode&0170000)!=0010000||
    (ids[3].flags&3)!=2||(ids[4].flags&3)!=2||(ids[5].flags&3)!=0||(ids[6].flags&3)!=1)return 0;
 for(int fd=3;fd<=4;fd++) {
  int type=0,domain=0;unsigned int n=4;
  if(S(55,fd,1,3,&type,&n,0)||n!=4||type!=5)return 0;
  n=4;if(S(55,fd,1,39,&domain,&n,0)||n!=4||domain!=1)return 0;
 }
 if(!setup_inventory())return 0;
 if(S(72,3,1030,7,0,0,0)!=7||setup_inventory())return 0; /* extra FD */
 if(S(292,5,3,0x80000,0,0,0)!=3||same_fd(3))return 0; /* pipe replaces socket */
 if(S(292,4,3,0x80000,0,0,0)!=3||same_fd(3))return 0; /* other socket inode */
 if(S(292,7,3,0x80000,0,0,0)!=3||S(3,7,0,0,0,0,0)||!setup_inventory())return 0;
 if(S(72,5,1030,7,0,0,0)!=7||S(292,6,5,0x80000,0,0,0)!=5||same_fd(5))return 0; /* same pipe, wrong access */
 if(S(292,7,5,0x80000,0,0,0)!=5||S(3,7,0,0,0,0,0)||!setup_inventory())return 0;
 if(S(72,3,2,0,0,0,0)||same_fd(3)||S(72,3,2,1,0,0,0)||!setup_inventory())return 0;
 return 1;
}

struct ins {unsigned short code;unsigned char jt,jf;unsigned int k;};
struct prog {unsigned short len;struct ins *filter;};
#include "sender_filters.h"
/* Kernel-created descriptors only; a single-threaded immutable live inventory. */
static int live_inventory=1;
static U last_rights,last_min,last_max;
static int ancillary(struct msg *msg,U *facts) {
 facts[0]=facts[1]=facts[2]=0;facts[3]=(U)(msg->flags & ~0x40000000);
 facts[4]=facts[5]=facts[6]=0;last_rights=0;last_min=64;last_max=0;
 if(msg->controllen>112)return 0;
 U offset=0;int okay=1;
 while(msg->controllen-offset>=16) {
  struct cm *h=(struct cm *)((unsigned char *)msg->control+offset);
  if(h->len<16||h->len>msg->controllen-offset)return 0;
  U size=h->len-16;unsigned char *data=(unsigned char *)h+16;
  if(h->level==1&&h->type==2) {
   facts[0]++;
   if(size!=12)okay=0;
   else {struct cred *c=(struct cred *)data;facts[4]=(U)c->pid;facts[5]=c->uid;facts[6]=c->gid;}
  } else if(h->level==1&&h->type==1) {
   facts[1]++;if(size%4)okay=0;
   for(U i=0;i<size/4;i++) {
    int fd=((int *)data)[i];
    if(fd<3||fd>=64||fd==3||fd==4||(live_inventory&&fd==6)){okay=0;continue;}
    if((S(72,fd,1,0,0,0,0)&1)!=1)okay=0;
    if((U)fd>maximum_fd)maximum_fd=(U)fd;
    if((U)fd>last_max)last_max=(U)fd;
    if((U)fd<last_min)last_min=(U)fd;
    if(S(3,fd,0,0,0,0,0)!=0)okay=0;
    else {closed_rights++;last_rights++;}
   }
  } else facts[2]++;
  U step=(h->len+7)&~(U)7;
  if(step>msg->controllen-offset){offset=msg->controllen;break;}
  offset+=step;
 }
 for(;offset<msg->controllen;offset++)if(((unsigned char *)msg->control)[offset])okay=0;
 return okay;
}
static int clean_inventory(void) {
 for(int fd=3;fd<64;fd++) {
  long flags=S(72,fd,1,0,0,0,0);int present=fd==3||fd==4||(live_inventory&&fd==6);
  if(present?(flags<0||!same_fd(fd)):flags!=-9)return 0;
 }
 return 1;
}

static int install(struct prog *p){return S(317,1,0,p,0,0,0)==0;}
static int denials(void) {
 return S(59,0,0,0,0,0,0)==-1&&S(41,1,1,0,0,0,0)==-1&&
 S(435,0,0,0,0,0,0)==-1&&S(272,0,0,0,0,0,0)==-1&&
 S(101,0,0,0,0,0,0)==-1&&S(57,0,0,0,0,0,0)==-1&&S(322,0,0,0,0,0,0)==-1;
}
struct pollfd {int fd;short events,revents;};
static int ready(int fd,int timeout) {
 struct pollfd p={fd,1,0};long result=S(7,&p,1,timeout,0,0,0);
 if(result==0){return 0;}
 if(result!=1||(p.revents&40)){return -1;}
 return (p.revents&1)?1:-1;
}
static int sender(void) {
 if(S(3,4,0,0,0,0,0)||S(3,6,0,0,0,0,0))return 30;
 if(!install(&sender_filter)||!same_fd(3)||!same_fd(5)||!denials()||S(317,1,0,&sender_filter,0,0,0)!=-1||S(46,4,0,0,0,0,0)!=-1)return 34;
 struct iov iov={(void *)packet,sizeof(packet)-1};struct msg m={0,0,&iov,1,0,0,0};
 for(int i=0;i<5;i++) {
  union control c={0};int rights=i==1||i==3?16:i==2?17:0;
  if(rights){struct cm *h=(struct cm *)c.bytes;h->len=16+(U)rights*4;h->level=1;h->type=1;
   for(int j=0;j<rights;j++)((int *)(c.bytes+16))[j]=5;
   m.control=c.bytes;m.controllen=(h->len+7)&~7UL;
  } else {m.control=0;m.controllen=0;}
  if(S(46,3,&m,0,0,0,0)!=(long)(sizeof(packet)-1))return 31;
 }
 char gate=0;
 if(S(0,5,&gate,1,0,0,0)!=1||gate!='G')return 32;
 if(S(3,3,0,0,0,0,0)||S(3,5,0,0,0,0,0))return 33;
 return 0;
}
static int receive_from(U pid,int expected_accept,int *wrong_refused,U rights,int truncated) {
 if(ready(4,2000)!=1)return 0;
 union control control={0};unsigned char raw[1024];U facts[7];
 struct iov iov={raw,sizeof(raw)};struct msg m={0,0,&iov,1,control.bytes,sizeof(control.bytes),0};
 long count=S(47,4,&m,0x40000040,0,0,0);
 if(count<=0||count>1024||!ancillary(&m,facts))return 0;
 received_messages++;
 int matched=facts[4]==pid&&facts[5]==me[1]&&facts[6]==me[2];
 if(expected_accept&&facts[4]!=me[0])*wrong_refused=1;
 int live=ready(3,0)==0;
 facts[4]=4242;facts[5]=62001;facts[6]=62001;
 int accepted=matched&&live&&accept(raw,(U)count,&expected,facts);
 return accepted==expected_accept&&last_rights==rights&&((facts[3]&8)!=0)==truncated&&clean_inventory()&&(!rights||(last_min==5&&last_max==(live_inventory?21:20)));
}
static int run(void) {
 me[0]=(U)S(39,0,0,0,0,0,0);me[1]=(U)S(102,0,0,0,0,0,0);me[2]=(U)S(104,0,0,0,0,0,0);
 if(!me[1])return 1;
 if(S(436,3,0xffffffffU,0,0,0,0))return 2;
 U old_limit[2],limit[2]={64,64},check[2];
 if(S(302,0,7,0,old_limit,0,0)||old_limit[0]<64||old_limit[1]<64||S(302,0,7,limit,0,0,0)||S(302,0,7,0,check,0,0)||check[0]!=64||check[1]!=64)return 18;
 if(S(157,38,1,0,0,0,0))return 18;
 int pair[2],gate[2],one=1;
 if(S(53,1,0x80005,0,pair,0,0)||pair[0]!=3||pair[1]!=4)return 3;
 if(S(293,gate,0x80000,0,0,0,0)||gate[0]!=5||gate[1]!=6)return 4;
 if(S(54,4,1,16,&one,4,0))return 5;
 if(!substitution_checks())return 22;
 long pid=S(57,0,0,0,0,0,0);if(pid<0)return 6;
 if(pid==0)return sender();
 if(S(3,3,0,0,0,0,0)||S(3,5,0,0,0,0,0))return 7;
 if(S(434,pid,0,0,0,0,0)!=3||!capture_fd(3)||!clean_inventory())return 8;
 struct cred connection={0};unsigned int length=sizeof(connection);
 if(S(55,4,1,17,&connection,&length,0)||length!=sizeof(connection))return 9;
 if((U)connection.pid!=me[0]||(U)connection.pid==(U)pid)return 10;
 for(U i=0;i<sizeof(bindings)/sizeof(bindings[0]);i++)bindings[i].code[bindings[i].index].k=(unsigned int)pid;
 if(!install(&receiver_live)||!denials()||S(61,pid+1,0,0,0,0,0)!=-1)return 19;
 int wrong_refused=0;
 if(!receive_from((U)pid,1,&wrong_refused,0,0)||!wrong_refused)return 11;
 if(!receive_from((U)pid,0,&wrong_refused,16,0)||!receive_from((U)pid,0,&wrong_refused,16,1))return 21;
 char token='G';if(S(1,6,&token,1,0,0,0)!=1||S(3,6,0,0,0,0,0))return 12;
 int status=-1;
 if(S(61,pid,&status,0,0,0,0)!=pid||status!=0||ready(3,0)!=1)return 13;
 live_inventory=0;
 if(!install(&receiver_drain)||!denials()||S(317,1,0,&receiver_live,0,0,0)!=-1||S(1,6,&token,1,0,0,0)!=-1||S(61,pid,0,0,0,0,0)!=-1)return 20;
 if(!receive_from((U)pid,0,&wrong_refused,16,0)||!receive_from((U)pid,0,&wrong_refused,0,0)||received_messages!=5||closed_rights!=48||maximum_fd!=21)return 14;
 if(S(3,3,0,0,0,0,0)||ready(3,0)!=-1||S(3,4,0,0,0,0,0))return 15;
 for(int fd=3;fd<64;fd++)if(S(72,fd,1,0,0,0,0)!=-9)return 16;
 U report[4]={5,48,21,64};
 if(S(1,1,report,sizeof(report),0,0,0)!=(long)sizeof(report))return 17;
 return 0;
}
void entry(void){S(60,run(),0,0,0,0,0);__builtin_unreachable();}
__asm__(".global _start\n_start:\nand $-16,%rsp\ncall entry\nud2\n");
