# Animation/controller data construction and container ownership

PRIMARY_STATIC_REVIEW_ONLY. Exact SHA-256 `25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f`; source revision `f184edabd1b5115ce5a24cb6d155ba5a669f5ba6`.25 declarations across animation, controller data/state and two file wrappers;152 integrity checks/10 negative controls. Native input creation/validation is not established, no target execution, independent semantic review or central promotion.

## Animation is not deeply immutable

Animation counterpart `Oo0OOo00Oo00oO00Ooo0O00O` stores name/loop/delay/weight/override references and narrows the supplied double length to float without local clamp/finite validation or a time conversion. Four supplied arrays become ReferenceArrayList.wrap views: bone animations, sound events, particle events and instruction events. These public final List references are not wrapped unmodifiable and do not clone element objects. The separate copied-from-default boolean starts false and remains mutable, as used by earlier hand compatibility logic.

isEmpty tests all four lists, not just whether any bone can animate. An animation with only events can be nonempty; that does not prove every event-list category has an executed consumer.

## Controller state uses mixed copy/view policies

State counterpart `O00ooo0OooOo00o0o0Oo00oO` pools its name, compares the pooled ID with the pooled"ysm-builtin" name, and recognizes a sub-entry by startsWith("ysm-entry-"). It stores the remaining suffix directly, including an empty suffix if supplied; no target existence validation occurs here.

Animation pairs, sounds, onEntry and onExit arrays are wrapped then exposed through unmodifiable ReferenceLists. Their backing arrays/contained objects are not deep-copied by those calls. Transition pairs follow a different path: each destination name is pooled into a new IntReferenceImmutablePair with the existing IValue reference, collected into a new array and unmodifiable list. This isolates the transition pair container from the input pair array, while retaining expression references. Blend-transition object and shortest-path boolean are retained directly; startNew/cursor semantics belong to the actual transition implementation.

## Initial-state existence and duplicate state IDs

Controller-data counterpart `ooOo0OoOoo0ooOOoOO0o000O` pools initialState and builds its state map by Arrays.stream→Collectors.toMap(pooledName,identity)→new Int2ReferenceOpenHashMap→unmodifiable wrapper. It does not check that the pooled initialState occurs in that map. The two-argument Collectors.toMap call supplies no merge function; duplicate pooled keys follow the JDK duplicate-key rejection rather than a locally defined first/last-wins rule. State objects themselves are not cloned. The constructor does not globally establish nonnull, acyclic or reachable transition targets.

The two file wrappers `OOo00OOOOO0OOOooOo0OOoOO` and `oo0o0o0o00000ooOoooo00o0` shallow-copy their supplied maps then expose unmodifiable maps. This is stronger container isolation than Animation's direct array wraps, but still not deep immutability of animations/states/expressions. Preserve the distinction when caching or sharing model assets across entities.

## Particle event field is not proof of an emitter path

The fixed955-class [field-read inventory](PARTICLE-KEYFRAME-READERS-EVIDENCE-2026-10-17.json) targets the exact particle-keyframe List field on the Animation counterpart. It finds one GETFIELD reader: isEmpty, and no bootstrap reference to that field. It does not find a direct Java emitter reading that exact field symbol. This scan is explicitly field reads, despite retaining the common inventory's calls/caller_methods container names.

This is narrower than asserting particle effects unsupported or globally unused. Molang ParticleFunction has its own [dispatch path](PARTICLE-SOUND-DISPATCH-RECOVERY-2026-10-17.md), and native/reflection/external or inherited-owner access is not closed by the exact-symbol scan. A data field's presence and participation in emptiness checks are not runtime event-delivery evidence.

## Reuse

Track which arrays/maps are copied, which are read-only views, which elements remain mutable, and which validation is left to producers/consumers. Do not assume a Java constructor labeled Native Access proves safe or normalized native inputs. This extends the [ordered-segment](ORDERED-SEGMENT-TRANSITION-RECOVERY-2026-10-17.md) and controller dossiers without changing their frozen receipts or historical correspondence confidence.
