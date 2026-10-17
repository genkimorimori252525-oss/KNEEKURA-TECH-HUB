import java.nio.ByteBuffer;
import java.util.concurrent.ConcurrentHashMap;
/** JDK-only API/arithmetic checks. No YSM, Netty, decoder or audio execution. */
class PcmCacheJdkContract {
 static void check(boolean x) { if (!x) throw new AssertionError(); }
 public static void main(String[] args) {
  Object key=new Object(), placeholder=new Object();
  var m=new ConcurrentHashMap<Object,Object>();m.put(key,placeholder);
  check(m.containsKey(key));check(!m.contains(key));check(m.contains(placeholder));
  ByteBuffer b=ByteBuffer.allocate(10);b.position(4);
  int len=Math.min(10,b.remaining());check(len==6);b.limit(len);check(b.remaining()==2);
  check(49L/10==4L);check(50L/10==5L);
  ByteBuffer source=ByteBuffer.allocate(8);source.position(2);source.limit(6);
  ByteBuffer copy=ByteBuffer.allocate(source.remaining());copy.duplicate().put(source.duplicate());
  check(source.position()==2 && source.limit()==6);check(copy.position()==0 && copy.remaining()==4);
  System.out.println("PASS 9 JDK-only cache/buffer contract checks; target and decoder NOT_RUN");
 }
}
