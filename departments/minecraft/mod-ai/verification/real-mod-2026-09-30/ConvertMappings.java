import java.nio.file.Path;
import java.util.Map;
import java.util.List;
import net.fabricmc.mappingio.MappingReader;
import net.fabricmc.mappingio.MappingWriter;
import net.fabricmc.mappingio.adapter.MappingNsRenamer;
import net.fabricmc.mappingio.adapter.MappingDstNsReorder;
import net.fabricmc.mappingio.tree.MemoryMappingTree;
import net.fabricmc.mappingio.format.MappingFormat;
public class ConvertMappings {
 public static void main(String[] args) throws Exception {
  MemoryMappingTree tree = new MemoryMappingTree();
  for (int i=0;i<2;i++) MappingReader.read(Path.of(args[i]), MappingFormat.PROGUARD_FILE, new MappingNsRenamer(tree,Map.of("source","mojmap","target","obf")));
  MappingReader.read(Path.of(args[2]), MappingFormat.TSRG_2_FILE, new MappingNsRenamer(tree,Map.of("left","mojmap","right","srg")));
  int fields=0,missing=0,methods=0,unmapped=0;
  int srg=tree.getNamespaceId("srg");
  for (var c:tree.getClasses()) {
   for(var f:c.getFields()){ fields++; if(f.getSrcDesc()==null) missing++; if(f.getDstName(srg)==null) unmapped++; }
   methods+=c.getMethods().size();
  }
  System.out.printf("classes=%d fields=%d methods=%d missing_field_descriptors=%d fields_without_srg=%d namespaces=%s -> %s%n",tree.getClasses().size(),fields,methods,missing,unmapped,tree.getSrcNamespace(),tree.getDstNamespaces());
  if(missing!=0) throw new IllegalStateException("Incomplete official descriptor merge");
  try(MappingWriter writer=MappingWriter.create(Path.of(args[3]),MappingFormat.TINY_2_FILE)){tree.accept(new MappingDstNsReorder(writer,List.of("srg")));}
 }
}
