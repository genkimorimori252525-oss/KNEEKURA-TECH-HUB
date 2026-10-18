#include <tmmintrin.h>
#include <stdio.h>
int main(void) {
 unsigned char a[16],b[16],r[16];
 while(fread(a,1,16,stdin)==16 && fread(b,1,16,stdin)==16) {
  __m128i x=_mm_loadu_si128((const __m128i *)a),y=_mm_loadu_si128((const __m128i *)b);
  _mm_storeu_si128((__m128i *)r,_mm_shuffle_epi8(x,y));
  if(fwrite(r,1,16,stdout)!=16)return 1;
 }
 return 0;
}
