/* Owned controller channel plus inert regular-file effects; no cgroup authority. */
#include "lifecycle.h"
#include "socket_types.h"
#include <sys/stat.h>
_Static_assert(sizeof(struct stat)==144,"installed native x86-64 stat ABI");
struct fd_identity {U dev,ino,mode,uid,gid,rdev;long flags;int bound;};
static struct fd_identity ids[13];
static int expected[64];
static int capture_fd(int fd) {
 struct stat st;long flags=S(72,fd,3,0,0,0,0);
 if(S(5,fd,&st,0,0,0,0)||flags<0||S(72,fd,1,0,0,0,0)!=1)return 0;
 ids[fd]=(struct fd_identity){st.st_dev,st.st_ino,st.st_mode,st.st_uid,st.st_gid,st.st_rdev,flags,1};expected[fd]=1;return 1;
}
static int same_fd(int fd) {
 struct stat st;struct fd_identity *x=&ids[fd];
 return x->bound&&S(5,fd,&st,0,0,0,0)==0&&S(72,fd,1,0,0,0,0)==1&&
 S(72,fd,3,0,0,0,0)==x->flags&&st.st_dev==x->dev&&st.st_ino==x->ino&&
 st.st_mode==x->mode&&st.st_uid==x->uid&&st.st_gid==x->gid&&st.st_rdev==x->rdev;
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
 for(int fd=3;fd<64;fd++){long flags=S(72,fd,1,0,0,0,0);if(expected[fd]?!same_fd(fd):flags!=-9)return 0;}
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
   for(U i=0;i<n/4;i++){int received=((int *)data)[i];if(received<3||received>=64||expected[received])return -1;if(S(3,received,0,0,0,0,0))return -1;}
  } else valid=0;
  U step=(h->len+7)&~7UL;if(step>m.controllen-at){at=m.controllen;break;}at+=step;
 }
 for(;at<m.controllen;at++)if(c.bytes[at])valid=0;
 return session_inventory()&&valid&&credentials==1&&matched&&poll_one(pidfd,0)==0?count:-1;
}

static int close_owned(int fd){if(S(3,fd,0,0,0,0,0))return 0;expected[fd]=0;return 1;}
static int narrow(struct prog *p){return S(317,1,0,p,0,0,0)==0;}
static int reap(int fd,U pid){
 int info[32];for(int i=0;i<32;i++)info[i]=0;
 return poll_one(fd,2000)==1&&S(247,3,fd,info,4,0,0)==0&&info[0]==17&&info[2]==1&&(U)info[4]==pid&&info[6]==0;
}
static int controller(void) {
 for(int fd=4;fd<=8;fd++)if(fd!=5&&!close_owned(fd))return 30;
 if(!narrow(&controller_filter)||!session_inventory())return 31;
 for(U i=0;i<6;i++){
  const struct packet_vector *v=&packets[i];unsigned char raw[1024];
  if(!transmit(3,v->request,v->request_size))return 32;
  long n=receive(3,5,self_pid,raw);
  if(i==5){if(n!=0)return 33;break;}
  if(n!=(long)v->reply_size)return 34;
  for(U j=0;j<(U)n;j++)if(raw[j]!=v->reply[j])return 35;
  struct message parsed;int invalid;if(!reply_parse(raw,(U)n,&parsed,&invalid)||invalid)return 37;
 }
 return close_owned(3)&&close_owned(5)?0:36;
}
static int worker(void){
 for(int fd=3;fd<=11;fd++)if(fd!=6&&!close_owned(fd))return 40;
 if(!narrow(&worker_filter)||!session_inventory())return 41;
 char c=0;if(poll_one(6,2000)!=1||S(0,6,&c,1,0,0,0)!=1||c!='G')return 42;
 return close_owned(6)?0:43;
}
static int run(void){
 self_pid=S(39,0,0,0,0,0,0);self_uid=S(102,0,0,0,0,0,0);self_gid=S(104,0,0,0,0,0,0);
 if(!self_uid||S(436,3,0xffffffffU,0,0,0,0)||S(157,38,1,0,0,0,0)||S(157,4,0,0,0,0,0))return 1;
 U limits[2]={64,64};if(S(302,0,7,limits,0,0,0))return 2;
 int pair[2],gate[2],one=1;
 if(S(53,1,0x80005,0,pair,0,0)||pair[0]!=3||pair[1]!=4||S(434,self_pid,0,0,0,0,0)!=5||
    S(293,gate,0x80000,0,0,0,0)||gate[0]!=6||gate[1]!=7||S(257,-100,".",0xb0000,0,0,0)!=8)return 3;
 if(S(54,3,1,16,&one,4,0)||S(54,4,1,16,&one,4,0))return 4;
 for(int fd=3;fd<=8;fd++)if(!capture_fd(fd))return 5;
 if((ids[3].mode&0170000)!=0140000||(ids[4].mode&0170000)!=0140000||
    (ids[6].mode&0170000)!=0010000||(ids[7].mode&0170000)!=0010000||
    (ids[8].mode&0170000)!=0040000)return 6;
 if(!narrow(&broker_boot))return 7;
 int cfd=-1,wfd=-1;long cp=S(56,0x1011,0,&cfd,0,0,0);if(cp<0)return 8;
 if(!cp)return controller();
 if(cfd!=9||!capture_fd(9)||!session_inventory())return 9;
 struct lab lab={NEW,1,0,0,0,0};U wp=0;int worker_done=0;
 for(U i=0;i<6;i++){
  unsigned char raw[1024],response[1024];U size=0;long n=receive(4,9,(U)cp,raw);
  if(n<=0)return 10;
  struct lab candidate=lab;
  int okay=dispatch(&candidate,raw,(U)n,1,1,worker_done,response,&size);
  if(i==5){if(okay||size||lab.state!=CLOSED)return 11;break;}
  if(!okay)return 12;
  if(i==0){
   if(S(258,8,"domain",0700,0,0,0)||S(257,8,"domain",0xb0000,0,0,0)!=10||!capture_fd(10)||
      S(257,10,"membership.inert",0xa00c2,0600,0,0)!=11||!capture_fd(11))return 13;
  }else if(i==1){
   long child=S(56,0x1011,0,&wfd,0,0,0);if(child<0)return 14;
   if(!child)return worker();
   wp=(U)child;
   if(wfd!=12||!capture_fd(12)||poll_one(12,0)!=0)return 15;
   unsigned char digits[20],back[20];U x=wp,count=0;do{digits[count++]=(unsigned char)('0'+x%10);x/=10;}while(x);
   for(U j=0;j<count/2;j++){unsigned char t=digits[j];digits[j]=digits[count-1-j];digits[count-1-j]=t;}
   if(S(1,11,digits,count,0,0,0)!=(long)count||S(17,11,back,count,0,0,0)!=(long)count)return 16;
   for(U j=0;j<count;j++)if(back[j]!=digits[j])return 17;
   if(!close_owned(3)||!close_owned(5)||!close_owned(6))return 18;
  }else if(i==2){
   if(!close_owned(11)||!narrow(&broker_sealed)||S(317,1,0,&broker_boot,0,0,0)!=-1)return 19;
  }else if(i==3){if(poll_one(12,0)!=0)return 20;
  }else if(i==4){
   if(!worker_done||!same_fd(10)||S(263,10,"membership.inert",0,0,0,0)||!close_owned(10)||
      S(263,8,"domain",512,0,0,0)||!close_owned(8))return 21;
  }
  lab=candidate;
  if(!transmit(4,response,size))return 22;
  if(i==3){char g='G';if(!same_fd(7)||S(1,7,&g,1,0,0,0)!=1||!reap(12,wp)||!close_owned(7)||!close_owned(12))return 23;worker_done=1;}
 }
 if(lab.count!=5||lab.creates!=1||lab.attaches!=1||lab.removes!=1||lab.state!=CLOSED)return 24;
 if(!close_owned(4)||!reap(9,(U)cp)||!close_owned(9)||!session_inventory())return 25;
 return 0;
}
void entry(void){S(60,run(),0,0,0,0,0);__builtin_unreachable();}
__asm__(".global _start\n_start:\nand $-16,%rsp\ncall entry\nud2\n");
