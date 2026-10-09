"""
Tactical RTS Combat System: Ballistics, Projectiles, Armor, and Damage
"""
import math
import random
import pygame

class Projectile:
    def __init__(self, start_x, start_y, target, damage, speed, p_type="bullet",
                 splash_radius=0, attacker_faction="player", target_pos=None):
        self.x = float(start_x)
        self.y = float(start_y)
        self.start_x = float(start_x)
        self.start_y = float(start_y)
        self.target = target
        self.damage = damage
        self.speed = speed
        self.type = p_type
        self.splash_radius = splash_radius
        self.faction = attacker_faction
        self.dead = False

        if target_pos:
            self.tx, self.ty = float(target_pos[0]), float(target_pos[1])
        elif target:
            self.tx, self.ty = float(target.x), float(target.y)
        else:
            self.tx, self.ty = self.x, self.y

        self.total_dist = math.hypot(self.tx - self.start_x, self.ty - self.start_y)
        self.dist_traveled = 0.0

        # Artillery parabola settings
        if self.type == "artillery":
            self.arc_height = min(220.0, max(80.0, self.total_dist * 0.4))
            self.whistle_played = False

    def update(self, dt, effect_mgr, sound_engine):
        # Update target position if target is still alive and not artillery
        if self.type != "artillery" and self.target and not getattr(self.target, 'dead', True):
            self.tx, self.ty = float(self.target.x), float(self.target.y)

        dx = self.tx - self.x
        dy = self.ty - self.y
        dist = math.hypot(dx, dy)

        step = self.speed * 60.0 * dt
        self.dist_traveled += step

        if self.type == "artillery":
            progress = min(1.0, self.dist_traveled / max(1.0, self.total_dist))
            if progress > 0.65 and not getattr(self, 'whistle_played', False):
                sound_engine.play("artillery_whistle")
                self.whistle_played = True

        if self.type == "rocket":
            # Add smoke trail behind rocket
            effect_mgr.add_rocket_smoke(self.x, self.y)

        if dist <= step or (self.type == "artillery" and self.dist_traveled >= self.total_dist):
            self.x = self.tx
            self.y = self.ty
            self.dead = True
        else:
            self.x += (dx / dist) * step
            self.y += (dy / dist) * step

    def get_render_pos(self):
        """For artillery, returns (visual_x, visual_y, shadow_x, shadow_y)."""
        if self.type == "artillery":
            progress = min(1.0, self.dist_traveled / max(1.0, self.total_dist))
            altitude = 4.0 * self.arc_height * progress * (1.0 - progress)
            return self.x, self.y - altitude, self.x, self.y
        return self.x, self.y, self.x, self.y

    def render(self, surface, camera):
        vx, vy, sx, sy = self.get_render_pos()
        if not camera.is_visible(vx, vy, 30):
            return

        screen_vx, screen_vy = camera.world_to_screen(vx, vy)
        screen_sx, screen_sy = camera.world_to_screen(sx, sy)

        if self.type == "artillery":
            # Ground shadow
            pygame.draw.circle(surface, (15, 18, 15), (screen_sx, screen_sy), 4)
            # High-arching shell
            pygame.draw.circle(surface, (230, 230, 230), (screen_vx, screen_vy), 4)
            pygame.draw.circle(surface, (255, 180, 50), (screen_vx, screen_vy), 2)
        elif self.type == "rocket":
            # Rocket head and fire
            pygame.draw.circle(surface, (255, 200, 50), (screen_vx, screen_vy), 3)
            pygame.draw.circle(surface, (255, 60, 20), (screen_vx, screen_vy), 2)
        elif self.type == "cannon":
            pygame.draw.circle(surface, (255, 235, 150), (screen_vx, screen_vy), 4)
            pygame.draw.circle(surface, (255, 120, 20), (screen_vx, screen_vy), 2)
        elif self.type == "flak":
            pygame.draw.circle(surface, (255, 255, 200), (screen_vx, screen_vy), 3)
        else:  # bullet / autocannon tracer
            pygame.draw.circle(surface, (255, 240, 180), (screen_vx, screen_vy), 2)

class CombatEngine:
    def __init__(self, sound_engine, effect_mgr, map_grid):
        self.sound = sound_engine
        self.effects = effect_mgr
        self.map_grid = map_grid
        self.projectiles = []

    def spawn_projectile(self, start_x, start_y, target, unit_cfg, faction, target_pos=None):
        p_type = unit_cfg.get("weapon_type", "bullet")
        speed = unit_cfg.get("projectile_speed", 18)
        damage = unit_cfg.get("damage", 15)
        splash = unit_cfg.get("splash", 0)

        proj = Projectile(start_x, start_y, target, damage, speed,
                          p_type=p_type, splash_radius=splash,
                          attacker_faction=faction, target_pos=target_pos)
        self.projectiles.append(proj)

        # Muzzle flash
        angle = math.atan2(proj.ty - start_y, proj.tx - start_x)
        self.effects.add_muzzle_flash(start_x, start_y, angle)

        # Firing sound
        if p_type == "bullet":
            self.sound.play("rifle_shot", min_interval=0.08)
        elif p_type == "autocannon":
            self.sound.play("autocannon", min_interval=0.12)
        elif p_type == "rocket":
            self.sound.play("rpg_launch", min_interval=0.2)
        elif p_type == "cannon":
            self.sound.play("tank_cannon", min_interval=0.25)
        elif p_type == "artillery":
            self.sound.play("artillery_shot", min_interval=0.3)
        elif p_type == "flak":
            self.sound.play("flak_shot", min_interval=0.15)

    def update(self, dt, all_entities):
        for p in self.projectiles:
            p.update(dt, self.effects, self.sound)
            if p.dead:
                self._resolve_impact(p, all_entities)

        self.projectiles = [p for p in self.projectiles if not p.dead]

    def _resolve_impact(self, proj, all_entities):
        tx, ty = proj.tx, proj.ty

        if proj.splash_radius > 0:
            # Splash damage to all hostile entities in radius
            is_large = proj.splash_radius >= 40
            self.effects.add_explosion(tx, ty, radius=proj.splash_radius, is_large=is_large)
            if is_large:
                self.sound.play("explosion_large", min_interval=0.15)
            else:
                self.sound.play("explosion_small", min_interval=0.1)

            for ent in all_entities:
                if ent.faction == proj.faction or getattr(ent, 'dead', False):
                    continue
                d = math.hypot(ent.x - tx, ent.y - ty)
                hit_radius = proj.splash_radius + getattr(ent, 'hit_radius', 16)
                if d <= hit_radius:
                    falloff = max(0.35, 1.0 - (d / hit_radius))
                    raw_dmg = proj.damage * falloff
                    self._apply_damage(ent, raw_dmg)
        else:
            # Single target direct hit
            self.effects.add_explosion(tx, ty, radius=12, is_large=False)
            self.sound.play("explosion_small", min_interval=0.12)
            if proj.target and not getattr(proj.target, 'dead', False):
                self._apply_damage(proj.target, proj.damage)

    def _apply_damage(self, entity, raw_dmg):
        # Forest cover mitigation for infantry
        if getattr(entity, 'category', '') == 'infantry':
            cover = self.map_grid.get_cover_defense_bonus(entity.x, entity.y, 'infantry')
            raw_dmg *= (1.0 - cover)

        final_dmg = max(1, int(round(raw_dmg)))
        entity.take_damage(final_dmg)
        self.effects.add_floating_text(entity.x, entity.y - 12, f"-{final_dmg}", (255, 90, 80))

    def render(self, surface, camera):
        for p in self.projectiles:
            p.render(surface, camera)
