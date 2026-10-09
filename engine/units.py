"""
Tactical RTS Combat Units: Infantry, Armored Vehicles, Artillery, and FPV Drones
"""
import math
import random
import pygame
from engine.config import (
    UNIT_CONFIGS, FACTION_PLAYER, FACTION_ENEMY, FACTION_NEUTRAL,
    COLOR_PLAYER, COLOR_PLAYER_GLOW, COLOR_ENEMY, COLOR_ENEMY_GLOW,
    COLOR_SELECTION, COLOR_HEALTH_GREEN, COLOR_HEALTH_YELLOW, COLOR_HEALTH_RED
)

STATE_IDLE = "idle"
STATE_MOVE = "move"
STATE_ATTACK = "attack"
STATE_ATTACK_MOVE = "attack_move"
STATE_CAPTURE = "capture"

class Unit:
    _id_counter = 0

    def __init__(self, u_type, x, y, faction=FACTION_PLAYER):
        Unit._id_counter += 1
        self.id = Unit._id_counter
        self.type_key = u_type
        self.cfg = UNIT_CONFIGS[u_type]
        self.x = float(x)
        self.y = float(y)
        self.faction = faction
        self.category = self.cfg["category"]

        self.max_hp = self.cfg["hp"]
        self.hp = self.max_hp
        self.speed = self.cfg["speed"]
        self.range = self.cfg["range"]
        self.min_range = self.cfg.get("min_range", 0)
        self.damage = self.cfg["damage"]
        self.reload_time = self.cfg["reload"]
        self.vision = self.cfg["vision"]
        self.hit_radius = 12 if self.category == "infantry" else (22 if u_type == "tank" else (10 if u_type == "fpv_drone" else 16))

        self.dead = False
        self.selected = False

        # States & Navigation
        self.state = STATE_IDLE
        self.target = None
        self.target_pos = None  # (tx, ty)
        self.path = []

        # Angles & Visuals
        self.angle = 0.0
        self.turret_angle = 0.0
        self.recoil = 0.0
        self.reload_timer = 0.0
        self.anim_walk = 0.0
        self.tread_timer = 0.0

    def take_damage(self, amount):
        self.hp -= amount
        if self.hp <= 0:
            self.hp = 0
            self.dead = True

    def issue_move(self, tx, ty):
        self.state = STATE_MOVE
        self.target_pos = (float(tx), float(ty))
        self.target = None

    def issue_attack(self, target_entity):
        self.state = STATE_ATTACK
        self.target = target_entity
        self.target_pos = None

    def issue_attack_move(self, tx, ty):
        self.state = STATE_ATTACK_MOVE
        self.target_pos = (float(tx), float(ty))
        self.target = None

    def issue_stop(self):
        self.state = STATE_IDLE
        self.target = None
        self.target_pos = None

    def issue_capture(self, resource_derrick):
        self.state = STATE_CAPTURE
        self.target = resource_derrick
        self.target_pos = (resource_derrick.x, resource_derrick.y)

    def update(self, dt, combat_eng, sound_engine, effect_mgr, map_grid, all_entities, all_units):
        if self.dead:
            return

        # Cooldowns
        if self.reload_timer > 0:
            self.reload_timer -= dt
        if self.recoil > 0:
            self.recoil = max(0.0, self.recoil - 15.0 * dt)

        # FPV Drone buzzing sound when moving
        if self.type_key == "fpv_drone" and self.state in (STATE_MOVE, STATE_ATTACK, STATE_ATTACK_MOVE):
            sound_engine.play("drone_buzz", min_interval=0.25)

        # 1. Target validation
        if self.target and (getattr(self.target, 'dead', False) or
                            (self.type_key in ("tank", "artillery") and getattr(self.target, 'category', '') == 'air')):
            self.target = None
            if self.state == STATE_ATTACK:
                self.state = STATE_IDLE

        # 2. AA Unit priority: intercept airborne FPV drones first!
        if self.type_key == "aa_vehicle" and (not self.target or getattr(self.target, 'category', '') != 'air'):
            for u in all_units:
                if u.faction != self.faction and not u.dead and u.category == 'air':
                    d = math.hypot(u.x - self.x, u.y - self.y)
                    if d <= self.range:
                        self.target = u
                        self.state = STATE_ATTACK
                        break

        # 3. Auto-acquire targets when IDLE or ATTACK_MOVE
        if (self.state == STATE_IDLE or self.state == STATE_ATTACK_MOVE) and not self.target:
            best_dist = self.vision
            for ent in all_entities:
                if ent.faction != self.faction and ent.faction != FACTION_NEUTRAL and not getattr(ent, 'dead', False):
                    # Heavy tanks and artillery cannot target airborne FPV drones
                    if self.type_key in ("tank", "artillery") and getattr(ent, 'category', '') == 'air':
                        continue
                    d = math.hypot(ent.x - self.x, ent.y - self.y)
                    if d <= best_dist:
                        best_dist = d
                        self.target = ent
                        if self.state == STATE_IDLE:
                            self.state = STATE_ATTACK

        # 4. Kamikaze FPV Drone Impact Detonation
        if self.type_key == "fpv_drone" and self.target:
            d = math.hypot(self.target.x - self.x, self.target.y - self.y)
            if d <= 32:
                # Detonate!
                self.dead = True
                effect_mgr.add_explosion(self.x, self.y, radius=self.cfg["splash"], is_large=True)
                sound_engine.play("explosion_large", min_interval=0.1)
                combat_eng._apply_damage(self.target, self.damage)
                # Splash nearby enemies
                for ent in all_entities:
                    if ent.faction != self.faction and not getattr(ent, 'dead', False):
                        sd = math.hypot(ent.x - self.x, ent.y - self.y)
                        if sd <= self.cfg["splash"]:
                            combat_eng._apply_damage(ent, self.damage * 0.5)
                return

        # 5. Combat Range & Attack Behavior
        if self.target and self.state in (STATE_ATTACK, STATE_ATTACK_MOVE):
            d = math.hypot(self.target.x - self.x, self.target.y - self.y)
            target_angle = math.atan2(self.target.y - self.y, self.target.x - self.x)
            self._smooth_rotate_turret(target_angle, dt)

            # Check if within firing range
            if self.min_range <= d <= self.range:
                # In range: stop and fire!
                if self.reload_timer <= 0:
                    combat_eng.spawn_projectile(self.x, self.y, self.target, self.cfg, self.faction)
                    self.reload_timer = self.reload_time
                    self.recoil = 8.0
                return  # don't move closer while firing
            elif d > self.range:
                # Need to move closer to target
                self._move_towards(self.target.x, self.target.y, dt, map_grid, effect_mgr, sound_engine)
            elif d < self.min_range:
                # Artillery: target is too close! Back up or reposition
                back_x = self.x - math.cos(target_angle) * 80
                back_y = self.y - math.sin(target_angle) * 80
                self._move_towards(back_x, back_y, dt, map_grid, effect_mgr, sound_engine)

        # 6. Standard Movement / Attack-Move Navigation
        elif self.target_pos and self.state in (STATE_MOVE, STATE_ATTACK_MOVE, STATE_CAPTURE):
            tx, ty = self.target_pos
            d = math.hypot(tx - self.x, ty - self.y)
            if d <= 8:
                self.target_pos = None
                self.state = STATE_IDLE
            else:
                self._move_towards(tx, ty, dt, map_grid, effect_mgr, sound_engine)

    def _smooth_rotate_turret(self, target_angle, dt):
        diff = (target_angle - self.turret_angle + math.pi) % (2 * math.pi) - math.pi
        self.turret_angle += max(-6.0 * dt, min(6.0 * dt, diff))

    def _move_towards(self, tx, ty, dt, map_grid, effect_mgr, sound_engine):
        dx = tx - self.x
        dy = ty - self.y
        dist = math.hypot(dx, dy)
        if dist < 0.001:
            return

        move_angle = math.atan2(dy, dx)
        diff = (move_angle - self.angle + math.pi) % (2 * math.pi) - math.pi
        self.angle += max(-7.0 * dt, min(7.0 * dt, diff))

        speed_mod = map_grid.get_speed_multiplier(self.x, self.y, self.category)
        step = self.speed * speed_mod * 60.0 * dt

        nx = self.x + math.cos(self.angle) * step
        ny = self.y + math.sin(self.angle) * step

        if map_grid.is_passable(nx, ny, self.category):
            self.x = nx
            self.y = ny
        else:
            # Simple slide along axis if colliding
            if map_grid.is_passable(nx, self.y, self.category):
                self.x = nx
            elif map_grid.is_passable(self.x, ny, self.category):
                self.y = ny

        self.anim_walk += dt * 10.0

        # Leave track marks and play engine sound for tanks and IFVs
        if self.category == "vehicle":
            self.tread_timer += dt
            if self.tread_timer >= 0.15:
                self.tread_timer = 0.0
                effect_mgr.add_track_mark(self.x, self.y, self.angle)
                if self.type_key == "tank":
                    sound_engine.play("tread_rumble", min_interval=0.35)

    def render(self, surface, camera):
        if not camera.is_visible(self.x, self.y, self.hit_radius + 20):
            return

        sx, sy = camera.world_to_screen(self.x, self.y)
        team_color = COLOR_PLAYER if self.faction == FACTION_PLAYER else COLOR_ENEMY
        team_glow = COLOR_PLAYER_GLOW if self.faction == FACTION_PLAYER else COLOR_ENEMY_GLOW

        # 1. Selection Circle
        if self.selected:
            pygame.draw.circle(surface, COLOR_SELECTION, (sx, sy), int(self.hit_radius + 6), 2)
            # Line to destination if moving
            if self.target_pos:
                tx_s, ty_s = camera.world_to_screen(self.target_pos[0], self.target_pos[1])
                pygame.draw.line(surface, (0, 255, 128), (sx, sy), (tx_s, ty_s), 1)
                pygame.draw.circle(surface, (0, 255, 128), (tx_s, ty_s), 3)

        # 2. Rendering by unit type
        if self.category == "infantry":
            # Infantry soldier: helmet, body, rifle
            body_color = (60, 75, 55) if self.faction == FACTION_PLAYER else (80, 50, 45)
            # Legs animation
            leg_off = math.sin(self.anim_walk) * 3 if self.state in (STATE_MOVE, STATE_ATTACK_MOVE) else 0
            lx1 = sx + math.cos(self.angle + 1.5) * 4 + math.cos(self.angle) * leg_off
            ly1 = sy + math.sin(self.angle + 1.5) * 4 + math.sin(self.angle) * leg_off
            lx2 = sx + math.cos(self.angle - 1.5) * 4 - math.cos(self.angle) * leg_off
            ly2 = sy + math.sin(self.angle - 1.5) * 4 - math.sin(self.angle) * leg_off
            pygame.draw.circle(surface, (30, 30, 30), (int(lx1), int(ly1)), 2)
            pygame.draw.circle(surface, (30, 30, 30), (int(lx2), int(ly2)), 2)

            # Torso & helmet
            pygame.draw.circle(surface, body_color, (sx, sy), 6)
            pygame.draw.circle(surface, team_color, (sx, sy), 3)

            # Weapon barrel
            wx = sx + math.cos(self.angle) * (10 - self.recoil)
            wy = sy + math.sin(self.angle) * (10 - self.recoil)
            pygame.draw.line(surface, (20, 20, 20), (sx, sy), (int(wx), int(wy)), 2 if self.type_key == "rifleman" else 4)

        elif self.type_key == "tank":
            # Heavy Tank: Hull rectangle, treads, rotating heavy turret + long cannon
            # Hull
            hull_w, hull_h = 32, 22
            hull_surf = pygame.Surface((hull_w, hull_h), pygame.SRCALPHA)
            pygame.draw.rect(hull_surf, (45, 48, 42), (0, 0, hull_w, hull_h), border_radius=4)
            # Treads on left and right
            pygame.draw.rect(hull_surf, (25, 25, 25), (0, 0, hull_w, 4))
            pygame.draw.rect(hull_surf, (25, 25, 25), (0, hull_h - 4, hull_w, 4))
            # Team color band
            pygame.draw.rect(hull_surf, team_color, (6, 6, hull_w - 12, 10))

            rot_hull = pygame.transform.rotate(hull_surf, -math.degrees(self.angle))
            surface.blit(rot_hull, (sx - rot_hull.get_width() // 2, sy - rot_hull.get_height() // 2))

            # Turret
            turret_len = 22 - self.recoil
            bx = sx + math.cos(self.turret_angle) * turret_len
            by = sy + math.sin(self.turret_angle) * turret_len
            pygame.draw.line(surface, (30, 32, 30), (sx, sy), (int(bx), int(by)), 4)
            pygame.draw.circle(surface, (55, 60, 54), (sx, sy), 8)
            pygame.draw.circle(surface, team_color, (sx, sy), 4)

        elif self.type_key == "ifv":
            # Fast IFV: 8-wheel vehicle with autocannon
            hull_w, hull_h = 28, 18
            hull_surf = pygame.Surface((hull_w, hull_h), pygame.SRCALPHA)
            pygame.draw.rect(hull_surf, (50, 55, 48), (0, 0, hull_w, hull_h), border_radius=3)
            # Wheels
            for wx_pos in (4, 12, 20):
                pygame.draw.circle(hull_surf, (20, 20, 20), (wx_pos, 2), 3)
                pygame.draw.circle(hull_surf, (20, 20, 20), (wx_pos, hull_h - 2), 3)
            pygame.draw.rect(hull_surf, team_color, (6, 5, 16, 8))

            rot_hull = pygame.transform.rotate(hull_surf, -math.degrees(self.angle))
            surface.blit(rot_hull, (sx - rot_hull.get_width() // 2, sy - rot_hull.get_height() // 2))

            # Autocannon
            bx = sx + math.cos(self.turret_angle) * (16 - self.recoil)
            by = sy + math.sin(self.turret_angle) * (16 - self.recoil)
            pygame.draw.line(surface, (25, 25, 25), (sx, sy), (int(bx), int(by)), 2)
            pygame.draw.circle(surface, (60, 65, 60), (sx, sy), 6)

        elif self.type_key == "artillery":
            # Self-Propelled Artillery: Heavy rear-mounted huge cannon
            hull_w, hull_h = 30, 20
            hull_surf = pygame.Surface((hull_w, hull_h), pygame.SRCALPHA)
            pygame.draw.rect(hull_surf, (40, 46, 42), (0, 0, hull_w, hull_h), border_radius=3)
            pygame.draw.rect(hull_surf, (20, 20, 20), (0, 0, hull_w, 4))
            pygame.draw.rect(hull_surf, (20, 20, 20), (0, hull_h - 4, hull_w, 4))
            pygame.draw.rect(hull_surf, team_color, (8, 6, 14, 8))

            rot_hull = pygame.transform.rotate(hull_surf, -math.degrees(self.angle))
            surface.blit(rot_hull, (sx - rot_hull.get_width() // 2, sy - rot_hull.get_height() // 2))

            # Long 155mm Howitzer barrel with muzzle brake
            bar_len = 28 - self.recoil
            bx = sx + math.cos(self.turret_angle) * bar_len
            by = sy + math.sin(self.turret_angle) * bar_len
            pygame.draw.line(surface, (30, 30, 30), (sx, sy), (int(bx), int(by)), 5)
            # Muzzle brake
            pygame.draw.circle(surface, (60, 60, 60), (int(bx), int(by)), 3)
            pygame.draw.circle(surface, (50, 56, 52), (sx, sy), 8)

        elif self.type_key == "aa_vehicle":
            # Anti-Air: Double flak barrels pointing up
            hull_w, hull_h = 28, 18
            hull_surf = pygame.Surface((hull_w, hull_h), pygame.SRCALPHA)
            pygame.draw.rect(hull_surf, (48, 52, 48), (0, 0, hull_w, hull_h), border_radius=3)
            pygame.draw.rect(hull_surf, team_color, (6, 5, 16, 8))

            rot_hull = pygame.transform.rotate(hull_surf, -math.degrees(self.angle))
            surface.blit(rot_hull, (sx - rot_hull.get_width() // 2, sy - rot_hull.get_height() // 2))

            # Twin flak cannons
            perp = self.turret_angle + math.pi * 0.5
            for off in (-3, 3):
                ox = math.cos(perp) * off
                oy = math.sin(perp) * off
                bx = sx + ox + math.cos(self.turret_angle) * (16 - self.recoil)
                by = sy + oy + math.sin(self.turret_angle) * (16 - self.recoil)
                pygame.draw.line(surface, (30, 30, 30), (sx + ox, sy + oy), (int(bx), int(by)), 2)
            pygame.draw.circle(surface, (60, 65, 60), (sx, sy), 7)

        elif self.type_key == "fpv_drone":
            # Kamikaze FPV Drone: Quadcopter frame with spinning rotors
            drone_sz = 14
            # X-Frame
            pygame.draw.line(surface, (30, 30, 30), (sx - 7, sy - 7), (sx + 7, sy + 7), 2)
            pygame.draw.line(surface, (30, 30, 30), (sx - 7, sy + 7), (sx + 7, sy - 7), 2)
            # Spinning rotor circles
            rotor_ang = self.anim_walk * 4.0
            for rx_off, ry_off in ((-7, -7), (7, -7), (-7, 7), (7, 7)):
                r_pos = (sx + rx_off, sy + ry_off)
                pygame.draw.circle(surface, (200, 220, 255), r_pos, 4, 1)
            # Center explosive payload & LED beacon
            pygame.draw.circle(surface, (80, 40, 20), (sx, sy), 4)
            pygame.draw.circle(surface, team_glow, (sx, sy), 2)

        # 3. Health Bar
        bar_w = int(self.hit_radius * 2)
        bar_h = 4
        bar_x = sx - bar_w // 2
        bar_y = sy - self.hit_radius - 8
        pct = max(0.0, self.hp / self.max_hp)
        h_col = COLOR_HEALTH_GREEN if pct > 0.5 else (COLOR_HEALTH_YELLOW if pct > 0.25 else COLOR_HEALTH_RED)

        pygame.draw.rect(surface, (20, 20, 20), (bar_x, bar_y, bar_w, bar_h))
        pygame.draw.rect(surface, h_col, (bar_x, bar_y, int(bar_w * pct), bar_h))
        pygame.draw.rect(surface, (0, 0, 0), (bar_x, bar_y, bar_w, bar_h), 1)
