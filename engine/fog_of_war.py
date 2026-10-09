"""
Dynamic Fog of War Engine for Frontline: Steel Vanguard RTS
3-State Visibility System:
0 = UNEXPLORED (Full Pitch Black Darkness)
1 = EXPLORED (Shroud / Fog - terrain visible, moving enemy units hidden)
2 = VISIBLE (Active Line of Sight - full intelligence)
"""
import numpy as np
import pygame
from engine.config import (
    MAP_WIDTH, MAP_HEIGHT, FOW_CELL_SIZE, FOW_COLS, FOW_ROWS,
    FOW_UNEXPLORED, FOW_EXPLORED, FOW_VISIBLE,
    COLOR_FOG_DARK, COLOR_FOG_EXPLORED
)

class FogOfWar:
    def __init__(self):
        self.cols = FOW_COLS
        self.rows = FOW_ROWS
        self.cell_size = FOW_CELL_SIZE
        # 0: Unexplored, 1: Explored, 2: Currently Visible
        self.grid = np.zeros((self.cols, self.rows), dtype=np.uint8)

        # Pre-calculated circular masks for vision radii (cached for fast stamping)
        self.masks = {}
        self._precalc_masks([180, 220, 240, 280, 300, 320, 340, 360, 380, 420])

        # Fog surface caching
        self.fog_surf_unexplored = pygame.Surface((self.cell_size, self.cell_size))
        self.fog_surf_unexplored.fill(COLOR_FOG_DARK)

        self.fog_surf_explored = pygame.Surface((self.cell_size, self.cell_size), pygame.SRCALPHA)
        self.fog_surf_explored.fill(COLOR_FOG_EXPLORED)

    def _precalc_masks(self, pixel_radii):
        for r_px in pixel_radii:
            r_cells = max(1, int(round(r_px / self.cell_size)))
            offsets = []
            for dx in range(-r_cells, r_cells + 1):
                for dy in range(-r_cells, r_cells + 1):
                    if dx * dx + dy * dy <= r_cells * r_cells:
                        offsets.append((dx, dy))
            self.masks[r_px] = offsets

    def get_mask(self, radius_px):
        if radius_px in self.masks:
            return self.masks[radius_px]
        # Calculate on the fly and cache
        r_cells = max(1, int(round(radius_px / self.cell_size)))
        offsets = []
        for dx in range(-r_cells, r_cells + 1):
            for dy in range(-r_cells, r_cells + 1):
                if dx * dx + dy * dy <= r_cells * r_cells:
                    offsets.append((dx, dy))
        self.masks[radius_px] = offsets
        return offsets

    def reset_to_explored(self):
        """At start of frame, cells that were VISIBLE become EXPLORED."""
        self.grid[self.grid == FOW_VISIBLE] = FOW_EXPLORED

    def reveal(self, wx, wy, radius_px):
        """Reveal cells in sight radius around world coordinates."""
        cx = int(wx // self.cell_size)
        cy = int(wy // self.cell_size)
        offsets = self.get_mask(radius_px)

        for dx, dy in offsets:
            gx = cx + dx
            gy = cy + dy
            if 0 <= gx < self.cols and 0 <= gy < self.rows:
                self.grid[gx, gy] = FOW_VISIBLE

    def is_visible(self, wx, wy):
        """Check if world position is currently in active line of sight."""
        gx = int(wx // self.cell_size)
        gy = int(wy // self.cell_size)
        if 0 <= gx < self.cols and 0 <= gy < self.rows:
            return self.grid[gx, gy] == FOW_VISIBLE
        return False

    def is_explored(self, wx, wy):
        """Check if world position has been scouted at least once."""
        gx = int(wx // self.cell_size)
        gy = int(wy // self.cell_size)
        if 0 <= gx < self.cols and 0 <= gy < self.rows:
            return self.grid[gx, gy] >= FOW_EXPLORED
        return False

    def render(self, surface, camera):
        """Render fog over the viewport."""
        start_col = max(0, int(camera.x // self.cell_size))
        end_col = min(self.cols, int((camera.x + camera.WINDOW_WIDTH if hasattr(camera, 'WINDOW_WIDTH') else camera.x + 1280) // self.cell_size) + 2)
        start_row = max(0, int(camera.y // self.cell_size))
        end_row = min(self.rows, int((camera.y + 720) // self.cell_size) + 2)

        for gx in range(start_col, end_col):
            for gy in range(start_row, end_row):
                val = self.grid[gx, gy]
                if val == FOW_VISIBLE:
                    continue  # fully transparent
                sx, sy = camera.world_to_screen(gx * self.cell_size, gy * self.cell_size)
                if val == FOW_UNEXPLORED:
                    surface.blit(self.fog_surf_unexplored, (sx, sy))
                elif val == FOW_EXPLORED:
                    surface.blit(self.fog_surf_explored, (sx, sy))
