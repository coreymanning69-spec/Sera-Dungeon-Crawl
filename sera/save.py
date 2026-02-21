"""Save/load framework for serializing run state."""

from __future__ import annotations
import json
from pathlib import Path

from sera.weapon import Weapon
from sera.crafting import CraftingMaterial, CRAFTING_MATERIALS
from sera.equipment import EquipmentItem
from sera.consumables import CONSUMABLE_REGISTRY

SAVE_VERSION = "1.11"
DEFAULT_SAVE_PATH = Path("savegame.json")


def serialize_state(state) -> dict:
    return {
        "saveVersion": SAVE_VERSION,
        "floor": state.floor,
        "max_floors": state.max_floors,
        "mode": state.mode,
        "rng_seed": state.rng_seed,
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
        "consumables": [c.key for c in state.consumables],
        "floors_cleared": state.floors_cleared,
    }


def deserialize_state(data: dict, state) -> None:
    weapon_map: dict[str, Weapon] = {w.display_name: w for w in state.all_weapons}
    material_map: dict[str, CraftingMaterial] = {m.name: m for m in CRAFTING_MATERIALS.values()}

    state.floor = data.get("floor", 0)
    state.max_floors = data.get("max_floors", 5)
    state.mode = data.get("mode", "campaign")
    state.rng_seed = data.get("rng_seed", state.rng_seed)

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
    keys = data.get("consumables", [])
    state.consumables = [CONSUMABLE_REGISTRY[key] for key in keys if key in CONSUMABLE_REGISTRY]
    if not state.consumables:
        legacy_flasks = data.get("healing_flasks", 2)
        state.add_consumable("healing_flask", legacy_flasks)
    state.floors_cleared = data.get("floors_cleared", 0)


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
