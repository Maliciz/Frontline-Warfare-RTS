"""
Tactical RTS Camera and Viewport Management
"""
import pygame
from engine.config import WINDOW_WIDTH, WINDOW_HEIGHT, MAP_WIDTH, MAP_HEIGHT

class Camera:
    def __init__(self, x=0, y=0):
        self.x = float(x)
        self.y = float(y)
        self.speed = 900.0  # pixels per second
        self.edge_margin = 16
        self.enable_edge_scroll = True
        self.zoom = 1.0

        # UI reserving space at bottom for command deck
        self.hud_bottom_height = 140
        self.clamp()

    def clamp(self):
        max_x = max(0, MAP_WIDTH - WINDOW_WIDTH)
        max_y = max(0, MAP_HEIGHT - (WINDOW_HEIGHT - self.hud_bottom_height))
        self.x = max(0.0, min(float(max_x), self.x))
        self.y = max(0.0, min(float(max_y), self.y))

    def center_on(self, wx, wy):
        self.x = wx - WINDOW_WIDTH / 2.0
        self.y = wy - (WINDOW_HEIGHT - self.hud_bottom_height) / 2.0
        self.clamp()

    def update(self, dt, mouse_pos=None):
        keys = pygame.key.get_pressed()
        dx, dy = 0.0, 0.0

        # Keyboard WASD / Arrows
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            dx -= 1.0
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            dx += 1.0
        if keys[pygame.K_w] or keys[pygame.K_UP]:
            dy -= 1.0
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            dy += 1.0

        # Mouse edge scrolling
        if self.enable_edge_scroll and mouse_pos and pygame.mouse.get_focused():
            mx, my = mouse_pos
            if mx < self.edge_margin:
                dx -= 1.0
            elif mx > WINDOW_WIDTH - self.edge_margin:
                dx += 1.0
            if my < self.edge_margin:
                dy -= 1.0
            elif my > WINDOW_HEIGHT - self.hud_bottom_height - self.edge_margin and my < WINDOW_HEIGHT - self.hud_bottom_height:
                dy += 1.0

        # Normalize diagonal movement
        if dx != 0.0 and dy != 0.0:
            dx *= 0.7071
            dy *= 0.7071

        self.x += dx * self.speed * dt
        self.y += dy * self.speed * dt
        self.clamp()

    def world_to_screen(self, wx, wy):
        return int(wx - self.x), int(wy - self.y)

    def screen_to_world(self, sx, sy):
        return sx + self.x, sy + self.y

    def is_visible(self, wx, wy, radius=64):
        sx, sy = self.world_to_screen(wx, wy)
        return (-radius <= sx <= WINDOW_WIDTH + radius and
                -radius <= sy <= WINDOW_HEIGHT - self.hud_bottom_height + radius)
