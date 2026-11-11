/* Research-only decoder throughput probe: deterministic UNTRAINED weights.
 * It measures the proposed coordinate MLP, not image quality or a codec.
 * cc -O3 -std=c11 tools/neuronte-video-decoder-bench.c -lm -o build/video-decoder-bench
 * Usage: WIDTH HEIGHT HIDDEN CODE_BYTES [RGB_FLOAT32_OUTPUT]
 */
#define _POSIX_C_SOURCE 200809L
#include <math.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <time.h>

static uint32_t state=19;
static float random_weight(void) { state=state*1664525u+1013904223u;return ((float)(state>>8)/16777216.f-.5f)*.2f; }
static double now(void) { struct timespec t;clock_gettime(CLOCK_MONOTONIC,&t);return t.tv_sec+t.tv_nsec*1e-9; }
static int clampi(int x,int hi) { return x<0?0:x>=hi?hi-1:x; }
int main(int argc,char **argv) {
    if(argc<5 || argc>6) return 2;
    int width=atoi(argv[1]),height=atoi(argv[2]),hidden=atoi(argv[3]),codes=atoi(argv[4]);
    if(width<1||height<1||width>4096||height>4096||(hidden!=32&&hidden!=48)||(codes!=16&&codes!=32)) return 2;
    int cols=(width+7)/8,rows=(height+15)/16;
    size_t cells=(size_t)cols*rows;
    float *latents=malloc(cells*codes*sizeof(float)), *projected=calloc(cells*hidden,sizeof(float));
    float *image=malloc((size_t)width*height*3*sizeof(float));
    float wp[48][26],wc[48][32],w2[48][48],w3[48][48],wo[3][48],pos[128][26],cached[128][48];
    if(!latents||!projected||!image) return 3;
    for(size_t i=0;i<cells*(size_t)codes;i++) latents[i]=random_weight()*5;
    for(int i=0;i<hidden;i++) {
        for(int j=0;j<26;j++)wp[i][j]=random_weight();
        for(int j=0;j<codes;j++)wc[i][j]=random_weight();
        for(int j=0;j<hidden;j++){w2[i][j]=random_weight();w3[i][j]=random_weight();}
    }
    for(int i=0;i<3;i++)for(int j=0;j<hidden;j++)wo[i][j]=random_weight();
    double begin=now();
    for(int y=0;y<16;y++)for(int x=0;x<8;x++) {
        int p=y*8+x;float xx=(x+.5f)/8,yy=(y+.5f)/8;
        pos[p][0]=2*xx-1;pos[p][1]=yy-1;
        for(int k=0;k<6;k++) {float f=6.28318530718f*(1<<k);pos[p][2+4*k]=sinf(f*xx);pos[p][3+4*k]=sinf(f*yy);pos[p][4+4*k]=cosf(f*xx);pos[p][5+4*k]=cosf(f*yy);}
        for(int i=0;i<hidden;i++){float v=0;for(int j=0;j<26;j++)v+=pos[p][j]*wp[i][j];cached[p][i]=v;}
    }
    for(size_t c=0;c<cells;c++)for(int i=0;i<hidden;i++)for(int j=0;j<codes;j++)projected[c*hidden+i]+=latents[c*codes+j]*wc[i][j];
    double preparation=now()-begin;begin=now();
    double sum=0;
    for(int y=0;y<height;y++)for(int x=0;x<width;x++) {
        float gx=(x+.5f)/8-.5f,gy=(y+.5f)/16-.5f;int ix=(int)floorf(gx),iy=(int)floorf(gy);float fx=gx-ix,fy=gy-iy;
        int x0=clampi(ix,cols),x1=clampi(ix+1,cols),y0=clampi(iy,rows),y1=clampi(iy+1,rows);
        size_t id[4]={(size_t)y0*cols+x0,(size_t)y0*cols+x1,(size_t)y1*cols+x0,(size_t)y1*cols+x1};
        float blend[4]={(1-fx)*(1-fy),fx*(1-fy),(1-fx)*fy,fx*fy},a[48],b[48],c[48];
        int p=(y%16)*8+x%8;
        for(int i=0;i<hidden;i++){float v=cached[p][i];for(int k=0;k<4;k++)v+=blend[k]*projected[id[k]*hidden+i];a[i]=fmaxf(0,v);}
        for(int i=0;i<hidden;i++){float v=0;for(int j=0;j<hidden;j++)v+=w2[i][j]*a[j];b[i]=fmaxf(0,v);}
        for(int i=0;i<hidden;i++){float v=0;for(int j=0;j<hidden;j++)v+=w3[i][j]*b[j];c[i]=fmaxf(0,v);}
        for(int i=0;i<3;i++){float v=0;for(int j=0;j<hidden;j++)v+=wo[i][j]*c[j];image[((size_t)y*width+x)*3+i]=v;sum+=v;}
    }
    double elapsed=now()-begin;
    printf("{\"width\":%d,\"height\":%d,\"hidden\":%d,\"code_bytes\":%d,\"projection_seconds\":%.9f,\"decode_seconds\":%.9f,\"fps\":%.6f,\"checksum\":%.9f,\"untrained\":true}\n",width,height,hidden,codes,preparation,elapsed,1/(preparation+elapsed),sum);
    if(argc==6){FILE *f=fopen(argv[5],"wb");if(!f)return 4;size_t n=(size_t)width*height*3;if(fwrite(image,sizeof(float),n,f)!=n)return 4;if(fclose(f))return 4;}
    free(image);free(projected);free(latents);return 0;
}
