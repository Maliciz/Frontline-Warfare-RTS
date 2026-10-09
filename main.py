"""
Frontline: Steel Vanguard RTS | Сталевий Рубіж
Standalone Military Real-Time Strategy Game
"""
import sys
import os
import pygame

# Add project root to sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from engine.config import (
    WINDOW_WIDTH, WINDOW_HEIGHT, FPS_NORMAL, FPS_BATTERY, GAME_TITLE,
    COLOR_BG, COLOR_UI_PANEL, COLOR_UI_BORDER, COLOR_UI_TEXT, COLOR_UI_ACCENT,
    COLOR_PLAYER, COLOR_ENEMY, COLOR_NEUTRAL
)
from engine.game_state import GameState
from engine.ai import DIFFICULTY_EASY, DIFFICULTY_NORMAL, DIFFICULTY_HARD

STATE_MENU = "menu"
STATE_GAME = "game"
STATE_GUIDE = "guide"

class FrontlineApp:
    def __init__(self):
        pygame.init()
        pygame.font.init()
        pygame.display.set_caption(GAME_TITLE)

        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        self.clock = pygame.time.Clock()
        self.running = True

        # State & Options
        self.app_state = STATE_MENU
        self.difficulty = DIFFICULTY_NORMAL
        self.battery_saver = False
        self.game_state = None
        self.paused = False

        # Fonts
        self.font_title = pygame.font.SysFont("Arial", 42, bold=True)
        self.font_subtitle = pygame.font.SysFont("Arial", 18)
        self.font_btn = pygame.font.SysFont("Arial", 18, bold=True)
        self.font_desc = pygame.font.SysFont("Arial", 14)
        self.font_code = pygame.font.SysFont("Consolas", 14)

        # Set tactical icon
        self._set_app_icon()

    def _set_app_icon(self):
        icon_surf = pygame.Surface((32, 32))
        icon_surf.fill((20, 24, 28))
        # Gold star / shield military insignia
        pygame.draw.polygon(icon_surf, (255, 193, 7), [(16, 2), (28, 8), (28, 22), (16, 30), (4, 22), (4, 8)])
        pygame.draw.circle(icon_surf, (33, 150, 243), (16, 16), 6)
        pygame.display.set_icon(icon_surf)

    def start_game(self):
        self.game_state = GameState(difficulty=self.difficulty)
        self.game_state.battery_saver = self.battery_saver
        self.app_state = STATE_GAME
        self.paused = False

    def run(self):
        while self.running:
            target_fps = FPS_BATTERY if (self.battery_saver or (self.game_state and self.game_state.battery_saver)) else FPS_NORMAL
            dt = self.clock.tick(target_fps) / 1000.0
            dt = min(dt, 0.05)  # clamp delta time to avoid physics tunneling

            if self.game_state:
                self.game_state.current_fps = int(self.clock.get_fps())
                self.battery_saver = self.game_state.battery_saver

            self._handle_events()
            self._update(dt)
            self._render()
            pygame.display.flip()

        pygame.quit()
        sys.exit(0)

    def _handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                return

            if self.app_state == STATE_MENU:
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    self._handle_menu_click(event.pos)

            elif self.app_state == STATE_GUIDE:
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    self.app_state = STATE_MENU
                elif event.type == pygame.KEYDOWN and (event.key == pygame.K_ESCAPE or event.key == pygame.K_SPACE):
                    self.app_state = STATE_MENU

            elif self.app_state == STATE_GAME:
                self._handle_game_events(event)

    def _handle_game_events(self, event):
        gs = self.game_state
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.paused = not self.paused
            else:
                if not self.paused:
                    gs.handle_key_down(event.key)

        elif not self.paused:
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left Click
                    # Check if clicking on UI deck or minimap
                    mx, my = event.pos
                    if my >= WINDOW_HEIGHT - gs.ui.hud_height or gs.ui.minimap_rect.collidepoint(mx, my):
                        gs.handle_left_click(mx, my)
                    else:
                        # If placing a building, execute immediately
                        if gs.ui.placement_building:
                            gs.handle_left_click(mx, my)
                        else:
                            gs.ui.start_selection_drag(mx, my)

                elif event.button == 3:  # Right Click
                    gs.handle_right_click(event.pos[0], event.pos[1])

            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1 and gs.ui.is_dragging:
                    rect = gs.ui.get_selection_rect(event.pos)
                    gs.ui.is_dragging = False
                    if rect and (rect.width > 8 or rect.height > 8):
                        gs.handle_selection_box_finish(rect)
                    else:
                        gs.handle_left_click(event.pos[0], event.pos[1])

    def _handle_menu_click(self, pos):
        mx, my = pos
        cx = WINDOW_WIDTH // 2

        # 1. Start Skirmish
        if cx - 180 <= mx <= cx + 180 and 260 <= my <= 315:
            self.start_game()

        # 2. Toggle Difficulty
        elif cx - 180 <= mx <= cx + 180 and 330 <= my <= 385:
            if self.difficulty == DIFFICULTY_EASY:
                self.difficulty = DIFFICULTY_NORMAL
            elif self.difficulty == DIFFICULTY_NORMAL:
                self.difficulty = DIFFICULTY_HARD
            else:
                self.difficulty = DIFFICULTY_EASY

        # 3. Guide & Hotkeys
        elif cx - 180 <= mx <= cx + 180 and 400 <= my <= 455:
            self.app_state = STATE_GUIDE

        # 4. Battery Saver Toggle
        elif cx - 180 <= mx <= cx + 180 and 470 <= my <= 525:
            self.battery_saver = not self.battery_saver

        # 5. Quit
        elif cx - 180 <= mx <= cx + 180 and 540 <= my <= 595:
            self.running = False

    def _update(self, dt):
        if self.app_state == STATE_GAME and self.game_state and not self.paused:
            mouse_pos = pygame.mouse.get_pos()
            self.game_state.camera.update(dt, mouse_pos)
            self.game_state.update(dt)

    def _render(self):
        if self.app_state == STATE_MENU:
            self._render_menu()
        elif self.app_state == STATE_GUIDE:
            self._render_guide()
        elif self.app_state == STATE_GAME and self.game_state:
            self.game_state.render(self.screen)
            if self.paused:
                self._render_pause_overlay()

    def _render_menu(self):
        # Dark camo tactical background
        self.screen.fill((18, 22, 20))

        # Grid lines pattern
        for x in range(0, WINDOW_WIDTH, 40):
            pygame.draw.line(self.screen, (24, 30, 26), (x, 0), (x, WINDOW_HEIGHT), 1)
        for y in range(0, WINDOW_HEIGHT, 40):
            pygame.draw.line(self.screen, (24, 30, 26), (0, y), (WINDOW_WIDTH, y), 1)

        # Title Emblem & Header
        cx = WINDOW_WIDTH // 2
        title_surf = self.font_title.render("FRONTLINE: STEEL VANGUARD", True, (255, 215, 0))
        sub_ua = self.font_subtitle.render("ВІЙСЬКОВА СТРАТЕГІЯ РЕАЛЬНОГО ЧАСУ | СТАЛЕВИЙ РУБІЖ", True, (0, 229, 255))
        sub_desc = self.font_desc.render("Повноцінна автономна RTS для гри офлайн без світла та інтернету", True, (180, 200, 210))

        self.screen.blit(title_surf, (cx - title_surf.get_width() // 2, 90))
        self.screen.blit(sub_ua, (cx - sub_ua.get_width() // 2, 145))
        self.screen.blit(sub_desc, (cx - sub_desc.get_width() // 2, 175))

        # Buttons
        mx, my = pygame.mouse.get_pos()

        diff_names = {
            DIFFICULTY_EASY: "РЕКРУТ (ЛЕГКО)",
            DIFFICULTY_NORMAL: "СЕРЖАНТ (НОРМАЛЬНО)",
            DIFFICULTY_HARD: "ВЕТЕРАН / КОМБАТ (ВАЖКО)"
        }
        diff_label = f"СКЛАДНІСТЬ: {diff_names[self.difficulty]}"
        bat_label = f"БАТАРЕЯ: {'ECO 30 FPS (БЕЗ СВІТЛА)' if self.battery_saver else 'МАКС. 60 FPS'}"

        menu_items = [
            ("ПОЧАТИ БІЙ (SKIRMISH)", 260, (0, 255, 128)),
            (diff_label, 330, (255, 180, 50)),
            ("ТАКТИЧНИЙ ПОСІБНИК [КЛАВІШІ]", 400, (0, 229, 255)),
            (bat_label, 470, (140, 200, 255)),
            ("ВИХІД З ГРИ", 540, (255, 80, 80))
        ]

        for text, btn_y, accent_col in menu_items:
            rect = pygame.Rect(cx - 190, btn_y, 380, 52)
            is_hov = rect.collidepoint(mx, my)
            bg_col = (36, 44, 40) if is_hov else (24, 30, 28)
            pygame.draw.rect(self.screen, bg_col, rect, border_radius=6)
            pygame.draw.rect(self.screen, accent_col if is_hov else (60, 75, 70), rect, 2 if is_hov else 1, border_radius=6)

            t_surf = self.font_btn.render(text, True, (255, 255, 255) if is_hov else (220, 230, 225))
            self.screen.blit(t_surf, (cx - t_surf.get_width() // 2, btn_y + 15))

        # Bottom copyright/version
        ver_surf = self.font_desc.render("Frontline Warfare v1.0.0 Standalone Edition | 100% Offline | Розроблено для Maliciz", True, (120, 140, 135))
        self.screen.blit(ver_surf, (cx - ver_surf.get_width() // 2, WINDOW_HEIGHT - 35))

    def _render_guide(self):
        self.screen.fill((16, 20, 22))
        cx = WINDOW_WIDTH // 2

        header = self.font_title.render("ТАКТИЧНИЙ ПОСІБНИК ТА КЕРУВАННЯ", True, (255, 215, 0))
        self.screen.blit(header, (cx - header.get_width() // 2, 40))

        guide_lines = [
            ("БАЗА ТА ВИРОБНИЦТВО:", (0, 229, 255)),
            (" • Командний пункт (HQ) — серце оборони. Дає базовий приріст припасів та радар.", (220, 230, 235)),
            (" • Казарми — тренування піхотинців (захоплюють вишки) та штурмовиків РПГ (проти танків).", (220, 230, 235)),
            (" • Завод бронетехніки — виробництво БМП «Буцефал», Танків Т-84 «Оплот», САУ «Богдана» та ЗРК.", (220, 230, 235)),
            (" • Станція БПЛА — запуск надшвидких ударних FPV-дронів камікадзе по ворожій важкій техніці.", (220, 230, 235)),
            (" • Склади постачання — збільшують ліміт військ (+15 од.) та логістику.", (220, 230, 235)),
            ("", (0, 0, 0)),
            ("ТАКТИКА ТА БОЙОВИЙ БАЛАНС:", (255, 180, 50)),
            (" • FPV-дрони завдають нищівного удару по Танкам та Артилерії, але збиваються системами ППО.", (220, 230, 235)),
            (" • САУ б'ють навісним вогнем через усю карту, руйнуючи бази супротивника з безпечної відстані.", (220, 230, 235)),
            (" • Захоплюйте нейтральні нафтові вишки піхотою — вони приносять +20 припасів кожні 3 секунди!", (220, 230, 235)),
            (" • Піхота в лісових масивах отримує +30% захисту від ворожого вогню.", (220, 230, 235)),
            ("", (0, 0, 0)),
            ("ГАРЯЧІ КЛАВІШІ ТА УПРАВЛІННЯ:", (0, 255, 128)),
            (" • ЛКМ: вибір юніта / будівлі; затискання та перетягування — виділення рамкою армії.", (220, 230, 235)),
            (" • ПКМ: наказ руху / атаки по ворогу / захоплення ресурсної вишки.", (220, 230, 235)),
            (" • WASD або Стрілки: панорамування камери по карті бою.", (220, 230, 235)),
            (" • Клік по Міні-карті: миттєвий перехід камери в обрану точку поля бою.", (220, 230, 235)),
            (" • Ctrl + 1..9: створення бойових загонів; 1..9: швидкий вибір загону.", (220, 230, 235)),
            (" • H: перемістити камеру на свій Штаб (HQ); SPACE: перейти до місця останнього бою.", (220, 230, 235)),
            (" • F: перемикання режиму економії батареї (60 FPS / 30 FPS); M: вимкнути/увімкнути звук.", (220, 230, 235)),
            (" • ESC: Пауза та меню налаштувань.", (220, 230, 235))
        ]

        y = 110
        for text, col in guide_lines:
            if not text:
                y += 10
                continue
            line_s = self.font_desc.render(text, True, col)
            self.screen.blit(line_s, (140, y))
            y += 24

        # Back button
        back_rect = pygame.Rect(cx - 120, WINDOW_HEIGHT - 65, 240, 44)
        pygame.draw.rect(self.screen, (40, 50, 45), back_rect, border_radius=4)
        pygame.draw.rect(self.screen, (0, 255, 128), back_rect, 1, border_radius=4)
        b_s = self.font_btn.render("« ПОВЕРНУТИСЯ", True, (255, 255, 255))
        self.screen.blit(b_s, (cx - b_s.get_width() // 2, WINDOW_HEIGHT - 53))

    def _render_pause_overlay(self):
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        overlay.fill((10, 12, 14, 200))
        self.screen.blit(overlay, (0, 0))

        cx = WINDOW_WIDTH // 2
        p_surf = self.font_title.render("ТАКТИЧНА ПАУЗА", True, (255, 215, 0))
        self.screen.blit(p_surf, (cx - p_surf.get_width() // 2, 220))

        btn_y = 300
        mx, my = pygame.mouse.get_pos()

        pause_options = [
            ("ПРОДОВЖИТИ БІЙ [ESC]", 300),
            ("ПЕРЕЗАПУСТИТИ МАТЧ [R]", 360),
            ("ВИЙТИ В ГОЛОВНЕ МЕНЮ", 420)
        ]

        for text, by in pause_options:
            rect = pygame.Rect(cx - 160, by, 320, 46)
            is_hov = rect.collidepoint(mx, my)
            pygame.draw.rect(self.screen, (36, 44, 40) if is_hov else (24, 30, 28), rect, border_radius=4)
            pygame.draw.rect(self.screen, (0, 229, 255) if is_hov else (60, 75, 70), rect, 1, border_radius=4)
            t_s = self.font_btn.render(text, True, (255, 255, 255))
            self.screen.blit(t_s, (cx - t_s.get_width() // 2, by + 12))

            if is_hov and pygame.mouse.get_pressed()[0]:
                if by == 300:
                    self.paused = False
                elif by == 360:
                    self.start_game()
                elif by == 420:
                    self.app_state = STATE_MENU
                    self.paused = False

def main():
    app = FrontlineApp()
    app.run()

if __name__ == "__main__":
    main()
