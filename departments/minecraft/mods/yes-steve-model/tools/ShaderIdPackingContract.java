/** JDK-only arithmetic model of captured I2S/I2L/LSHL/LOR operations.
 * Does not load YSM, Minecraft, Iris or native code; not a target runtime test. */
class ShaderIdPackingContract {
    static long pack(int entity, int block, int item) {
        short a=(short)entity, b=(short)block, c=(short)item;
        return a | ((long)b << 16) | ((long)c << 32);
    }
    static void check(boolean ok) { if (!ok) throw new AssertionError(); }
    public static void main(String[] args) {
        check(pack(1,2,3)==0x000300020001L);
        check(pack(-1,2,3)==-1L);
        check(pack(-1,200,300)==pack(-1,2,3));
        check(pack(0,-1,3)==-65536L);
        check(pack(0,0,-1)==-4294967296L);
        check(pack(65536,0,0)==0L);
        check(pack(32768,2,3)==-32768L);
        System.out.println("PASS 7 JDK-only signed packing model cases; target runtime NOT_RUN");
    }
}
