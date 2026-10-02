"""Small checks shared by the bounded real-MOD verification harness."""

def require_all_class_comparisons(comparisons):
    assert comparisons and all(c.get("same_normalized_javap") is True for c in comparisons), "Empty or mismatched remapped class inventory"
    return len(comparisons)

POLICY_SMOKE_SOURCE = 'import org.kneekura.staff.StaffUsePolicy; public class SmokePolicy { public static void main(String[] args) throws Exception { if(StaffUsePolicy.class.getField("GLOW_TICKS").getInt(null) != 60 || StaffUsePolicy.class.getField("COOLDOWN_TICKS").getInt(null) != 100) throw new AssertionError(); if(StaffUsePolicy.decide(true,false) != StaffUsePolicy.Decision.CLIENT_ACK || StaffUsePolicy.decide(true,true) != StaffUsePolicy.Decision.CLIENT_ACK || StaffUsePolicy.decide(false,true) != StaffUsePolicy.Decision.COOLDOWN || StaffUsePolicy.decide(false,false) != StaffUsePolicy.Decision.APPLY) throw new AssertionError(); System.out.println("PASS: constants and all four policy branches"); }}'


def bound_mod_revision(captured_profile, source_fingerprint):
    import re
    manifest=captured_profile.get('manifest',{})
    revision=manifest.get('workspace_revision')
    assert isinstance(revision,str) and re.fullmatch(r'[0-9a-f]{40}',revision), 'Captured MOD revision required'
    assert manifest.get('dirty_hash')==source_fingerprint, 'Captured MOD source generation differs'
    return revision


def require_same_archive_inventory(original_names, transformed_names):
    assert original_names and len(original_names)==len(set(original_names)), 'Invalid original inventory'
    assert len(transformed_names)==len(set(transformed_names)), 'Duplicate transformed entries'
    assert set(original_names)==set(transformed_names), 'Transformed class/resource inventory differs from original named input'


def verification_name(value):
    import re
    if not isinstance(value,str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,79}',value):
        raise ValueError('Simple bounded output directory name required')
    return value
