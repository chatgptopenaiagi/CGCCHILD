/* Owned nonroot socketpair mechanics; no broker, peer target or privileged operation. */
#include "payload.h"
struct iov {void *base;U len;};
struct msg {void *name;unsigned int namelen;struct iov *iov;U iovlen;void *control;U controllen;int flags;};
struct cm {U len;int level,type;};
struct cred {int pid;unsigned int uid,gid;};
_Static_assert(sizeof(struct msg)==56,"x86-64 msghdr");
_Static_assert(sizeof(struct cm)==16,"x86-64 cmsghdr");
_Static_assert(sizeof(struct cred)==12,"Linux ucred");
union control {U aligned;unsigned char bytes[112];};
__attribute__((noinline,noclone)) static long call(U n,U a,U b,U c,U d,U e,U f) {
 register U r10 __asm__("r10")=d,r8 __asm__("r8")=e,r9 __asm__("r9")=f;long out;
 __asm__ volatile("syscall":"=a"(out):"a"(n),"D"(a),"S"(b),"d"(c),"r"(r10),"r"(r8),"r"(r9):"rcx","r11","memory");return out;
}
#define S(n,a,b,c,d,e,f) call(n,(U)(a),(U)(b),(U)(c),(U)(d),(U)(e),(U)(f))
static const char packet[]="{\"NONCE\":\"11111111111111111111111111111111\",\"TYPE\":\"READY\",\"VERSION\":1}";
static const struct message expected={.kind=1,.nonce="11111111111111111111111111111111"};
static U me[3],closed_rights,received_messages,maximum_fd;
static int inventory(void) {
 for(int fd=0;fd<64;fd++){long r=S(72,fd,1,0,0,0,0);if(fd<7?r<0:r!=-9)return 0;}
 return 1;
}
/* Only kernel-produced ancillary buffers reach this function in receive tests. */
static int ancillary(struct msg *msg,U *facts) {
 facts[0]=facts[1]=facts[2]=0;facts[3]=(U)(msg->flags & ~0x40000000);
 facts[4]=facts[5]=facts[6]=0;
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
   facts[1]++;
   if(size%4)okay=0;
   for(U i=0;i<size/4;i++) {
    int fd=((int *)data)[i];
    if(fd<7||fd>=64){okay=0;continue;}
    if((S(72,fd,1,0,0,0,0)&1)!=1)okay=0;
    if((U)fd>maximum_fd)maximum_fd=(U)fd;
    if(S(3,fd,0,0,0,0,0)!=0)okay=0;
    else closed_rights++;
   }
  } else facts[2]++;
  U step=(h->len+7)&~(U)7;
  if(step>msg->controllen-offset){offset=msg->controllen;break;}
  offset+=step;
 }
 for(;offset<msg->controllen;offset++)if(((unsigned char *)msg->control)[offset])okay=0;
 return okay;
}
static int exchange(int rights,U payload_capacity,U control_capacity,int expected_ok,int wrong_pid) {
 union control send_control={0},receive_control={0};unsigned char raw[1024];
 struct iov send_iov={(void *)packet,sizeof(packet)-1},receive_iov={raw,payload_capacity};
 struct msg send={0,0,&send_iov,1,0,0,0},receive={0,0,&receive_iov,1,receive_control.bytes,control_capacity,0};
 if(rights) {
  struct cm *h=(struct cm *)send_control.bytes;h->len=16+(U)rights*4;h->level=1;h->type=1;
  for(int i=0;i<rights;i++)((int *)(send_control.bytes+16))[i]=5;
  send.control=send_control.bytes;send.controllen=(h->len+7)&~(U)7;
 }
 if(S(46,3,&send,0,0,0,0)!=(long)(sizeof(packet)-1))return 0;
 long count=S(47,4,&receive,0x40000000,0,0,0);
 if(count<0||count>1024)return 0;
 received_messages++;
 U facts[7];int valid=ancillary(&receive,facts);
 if(facts[4]!=(me[0]+(U)wrong_pid)||facts[5]!=me[1]||facts[6]!=me[2])valid=0;
 /* The M17 payload model uses dummy tuple constants after this real tuple comparison. */
 facts[4]=4242;facts[5]=62001;facts[6]=62001;
 int accepted=valid&&accept(raw,(U)count,&expected,facts);
 return accepted==expected_ok&&inventory();
}
static int run(void) {
 me[0]=(U)S(39,0,0,0,0,0,0);me[1]=(U)S(102,0,0,0,0,0,0);me[2]=(U)S(104,0,0,0,0,0,0);
 if(!me[1])return 1;
 if(S(436,3,0xffffffffU,0,0,0,0))return 2;
 int pair[2],pipe[2],one=1,zero=0;
 if(S(53,1,0x80005,0,pair,0,0)||pair[0]!=3||pair[1]!=4)return 3;
 if(S(293,pipe,0x80000,0,0,0,0)||pipe[0]!=5||pipe[1]!=6)return 4;
 if(S(54,4,1,16,&one,4,0))return 5;
 if(!exchange(0,1024,112,1,0))return 10;
 if(!exchange(0,1024,112,0,1))return 11;
 if(!exchange(1,1024,112,0,0)||closed_rights!=1)return 12;
 if(!exchange(0,8,112,0,0))return 13;
 if(!exchange(16,1024,32,0,0))return 14;
 if(S(54,4,1,16,&zero,4,0)||!exchange(0,1024,112,0,0)||S(54,4,1,16,&one,4,0))return 15;
 for(int i=0;i<32;i++)if(!exchange(16,1024,112,0,0))return 16;
 if(closed_rights!=513||received_messages!=38||maximum_fd!=22)return 17;
 for(int fd=3;fd<=6;fd++)if(S(3,fd,0,0,0,0,0))return 18;
 U report[3]={received_messages,closed_rights,maximum_fd};
 if(S(1,1,report,sizeof(report),0,0,0)!=(long)sizeof(report))return 19;
 return 0;
}
void entry(void){S(60,run(),0,0,0,0,0);__builtin_unreachable();}
__asm__(".global _start\n_start:\nand $-16,%rsp\ncall entry\nud2\n");
