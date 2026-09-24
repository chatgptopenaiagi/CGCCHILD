/* Exactly three dummy query selectors; no caller-selected destination or method. */
#include "encoder.h"
U fixed_encode(U selector,unsigned char *out,U capacity) {
 if(selector==1||selector==2)return encode(selector,out,capacity);
 if(selector!=3)return 0;
 unsigned char body[128],header[512];
 struct writer b={body,0,sizeof(body),1},h={header,0,sizeof(header),1};
 text(&b,0,"org.freedesktop.systemd1.Manager");text(&b,0,"Version");
 byte(&h,108);byte(&h,1);byte(&h,2);byte(&h,1);
 scalar(&h,4,b.n);scalar(&h,4,3);scalar(&h,4,0);
 field(&h,1,"o","/org/freedesktop/systemd1");
 field(&h,2,"s","org.freedesktop.DBus.Properties");
 field(&h,3,"s","Get");field(&h,6,"s",":1.42");field(&h,8,"g","ss");
 patch(&h,12,h.n-16);pad(&h,8);
 if(!h.ok||!b.ok||h.n>capacity||b.n>capacity-h.n)return 0;
 for(U i=0;i<h.n;i++)out[i]=header[i];
 for(U i=0;i<b.n;i++)out[h.n+i]=body[i];
 return h.n+b.n;
}
