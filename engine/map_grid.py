"""
Tactical Battlefield Map Grid, Terrain Types and Passability
"""
import numpy as np
import pygame
from engine.config import (
    MAP_WIDTH, MAP_HEIGHT, TILE_SIZE, GRID_COLS, GRID_ROWS,
    COLOR_TERRAIN_GRASS, COLOR_TERRAIN_DIRT, COLOR_TERRAIN_ROAD,
    COLOR_TERRAIN_WATER, COLOR_TERRAIN_FOREST
)

# Terrain Tile IDs
TILE_GRASS = 0
TILE_DIRT = 1
TILE_ROAD = 2
TILE_WATER = 3
TILE_BRIDGE = 4
TILE_FOREST = 5
TILE_ROCK = 6

class MapGrid:
    def __init__(self):
        self.cols = GRID_COLS
        self.rows = GRID_ROWS
        self.tile_size = TILE_SIZE
        self.width = MAP_WIDTH
        self.height = MAP_HEIGHT

        self.tiles = np.zeros((self.cols, self.rows), dtype=np.uint8)
        self.decorations = []  # trees, road markings, craters
        self.resource_locations = []
        self._generate_map()
        self._bake_background_surface()

    def _generate_map(self):
        """Generate a strategic RTS map with 2 bases, river, bridges, roads, forests, and resource points."""
        # 1. Base terrain: Grass with dirt variations
        np.random.seed(42)  # consistent tactical battlefield
        for x in range(self.cols):
            for y in range(self.rows):
                val = np.random.random()
                if val < 0.15:
                    self.tiles[x, y] = TILE_DIRT
                else:
                    self.tiles[x, y] = TILE_GRASS

        # 2. Diagonal / Curving River dividing Player (South-West) and Enemy (North-East)
        # Center line from (0, 30) down to (80, 25) with thickness
        for x in range(self.cols):
            # Sigmoid / sine curve for river
            center_y = int(30 + 10 * np.sin(x * 0.08) - (x - 40) * 0.25)
            for dy in range(-2, 3):
                ry = center_y + dy
                if 0 <= ry < self.rows:
                    self.tiles[x, ry] = TILE_WATER

        # 3. Tactical Bridges across the river (3 strategic choke points)
        bridge_xs = [20, 40, 60]
        for bx in bridge_xs:
            for dx in range(-1, 2):
                x = bx + dx
                if 0 <= x < self.cols:
                    center_y = int(30 + 10 * np.sin(x * 0.08) - (x - 40) * 0.25)
                    for dy in range(-3, 4):
                        ry = center_y + dy
                        if 0 <= ry < self.rows:
                            self.tiles[x, ry] = TILE_BRIDGE

        # 4. Strategic Highway System connecting bases across the bridges
        # Player base at ~(12, 48), Enemy base at ~(68, 12)
        # Road from Player Base to bridges
        self._draw_road_line(12, 48, 20, 30)
        self._draw_road_line(20, 30, 40, 30)
        self._draw_road_line(40, 30, 60, 25)
        self._draw_road_line(60, 25, 68, 12)

        # Secondary roads
        self._draw_road_line(12, 48, 40, 45)
        self._draw_road_line(40, 45, 40, 30)
        self._draw_road_line(40, 30, 40, 15)
        self._draw_road_line(40, 15, 68, 12)

        # 5. Forest Groves (Tactical ambush and infantry cover zones)
        forest_patches = [
            (10, 25, 6), (25, 45, 7), (55, 42, 6),
            (28, 15, 6), (52, 18, 7), (65, 32, 5)
        ]
        for fx, fy, fr in forest_patches:
            for dx in range(-fr, fr + 1):
                for dy in range(-fr, fr + 1):
                    if dx * dx + dy * dy <= fr * fr:
                        gx = fx + dx
                        gy = fy + dy
                        if 0 <= gx < self.cols and 0 <= gy < self.rows:
                            if self.tiles[gx, gy] not in (TILE_WATER, TILE_BRIDGE, TILE_ROAD):
                                self.tiles[gx, gy] = TILE_FOREST

        # 6. Resource Derrick Strategic Positions
        self.resource_locations = [
            (MAP_WIDTH * 0.5, MAP_HEIGHT * 0.5),      # Central Island / Bridge Depot
            (MAP_WIDTH * 0.25, MAP_HEIGHT * 0.72),    # SW Player Expansion
            (MAP_WIDTH * 0.75, MAP_HEIGHT * 0.28),    # NE Enemy Expansion
            (MAP_WIDTH * 0.22, MAP_HEIGHT * 0.32),    # West Flank Depot
            (MAP_WIDTH * 0.78, MAP_HEIGHT * 0.68),    # East Flank Depot
        ]

    def _draw_road_line(self, x0, y0, x1, y1):
        """Draw 2-tile wide road between two points."""
        dx = abs(x1 - x0)
        dy = abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx - dy

        curr_x, curr_y = x0, y0
        while True:
            for ox in (0, 1):
                for oy in (0, 1):
                    gx = curr_x + ox
                    gy = curr_y + oy
                    if 0 <= gx < self.cols and 0 <= gy < self.rows:
                        if self.tiles[gx, gy] != TILE_WATER:
                            self.tiles[gx, gy] = TILE_ROAD
            if curr_x == x1 and curr_y == y1:
                break
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                curr_x += sx
            if e2 < dx:
                err += dx
                curr_y += sy

    def _bake_background_surface(self):
        """Pre-bake detailed static battlefield map into cached surfaces for ultra-high FPS."""
        self.bg_surface = pygame.Surface((self.width, self.height))
        
        # Color mapping
        tile_colors = {
            TILE_GRASS: COLOR_TERRAIN_GRASS,
            TILE_DIRT: COLOR_TERRAIN_DIRT,
            TILE_ROAD: COLOR_TERRAIN_ROAD,
            TILE_WATER: COLOR_TERRAIN_WATER,
            TILE_BRIDGE: (90, 85, 78),
            TILE_FOREST: COLOR_TERRAIN_FOREST,
            TILE_ROCK: (70, 70, 72)
        }

        # Draw base tiles
        for x in range(self.cols):
            for y in range(self.rows):
                t = self.tiles[x, y]
                col = tile_colors.get(t, COLOR_TERRAIN_GRASS)
                rect = (x * self.tile_size, y * self.tile_size, self.tile_size, self.tile_size)
                self.bg_surface.fill(col, rect)

                # Add texture accents
                if t == TILE_ROAD:
                    # Road border lines
                    pygame.draw.line(self.bg_surface, (50, 52, 55), (rect[0], rect[1]), (rect[0] + self.tile_size, rect[1]), 1)
                elif t == TILE_WATER:
                    # Water ripples
                    pygame.draw.line(self.bg_surface, (45, 80, 108), (rect[0] + 4, rect[1] + 16), (rect[0] + 28, rect[1] + 16), 1)
                elif t == TILE_BRIDGE:
                    # Bridge planks
                    pygame.draw.line(self.bg_surface, (110, 100, 90), (rect[0], rect[1] + 8), (rect[0] + self.tile_size, rect[1] + 8), 2)
                    pygame.draw.line(self.bg_surface, (110, 100, 90), (rect[0], rect[1] + 24), (rect[0] + self.tile_size, rect[1] + 24), 2)
                elif t == TILE_FOREST:
                    # Dense tree foliage canopy
                    cx = rect[0] + self.tile_size // 2
                    cy = rect[1] + self.tile_size // 2
                    pygame.draw.circle(self.bg_surface, (20, 36, 18), (cx, cy), self.tile_size // 2 - 2)
                    pygame.draw.circle(self.bg_surface, (34, 58, 30), (cx - 2, cy - 2), self.tile_size // 3)

        # Draw subtle grid lines on roads/pavements for tactical feel
        # Roads get dashed center stripes
        pass

    def get_tile(self, wx, wy):
        gx = int(wx // self.tile_size)
        gy = int(wy // self.tile_size)
        if 0 <= gx < self.cols and 0 <= gy < self.rows:
            return self.tiles[gx, gy]
        return TILE_ROCK

    def is_passable(self, wx, wy, category="ground"):
        if category == "air":
            return 0 <= wx < self.width and 0 <= wy < self.height
        
        gx = int(wx // self.tile_size)
        gy = int(wy // self.tile_size)
        if 0 <= gx < self.cols and 0 <= gy < self.rows:
            t = self.tiles[gx, gy]
            return t != TILE_WATER and t != TILE_ROCK
        return False

    def get_speed_multiplier(self, wx, wy, category="ground"):
        if category == "air":
            return 1.0
        t = self.get_tile(wx, wy)
        if t == TILE_ROAD or t == TILE_BRIDGE:
            return 1.3  # Speed boost on roads!
        elif t == TILE_FOREST:
            return 0.75  # Slower through dense trees
        return 1.0

    def get_cover_defense_bonus(self, wx, wy, category="infantry"):
        if category == "infantry" and self.get_tile(wx, wy) == TILE_FOREST:
            return 0.30  # 30% damage reduction in forest cover!
        return 0.0

    def render(self, surface, camera):
        """Render visible viewport of background."""
        src_rect = pygame.Rect(int(camera.x), int(camera.y), 1280, 720)
        surface.blit(self.bg_surface, (0, 0), src_rect)
