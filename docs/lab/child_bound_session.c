/* Native admission session MODEL over owned sockets. No broker/cgroup effects. */
#include "lifecycle.h"
#include "socket_types.h"
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
#include "session_filters.h"
struct packet_vector {const unsigned char *request,*reply;U request_size,reply_size;};
#include "session_vectors.h"
static U self_pid,self_uid,self_gid;
struct pollfd {int fd;short events,revents;};
static int poll_one(int fd,int timeout) {
 struct pollfd p={fd,1,0};long result=S(7,&p,1,timeout,0,0,0);
 if(result==0)return 0;
 if(result!=1||(p.revents&40))return -1;
 return (p.revents&1)?1:-1;
}
static int session_inventory(void) {
 for(int fd=3;fd<64;fd++){long flags=S(72,fd,1,0,0,0,0);if(fd<=4?!same_fd(fd):flags!=-9)return 0;}
 return 1;
}
static int transmit(int fd,const unsigned char *raw,U n) {
 if(!session_inventory())return 0;
 struct iov iov={(void *)raw,n};struct msg m={0,0,&iov,1,0,0,0};
 return S(46,fd,&m,0,0,0,0)==(long)n;
}
/* Kernel-origin ancillary only; fixed3/4 protected, all other slots closed. */
static long receive(int fd,int pidfd,U peer,unsigned char *raw) {
 if(!session_inventory()||poll_one(fd,2000)!=1)return -1;
 union control c={0};struct iov iov={raw,1024};struct msg m={0,0,&iov,1,c.bytes,sizeof(c.bytes),0};
 long count=S(47,fd,&m,0x40000040,0,0,0);if(count==0)return 0;
 if(count<0||count>1024||m.controllen>112)return -1;
 U at=0,credentials=0;int valid=!(m.flags&~0x40000000),matched=0;
 while(m.controllen-at>=16) {
  struct cm *h=(struct cm *)(c.bytes+at);
  if(h->len<16||h->len>m.controllen-at)return -1;
  U n=h->len-16;unsigned char *data=(unsigned char *)h+16;
  if(h->level==1&&h->type==2) {
   credentials++;
   if(n!=12)valid=0;
   else {struct cred *v=(struct cred *)data;matched=(U)v->pid==peer&&v->uid==self_uid&&v->gid==self_gid;}
  } else if(h->level==1&&h->type==1) {
   valid=0;
   if(n%4)return -1;
   for(U i=0;i<n/4;i++){int received=((int *)data)[i];if(received<5||received>=64)return -1;if(S(3,received,0,0,0,0,0))return -1;}
  } else valid=0;
  U step=(h->len+7)&~7UL;if(step>m.controllen-at){at=m.controllen;break;}at+=step;
 }
 for(;at<m.controllen;at++)if(c.bytes[at])valid=0;
 return session_inventory()&&valid&&credentials==1&&matched&&poll_one(pidfd,0)==0?count:-1;
}
static int denied(void) {
 return S(59,0,0,0,0,0,0)==-1&&S(41,1,1,0,0,0,0)==-1&&S(57,0,0,0,0,0,0)==-1&&S(101,0,0,0,0,0,0)==-1&&S(292,3,7,0x80000,0,0,0)==-1&&S(72,3,2,0,0,0,0)==-1;
}
static int controller(void) {
 if(S(3,4,0,0,0,0,0)||S(3,6,0,0,0,0,0)||S(434,self_pid,0,0,0,0,0)!=4||!capture_fd(4))return 30;
 if(S(317,1,0,&controller_filter,0,0,0)||!denied())return 31;
 char gate=0;if(!same_fd(5)||S(0,5,&gate,1,0,0,0)!=1||gate!='G'||S(3,5,0,0,0,0,0))return 32;
 for(U i=0;i<6;i++) {
  const struct packet_vector *v=&packets[i];unsigned char raw[1024];
  if(!transmit(3,v->request,v->request_size))return 33;
  long n=receive(3,4,self_pid,raw);
  if(i==5){if(n!=0)return 34;break;}
  if(n!=(long)v->reply_size)return 35;
  for(U j=0;j<(U)n;j++)if(raw[j]!=v->reply[j])return 36;
  struct message parsed;int invalid;
  if(!reply_parse(raw,(U)n,&parsed,&invalid)||invalid)return 37;
 }
 if(S(317,1,0,&controller_filter,0,0,0)!=-1||S(3,3,0,0,0,0,0)||S(3,4,0,0,0,0,0))return 38;
 return 0;
}
static int run(void) {
 self_pid=(U)S(39,0,0,0,0,0,0);self_uid=(U)S(102,0,0,0,0,0,0);self_gid=(U)S(104,0,0,0,0,0,0);
 if(!self_uid||S(436,3,0xffffffffU,0,0,0,0))return 1;
 U old[2],limit[2]={64,64};
 if(S(302,0,7,0,old,0,0)||old[0]<64||old[1]<64||S(302,0,7,limit,0,0,0)||S(157,38,1,0,0,0,0))return 2;
 int pair[2],gate[2],one=1;
 if(S(53,1,0x80005,0,pair,0,0)||pair[0]!=3||pair[1]!=4||
    S(293,gate,0x80000,0,0,0,0)||gate[0]!=5||gate[1]!=6||
    S(54,3,1,16,&one,4,0)||S(54,4,1,16,&one,4,0))return 3;
 if(!substitution_checks())return 18;
 long pid=S(57,0,0,0,0,0,0);if(pid<0)return 4;if(!pid)return controller();
 if(S(3,3,0,0,0,0,0)||S(3,5,0,0,0,0,0)||S(434,pid,0,0,0,0,0)!=3||!capture_fd(3))return 5;
 for(U i=0;i<sizeof(bindings)/sizeof(bindings[0]);i++)bindings[i].code[bindings[i].index].k=(unsigned int)pid;
 if(S(317,1,0,&broker_open,0,0,0)||!denied())return 6;
 char release='G';if(!same_fd(6)||S(1,6,&release,1,0,0,0)!=1||S(3,6,0,0,0,0,0))return 7;
 struct lab lab={NEW,1,0,0,0,0};
 for(U i=0;i<6;i++) {
  unsigned char raw[1024],reply[1024];U reply_size=0;long n=receive(4,3,(U)pid,raw);
  if(n<=0)return 8;
  /* Continuity and empty are MODEL inputs. Effects remain counters only. */
  int okay=dispatch(&lab,raw,(U)n,1,1,1,reply,&reply_size);
  if(i==5){if(okay||reply_size||lab.state!=CLOSED)return 9;break;}
  if(!okay)return 10;
  if(i==2&&(S(317,1,0,&broker_sealed,0,0,0)||S(317,1,0,&broker_open,0,0,0)!=-1))return 11;
  if(!transmit(4,reply,reply_size))return 12;
 }
 if(lab.creates!=1||lab.attaches!=1||lab.removes!=1||lab.count!=5||lab.state!=CLOSED)return 13;
 if(S(3,4,0,0,0,0,0))return 14;
 int status=-1;if(S(61,pid,&status,0,0,0,0)!=pid||status||poll_one(3,0)!=1||S(3,3,0,0,0,0,0))return 15;
 for(int fd=3;fd<64;fd++)if(S(72,fd,1,0,0,0,0)!=-9)return 16;
 U report[4]={6,5,1,1};if(S(1,1,report,sizeof(report),0,0,0)!=(long)sizeof(report))return 17;
 return 0;
}
void entry(void){S(60,run(),0,0,0,0,0);__builtin_unreachable();}
__asm__(".global _start\n_start:\nand $-16,%rsp\ncall entry\nud2\n");
