/** JDK-only arithmetic model of a channel conversion. Never loads YSM. */
public class ColorChannelJdkContract {
    private static int channel(float x) { return ((int)((double)(x * 255.0f) + 0.5d)) & 255; }
    public static void main(String[] args) {
        float[] inputs={0f,.5f,1f,2f,Float.NaN,Float.POSITIVE_INFINITY,Float.NEGATIVE_INFINITY};
        int[] expected={0,128,255,254,0,255,0};
        for(int i=0;i<inputs.length;i++) {
            int actual=channel(inputs[i]);
            if(actual!=expected[i]) throw new AssertionError("channel "+i);
            System.out.println("case="+i+" channel="+actual);
        }
        int packed=((128&255)<<24)|((257&255)<<16)|((-1&255)<<8)|(256&255);
        if(packed!=0x8001ff00) throw new AssertionError("integer mask/ARGB");
        if((0xff000000|0x12345678)!=0xff345678) throw new AssertionError("opaque");
        System.out.println("checks=9 status=PASS target_executed=false");
    }
}
