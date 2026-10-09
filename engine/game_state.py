"""
Central Match State, Entities, Strategic Economy, and Control Groups
"""
import math
import random
import pygame
from engine.config import (
    MAP_WIDTH, MAP_HEIGHT,
    FACTION_PLAYER, FACTION_ENEMY, FACTION_NEUTRAL,
    BUILDING_CONFIGS, UNIT_CONFIGS
)
from engine.map_grid import MapGrid
from engine.fog_of_war import FogOfWar
from engine.sound import SoundEngine
from engine.effects import EffectManager
from engine.combat import CombatEngine
from engine.buildings import Building
from engine.units import Unit
from engine.ai import EnemyAI, DIFFICULTY_NORMAL
from engine.camera import Camera
from engine.ui import UI

class GameState:
    def __init__(self, difficulty=DIFFICULTY_NORMAL):
        self.difficulty = difficulty
        self.reset()

    def reset(self):
        # Systems
        self.map_grid = MapGrid()
        self.fow = FogOfWar()
        self.sound = SoundEngine()
        self.effects = EffectManager()
        self.combat = CombatEngine(self.sound, self.effects, self.map_grid)
        self.camera = Camera(x=0, y=MAP_HEIGHT - 720)  # start near player base
        self.ui = UI()
        self.ai = EnemyAI(difficulty=self.difficulty, base_x=2200, base_y=340)

        # Economy & Units
        self.resources = 750.0
        self.income_rate = (12.0 + 8.0) / 3.0  # HQ (12) + Supply Depot (8) per 3s
        self.max_pop = 20
        self.current_pop = 0

        self.units = []
        self.buildings = []
        self.control_groups = {i: [] for i in range(1, 10)}

        # Match Status
        self.match_time = 0.0
        self.game_over = False
        self.victory = False
        self.battery_saver = False
        self.current_fps = 60

        # Statistics
        self.stats_enemies_killed = 0
        self.stats_units_lost = 0
        self.stats_resources_gathered = 0

        # Last alert position for quick camera jump (Space key)
        self.last_alert_pos = (400, 1550)

        self._init_battlefield()

    def _init_battlefield(self):
        # 1. Player Headquarters (South-West)
        player_hq_x = 380
        player_hq_y = 1580
        self.spawn_building("hq", player_hq_x, player_hq_y, faction=FACTION_PLAYER)
        self.camera.center_on(player_hq_x, player_hq_y)

        # Player Starter Barracks & Supply Depot
        self.spawn_building("barracks", player_hq_x + 120, player_hq_y - 40, faction=FACTION_PLAYER)
        self.spawn_building("supply_depot", player_hq_x - 40, player_hq_y + 110, faction=FACTION_PLAYER)
        self.max_pop += 15

        # Player Starter Squad
        self.spawn_unit("rifleman", player_hq_x + 80, player_hq_y + 40, faction=FACTION_PLAYER)
        self.spawn_unit("rifleman", player_hq_x + 100, player_hq_y + 60, faction=FACTION_PLAYER)
        self.spawn_unit("rpg", player_hq_x + 60, player_hq_y + 80, faction=FACTION_PLAYER)
        self.spawn_unit("ifv", player_hq_x + 140, player_hq_y + 20, faction=FACTION_PLAYER)

        # 2. Enemy Headquarters (North-East)
        enemy_hq_x = 2180
        enemy_hq_y = 340
        self.spawn_building("hq", enemy_hq_x, enemy_hq_y, faction=FACTION_ENEMY)

        # Enemy Starter Units
        self.spawn_unit("rifleman", enemy_hq_x - 80, enemy_hq_y + 40, faction=FACTION_ENEMY)
        self.spawn_unit("rpg", enemy_hq_x - 60, enemy_hq_y + 80, faction=FACTION_ENEMY)
        self.spawn_unit("ifv", enemy_hq_x - 120, enemy_hq_y + 20, faction=FACTION_ENEMY)

        # 3. Contested Resource Derricks on Strategic Crossroads
        for rx, ry in self.map_grid.resource_locations:
            self.spawn_building("resource_derrick", rx, ry, faction=FACTION_NEUTRAL)

    def spawn_building(self, b_type, x, y, faction=FACTION_PLAYER):
        b = Building(b_type, x, y, faction=faction, is_constructed=True)
        self.buildings.append(b)
        return b

    def spawn_unit(self, u_type, x, y, faction=FACTION_PLAYER):
        u = Unit(u_type, x, y, faction=faction)
        self.units.append(u)
        return u

    def update(self, dt):
        if self.game_over:
            return

        self.match_time += dt

        # 1. Update Population count
        player_units = [u for u in self.units if u.faction == FACTION_PLAYER and not u.dead]
        self.current_pop = sum(u.cfg["pop"] for u in player_units)

        # 2. Calculate Strategic Resources & Passive Income
        income_tick = 0.0
        # Headquarters income
        for b in self.buildings:
            if b.faction == FACTION_PLAYER and not b.dead:
                income_tick += b.cfg.get("passive_income", 0)

        # Derricks income
        captured_derricks = sum(1 for b in self.buildings if b.is_capturable and b.faction == FACTION_PLAYER and not b.dead)
        income_tick += captured_derricks * 20.0

        self.income_rate = income_tick / 3.0
        gained = self.income_rate * dt
        self.resources += gained
        self.stats_resources_gathered += gained

        # 3. Fog of War Update
        self.fow.reset_to_explored()
        for ent in player_units + [b for b in self.buildings if b.faction == FACTION_PLAYER and not b.dead]:
            self.fow.reveal(ent.x, ent.y, ent.vision if hasattr(ent, 'vision') else ent.cfg.get("vision", 240))

        # 4. Update Buildings and Production Queues
        all_entities = [u for u in self.units if not u.dead] + [b for b in self.buildings if not b.dead]
        for b in self.buildings:
            if b.dead:
                continue
            ready_unit = b.update(dt, self.combat, self.sound, self.effects, self.units, all_entities)
            if ready_unit:
                # Spawn completed unit
                spawn_x = b.x + b.w * 0.5 + 24
                spawn_y = b.y + b.h * 0.5 + 24
                new_u = self.spawn_unit(ready_unit, spawn_x, spawn_y, faction=b.faction)
                new_u.issue_move(b.rally_point[0], b.rally_point[1])
                if b.faction == FACTION_PLAYER:
                    self.sound.play("unit_ready")
                    self.ui.add_notification(f"{new_u.cfg['name']} готовий до бою!", (0, 229, 255))

        # 5. Update Units
        for u in self.units:
            if not u.dead:
                u.update(dt, self.combat, self.sound, self.effects, self.map_grid, all_entities, self.units)

        # 6. Update Projectiles & Combat
        self.combat.update(dt, all_entities)

        # 7. Update Effects
        self.effects.update(dt)

        # 8. Enemy AI Update
        self.ai.update(dt, self)

        # 9. Clean up dead entities & update statistics
        for u in self.units:
            if u.dead:
                if u.faction == FACTION_ENEMY:
                    self.stats_enemies_killed += 1
                elif u.faction == FACTION_PLAYER:
                    self.stats_units_lost += 1

        self.units = [u for u in self.units if not u.dead]

        # Check buildings destroyed
        for b in self.buildings:
            if b.dead and b.type_key == "hq":
                if b.faction == FACTION_PLAYER:
                    self.game_over = True
                    self.victory = False
                    self.sound.play("defeat")
                elif b.faction == FACTION_ENEMY:
                    self.game_over = True
                    self.victory = True
                    self.sound.play("victory")

        self.buildings = [b for b in self.buildings if not b.dead or b.is_capturable]

        # 10. Update UI
        self.ui.update(dt)

    def handle_left_click(self, sx, sy):
        # 1. Check UI Command Deck buttons
        for btn in self.ui.action_buttons:
            if btn.is_hovered(sx, sy):
                self._execute_action_btn(btn)
                return

        # 2. Check Minimap click
        if self.ui.handle_minimap_click(sx, sy, self.camera):
            return

        # 3. If in Building Placement Mode: Confirm placement!
        if self.ui.placement_building:
            wx, wy = self.camera.screen_to_world(sx, sy)
            cfg = BUILDING_CONFIGS[self.ui.placement_building]
            if self.resources >= cfg["cost"] and self.map_grid.is_passable(wx, wy, "ground"):
                self.spawn_building(self.ui.placement_building, wx, wy, faction=FACTION_PLAYER)
                self.resources -= cfg["cost"]
                if "pop_bonus" in cfg:
                    self.max_pop += cfg["pop_bonus"]
                self.sound.play("order_ack")
                self.ui.add_notification(f"Будівництво: {cfg['name']}", (0, 255, 128))
                self.ui.placement_building = None
            return

        # 4. Normal Battlefield Entity Selection
        wx, wy = self.camera.screen_to_world(sx, sy)
        # Deselect all
        for u in self.units:
            u.selected = False
        for b in self.buildings:
            b.selected = False

        # Select unit first
        clicked_unit = None
        for u in self.units:
            if u.faction == FACTION_PLAYER and not u.dead:
                if math.hypot(u.x - wx, u.y - wy) <= u.hit_radius + 4:
                    clicked_unit = u
                    break

        if clicked_unit:
            clicked_unit.selected = True
            self.sound.play("order_ack", min_interval=0.1)
            return

        # Select building
        clicked_b = None
        for b in self.buildings:
            if not b.dead and math.hypot(b.x - wx, b.y - wy) <= b.hit_radius:
                clicked_b = b
                break

        if clicked_b:
            clicked_b.selected = True
            self.sound.play("order_ack", min_interval=0.1)

    def handle_selection_box_finish(self, rect):
        """Select all friendly player units enclosed in selection drag rectangle."""
        if not rect or rect.width < 8 or rect.height < 8:
            return

        # Deselect all
        for u in self.units:
            u.selected = False
        for b in self.buildings:
            b.selected = False

        selected_any = False
        for u in self.units:
            if u.faction == FACTION_PLAYER and not u.dead:
                sx, sy = self.camera.world_to_screen(u.x, u.y)
                if rect.collidepoint(sx, sy):
                    u.selected = True
                    selected_any = True

        if selected_any:
            self.sound.play("order_ack", min_interval=0.1)

    def handle_right_click(self, sx, sy):
        # Cancel placement mode if active
        if self.ui.placement_building:
            self.ui.placement_building = None
            return

        wx, wy = self.camera.screen_to_world(sx, sy)
        selected_player_units = [u for u in self.units if u.selected and u.faction == FACTION_PLAYER and not u.dead]
        selected_player_bld = next((b for b in self.buildings if b.selected and b.faction == FACTION_PLAYER and not b.dead), None)

        # Set rally point for selected building
        if selected_player_bld and not selected_player_units:
            selected_player_bld.rally_point = (wx, wy)
            self.sound.play("order_ack")
            self.ui.add_notification("Точку збору встановлено", (0, 255, 128))
            return

        if not selected_player_units:
            return

        # Check if right-clicked on an enemy unit/building -> Attack order!
        enemy_target = None
        for ent in self.units + self.buildings:
            if ent.faction == FACTION_ENEMY and not getattr(ent, 'dead', False):
                if math.hypot(ent.x - wx, ent.y - wy) <= getattr(ent, 'hit_radius', 20):
                    enemy_target = ent
                    break

        if enemy_target:
            for u in selected_player_units:
                u.issue_attack(enemy_target)
            self.sound.play("order_ack")
            self.ui.add_notification("Наказ: Атакувати ціль!", (255, 100, 100))
            return

        # Check if right-clicked on a capturable derrick -> Capture order!
        for b in self.buildings:
            if b.is_capturable and not b.dead:
                if math.hypot(b.x - wx, b.y - wy) <= b.hit_radius + 15:
                    for u in selected_player_units:
                        if u.cfg.get("can_capture", False):
                            u.issue_capture(b)
                        else:
                            u.issue_move(b.x + random.uniform(-40, 40), b.y + random.uniform(-40, 40))
                    self.sound.play("order_ack")
                    self.ui.add_notification("Наказ: Захопити вишку!", (255, 215, 0))
                    return

        # Move order with tactical formation spread
        count = len(selected_player_units)
        cols = int(math.ceil(math.sqrt(count)))
        spacing = 30.0

        for i, u in enumerate(selected_player_units):
            row = i // cols
            col = i % cols
            ox = (col - cols * 0.5) * spacing
            oy = (row - cols * 0.5) * spacing
            u.issue_move(wx + ox, wy + oy)

        self.sound.play("order_ack")

    def _execute_action_btn(self, btn):
        act = btn.action_id
        if act.startswith("train_"):
            unit_key = act.replace("train_", "")
            selected_bld = next((b for b in self.buildings if b.selected and b.faction == FACTION_PLAYER), None)
            if selected_bld:
                cfg = UNIT_CONFIGS[unit_key]
                if self.resources >= cfg["cost"] and (self.current_pop + cfg["pop"]) <= self.max_pop:
                    if selected_bld.enqueue_unit(unit_key, self.resources):
                        self.resources -= cfg["cost"]
                        self.sound.play("order_ack")
                elif (self.current_pop + cfg["pop"]) > self.max_pop:
                    self.ui.add_notification("Ліміт військ вичерпано! Збудуйте Склад.", (255, 60, 60))
                else:
                    self.ui.add_notification("Недостатньо припасів!", (255, 60, 60))

        elif act.startswith("build_"):
            b_key = act.replace("build_", "")
            self.ui.placement_building = b_key
            self.sound.play("order_ack")
            self.ui.add_notification("Оберіть місце на карті для будівництва", (255, 215, 0))

        elif act == "order_attack":
            # Set selected units to attack-move towards mouse or current target
            for u in self.units:
                if u.selected and u.faction == FACTION_PLAYER:
                    u.state = "attack_move"
            self.sound.play("order_ack")

        elif act == "order_stop":
            for u in self.units:
                if u.selected and u.faction == FACTION_PLAYER:
                    u.issue_stop()
            self.sound.play("order_ack")

    def handle_key_down(self, key):
        mods = pygame.key.get_mods()

        # Restart match
        if self.game_over and (key == pygame.K_SPACE or key == pygame.K_r):
            self.reset()
            return

        # Control Groups 1..9
        if pygame.K_1 <= key <= pygame.K_9:
            group_idx = key - pygame.K_0
            if mods & pygame.KMOD_CTRL:
                # Assign selected units to group
                self.control_groups[group_idx] = [
                    u for u in self.units if u.selected and u.faction == FACTION_PLAYER and not u.dead
                ]
                self.ui.add_notification(f"Загін {group_idx} сформовано ({len(self.control_groups[group_idx])} од.)", (0, 255, 128))
                self.sound.play("order_ack")
            else:
                # Select group
                for u in self.units:
                    u.selected = False
                for u in self.control_groups[group_idx]:
                    if not u.dead:
                        u.selected = True
                if self.control_groups[group_idx]:
                    self.sound.play("order_ack")

        # Stop (S)
        elif key == pygame.K_s:
            for u in self.units:
                if u.selected and u.faction == FACTION_PLAYER:
                    u.issue_stop()

        # Attack-Move (A)
        elif key == pygame.K_a:
            mx, my = pygame.mouse.get_pos()
            wx, wy = self.camera.screen_to_world(mx, my)
            for u in self.units:
                if u.selected and u.faction == FACTION_PLAYER:
                    u.issue_attack_move(wx, wy)

        # Home / HQ Camera Jump (H)
        elif key == pygame.K_h:
            player_hq = next((b for b in self.buildings if b.faction == FACTION_PLAYER and b.type_key == "hq"), None)
            if player_hq:
                self.camera.center_on(player_hq.x, player_hq.y)

        # Space (Jump to last combat event / HQ)
        elif key == pygame.K_SPACE:
            self.camera.center_on(self.last_alert_pos[0], self.last_alert_pos[1])

        # Battery Saver Toggle (F)
        elif key == pygame.K_f:
            self.battery_saver = not self.battery_saver
            mode_txt = "РЕЖИМ ЕКОНОМІЇ БАТАРЕЇ (30 FPS)" if self.battery_saver else "МАКСИМАЛЬНА ПРОДУКТИВНІСТЬ (60 FPS)"
            self.ui.add_notification(mode_txt, (0, 255, 128))

        # Audio Mute Toggle (M)
        elif key == pygame.K_m:
            is_on = self.sound.toggle_sound()
            self.ui.add_notification(f"Звук: {'УВІМКНЕНО' if is_on else 'ВИМКНЕНО'}", (255, 215, 0))

    def render(self, surface):
        # 1. Render map background (terrain, roads, rivers, trees)
        self.map_grid.render(surface, self.camera)

        # 2. Render ground effects (craters, track marks)
        self.effects.render_ground(surface, self.camera)

        # 3. Render buildings
        for b in self.buildings:
            if not b.dead:
                # Enemy building visible if explored or in active LOS
                if b.faction == FACTION_ENEMY:
                    if self.fow.is_visible(b.x, b.y):
                        b.render(surface, self.camera, is_explored_only=False)
                    elif self.fow.is_explored(b.x, b.y):
                        b.render(surface, self.camera, is_explored_only=True)
                else:
                    b.render(surface, self.camera, is_explored_only=False)

        # 4. Render units
        for u in self.units:
            if not u.dead:
                # Enemy units only visible in active line of sight!
                if u.faction == FACTION_ENEMY and not self.fow.is_visible(u.x, u.y):
                    continue
                u.render(surface, self.camera)

        # 5. Render projectiles
        self.combat.render(surface, self.camera)

        # 6. Render air particles & smoke
        self.effects.render_air(surface, self.camera, self.ui.font_sub)

        # 7. Render Fog of War Shroud
        self.fow.render(surface, self.camera)

        # 8. Render UI, Minimap, and HUD
        self.ui.render(surface, self, self.camera)
