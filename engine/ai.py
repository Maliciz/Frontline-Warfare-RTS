"""
Combat Artificial Intelligence Engine for Frontline: Steel Vanguard RTS
Features multi-tier build orders, resource capture, coordinated strike waves,
precision FPV drone strikes, and home base defense.
"""
import math
import random
from engine.config import (
    FACTION_ENEMY, FACTION_PLAYER, FACTION_NEUTRAL,
    BUILDING_CONFIGS, UNIT_CONFIGS
)

DIFFICULTY_EASY = "easy"
DIFFICULTY_NORMAL = "normal"
DIFFICULTY_HARD = "hard"

class EnemyAI:
    def __init__(self, difficulty=DIFFICULTY_NORMAL, base_x=2160, base_y=360):
        self.difficulty = difficulty
        self.base_x = float(base_x)
        self.base_y = float(base_y)
        self.resources = 600
        self.max_pop = 20

        # Timers & state
        self.think_timer = 0.0
        self.attack_timer = 0.0
        self.drone_strike_timer = 0.0

        if difficulty == DIFFICULTY_EASY:
            self.attack_interval = 70.0
            self.wave_size = 5
            self.income_mult = 0.85
        elif difficulty == DIFFICULTY_HARD:
            self.attack_interval = 32.0
            self.wave_size = 9
            self.income_mult = 1.35
        else:  # NORMAL
            self.attack_interval = 48.0
            self.wave_size = 7
            self.income_mult = 1.0

        # Planned building blueprint offsets relative to base_x, base_y
        self.build_plan = [
            ("barracks", 120, -40),
            ("supply_depot", -40, 120),
            ("war_factory", -140, 60),
            ("drone_bay", 100, 130),
            ("missile_turret", -120, 180),
            ("bunker", 160, -120),
            ("supply_depot", 40, 180)
        ]

    def update(self, dt, game_state):
        self.think_timer += dt
        self.attack_timer += dt
        self.drone_strike_timer += dt

        # Passive base resource income
        self.resources += (14.0 * self.income_mult) * (dt / 3.0)

        # Run AI strategic logic every 1.0 second
        if self.think_timer >= 1.0:
            self.think_timer = 0.0
            self._manage_economy_and_building(game_state)
            self._manage_production(game_state)
            self._manage_resource_capture(game_state)
            self._manage_defense(game_state)

        # Launch FPV drone precision strike periodically
        if self.drone_strike_timer >= (18.0 if self.difficulty == DIFFICULTY_HARD else 28.0):
            self.drone_strike_timer = 0.0
            self._launch_drone_strike(game_state)

        # Launch coordinated ground attack wave
        if self.attack_timer >= self.attack_interval:
            self.attack_timer = 0.0
            self._launch_attack_wave(game_state)

    def _manage_economy_and_building(self, game_state):
        """Construct planned base structures if resources are available."""
        ai_buildings = [b for b in game_state.buildings if b.faction == FACTION_ENEMY and not b.dead]
        existing_types = [b.type_key for b in ai_buildings]

        for b_type, ox, oy in self.build_plan:
            cfg = BUILDING_CONFIGS[b_type]
            # Build if we don't have enough of this type
            count = existing_types.count(b_type)
            max_wanted = 2 if b_type == "supply_depot" else 1
            if count < max_wanted and self.resources >= cfg["cost"]:
                # Construct!
                bx = self.base_x + ox
                by = self.base_y + oy
                game_state.spawn_building(b_type, bx, by, faction=FACTION_ENEMY)
                self.resources -= cfg["cost"]
                if "pop_bonus" in cfg:
                    self.max_pop += cfg["pop_bonus"]
                break

    def _manage_production(self, game_state):
        """Queue up military units in production facilities."""
        ai_units = [u for u in game_state.units if u.faction == FACTION_ENEMY and not u.dead]
        current_pop = sum(u.cfg["pop"] for u in ai_units)

        if current_pop >= self.max_pop:
            return  # pop capped

        ai_buildings = [b for b in game_state.buildings if b.faction == FACTION_ENEMY and not b.dead]

        for b in ai_buildings:
            if not b.is_constructed or len(b.queue) >= 2 or b.current_unit:
                continue

            if b.type_key == "barracks":
                # Produce Rifleman or RPG
                choice = "rpg" if random.random() < 0.45 else "rifleman"
                cost = UNIT_CONFIGS[choice]["cost"]
                if self.resources >= cost:
                    b.enqueue_unit(choice, self.resources)
                    self.resources -= cost

            elif b.type_key == "war_factory":
                # Produce Tank, IFV, Artillery, AA
                roll = random.random()
                if roll < 0.40:
                    choice = "tank"
                elif roll < 0.65:
                    choice = "ifv"
                elif roll < 0.85:
                    choice = "artillery"
                else:
                    choice = "aa_vehicle"

                cost = UNIT_CONFIGS[choice]["cost"]
                if self.resources >= cost:
                    b.enqueue_unit(choice, self.resources)
                    self.resources -= cost

            elif b.type_key == "drone_bay":
                # Produce Kamikaze FPV drone
                cost = UNIT_CONFIGS["fpv_drone"]["cost"]
                if self.resources >= cost:
                    b.enqueue_unit("fpv_drone", self.resources)
                    self.resources -= cost

    def _manage_resource_capture(self, game_state):
        """Send riflemen to capture contested resource derricks."""
        unowned_derricks = [
            b for b in game_state.buildings
            if b.is_capturable and b.faction != FACTION_ENEMY and not b.dead
        ]
        if not unowned_derricks:
            return

        capturers = [
            u for u in game_state.units
            if u.faction == FACTION_ENEMY and not u.dead and u.cfg.get("can_capture", False) and u.state == "idle"
        ]

        for derrick in unowned_derricks:
            if not capturers:
                break
            # Send 2 infantry units to capture
            for _ in range(min(2, len(capturers))):
                soldier = capturers.pop(0)
                soldier.issue_capture(derrick)

    def _manage_defense(self, game_state):
        """If AI base is under direct attack, pull defenders back."""
        hostiles_near_base = [
            u for u in game_state.units
            if u.faction == FACTION_PLAYER and not u.dead and math.hypot(u.x - self.base_x, u.y - self.base_y) < 550
        ]

        if hostiles_near_base:
            # Emergency alarm: redirect idle units to defend
            target_threat = hostiles_near_base[0]
            for u in game_state.units:
                if u.faction == FACTION_ENEMY and not u.dead and u.state == "idle":
                    u.issue_attack(target_threat)

    def _launch_drone_strike(self, game_state):
        """Direct FPV drones towards high value player targets (tanks, artillery, HQ)."""
        drones = [
            u for u in game_state.units
            if u.faction == FACTION_ENEMY and not u.dead and u.type_key == "fpv_drone"
        ]
        if not drones:
            return

        # Find best player target
        player_targets = [
            u for u in game_state.units
            if u.faction == FACTION_PLAYER and not u.dead and u.type_key in ("tank", "artillery", "ifv")
        ]
        if not player_targets:
            player_targets = [b for b in game_state.buildings if b.faction == FACTION_PLAYER and not b.dead]

        if player_targets:
            target = random.choice(player_targets)
            for drone in drones:
                drone.issue_attack(target)

    def _launch_attack_wave(self, game_state):
        """Form strike force and march on player territory."""
        combat_units = [
            u for u in game_state.units
            if u.faction == FACTION_ENEMY and not u.dead and u.type_key != "fpv_drone"
        ]

        if len(combat_units) >= self.wave_size:
            # Pick objective: Player HQ or nearest player building/unit
            player_hq = next((b for b in game_state.buildings if b.faction == FACTION_PLAYER and b.type_key == "hq"), None)
            target_x = player_hq.x if player_hq else 400
            target_y = player_hq.y if player_hq else 1600

            # Issue attack-move to the assault wave
            for u in combat_units:
                # Add slight tactical spread
                ox = random.uniform(-60, 60)
                oy = random.uniform(-60, 60)
                u.issue_attack_move(target_x + ox, target_y + oy)
