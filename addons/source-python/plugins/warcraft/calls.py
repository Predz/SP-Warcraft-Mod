## IMPORTS

from commands.client import ClientCommandFilter
from entities import TakeDamageInfo
from entities.entity import Entity
from entities.helpers import index_from_pointer
from entities.hooks import EntityCondition
from entities.hooks import EntityPreHook
from events import Event
from memory import make_object
from players import UserCmd
from players.helpers import userid_from_pointer

from .players import players

## ALL DECLARATION

__all__ = (
    '_pre_damage_call_events',
    )

## CALL EVENTS

@Event('round_end', 'round_start')
def _on_round_call_events(event_data):
    kwargs = event_data.variables.as_dict()

    for player in players.values():
        player.hero.call_events(event_data.name, player=player, **kwargs)

@Event('player_death')
def _on_kill_assist_call_events(event_data):
    if event_data['userid'] == event_data['attacker'] or event_data['attacker'] == 0:
        player = players.from_userid(event_data['userid'])
        player.hero.call_events('player_suicide', player=player)
        return

    attacker = players.from_userid(event_data['attacker'])
    victim = players.from_userid(event_data['userid'])
    assister = None
    if 'assister' in event_data.variables and event_data['assister']:
        assister = players.from_userid(event_data['assister'])

    attacker.hero.call_events('player_kill', player=attacker, victim=victim,
        assister=assister)
    victim.hero.call_events('player_death', player=victim, attacker=attacker,
        assister=assister)
    if assister:
        assister.hero.call_events('player_assist', player=assister, attacker=attacker,
            victim=victim)

@Event('bomb_dropped', 'bomb_exploded', 'bomb_pickup',
    'bomb_planted', 'bomb_defused', 'bomb_beginplant', 'bomb_begindefuse',
    'bomb_abortplant', 'bomb_abortdefuse', 'bot_takeover', 'break_breakable',
    'break_prop', 'bullet_impact', 'buymenu_close', 'buymenu_open', 'decoy_detonate',
    'decoy_started', 'decoy_firing', 'defuser_pickup', 'door_moving', 'enter_bombzone',
    'enter_buyzone', 'enter_rescue_zone', 'exit_bombzone', 'exit_buyzone',
    'exit_rescue_zone', 'flashbang_detonate', 'grenade_bounce', 'hegrenade_detonate',
    'hostage_follows', 'hostage_hurt', 'hostage_killed', 'hostage_rescued',
    'hostage_stops_following', 'item_purchase', 'player_blind', 'player_spawn',
    'player_jump', 'player_changename', 'player_footstep', 'player_shoot', 'player_use',
    'round_mvp', 'silencer_on', 'silencer_off', 'weapon_fire', 'weapon_fire_on_empty',
    'weapon_reload', 'weapon_zoom')
def _on_personal_call_events(event_data):
    player = players.from_userid(event_data['userid'])
    if player.index == 0 or player.userid == 0:
        return
    kwargs = event_data.variables.as_dict()

    player.hero.call_events(event_data.name, player=player, **kwargs)

@Event('player_hurt')
def _on_hurt_call_events(event_data):
    if event_data['userid'] == event_data['attacker'] or event_data['attacker'] == 0:
        return

    attacker = players.from_userid(event_data['attacker'])
    victim = players.from_userid(event_data['userid'])

    if victim.team == attacker.team:
        attacker.hero.call_events('player_teammate_attack', player=attacker,
            victim=victim, attacker=attacker)
        victim.hero.call_events('player_teammate_victim', player=victim,
            attacker=attacker, victim=victim)
        return

    attacker.hero.call_events('player_attack', player=attacker, victim=victim,
        attacker=attacker)
    victim.hero.call_events('player_victim', player=victim, attacker=attacker,
        victim=victim)

@EntityPreHook(EntityCondition.is_player, 'on_take_damage')
def _pre_damage_call_events(stack_data):
    take_damage_info = make_object(TakeDamageInfo, stack_data[1])
    if not take_damage_info.attacker:
        return
    entity = Entity(take_damage_info.attacker)
    attacker = players[entity.index] if entity.is_player() else None
    victim = players[index_from_pointer(stack_data[0])]

    event_args = {
        'attacker': attacker,
        'victim': victim,
        'take_damage_info': take_damage_info,
    }

    if attacker:
        if victim.team == attacker.team:
            attacker.hero.call_events('player_pre_teammate_attack', player=attacker,
                **event_args)
            victim.hero.call_events('player_pre_teammate_victim', player=victim, **event_args)
            return

        attacker.hero.call_events('player_pre_attack', player=attacker, **event_args)
        victim.hero.call_events('player_pre_victim', player=victim, **event_args)

        if victim.health <= take_damage_info.damage:
            attacker.hero.call_events('player_pre_death', player=victim, **event_args)

@EntityPreHook(EntityCondition.is_human_player, 'run_command')
def _pre_run_command_call_events(stack_data):
    player = players[index_from_pointer(stack_data[0])]
    usercmd = make_object(UserCmd, stack_data[1])

    player.hero.call_events('player_pre_run_command', player=player, usercmd=usercmd)

@ClientCommandFilter
def _filter_commands_call_events(command, index):
    player = players[index]
    command_name = command[0]

    player.hero.call_clientcommands(command_name, player=player, command=command)
