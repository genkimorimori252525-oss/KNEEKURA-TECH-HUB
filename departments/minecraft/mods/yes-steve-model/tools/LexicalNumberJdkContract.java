/** JDK-only numeric conversion probes. Does not load or execute YSM classes. */
public class LexicalNumberJdkContract {
    public static void main(String[] args) {
        String[] values = {"0", ".", ".5", ".5.6", "\u0661", "1e3", "0x1p0", "-1"};
        boolean[] expected = {true, false, true, false, false, true, true, true};
        for (int i = 0; i < values.length; i++) {
            boolean accepted;
            try { Float.parseFloat(values[i]); accepted = true; }
            catch (NumberFormatException expectedFailure) { accepted = false; }
            if (accepted != expected[i]) throw new AssertionError("case " + i);
            System.out.println("case=" + i + " accepted=" + accepted);
        }
        if (!Character.isDigit('\u0661')) throw new AssertionError("digit classification");
        System.out.println("checks=9 status=PASS target_executed=false");
    }
}
