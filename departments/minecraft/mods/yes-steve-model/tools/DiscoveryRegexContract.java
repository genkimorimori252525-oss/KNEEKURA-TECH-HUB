import java.util.function.Predicate;
import java.util.regex.Pattern;

/** Exercises only JDK Pattern on captured format strings; never loads YSM or Minecraft. */
class DiscoveryRegexContract {
    public static void main(String[] args) {
        String[] formats = {"^%s\\.%s_.+", "^%s_ctrl_%s_.+"};
        String[] separators = {".", "_ctrl_"};
        String[] categories = {"fp.arm", "fpXarm", "fp/arm", "fpXYarm"};
        boolean[] expected = {true, true, true, false};
        int count = 0;
        for (int kind = 0; kind < formats.length; kind++) {
            Predicate<String> matches = Pattern.compile(String.format(formats[kind], "fp.arm", "parallel")).asMatchPredicate();
            for (int i = 0; i < categories.length; i++) {
                String input = categories[i] + separators[kind] + "parallel_0";
                boolean actual = matches.test(input);
                if (actual != expected[i]) throw new AssertionError(input);
                System.out.println("{\"input\":\"" + input + "\",\"matches\":" + actual + "}");
                count++;
            }
        }
        if (count != 8) throw new AssertionError(count);
    }
}
