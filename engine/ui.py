"""
Tactical RTS User Interface: Minimap, Command Deck, Building Placement,
Selection Box, and Combat HUD
"""
import math
import pygame
from engine.config import (
    WINDOW_WIDTH, WINDOW_HEIGHT, MAP_WIDTH, MAP_HEIGHT,
    MINIMAP_W, MINIMAP_H, MINIMAP_X, MINIMAP_Y,
    COLOR_UI_PANEL, COLOR_UI_BORDER, COLOR_UI_TEXT, COLOR_UI_ACCENT,
    COLOR_PLAYER, COLOR_PLAYER_GLOW, COLOR_ENEMY, COLOR_ENEMY_GLOW,
    COLOR_NEUTRAL, COLOR_HEALTH_GREEN, COLOR_HEALTH_YELLOW, COLOR_HEALTH_RED,
    COLOR_SELECTION, FACTION_PLAYER, FACTION_ENEMY, FACTION_NEUTRAL,
    BUILDING_CONFIGS, UNIT_CONFIGS
)

class Button:
    def __init__(self, rect, text, subtext="", icon_key="", cost=0, action_id=""):
        self.rect = pygame.Rect(rect)
        self.text = text
        self.subtext = subtext
        self.icon_key = icon_key
        self.cost = cost
        self.action_id = action_id
        self.hovered = False

    def is_hovered(self, mx, my):
        self.hovered = self.rect.collidepoint(mx, my)
        return self.hovered

class UI:
    def __init__(self):
        self.hud_height = 140
        self.deck_rect = pygame.Rect(0, WINDOW_HEIGHT - self.hud_height, WINDOW_WIDTH, self.hud_height)
        self.top_bar_rect = pygame.Rect(0, 0, WINDOW_WIDTH, 36)

        # Fonts
        pygame.font.init()
        self.font_title = pygame.font.SysFont("Arial", 16, bold=True)
        self.font_main = pygame.font.SysFont("Arial", 13, bold=True)
        self.font_sub = pygame.font.SysFont("Arial", 11)
        self.font_hud = pygame.font.SysFont("Arial", 14, bold=True)
        self.font_big = pygame.font.SysFont("Arial", 32, bold=True)

        # Minimap surface
        self.minimap_rect = pygame.Rect(MINIMAP_X, MINIMAP_Y, MINIMAP_W, MINIMAP_H)
        self.minimap_scale_x = MINIMAP_W / float(MAP_WIDTH)
        self.minimap_scale_y = MINIMAP_H / float(MAP_HEIGHT)

        # Selection Drag Box
        self.drag_start = None
        self.is_dragging = False

        # Building Placement Mode
        self.placement_building = None  # b_type key

        # Buttons cache
        self.action_buttons = []
        self.notifications = []  # (text, color, time_left)

    def add_notification(self, text, color=(255, 235, 59), duration=3.5):
        self.notifications.append({"text": text, "color": color, "time": duration})

    def update(self, dt):
        for n in self.notifications:
            n["time"] -= dt
        self.notifications = [n for n in self.notifications if n["time"] > 0]

    def handle_minimap_click(self, mx, my, camera):
        """If mouse clicked inside minimap, jump camera to world coordinate."""
        if self.minimap_rect.collidepoint(mx, my):
            rel_x = mx - self.minimap_rect.left
            rel_y = my - self.minimap_rect.top
            wx = rel_x / self.minimap_scale_x
            wy = rel_y / self.minimap_scale_y
            camera.center_on(wx, wy)
            return True
        return False

    def start_selection_drag(self, sx, sy):
        if sy < WINDOW_HEIGHT - self.hud_height and not self.minimap_rect.collidepoint(sx, sy):
            self.drag_start = (sx, sy)
            self.is_dragging = True

    def get_selection_rect(self, current_mouse):
        if not self.is_dragging or not self.drag_start:
            return None
        x0, y0 = self.drag_start
        x1, y1 = current_mouse
        x = min(x0, x1)
        y = min(y0, y1)
        w = abs(x1 - x0)
        h = abs(y1 - y0)
        return pygame.Rect(x, y, w, h)

    def render(self, surface, game_state, camera):
        # 1. Selection Box Dragging
        if self.is_dragging and self.drag_start:
            rect = self.get_selection_rect(pygame.mouse.get_pos())
            if rect and rect.width > 2 and rect.height > 2:
                box_surf = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
                box_surf.fill((0, 255, 128, 45))
                surface.blit(box_surf, (rect.x, rect.y))
                pygame.draw.rect(surface, COLOR_SELECTION, rect, 1)

        # 2. Building Placement Ghost
        if self.placement_building:
            self._render_placement_ghost(surface, game_state, camera)

        # 3. Top Status Bar
        self._render_top_bar(surface, game_state)

        # 4. Bottom Command Deck
        self._render_command_deck(surface, game_state)

        # 5. Minimap / Radar
        self._render_minimap(surface, game_state, camera)

        # 6. Notifications
        self._render_notifications(surface)

        # 7. Match End Screen (Victory / Defeat)
        if game_state.game_over:
            self._render_game_over(surface, game_state)

    def _render_top_bar(self, surface, game_state):
        pygame.draw.rect(surface, (16, 20, 24), self.top_bar_rect)
        pygame.draw.line(surface, COLOR_UI_BORDER, (0, 36), (WINDOW_WIDTH, 36), 1)

        # Resources & Income
        res_text = f"📦 ПРИПАСИ: {int(game_state.resources)}  (+{int(game_state.income_rate)}/с)"
        r_surf = self.font_hud.render(res_text, True, (255, 215, 0))
        surface.blit(r_surf, (20, 9))

        # Army Limit
        pop_color = (255, 100, 100) if game_state.current_pop >= game_state.max_pop else (200, 240, 255)
        pop_text = f"👥 ВІЙСЬКА: {game_state.current_pop} / {game_state.max_pop}"
        p_surf = self.font_hud.render(pop_text, True, pop_color)
        surface.blit(p_surf, (330, 9))

        # Strategic Derricks Captured
        derricks_captured = sum(1 for b in game_state.buildings if b.is_capturable and b.faction == FACTION_PLAYER)
        total_derricks = sum(1 for b in game_state.buildings if b.is_capturable)
        d_text = f"🚩 ВИШКИ: {derricks_captured} / {total_derricks}"
        d_surf = self.font_hud.render(d_text, True, (0, 229, 255))
        surface.blit(d_surf, (550, 9))

        # Game Clock & Mode
        m = int(game_state.match_time // 60)
        s = int(game_state.match_time % 60)
        clock_text = f"⏱️ ЧАС: {m:02d}:{s:02d} | FPS: {game_state.current_fps} ({'ECO 30' if game_state.battery_saver else '60'})"
        c_surf = self.font_sub.render(clock_text, True, (180, 195, 205))
        surface.blit(c_surf, (WINDOW_WIDTH - 280, 11))

    def _render_command_deck(self, surface, game_state):
        deck_surf = pygame.Surface((self.deck_rect.width, self.deck_rect.height), pygame.SRCALPHA)
        deck_surf.fill(COLOR_UI_PANEL)
        surface.blit(deck_surf, (self.deck_rect.x, self.deck_rect.y))
        pygame.draw.line(surface, COLOR_UI_BORDER, (0, self.deck_rect.y), (WINDOW_WIDTH, self.deck_rect.y), 2)

        # Clear buttons for this frame
        self.action_buttons = []
        selected_units = [u for u in game_state.units if u.selected and u.faction == FACTION_PLAYER]
        selected_building = next((b for b in game_state.buildings if b.selected and b.faction == FACTION_PLAYER), None)

        # Left Section: Selected Entity Info
        info_x = 24
        info_y = self.deck_rect.y + 16

        if selected_units:
            u = selected_units[0]
            count_str = f" ({len(selected_units)} од.)" if len(selected_units) > 1 else ""
            title_surf = self.font_title.render(f"{u.cfg['name']}{count_str}", True, (255, 255, 255))
            surface.blit(title_surf, (info_x, info_y))

            # HP Bar
            bar_w = 180
            bar_h = 8
            pct = max(0.0, u.hp / u.max_hp)
            h_col = COLOR_HEALTH_GREEN if pct > 0.5 else (COLOR_HEALTH_YELLOW if pct > 0.25 else COLOR_HEALTH_RED)
            pygame.draw.rect(surface, (30, 30, 30), (info_x, info_y + 24, bar_w, bar_h))
            pygame.draw.rect(surface, h_col, (info_x, info_y + 24, int(bar_w * pct), bar_h))
            pygame.draw.rect(surface, (0, 0, 0), (info_x, info_y + 24, bar_w, bar_h), 1)

            hp_txt = self.font_sub.render(f"Міцність: {int(u.hp)} / {u.max_hp}", True, (200, 200, 200))
            surface.blit(hp_txt, (info_x + bar_w + 10, info_y + 22))

            stats_txt = f"Урон: {u.damage} | Дистанція: {u.range} | Швидкість: {u.speed}"
            s_surf = self.font_sub.render(stats_txt, True, (160, 185, 200))
            surface.blit(s_surf, (info_x, info_y + 38))

            desc_txt = self.font_sub.render(u.cfg.get("description", "")[:55], True, (140, 160, 175))
            surface.blit(desc_txt, (info_x, info_y + 56))

            # Command Action Buttons
            btn_y = self.deck_rect.y + 82
            self._add_action_btn(info_x, btn_y, 80, 36, "АТАКА", "[A]", "order_attack")
            self._add_action_btn(info_x + 90, btn_y, 80, 36, "СТОП", "[S]", "order_stop")

        elif selected_building:
            b = selected_building
            title_surf = self.font_title.render(b.cfg["name"], True, (255, 255, 255))
            surface.blit(title_surf, (info_x, info_y))

            # HP Bar
            bar_w = 180
            pct = max(0.0, b.hp / b.max_hp)
            h_col = COLOR_HEALTH_GREEN if pct > 0.5 else (COLOR_HEALTH_YELLOW if pct > 0.25 else COLOR_HEALTH_RED)
            pygame.draw.rect(surface, (30, 30, 30), (info_x, info_y + 24, bar_w, 8))
            pygame.draw.rect(surface, h_col, (info_x, info_y + 24, int(bar_w * pct), 8))

            hp_txt = self.font_sub.render(f"Міцність: {int(b.hp)} / {b.max_hp}", True, (200, 200, 200))
            surface.blit(hp_txt, (info_x + bar_w + 10, info_y + 22))

            # Production options for this building
            if "produces" in b.cfg:
                bx = 360
                by = self.deck_rect.y + 16
                for unit_key in b.cfg["produces"]:
                    ucfg = UNIT_CONFIGS[unit_key]
                    self._add_action_btn(bx, by, 130, 52, ucfg["name"], f"📦 {ucfg['cost']} | ⏱️ {int(ucfg['build_time'])}с", f"train_{unit_key}", cost=ucfg["cost"])
                    bx += 140

                # Queue display
                q_text = f"Черга виробництва: {len(b.queue) + (1 if b.current_unit else 0)} / 5"
                q_surf = self.font_sub.render(q_text, True, (0, 229, 255))
                surface.blit(q_surf, (360, self.deck_rect.y + 78))
            else:
                desc_surf = self.font_sub.render(b.cfg.get("description", ""), True, (160, 185, 200))
                surface.blit(desc_surf, (info_x, info_y + 40))

        else:
            # Base Construction Deck (when nothing specific is selected)
            h_surf = self.font_title.render("БУДІВНИЦТВО БАЗИ:", True, (255, 215, 0))
            surface.blit(h_surf, (info_x, info_y))

            bx = 200
            by = self.deck_rect.y + 14
            build_types = [
                ("barracks", "Казарми"),
                ("war_factory", "Завод техніки"),
                ("drone_bay", "БПЛА станція"),
                ("supply_depot", "Склад"),
                ("bunker", "Кулеметний ДОТ"),
                ("missile_turret", "Ракетна турель")
            ]

            for i, (b_type, label) in enumerate(build_types):
                row = i // 3
                col = i % 3
                cfg = BUILDING_CONFIGS[b_type]
                btn_x = bx + col * 145
                btn_y = by + row * 58
                self._add_action_btn(btn_x, btn_y, 135, 50, label, f"📦 {cfg['cost']}", f"build_{b_type}", cost=cfg["cost"])

        # Render all action buttons
        mx, my = pygame.mouse.get_pos()
        for btn in self.action_buttons:
            is_hov = btn.is_hovered(mx, my)
            can_afford = game_state.resources >= btn.cost
            bg_col = (45, 60, 75) if is_hov else (30, 36, 42)
            if not can_afford and btn.cost > 0:
                bg_col = (35, 30, 30)

            pygame.draw.rect(surface, bg_col, btn.rect, border_radius=4)
            border_col = COLOR_UI_ACCENT if is_hov else COLOR_UI_BORDER
            pygame.draw.rect(surface, border_col, btn.rect, 1, border_radius=4)

            t_col = (255, 255, 255) if can_afford else (160, 140, 140)
            txt_s = self.font_main.render(btn.text, True, t_col)
            surface.blit(txt_s, (btn.rect.x + 8, btn.rect.y + 6))

            if btn.subtext:
                sub_col = (255, 215, 0) if can_afford else (180, 100, 100)
                sub_s = self.font_sub.render(btn.subtext, True, sub_col)
                surface.blit(sub_s, (btn.rect.x + 8, btn.rect.y + 26))

    def _add_action_btn(self, x, y, w, h, text, subtext, action_id, cost=0):
        btn = Button((x, y, w, h), text, subtext=subtext, cost=cost, action_id=action_id)
        self.action_buttons.append(btn)

    def _render_minimap(self, surface, game_state, camera):
        # Background frame
        pygame.draw.rect(surface, (12, 14, 16), self.minimap_rect)
        pygame.draw.rect(surface, COLOR_UI_BORDER, self.minimap_rect, 2)

        # Draw terrain representation on minimap
        # Draw rivers & bridges
        map_g = game_state.map_grid
        for x in range(0, map_g.cols, 2):
            for y in range(0, map_g.rows, 2):
                t = map_g.tiles[x, y]
                mx = self.minimap_rect.left + int(x * map_g.tile_size * self.minimap_scale_x)
                my = self.minimap_rect.top + int(y * map_g.tile_size * self.minimap_scale_y)
                if t == 3:  # water
                    pygame.draw.rect(surface, (40, 80, 120), (mx, my, 2, 2))
                elif t == 2 or t == 4:  # road or bridge
                    pygame.draw.rect(surface, (80, 80, 85), (mx, my, 2, 2))

        # Fog of war mask on minimap
        fow = game_state.fow
        for gx in range(0, fow.cols, 2):
            for gy in range(0, fow.rows, 2):
                val = fow.grid[gx, gy]
                if val == 0:  # unexplored
                    mx = self.minimap_rect.left + int(gx * fow.cell_size * self.minimap_scale_x)
                    my = self.minimap_rect.top + int(gy * fow.cell_size * self.minimap_scale_y)
                    pygame.draw.rect(surface, (8, 10, 12), (mx, my, 3, 3))

        # Buildings on minimap
        for b in game_state.buildings:
            if b.dead:
                continue
            if b.faction == FACTION_ENEMY and not fow.is_explored(b.x, b.y):
                continue
            mx = self.minimap_rect.left + int(b.x * self.minimap_scale_x)
            my = self.minimap_rect.top + int(b.y * self.minimap_scale_y)
            col = COLOR_PLAYER if b.faction == FACTION_PLAYER else (COLOR_ENEMY if b.faction == FACTION_ENEMY else COLOR_NEUTRAL)
            pygame.draw.rect(surface, col, (mx - 2, my - 2, 5, 5))

        # Units on minimap
        for u in game_state.units:
            if u.dead:
                continue
            if u.faction == FACTION_ENEMY and not fow.is_visible(u.x, u.y):
                continue
            mx = self.minimap_rect.left + int(u.x * self.minimap_scale_x)
            my = self.minimap_rect.top + int(u.y * self.minimap_scale_y)
            col = COLOR_PLAYER_GLOW if u.faction == FACTION_PLAYER else COLOR_ENEMY_GLOW
            pygame.draw.circle(surface, col, (mx, my), 2)

        # Camera viewport boundary rectangle
        cam_x = self.minimap_rect.left + int(camera.x * self.minimap_scale_x)
        cam_y = self.minimap_rect.top + int(camera.y * self.minimap_scale_y)
        cam_w = int(WINDOW_WIDTH * self.minimap_scale_x)
        cam_h = int((WINDOW_HEIGHT - self.hud_height) * self.minimap_scale_y)
        pygame.draw.rect(surface, (255, 255, 255), (cam_x, cam_y, cam_w, cam_h), 1)

    def _render_placement_ghost(self, surface, game_state, camera):
        mx, my = pygame.mouse.get_pos()
        wx, wy = camera.screen_to_world(mx, my)
        cfg = BUILDING_CONFIGS[self.placement_building]
        bw, bh = cfg["size"]

        # Check validity (passable and enough money)
        can_place = True
        if game_state.resources < cfg["cost"]:
            can_place = False
        if not game_state.map_grid.is_passable(wx, wy, "ground"):
            can_place = False

        # Check overlapping with other buildings
        for b in game_state.buildings:
            if not b.dead and math.hypot(b.x - wx, b.y - wy) < (b.hit_radius + max(bw, bh) * 0.5):
                can_place = False
                break

        sx, sy = camera.world_to_screen(wx - bw * 0.5, wy - bh * 0.5)
        ghost_color = (0, 255, 128, 120) if can_place else (255, 40, 40, 120)
        ghost_surf = pygame.Surface((bw, bh), pygame.SRCALPHA)
        ghost_surf.fill(ghost_color)
        surface.blit(ghost_surf, (sx, sy))
        pygame.draw.rect(surface, (0, 255, 128) if can_place else (255, 40, 40), (sx, sy, bw, bh), 2)

    def _render_notifications(self, surface):
        y = 52
        for n in self.notifications:
            txt_s = self.font_title.render(n["text"], True, n["color"])
            bg_rect = pygame.Rect(WINDOW_WIDTH // 2 - txt_s.get_width() // 2 - 12, y - 2, txt_s.get_width() + 24, txt_s.get_height() + 4)
            pygame.draw.rect(surface, (16, 20, 24, 210), bg_rect, border_radius=4)
            pygame.draw.rect(surface, COLOR_UI_BORDER, bg_rect, 1, border_radius=4)
            surface.blit(txt_s, (WINDOW_WIDTH // 2 - txt_s.get_width() // 2, y))
            y += 28

    def _render_game_over(self, surface, game_state):
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        overlay.fill((10, 12, 14, 210))
        surface.blit(overlay, (0, 0))

        is_win = game_state.victory
        title_text = "ПЕРЕМОГА! РУБІЖ ЗАХИЩЕНО!" if is_win else "ПОРАЗКА! БАЗУ ЗНИЩЕНО!"
        title_col = (0, 255, 128) if is_win else (255, 50, 50)
        t_surf = self.font_big.render(title_text, True, title_col)
        surface.blit(t_surf, (WINDOW_WIDTH // 2 - t_surf.get_width() // 2, 220))

        sub = "Всі ворожі командні сили нейтралізовано." if is_win else "Головний командний пункт зруйновано."
        s_surf = self.font_hud.render(sub, True, (220, 230, 240))
        surface.blit(s_surf, (WINDOW_WIDTH // 2 - s_surf.get_width() // 2, 275))

        stats = [
            f"Час битви: {int(game_state.match_time // 60)} хв {int(game_state.match_time % 60)} сек",
            f"Знищено ворожих одиниць: {game_state.stats_enemies_killed}",
            f"Власні втрати: {game_state.stats_units_lost}",
            f"Видобуто припасів: {int(game_state.stats_resources_gathered)}"
        ]
        for idx, line in enumerate(stats):
            line_surf = self.font_main.render(line, True, (200, 215, 225))
            surface.blit(line_surf, (WINDOW_WIDTH // 2 - line_surf.get_width() // 2, 330 + idx * 26))

        # Restart instruction
        hint_surf = self.font_title.render("Натисніть [ПРОБІЛ] або [R] для перезапуску | [ESC] для виходу", True, (255, 215, 0))
        surface.blit(hint_surf, (WINDOW_WIDTH // 2 - hint_surf.get_width() // 2, 480))
