package org.kneekura.observer;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;

/** Exact Linux process-start ticks, included only in authenticated client responses. */
public final class LinuxClientIdentity {
    private LinuxClientIdentity() {}
    public static String processStart() throws IOException {
        String stat=Files.readString(Path.of("/proc/self/stat"));
        // The comm field may contain spaces and ')'; starttime is Linux field 22.
        int end=stat.lastIndexOf(')');
        if(end<0) throw new IOException("Invalid local process identity");
        String[] fields=stat.substring(end+1).trim().split("\\s+");
        if(fields.length<20 || !fields[19].matches("[0-9]+"))
            throw new IOException("Invalid local process start identity");
        return fields[19];
    }
}
