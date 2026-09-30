"""Fixed creative-mode setup for the two approved disposable staff-test players.

This is a fixture definition, not a command API. It accepts no command text,
mode, selector, new name or new UUID, performs no I/O and executes nothing.
The caller must register the result in a fresh, separately authorized session;
existing command registrations, receipts and unknown outcomes are immutable.
"""
from kneekura_tech_hub.minecraft.storage import ContractError


# Exact synthetic, offline test identities approved for this disposable scenario.
_PLAYERS = (
    ('client', 'creative_invoker', 'KneekuraTest', '57e9ec72-85ae-3dd2-8fb4-2672e58b0ffe'),
    ('control', 'creative_control', 'KneekuraControl', '59503c28-8713-3baf-bfd8-8c411b004b66'),
)
_FIELDS = {'account_sign_in', 'kind', 'name', 'uuid'}


def build_creative_commands(identities: dict) -> dict[str, str]:
    """Validate exact name/UUID role bindings, then return two inert commands.

    Minecraft 1.20.1 classifies a bare UUID as an entity selector. Passing it
    directly to gamemode's players-only argument fails at parse time. Execute
    as the exact UUID instead; its nested gamemode @s resolves that same source
    only if it is a player. An absent/non-player UUID cannot broaden the target.
    """
    if type(identities) is not dict or set(identities) != {'client', 'control'}:
        raise ContractError('Exactly the approved client/control fixture identities are required')
    for role, _, name, identifier in _PLAYERS:
        identity = identities[role]
        if (type(identity) is not dict or set(identity) != _FIELDS
                or identity['account_sign_in'] is not False
                or identity['kind'] != 'local_synthetic_offline_test_identity'
                or type(identity['name']) is not str or identity['name'] != name
                or type(identity['uuid']) is not str or identity['uuid'] != identifier):
            raise ContractError('Fixture role must keep its exact approved offline player name and UUID')
    return {key: f'execute as {identifier} run gamemode creative @s'
            for _, key, _, identifier in _PLAYERS}
