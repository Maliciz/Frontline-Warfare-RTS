"""
Unit and integration tests for Frontline Warfare Game Logic
"""
import unittest
import math
from engine.config import (
    MAP_WIDTH, MAP_HEIGHT,
    FACTION_PLAYER, FACTION_ENEMY, FACTION_NEUTRAL,
    FOW_UNEXPLORED, FOW_EXPLORED, FOW_VISIBLE
)
from engine.game_state import GameState
from engine.camera import Camera
from engine.fog_of_war import FogOfWar
from engine.map_grid import MapGrid

class TestGameLogic(unittest.TestCase):
    def setUp(self):
        self.gs = GameState()

    def test_map_and_passability(self):
        grid = self.gs.map_grid
        self.assertGreater(grid.cols, 0)
        self.assertGreater(grid.rows, 0)
        # Check water passability
        # Air units can fly anywhere inside map
        self.assertTrue(grid.is_passable(500, 500, "air"))
        # Verify speed modifier returns reasonable values
        spd_mod = grid.get_speed_multiplier(100, 100, "ground")
        self.assertGreater(spd_mod, 0.5)
        self.assertLessEqual(spd_mod, 2.0)

    def test_camera_clamping(self):
        cam = Camera(x=-500, y=-500)
        self.assertGreaterEqual(cam.x, 0)
        self.assertGreaterEqual(cam.y, 0)

        cam = Camera(x=99999, y=99999)
        self.assertLessEqual(cam.x, MAP_WIDTH)
        self.assertLessEqual(cam.y, MAP_HEIGHT)

        # Coordinate roundtrip
        cam.center_on(1000, 1000)
        sx, sy = cam.world_to_screen(1000, 1000)
        wx, wy = cam.screen_to_world(sx, sy)
        self.assertAlmostEqual(wx, 1000, delta=1.0)
        self.assertAlmostEqual(wy, 1000, delta=1.0)

    def test_fog_of_war(self):
        fow = FogOfWar()
        # Initial state: unexplored
        self.assertFalse(fow.is_explored(1000, 1000))
        self.assertFalse(fow.is_visible(1000, 1000))

        # Reveal
        fow.reveal(1000, 1000, 200)
        self.assertTrue(fow.is_visible(1000, 1000))
        self.assertTrue(fow.is_explored(1000, 1000))

        # Reset to explored
        fow.reset_to_explored()
        self.assertFalse(fow.is_visible(1000, 1000))
        self.assertTrue(fow.is_explored(1000, 1000))

    def test_strategic_economy_and_capture(self):
        initial_resources = self.gs.resources
        initial_income = self.gs.income_rate

        # Simulate 1 second
        self.gs.update(1.0)
        self.assertGreater(self.gs.resources, initial_resources)

        # Find capturable derrick
        derrick = next(b for b in self.gs.buildings if b.is_capturable)
        self.assertEqual(derrick.faction, FACTION_NEUTRAL)

        # Spawn player rifleman right on derrick
        capturer = self.gs.spawn_unit("rifleman", derrick.x, derrick.y, faction=FACTION_PLAYER)

        # Simulate until captured (approx 6 seconds)
        for _ in range(450):
            self.gs.update(0.016)
            if derrick.faction == FACTION_PLAYER:
                break

        self.assertEqual(derrick.faction, FACTION_PLAYER)
        # Advance 1 tick to update income rate
        self.gs.update(0.1)
        self.assertGreater(self.gs.income_rate, initial_income)

    def test_building_production_queue(self):
        barracks = next(b for b in self.gs.buildings if b.type_key == "barracks" and b.faction == FACTION_PLAYER)
        self.gs.resources = 500
        success = barracks.enqueue_unit("rifleman", self.gs.resources)
        self.assertTrue(success)
        self.assertEqual(len(barracks.queue), 1)

    def test_control_groups(self):
        u1 = self.gs.spawn_unit("tank", 400, 1500, faction=FACTION_PLAYER)
        u2 = self.gs.spawn_unit("tank", 450, 1500, faction=FACTION_PLAYER)
        u1.selected = True
        u2.selected = True

        self.gs.control_groups[1] = [u1, u2]
        self.assertEqual(len(self.gs.control_groups[1]), 2)

if __name__ == "__main__":
    unittest.main()
