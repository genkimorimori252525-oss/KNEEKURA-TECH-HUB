import importlib
import pytest
from kneekura_tech_hub.minecraft.storage import ContractError


def api():
    spec = importlib.util.find_spec('kneekura_tech_hub.minecraft.mappings')
    assert spec is not None, 'mapping lookup not implemented'
    return importlib.import_module(spec.name)

TINY = 'tiny\t2\t0\tobf\tmojmap\tintermediary\n' \
       'c\ta\tgame/Mob\tnet/minecraft/class_1\n' \
       '\tm\t(La;[Lb;)La;\ta\tattack\tmethod_1\n' \
       '\tm\t(I)V\ta\tattack\tmethod_2\n' \
       '\tf\tLb;\tb\ttarget\tfield_1\n' \
       'c\tb\tgame/Target\tnet/minecraft/class_2\n'


def test_tiny_maps_owner_member_and_descriptor_types():
    m = api().MappingTable.parse(TINY, 'tiny')
    r = m.resolve('obf','mojmap','a', 'a', '(La;[Lb;)La;')
    assert r['status'] == 'OK'
    assert r['results'][0]['owner'] == 'game/Mob'
    assert r['results'][0]['name'] == 'attack'
    assert r['results'][0]['descriptor'] == '(Lgame/Mob;[Lgame/Target;)Lgame/Mob;'


def test_overloads_remain_ambiguous_without_descriptor():
    r = api().MappingTable.parse(TINY,'tiny').resolve('mojmap','intermediary','game/Mob','attack')
    assert r['status'] == 'AMBIGUOUS' and len(r['results']) == 2
    assert len({x['descriptor'] for x in r['results']}) == 2


def test_reverse_and_field_mapping():
    m = api().MappingTable.parse(TINY,'tiny')
    r = m.resolve('mojmap','obf','game/Mob','target','Lgame/Target;')
    assert r['results'][0]['descriptor'] == 'Lb;'
    assert r['results'][0]['name'] == 'b'


def test_unknown_symbol_does_not_use_identity_fallback():
    r = api().MappingTable.parse(TINY,'tiny').resolve('obf','mojmap','missing','a','()V')
    assert r['status'] == 'NOT_FOUND' and not r['results']
    assert 'mapping_domain_only' in r['coverage']


def test_explicit_alias_is_scoped_not_global():
    m = api().MappingTable.parse(TINY,'tiny')
    with pytest.raises(ContractError): m.resolve('official','srg','a')
    assert m.resolve('official','obf','game/Mob',aliases={'official':'mojmap'})['status'] == 'OK'
    with pytest.raises(ContractError): m.resolve('parchment','obf','game/Mob')


def test_proguard_mojmap_line_prefixes_and_arrays():
    text = '# mapping\ngame.Mob -> a:\n    game.Target target -> b\n    10:15:game.Mob attack(game.Mob,game.Target[]):30:35 -> a\ngame.Target -> b:\n'
    m = api().MappingTable.parse(text,'proguard',source_namespace='mojmap',target_namespace='obf')
    r = m.resolve('obf','mojmap','a','a','(La;[Lb;)La;')
    assert r['results'][0]['name'] == 'attack'
    assert r['results'][0]['descriptor'].startswith('(Lgame/Mob;')


def test_tsrg2_uses_declared_namespaces_and_skips_parameter_rows():
    text = 'tsrg2 obf srg\na game/Mob\n\ta (La;)V m_42_\n\t\t0 x p_42_\n\tb f_1_\n'
    m = api().MappingTable.parse(text,'tsrg')
    assert m.resolve('obf','srg','a','a','(La;)V')['results'][0]['descriptor'] == '(Lgame/Mob;)V'
    assert m.resolve('srg','obf','game/Mob','f_1_')['results'][0]['descriptor'] is None


def test_tsrg1_requires_explicit_namespaces():
    with pytest.raises(ContractError): api().MappingTable.parse('a game/Mob\n\ta ()V m_1_\n','tsrg')
    m = api().MappingTable.parse('a game/Mob\n\ta ()V m_1_\n','tsrg',source_namespace='obf',target_namespace='srg')
    assert m.resolve('srg','obf','game/Mob','m_1_','()V')['status'] == 'OK'


@pytest.mark.parametrize('desc', ['(Lbad)V','(V)V','Q','(I)','[V','(I)Vjunk'])
def test_reject_malformed_jvm_descriptor(desc):
    with pytest.raises(ContractError): api().remap_descriptor(desc,{})


def test_missing_target_mapping_stays_unresolved():
    m = api().MappingTable.parse('tiny\t2\t0\tobf\tmojmap\nc\ta\tgame/Mob\n\tm\t()V\ta\t\n','tiny')
    r = m.resolve('obf','mojmap','a','a','()V')
    assert r['status'] == 'PARTIAL' and r['unresolved']


def test_mapping_collision_does_not_choose_first_owner():
    m = api().MappingTable.parse('tiny\t2\t0\tobf\tmojmap\nc\ta\tgame/Mob\nc\tb\tgame/Mob\n','tiny')
    assert m.resolve('mojmap','obf','game/Mob')['status'] == 'AMBIGUOUS'

def test_unsupported_escaped_tiny_names_are_not_silently_misread():
    from kneekura_tech_hub.minecraft.mappings import MappingTable
    from kneekura_tech_hub.minecraft.storage import ContractError
    import pytest
    with pytest.raises(ContractError,match='escaped'):
        MappingTable.parse('tiny\t2\t0\tintermediary\tmojmap\n\tescaped-names\nc\ta\\tb\tx\\ty\n','tiny')
