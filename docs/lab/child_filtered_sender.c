/* Filtered owned sender composition. No protected UID or broker authority. */
#include "payload.h"
#include "receive.h"
struct ins {unsigned short code;unsigned char jt,jf;unsigned int k;};
struct prog {unsigned short len;struct ins *filter;};
#include "sender_filters.h"
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
 if(!install(&sender_filter)||!denials()||S(317,1,0,&sender_filter,0,0,0)!=-1||S(46,4,0,0,0,0,0)!=-1)return 34;
 struct iov iov={(void *)packet,sizeof(packet)-1};struct msg m={0,0,&iov,1,0,0,0};
 for(int i=0;i<2;i++)if(S(46,3,&m,0,0,0,0)!=(long)(sizeof(packet)-1))return 31;
 char gate=0;
 if(S(0,5,&gate,1,0,0,0)!=1||gate!='G')return 32;
 if(S(3,3,0,0,0,0,0)||S(3,5,0,0,0,0,0))return 33;
 return 0;
}
static int receive_from(U pid,int expect_alive,int *wrong_refused) {
 if(ready(4,2000)!=1)return 0;
 union control control={0};unsigned char raw[1024];U facts[7];
 struct iov iov={raw,sizeof(raw)};struct msg m={0,0,&iov,1,control.bytes,sizeof(control.bytes),0};
 long count=S(47,4,&m,0x40000040,0,0,0);
 if(count<=0||count>1024||!ancillary(&m,facts))return 0;
 received_messages++;
 int matched=facts[4]==pid&&facts[5]==me[1]&&facts[6]==me[2];
 if(expect_alive&&facts[4]!=me[0])*wrong_refused=1;
 int live=ready(3,0)==0;
 facts[4]=4242;facts[5]=62001;facts[6]=62001;
 int accepted=matched&&live&&accept(raw,(U)count,&expected,facts);
 return accepted==expect_alive;
}
static int run(void) {
 me[0]=(U)S(39,0,0,0,0,0,0);me[1]=(U)S(102,0,0,0,0,0,0);me[2]=(U)S(104,0,0,0,0,0,0);
 if(!me[1])return 1;
 if(S(436,3,0xffffffffU,0,0,0,0))return 2;
 if(S(157,38,1,0,0,0,0))return 18;
 int pair[2],gate[2],one=1;
 if(S(53,1,0x80005,0,pair,0,0)||pair[0]!=3||pair[1]!=4)return 3;
 if(S(293,gate,0x80000,0,0,0,0)||gate[0]!=5||gate[1]!=6)return 4;
 if(S(54,4,1,16,&one,4,0))return 5;
 long pid=S(57,0,0,0,0,0,0);if(pid<0)return 6;
 if(pid==0)return sender();
 if(S(3,3,0,0,0,0,0)||S(3,5,0,0,0,0,0))return 7;
 if(S(434,pid,0,0,0,0,0)!=3)return 8;
 struct cred connection={0};unsigned int length=sizeof(connection);
 if(S(55,4,1,17,&connection,&length,0)||length!=sizeof(connection))return 9;
 if((U)connection.pid!=me[0]||(U)connection.pid==(U)pid)return 10;
 for(U i=0;i<sizeof(bindings)/sizeof(bindings[0]);i++)bindings[i].code[bindings[i].index].k=(unsigned int)pid;
 if(!install(&receiver_live)||!denials()||S(61,pid+1,0,0,0,0,0)!=-1)return 19;
 int wrong_refused=0;
 if(!receive_from((U)pid,1,&wrong_refused)||!wrong_refused)return 11;
 char token='G';if(S(1,6,&token,1,0,0,0)!=1||S(3,6,0,0,0,0,0))return 12;
 int status=-1;
 if(S(61,pid,&status,0,0,0,0)!=pid||status!=0||ready(3,0)!=1)return 13;
 if(!install(&receiver_drain)||!denials()||S(317,1,0,&receiver_live,0,0,0)!=-1||S(1,6,&token,1,0,0,0)!=-1||S(61,pid,0,0,0,0,0)!=-1)return 20;
 if(!receive_from((U)pid,0,&wrong_refused)||received_messages!=2||closed_rights)return 14;
 if(S(3,3,0,0,0,0,0)||ready(3,0)!=-1||S(3,4,0,0,0,0,0))return 15;
 for(int fd=3;fd<64;fd++)if(S(72,fd,1,0,0,0,0)!=-9)return 16;
 U report[4]={2,1,1,1};
 if(S(1,1,report,sizeof(report),0,0,0)!=(long)sizeof(report))return 17;
 return 0;
}
void entry(void){S(60,run(),0,0,0,0,0);__builtin_unreachable();}
__asm__(".global _start\n_start:\nand $-16,%rsp\ncall entry\nud2\n");
