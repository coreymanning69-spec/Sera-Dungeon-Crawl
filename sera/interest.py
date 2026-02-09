"""
The Patience Engine — Sera's "HP" system.

Sera doesn't take damage. She gets bored.
Patience drains every turn, enemies annoy her,
and the only way to heal is to do something impressive.

Hit 0 Patience and she leaves. Game Over.
"""

from __future__ import annotations
from dataclasses import dataclass, field


@dataclass
class InterestManager:
    """
    Tracks Sera's willingness to keep playing.

    Core loop:
        - Every turn: -1 (time is the enemy)
        - Enemy action:  -N (annoyance cost)
        - Kill:          +2
        - Multi-kill:    +10
        - Overkill:      +excess_damage (the BIG heal)
    """
    max_patience: int = 100
    current_patience: int = 100
    total_kills: int = 0
    turn_number: int = 0
    game_over: bool = False

    # Tracking for multi-kill detection
    _kills_this_turn: int = field(default=0, repr=False)

    # --- Constants ---
    TICK_DRAIN: int = 1
    KILL_RESTORE: int = 2
    MULTI_KILL_RESTORE: int = 10
    MULTI_KILL_THRESHOLD: int = 2  # kills in one turn to count

    # --- Core operations ---

    def start_turn(self) -> list[str]:
        """Begin a new turn. Apply the passive drain."""
        self.turn_number += 1
        self._kills_this_turn = 0
        log = [f"\n{'='*50}",
               f"  TURN {self.turn_number}  |  Patience: {self.current_patience}/{self.max_patience}",
               f"{'='*50}"]
        self._drain(self.TICK_DRAIN, "Time passes. Boring.")
        log.append(f"  [-{self.TICK_DRAIN} Patience] Time ticks. \"{self._time_quip()}\"")
        return log

    def take_annoyance(self, cost: int, source: str) -> list[str]:
        """Enemy did something annoying."""
        log = []
        self._drain(cost, source)
        log.append(f"  [-{cost} Patience] {source}")
        if self.game_over:
            log.append(self._game_over_text())
        return log

    def register_kill(self, enemy_name: str, damage_dealt: int, enemy_hp_was: int) -> list[str]:
        """
        Process a kill. This is where aggressive play pays off.

        Overkill: if damage > remaining HP, restore the excess as Patience.
        Multi-kill: 2+ kills in one turn = +10 bonus.
        """
        log = []
        self._kills_this_turn += 1
        self.total_kills += 1

        # Base kill restore
        self._restore(self.KILL_RESTORE)
        log.append(f'  [+{self.KILL_RESTORE} Patience] Killed {enemy_name}. "Adequate."')

        # Overkill bonus
        excess = max(0, damage_dealt - enemy_hp_was)
        if excess > 0:
            self._restore(excess)
            log.append(f'  [+{excess} Patience] OVERKILL! "Now THAT was satisfying."')

        # Multi-kill check
        if self._kills_this_turn >= self.MULTI_KILL_THRESHOLD:
            self._restore(self.MULTI_KILL_RESTORE)
            log.append(f'  [+{self.MULTI_KILL_RESTORE} Patience] MULTI-KILL! "More. Do that again."')

        return log

    def end_turn(self) -> list[str]:
        """End-of-turn status report."""
        log = []
        bar = self._patience_bar()
        log.append(f"  Patience: [{bar}] {self.current_patience}/{self.max_patience}")
        if self.game_over:
            log.append(self._game_over_text())
        return log

    # --- Internal ---

    def _drain(self, amount: int, _reason: str = ""):
        self.current_patience = max(0, self.current_patience - amount)
        if self.current_patience <= 0:
            self.game_over = True

    def _restore(self, amount: int):
        self.current_patience = min(self.max_patience, self.current_patience + amount)

    def _patience_bar(self, width: int = 20) -> str:
        filled = int((self.current_patience / self.max_patience) * width)
        return "#" * filled + "-" * (width - filled)

    def _time_quip(self) -> str:
        p = self.current_patience
        if p > 80:
            return "Fine. I'll entertain this."
        if p > 60:
            return "You have my attention. Barely."
        if p > 40:
            return "This better get interesting soon."
        if p > 20:
            return "I'm running out of reasons to stay."
        return "One more disappointment and I'm leaving."

    @staticmethod
    def _game_over_text() -> str:
        return ('\n  *** GAME OVER ***\n'
                '  Sera rolls her eyes.\n'
                '  "This is a waste of time."\n'
                '  She teleports away. The dungeon collapses.\n'
                '  You have failed to be interesting.\n')

    def __repr__(self) -> str:
        return f"Patience: {self.current_patience}/{self.max_patience} (Turn {self.turn_number})"
