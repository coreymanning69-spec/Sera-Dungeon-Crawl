"""
The Patience Engine — Sera's "HP" system.

Sera doesn't take damage. She gets bored.
Patience drains every turn, enemies annoy her,
and the only way to heal is to do something impressive.

Hit 0 Patience and she leaves. Game Over.
"""

from __future__ import annotations
import random
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
    _last_kill_turn: int = field(default=-99, repr=False)  # rapid-kill tracker

    # --- Constants ---
    TICK_DRAIN: int = 1
    KILL_RESTORE: int = 5
    MULTI_KILL_RESTORE: int = 10
    MULTI_KILL_THRESHOLD: int = 2  # kills in one turn to count
    RAPID_KILL_WINDOW: int = 2     # turns between kills for bonus
    RAPID_KILL_RESTORE: int = 3    # bonus for kills in quick succession

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

    def comment_on_regen(self, enemy_name: str) -> str:
        """Sera's opinion on an enemy healing itself."""
        return random.choice([
            "Stop healing. It's dragging on.",
            "Nobody asked for a second act.",
            "I will end this personally.",
            "You're not broken. You're just stalling.",
            "A troll with better manners, at least, would die first.",
            "Regeneration is just dying slowly in reverse.",
            "You heal. I hit harder. Do the math.",
            "The longer you heal, the worse I make it.",
            "Even a phoenix has the decency to die before coming back.",
            "You're not Halaster. Stop acting immortal.",
            "Close the wound. I'll open a bigger one.",
            "Healing in front of me is a personal insult.",
            "You can't out-heal contempt.",
            "That's not resilience. That's denial.",
        ])

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
        kill_quip = random.choice([
            "Adequate.",
            "Gone. Next.",
            "It won't be missed.",
            "Shh.",
            "No. That doesn't get to continue.",
            "I told you once.",
            "I don't need a second hit.",
            "You're done.",
            "Back to the Fugue Plane with you.",
            "That's what happens when you bore a goddess.",
            "One less problem. Several more to go.",
            "Removed from the encounter. Permanently.",
            "The Astral Plane can sort you out.",
            "Even Ao couldn't save that one.",
            "I've dismissed greater threats over breakfast.",
            "Don't worry. Nobody will remember you.",
            "That was your last turn. In every sense.",
            "Consider yourself pruned from reality.",
        ])
        log.append(f'  [+{self.KILL_RESTORE} Patience] Killed {enemy_name}. "{kill_quip}"')

        # Overkill bonus
        excess = max(0, damage_dealt - enemy_hp_was)
        if excess > 0:
            self._restore(excess)
            overkill_quip = random.choice([
                "Now THAT was satisfying.",
                "Efficient. Almost artistic.",
                "NOW that had commitment.",
                "NOW we're talking.",
                "THAT is how you kill something.",
                "That's the good part. Do it again.",
                "Oh. You meant that.",
                "That wasn't death. That was erasure.",
                "Excessive force is just force with conviction.",
                "The excess damage is the interesting part.",
                "You killed it twice. I respect the redundancy.",
                "Even a tarrasque would have flinched at that.",
                "That hit so hard it retroactively hurt.",
                "MORE. Always more.",
                "Spectacular violence. My favorite kind.",
                "That was worth staying for.",
                "I felt that in the divine register.",
            ])
            log.append(f'  [+{excess} Patience] OVERKILL! "{overkill_quip}"')

        # Multi-kill check
        if self._kills_this_turn >= self.MULTI_KILL_THRESHOLD:
            self._restore(self.MULTI_KILL_RESTORE)
            multi_quip = random.choice([
                "More. Do that again.",
                "Don't stop. I mean it.",
                "THAT is how you hold my interest.",
                "We're not even gonna die.",
                "Somebody duck. There are more coming.",
                "NOW we're talking.",
                "Two for one. My favorite math.",
                "A chain of kills. Beautiful.",
                "The pile grows. I approve.",
                "Multiple targets, zero survivors. Efficient.",
                "That's a cleave worthy of a vorpal blade.",
                "Stack the bodies. I'm counting.",
                "Consecutive elimination. Keep the tempo.",
                "Two down in one breath. Impressive.",
                "Mass deletion. The best kind of crowd control.",
                "They came in numbers. They leave in pieces.",
            ])
            log.append(f'  [+{self.MULTI_KILL_RESTORE} Patience] MULTI-KILL! "{multi_quip}"')

        # Rapid-kill check (kills within 2 turns of each other)
        if (self._last_kill_turn >= 0
                and self.turn_number - self._last_kill_turn <= self.RAPID_KILL_WINDOW
                and self._kills_this_turn < self.MULTI_KILL_THRESHOLD):
            self._restore(self.RAPID_KILL_RESTORE)
            rapid_quip = random.choice([
                "Fast. I like fast.",
                "No pause between executions. Good.",
                "Back to back. Keep that tempo.",
                "Efficient carnage. Almost artistic.",
                "Quick succession. My favorite kind of pacing.",
                "Two kills, barely a breath between them. Acceptable.",
                "Speed kills. Literally.",
                "Momentum. Don't lose it.",
                "That's the rhythm of violence. Keep the beat.",
                "Rapid elimination. Like a vorpal blade through a speech.",
                "You're not pausing. Good. Pausing is for mortals.",
                "Consecutive kills. The dungeon notices.",
                "Fast hands. Faster results. Almost interesting.",
                "Kill tempo rising. My attention follows.",
            ])
            log.append(f'  [+{self.RAPID_KILL_RESTORE} Patience] RAPID KILL! "{rapid_quip}"')

        self._last_kill_turn = self.turn_number
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
            return random.choice([
                "Fine. I'll entertain this.",
                "Not terrible. Yet.",
                "Relax. I'm in a good mood.",
                "We're just looking.",
                "This place is kinda cute.",
                "I'm comfortable. Don't ruin it.",
                "This dungeon has... potential. Low potential.",
                "Proceed. I'll watch.",
                "Almost pleasant. Almost.",
                "I've seen worse planes of existence. This morning.",
                "The ambiance is adequate. Like a tomb, but warmer.",
                "Keep going. I haven't yawned yet.",
                "Not bored. Not entertained. Neutral. Enjoy it.",
                "You have my full indifference. That's generous.",
                "Cozy. In a damp, monster-infested sort of way.",
            ])
        if p > 60:
            return random.choice([
                "You have my attention. Barely.",
                "You have my attention. Don't squander it.",
                "That's new.",
                "You're cute. Don't ruin it.",
                "Duh.",
                "Mildly engaged. Don't let it go to your head.",
                "I suppose this is what passes for action.",
                "You're holding my interest. Loosely.",
                "Interesting enough to not leave. For now.",
                "The Forgotten Realms forgot more exciting things than this.",
                "Showing promise. Like a cantrip that might scale.",
                "I'm watching. That's more than most get.",
                "Passable. Like a side quest in Amn.",
                "You've earned a raised eyebrow. Treasure it.",
                "Adequate pacing. Keep it up.",
            ])
        if p > 40:
            return random.choice([
                "This better get interesting soon.",
                "Pick up the pace. I mean it.",
                "What are you worried about?",
                "Clear the air.",
                "That's it? That's your miracle?",
                "I'm getting restless. You won't like me restless.",
                "Tempo's dropping. Fix it.",
                "I came here for violence, not a nature walk.",
                "Even a gelatinous cube moves with more purpose.",
                "If this were a play in Waterdeep, I'd have left at intermission.",
                "My interest is a candle. It's flickering.",
                "This dungeon is testing my patience. That's my line.",
                "Speed. Violence. Momentum. Pick at least one.",
                "You're losing me. That's not a figure of speech.",
                "A yuan-ti could scheme faster than you kill.",
            ])
        if p > 20:
            return random.choice([
                "I'm running out of reasons to stay.",
                "My patience is not infinite. Shocking, I know.",
                "You're not a law. You're a problem.",
                "You don't get a turn.",
                "I don't need magic. I just need you to decide.",
                "The hourglass is almost empty. So am I.",
                "Do something spectacular. NOW.",
                "I am one bad turn from folding this reality.",
                "Even Bhaal's chosen would be concerned right now.",
                "You're hemorrhaging my goodwill.",
                "This is your last act. Make it memorable.",
                "I can feel the multiverse calling me elsewhere.",
                "My patience has hit single digits. Emotionally.",
                "Kill something. Anything. Immediately.",
                "You are dangerously close to boring me to death. My death. Of interest.",
            ])
        return random.choice([
            "One more disappointment and I'm leaving.",
            "Last warning. Make it count.",
            "You're loud.",
            "You picked the wrong axis.",
            "I'm going to fix this.",
            "I'm already planning my exit. Convince me otherwise.",
            "This is the part where mortals beg.",
            "One. More. Chance.",
            "The dungeon feels my displeasure. You should too.",
            "I'm counting down from a number you can't afford.",
            "Every god in the pantheon is watching you fail.",
            "My patience is an endangered species.",
            "Say goodbye to the dungeon. It's about to not exist.",
            "You're out of second chances. You're on third.",
            "The only thing keeping this reality together is spite.",
        ])

    @staticmethod
    def _game_over_text() -> str:
        outro = random.choice([
            '"This is a waste of time."',
            '"I gave you every chance."',
            '"You had a chance. You used it wrong."',
            '"Soliera\'s still looking. That\'s your last warning. Too late."',
            '"The Weave bends to my boredom. Goodbye."',
            '"I\'ve seen civilizations fall. This was less interesting."',
            '"Tell the next adventurer to try harder."',
            '"The dungeon was fine. YOU were the problem."',
            '"I\'m going somewhere that deserves my attention."',
            '"Disappointing. Like a wish spell wasted on cantrips."',
            '"Reality doesn\'t collapse because I\'m angry. It collapses because I stopped caring."',
            '"You fought like a commoner with a rusty spoon."',
            '"Myrkul can have this place. I\'m done."',
            '"I outlast everything. Except boredom. Boredom wins."',
        ])
        return ('\n  *** GAME OVER ***\n'
                f'  Sera rolls her eyes.\n'
                f'  {outro}\n'
                '  She teleports away. The dungeon collapses.\n'
                '  You have failed to be interesting.\n')

    def __repr__(self) -> str:
        return f"Patience: {self.current_patience}/{self.max_patience} (Turn {self.turn_number})"
