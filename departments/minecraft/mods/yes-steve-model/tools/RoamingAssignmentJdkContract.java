import java.util.regex.Pattern;
/** JDK lexical-predicate examples only. No YSM class or expression is executed. */
public class RoamingAssignmentJdkContract {
    public static void main(String[] args) {
        Pattern p = Pattern.compile("^([;\\s]*(v|variable)\\.roaming\\.[A-Za-z0-9_]+\\s*=[^;]+[;\\s]*)+$", Pattern.CASE_INSENSITIVE);
        String[] values = {"v.roaming.color=1", "VARIABLE.ROAMING.color = 2;", "v.roaming.a=1;v.roaming.b=2", "v.local.a=1", "v.roaming.a=", "v.roaming.a= ", "v.roaming.a='red;blue'", "v.roaming.a=math.sin(1)"};
        boolean[] expected = {true,true,true,false,false,true,false,true};
        for (int i=0;i<values.length;i++) {
            boolean actual=p.matcher(values[i]).find();
            if(actual!=expected[i]) throw new AssertionError("case="+i);
            System.out.println("case="+i+" matches="+actual);
        }
        System.out.println("checks=8 status=PASS target_executed=false");
    }
}
