# Pooled names and roaming change representations

Primary static review; independent review NOT_RUN. Fixed artifact SHA-256
`25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f`, source
candidate `f184edabd1b5115ce5a24cb6d155ba5a669f5ba6`. Twenty-four selected
methods across six owners: StringPool, pooled map/set, VariableChanges, roaming
data codec and one outgoing player-change method. No packet was sent, crafted
for testing, or received. This is representation analysis, not a security audit,
authorization proof or target runtime test. Mapping669 is unchanged.

## Names are process-local interned IDs, not stable hashes

StringPool assigns IDs by AtomicInteger.incrementAndGet inside forward-map
computeIfAbsent and stores the reverse mapping. Static initialization interns the
empty string. getName does not insert; it returns Integer.MIN_VALUE when absent.
getString returns empty string when a reverse lookup is absent. The methods do not
perform lowercase normalization. getAllName returns the forward map's keySet view.

These IDs depend on interning order and must not be treated as stable identifiers
across processes or persisted as a portable name encoding. The concurrent maps
and atomic counter are captured but do not establish every possible multi-map
observation invariant or behavior under external mutation of the exposed view.

PooledStringHashMap.get(String) resolves without interning and returns null for
NONE; put interns. The map-copy constructor delegates to the superclass constructor
with the existing map; it has no recursive Struct/value cloning code. The pooled
set likewise avoids insertion for contains and interns for add; collection
construction maps names to pooled IDs before collecting into a set.

## Outgoing changes convert IDs back to names

The inspected PlayerAnimatableCapability method requires local-player state,
nonzero current model hash, LocalRoamingStruct and dirty=true. It pops changes,
updates associated vehicle state, allocates name/value arrays sized to the change
map, and converts each pooled key through getString. Names with length<=32 retain
name/value; longer names produce an empty-string/0 slot rather than removing that
array position. It builds the named-map representation and invokes sendToServer.
This is a static call path, not evidence of actual delivery, receiver acceptance,
server authorization or model synchronization. Failure after pop is not covered
by a local rollback/finally in this method.

## Codec preserves text names across the process boundary

The data encoder writes modelHashShort as an int, entityId using the VarInt helper,
then one-byte count and each text name/float from variablesServerBound. The field
name modelHashShort is not a two-byte wire type in this method. Decoding reads the
corresponding values. With clientBound=true it interns each received name and
constructs an integer-key map; with false it retains the string-key map. The other
map field is null in each branch.

Thus client pooled IDs are reconstructed locally from text, not transmitted as
shared process IDs. The encoder expects the named representation; a decoded
client-bound object is not automatically a symmetric encoder input, because its
named map is null. Counts/field operations are recorded as declared; validation
or limits in other producers/receivers are not inferred from this codec alone.
No malformed-input behavior or exploit was executed.

## Checks and continuation

151 static checks pass;11 malformed-evidence controls reject changed count/name/
value operations, name-length rule and missing outgoing tail. A development-time
negative-control lookup was corrected to the artifact's remapped UTF-read name
before this passing receipt. This remains outside the fixed17-cohort checkpoint.
Whole source equivalence and independent semantic review remain unproven. Next
follow ordinary remote-state application/model-hash selection and storage merge
ordering, without treating codec success as authorization or successful delivery.
