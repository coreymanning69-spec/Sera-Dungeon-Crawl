"""Save/load framework for serializing run state. Revision 1.20a."""

from __future__ import annotations
import json
from pathlib import Path

from sera import REVISION
from sera.weapon import Weapon
from sera.crafting import CraftingMaterial, CRAFTING_MATERIALS
from sera.equipment import EquipmentItem
from sera.consumables import CONSUMABLE_REGISTRY
from sera.randomization import RunRNG
from sera.modes.endless import EndlessProgress
from sera.npc import NPC_POOL

SAVE_VERSION = REVISION
DEFAULT_SAVE_PATH = Path("savegame.json")


def serialize_state(state) -> dict:
    return {
        "saveVersion": SAVE_VERSION,
        "floor": state.floor,
        "max_floors": state.max_floors,
        "mode": state.mode,
        "rng_seed": state.rng_seed,
        "endless": {
            "wave": state.endless.wave,
            "total_waves_cleared": state.endless.total_waves_cleared,
            "cumulative_kills": state.endless.cumulative_kills,
        },
        "interest": {
            "current_patience": state.interest.current_patience,
            "max_patience": state.interest.max_patience,
            "turn_number": state.interest.turn_number,
            "total_kills": state.interest.total_kills,
        },
        "weapons": [w.display_name for w in state.weapons],
        "equipped_idx": state.equipped_idx,
        "materials": [m.name for m in state.materials],
        "upgrade_shards": state.upgrade_shards,
        "gold": state.gold,
        "consumables": [c.key for c in state.consumables],
        "floors_cleared": state.floors_cleared,
        "auto_battle_enabled": state.auto_battle_enabled,
        "auto_battle_turns": state.auto_battle_turns,
        "run_stats": {
            "total_damage": state.run_stats.total_damage,
            "best_overkill": state.run_stats.best_overkill,
            "weapons_found": state.run_stats.weapons_found,
            "materials_used": state.run_stats.materials_used,
            "gold_collected": state.run_stats.gold_collected,
            "gold_spent": state.run_stats.gold_spent,
        },
        "current_npc": state.current_npc.name if state.current_npc else None,
        "equipment_stash": [item.name for item in state.equipment_stash],
        "equipped_slots": {
            slot: item.name if item else None
            for slot, item in state.equipment_loadout.equipped.items()
        },
        "balance": {
            "endless_enemy_hp_bonus_per_wave": state.balance.endless_enemy_hp_bonus_per_wave,
            "endless_player_damage_bonus_per_wave": state.balance.endless_player_damage_bonus_per_wave,
        },
    }


def deserialize_state(data: dict, state) -> None:
    weapon_map: dict[str, Weapon] = {w.display_name: w for w in state.all_weapons}
    material_map: dict[str, CraftingMaterial] = {m.name: m for m in CRAFTING_MATERIALS.values()}

    state.floor = data.get("floor", 0)
    state.max_floors = data.get("max_floors", 5)
    state.mode = data.get("mode", "campaign")
    state.rng_seed = data.get("rng_seed", state.rng_seed)

    state.rng = RunRNG(state.rng_seed)
    state.endless = EndlessProgress(seed=state.rng_seed)
    endless = data.get("endless", {})
    state.endless.wave = endless.get("wave", state.endless.wave)
    state.endless.total_waves_cleared = endless.get("total_waves_cleared", 0)
    state.endless.cumulative_kills = endless.get("cumulative_kills", 0)
    interest = data.get("interest", {})
    state.interest.current_patience = interest.get("current_patience", state.interest.current_patience)
    state.interest.max_patience = interest.get("max_patience", state.interest.max_patience)
    state.interest.turn_number = interest.get("turn_number", 0)
    state.interest.total_kills = interest.get("total_kills", 0)

    names = data.get("weapons", [])
    state.weapons = [weapon_map[name] for name in names if name in weapon_map]
    if not state.weapons:
        state.weapons = [state.all_weapons[0]]
    state.equipped_idx = min(data.get("equipped_idx", 0), len(state.weapons) - 1)

    mat_names = data.get("materials", [])
    state.materials = [material_map[name] for name in mat_names if name in material_map]
    state.upgrade_shards = data.get("upgrade_shards", 0)
    state.gold = data.get("gold", 0)
    keys = data.get("consumables", [])
    state.consumables = [CONSUMABLE_REGISTRY[key] for key in keys if key in CONSUMABLE_REGISTRY]
    if not state.consumables:
        legacy_flasks = data.get("healing_flasks", 2)
        state.add_consumable("healing_flask", legacy_flasks)
    state.floors_cleared = data.get("floors_cleared", 0)
    state.auto_battle_enabled = data.get("auto_battle_enabled", state.auto_battle_enabled)
    state.auto_battle_turns = max(1, min(30, data.get("auto_battle_turns", state.auto_battle_turns)))

    run_stats = data.get("run_stats", {})
    state.run_stats.total_damage = run_stats.get("total_damage", 0)
    state.run_stats.best_overkill = run_stats.get("best_overkill", 0)
    state.run_stats.weapons_found = run_stats.get("weapons_found", 0)
    state.run_stats.materials_used = run_stats.get("materials_used", 0)
    state.run_stats.gold_collected = run_stats.get("gold_collected", 0)
    state.run_stats.gold_spent = run_stats.get("gold_spent", 0)

    npc_name = data.get("current_npc")
    state.current_npc = next((npc for npc in NPC_POOL if npc.name == npc_name), None)

    equipment_map: dict[str, EquipmentItem] = {item.name: item for item in state.all_equipment}
    stash_names = data.get("equipment_stash", [])
    state.equipment_stash = [equipment_map[name] for name in stash_names if name in equipment_map]

    equipped_slots = data.get("equipped_slots", {})
    if isinstance(equipped_slots, dict):
        for slot in state.equipment_loadout.equipped.keys():
            item_name = equipped_slots.get(slot)
            state.equipment_loadout.equipped[slot] = equipment_map.get(item_name) if item_name else None

    balance = data.get("balance", {})
    state.balance.endless_enemy_hp_bonus_per_wave = balance.get("endless_enemy_hp_bonus_per_wave", 0.0)
    state.balance.endless_player_damage_bonus_per_wave = balance.get("endless_player_damage_bonus_per_wave", 0)


def save_to_file(path: Path | str, state) -> Path:
    target = Path(path)
    target.write_text(json.dumps(serialize_state(state), indent=2) + "\n")
    return target


def load_from_file(path: Path | str, state) -> bool:
    target = Path(path)
    if not target.exists():
        return False
    try:
        data = json.loads(target.read_text())
    except json.JSONDecodeError:
        return False
    if not isinstance(data, dict):
        return False
    save_version = data.get("saveVersion", data.get("version"))
    if save_version is None:
        return False
    try:
        deserialize_state(data, state)
    except Exception:
        return False
    return True
