/* Assistant-authored ISA fixture only. Contains no YSM instructions or input bytes. */
#include <stdint.h>
#include <stdio.h>
int main(void) {
#if defined(__x86_64__) && defined(__GNUC__)
    const uint64_t initial[] = {0, 1, UINT64_MAX, UINT64_C(0xffffffff00000000), UINT64_C(0x1122334455667788), UINT64_C(0x8000000000000000)};
    const uint32_t memory[] = {0, 1, UINT32_MAX, UINT32_C(0x80000000), UINT32_C(0x12345678), UINT32_C(0xaaaaaaaa)};
    unsigned passed=0;
    for(unsigned i=0;i<6;i++) for(unsigned j=0;j<6;j++) {
        register uint64_t value __asm__("r9")=initial[i];
        uint32_t slot=memory[j];
        __asm__ volatile("xchgl %%r9d, %1" : "+r"(value), "+m"(slot) : : "memory");
        if(value!=(uint64_t)memory[j] || slot!=(uint32_t)initial[i]) {
            printf("FAIL %u %u register=%016llx memory=%08x\n",i,j,(unsigned long long)value,slot);return 1;
        }
        passed++;
    }
    printf("HOST_TOY_XCHG32_PASS %u ysm_target_executed=false\n",passed);return 0;
#else
    puts("SKIP requires GNU-compatible x86-64 compiler");return 77;
#endif
}
