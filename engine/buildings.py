"""
Tactical RTS Buildings, Defensive Structures, and Capturable Derricks
"""
import math
import pygame
from engine.config import (
    BUILDING_CONFIGS, UNIT_CONFIGS,
    COLOR_PLAYER, COLOR_PLAYER_GLOW, COLOR_ENEMY, COLOR_ENEMY_GLOW,
    COLOR_NEUTRAL, COLOR_HEALTH_GREEN, COLOR_HEALTH_YELLOW, COLOR_HEALTH_RED,
    COLOR_SELECTION, FACTION_PLAYER, FACTION_ENEMY, FACTION_NEUTRAL
)

class Building:
    def __init__(self, b_type, x, y, faction=FACTION_PLAYER, is_constructed=True):
        self.type_key = b_type
        self.cfg = BUILDING_CONFIGS[b_type]
        self.x = float(x)
        self.y = float(y)
        self.faction = faction
        self.w, self.h = self.cfg["size"]
        self.hit_radius = max(self.w, self.h) * 0.55

        self.max_hp = self.cfg["hp"]
        self.hp = self.max_hp
        self.dead = False
        self.selected = False

        self.is_constructed = is_constructed
        self.build_time = self.cfg["build_time"]
        self.build_progress = self.build_time if is_constructed else 0.0

        # Production Queue
        self.queue = []  # list of unit_type keys
        self.current_unit = None
        self.unit_prod_time = 0.0
        self.unit_prod_progress = 0.0
        self.rally_point = (self.x + self.w * 0.5 + 40, self.y + self.h * 0.5 + 40)

        # Defense weapon (for bunkers and missile turrets)
        self.has_weapon = "damage" in self.cfg
        self.range = self.cfg.get("range", 0)
        self.reload_time = self.cfg.get("reload", 1.0)
        self.reload_timer = 0.0
        self.target = None

        # Capturable points (resource derricks)
        self.is_capturable = self.cfg.get("is_capturable", False)
        self.capture_points = 0.0  # -100 (Enemy) to 0 (Neutral) to +100 (Player)
        if self.is_capturable:
            self.faction = FACTION_NEUTRAL
            self.capture_max = 6.0  # 6 seconds to capture

        # Income generation
        self.income_timer = 0.0
        self.income_interval = 3.0

        # Animation timers
        self.anim_phase = 0.0

    def take_damage(self, amount):
        self.hp -= amount
        if self.hp <= 0:
            self.hp = 0
            self.dead = True

    def repair(self, amount):
        self.hp = min(self.max_hp, self.hp + amount)

    def enqueue_unit(self, unit_type, player_resources):
        unit_cfg = UNIT_CONFIGS.get(unit_type)
        if not unit_cfg:
            return False
        if player_resources >= unit_cfg["cost"] and len(self.queue) < 5:
            self.queue.append(unit_type)
            return True
        return False

    def cancel_queued(self, index=0):
        if 0 <= index < len(self.queue):
            return self.queue.pop(index)
        return None

    def update(self, dt, combat_eng, sound_engine, effect_mgr, all_units, all_entities):
        self.anim_phase += dt

        # 1. Construction Progress
        if not self.is_constructed:
            self.build_progress += dt
            if self.build_progress >= self.build_time:
                self.is_constructed = True
                self.hp = self.max_hp
                if self.faction == FACTION_PLAYER:
                    sound_engine.play("build_complete")
            return

        # 2. Turret Weapon Reload and Target Acquisition
        if self.has_weapon:
            if self.reload_timer > 0:
                self.reload_timer -= dt

            # Check if current target is valid
            if self.target and (getattr(self.target, 'dead', True) or
                                math.hypot(self.target.x - self.x, self.target.y - self.y) > self.range):
                self.target = None

            # Acquire nearest hostile unit
            if not self.target:
                best_dist = self.range
                for u in all_units:
                    if u.faction != self.faction and u.faction != FACTION_NEUTRAL and not u.dead:
                        d = math.hypot(u.x - self.x, u.y - self.y)
                        if d < best_dist:
                            best_dist = d
                            self.target = u

            # Fire weapon
            if self.target and self.reload_timer <= 0:
                combat_eng.spawn_projectile(
                    self.x, self.y, self.target,
                    {"weapon_type": "rocket" if self.type_key == "missile_turret" else "bullet",
                     "damage": self.cfg["damage"],
                     "projectile_speed": 18,
                     "splash": self.cfg.get("splash", 0)},
                    self.faction
                )
                self.reload_timer = self.reload_time

        # 3. Unit Production Queue
        if self.queue and not self.current_unit:
            self.current_unit = self.queue.pop(0)
            self.unit_prod_time = UNIT_CONFIGS[self.current_unit]["build_time"]
            self.unit_prod_progress = 0.0

        if self.current_unit:
            self.unit_prod_progress += dt
            if self.unit_prod_progress >= self.unit_prod_time:
                # Unit Ready! Handled by game_state spawner
                ready_type = self.current_unit
                self.current_unit = None
                return ready_type  # return type to spawn

        # 4. Capturable Resource Points
        if self.is_capturable:
            capture_radius = 90
            player_capturers = 0
            enemy_capturers = 0

            for u in all_units:
                if not u.dead and u.cfg.get("can_capture", False):
                    d = math.hypot(u.x - self.x, u.y - self.y)
                    if d <= capture_radius:
                        if u.faction == FACTION_PLAYER:
                            player_capturers += 1
                        elif u.faction == FACTION_ENEMY:
                            enemy_capturers += 1

            if player_capturers > 0 and enemy_capturers == 0:
                # Capture towards Player
                if self.faction != FACTION_PLAYER:
                    self.capture_points += dt * (1.0 + 0.3 * (player_capturers - 1))
                    if self.capture_points >= self.capture_max:
                        self.faction = FACTION_PLAYER
                        self.capture_points = self.capture_max
                        sound_engine.play("capture_complete")
                        effect_mgr.add_floating_text(self.x, self.y - 30, "ЗАХОПЛЕНО!", (0, 255, 128))
            elif enemy_capturers > 0 and player_capturers == 0:
                # Capture towards Enemy
                if self.faction != FACTION_ENEMY:
                    self.capture_points -= dt * (1.0 + 0.3 * (enemy_capturers - 1))
                    if self.capture_points <= -self.capture_max:
                        self.faction = FACTION_ENEMY
                        self.capture_points = -self.capture_max
                        effect_mgr.add_floating_text(self.x, self.y - 30, "ВТРАЧЕНО!", (255, 60, 60))

        # Damaged smoke effect
        if self.hp < self.max_hp * 0.4 and int(self.anim_phase * 10) % 6 == 0:
            effect_mgr.add_rocket_smoke(self.x + self.w * 0.3, self.y + self.h * 0.3)

        return None

    def render(self, surface, camera, is_explored_only=False):
        if not camera.is_visible(self.x, self.y, int(self.hit_radius) + 16):
            return

        sx, sy = camera.world_to_screen(self.x - self.w * 0.5, self.y - self.h * 0.5)
        rect = pygame.Rect(sx, sy, int(self.w), int(self.h))

        # Base building foundation
        base_color = (40, 44, 46)
        pygame.draw.rect(surface, base_color, rect, border_radius=4)
        pygame.draw.rect(surface, (20, 22, 24), rect, width=2, border_radius=4)

        # Team Color Accent
        team_col = COLOR_NEUTRAL
        if self.faction == FACTION_PLAYER:
            team_col = COLOR_PLAYER
        elif self.faction == FACTION_ENEMY:
            team_col = COLOR_ENEMY

        accent_rect = pygame.Rect(sx + 6, sy + 6, int(self.w - 12), 10)
        pygame.draw.rect(surface, team_col, accent_rect, border_radius=2)

        # Inner structure details
        if self.type_key == "hq":
            # Headquarters: Radar tower + command dome
            cx, cy = sx + self.w * 0.5, sy + self.h * 0.5
            pygame.draw.circle(surface, (60, 68, 72), (int(cx), int(cy)), int(self.w * 0.28))
            pygame.draw.circle(surface, team_col, (int(cx), int(cy)), int(self.w * 0.16))
            # Rotating radar arm
            radar_angle = self.anim_phase * 2.5
            rx = cx + math.cos(radar_angle) * (self.w * 0.26)
            ry = cy + math.sin(radar_angle) * (self.h * 0.26)
            pygame.draw.line(surface, (200, 230, 255), (int(cx), int(cy)), (int(rx), int(ry)), 2)
        elif self.type_key == "barracks":
            # Barracks: Quonset hut metal ribs
            for i in range(4):
                y_rib = sy + 22 + i * 14
                pygame.draw.line(surface, (65, 75, 80), (sx + 8, y_rib), (sx + self.w - 8, y_rib), 3)
        elif self.type_key == "war_factory":
            # War Factory: Assembly crane & bay doors
            bay_rect = pygame.Rect(sx + 14, sy + 26, int(self.w - 28), int(self.h - 38))
            pygame.draw.rect(surface, (25, 28, 30), bay_rect)
            # Hazard stripes
            pygame.draw.line(surface, (255, 180, 0), (bay_rect.left, bay_rect.top), (bay_rect.left + 15, bay_rect.bottom), 2)
            pygame.draw.line(surface, (255, 180, 0), (bay_rect.left + 20, bay_rect.top), (bay_rect.left + 35, bay_rect.bottom), 2)
        elif self.type_key == "drone_bay":
            # Drone Bay: Helipad with 'H' marking and antenna
            cx, cy = sx + self.w * 0.5, sy + self.h * 0.5 + 4
            pygame.draw.circle(surface, (45, 52, 58), (int(cx), int(cy)), 22)
            pygame.draw.circle(surface, (255, 200, 0), (int(cx), int(cy)), 20, 2)
            # 'H' mark
            pygame.draw.line(surface, (255, 255, 255), (cx - 8, cy - 10), (cx - 8, cy + 10), 3)
            pygame.draw.line(surface, (255, 255, 255), (cx + 8, cy - 10), (cx + 8, cy + 10), 3)
            pygame.draw.line(surface, (255, 255, 255), (cx - 8, cy), (cx + 8, cy), 3)
        elif self.type_key == "supply_depot":
            # Crates and oil barrels
            for bx, by in [(sx + 10, sy + 24), (sx + 32, sy + 24), (sx + 20, sy + 42)]:
                pygame.draw.rect(surface, (80, 70, 50), (bx, by, 16, 14))
                pygame.draw.rect(surface, (50, 40, 30), (bx, by, 16, 14), 1)
        elif self.type_key == "bunker":
            # Pillbox machine gun slits
            cx, cy = sx + self.w * 0.5, sy + self.h * 0.5
            pygame.draw.circle(surface, (55, 60, 62), (int(cx), int(cy)), 20)
            pygame.draw.circle(surface, (20, 22, 24), (int(cx), int(cy)), 10)
        elif self.type_key == "missile_turret":
            # Missile silo launcher
            cx, cy = sx + self.w * 0.5, sy + self.h * 0.5
            pygame.draw.circle(surface, (50, 55, 60), (int(cx), int(cy)), 22)
            pygame.draw.rect(surface, (80, 85, 90), (cx - 10, cy - 16, 8, 28))
            pygame.draw.rect(surface, (80, 85, 90), (cx + 2, cy - 16, 8, 28))
        elif self.type_key == "resource_derrick":
            # Pumping unit derrick
            cx, cy = sx + self.w * 0.5, sy + self.h * 0.5
            # Tower scaffolding
            pygame.draw.polygon(surface, (90, 85, 75), [(cx - 16, sy + self.h - 8), (cx + 16, sy + self.h - 8), (cx, sy + 10)], 2)
            # Flag banner indicating faction
            flag_col = team_col
            pygame.draw.rect(surface, flag_col, (cx, sy + 8, 16, 10))

        # Selection ring
        if self.selected and not is_explored_only:
            pygame.draw.circle(surface, COLOR_SELECTION, (int(sx + self.w * 0.5), int(sy + self.h * 0.5)), int(self.hit_radius + 4), 2)
            # Rally point line for production buildings
            if self.queue or self.current_unit:
                rx, ry = camera.world_to_screen(self.rally_point[0], self.rally_point[1])
                pygame.draw.line(surface, (0, 255, 128), (sx + self.w * 0.5, sy + self.h * 0.5), (rx, ry), 1)
                pygame.draw.circle(surface, (0, 255, 128), (rx, ry), 4)

        # Health bar (if not hidden in fog)
        if not is_explored_only:
            bar_w = int(self.w)
            bar_h = 5
            bar_x = sx
            bar_y = sy - 10
            pct = max(0.0, self.hp / self.max_hp)
            h_col = COLOR_HEALTH_GREEN if pct > 0.5 else (COLOR_HEALTH_YELLOW if pct > 0.25 else COLOR_HEALTH_RED)

            pygame.draw.rect(surface, (20, 20, 20), (bar_x, bar_y, bar_w, bar_h))
            pygame.draw.rect(surface, h_col, (bar_x, bar_y, int(bar_w * pct), bar_h))
            pygame.draw.rect(surface, (0, 0, 0), (bar_x, bar_y, bar_w, bar_h), 1)

            # Production bar
            if self.current_unit:
                p_pct = min(1.0, self.unit_prod_progress / max(0.1, self.unit_prod_time))
                py_bar = sy - 4
                pygame.draw.rect(surface, (30, 40, 50), (bar_x, py_bar, bar_w, 3))
                pygame.draw.rect(surface, (0, 229, 255), (bar_x, py_bar, int(bar_w * p_pct), 3))
