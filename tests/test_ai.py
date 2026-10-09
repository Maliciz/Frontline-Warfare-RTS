"""
Unit tests for Frontline Warfare Combat AI
"""
import unittest
from engine.config import FACTION_ENEMY, BUILDING_CONFIGS
from engine.game_state import GameState
from engine.ai import DIFFICULTY_EASY, DIFFICULTY_NORMAL, DIFFICULTY_HARD

class TestAI(unittest.TestCase):
    def test_ai_build_progression(self):
        gs = GameState(difficulty=DIFFICULTY_HARD)
        gs.ai.resources = 2000.0  # give AI resources to build

        # Trigger AI decisions
        for _ in range(10):
            gs.ai.think_timer = 1.0
            gs.ai._manage_economy_and_building(gs)

        ai_blds = [b for b in gs.buildings if b.faction == FACTION_ENEMY]
        # AI should have constructed barracks, supply depot, war factory, drone bay
        built_types = [b.type_key for b in ai_blds]
        self.assertIn("barracks", built_types)
        self.assertIn("supply_depot", built_types)
        self.assertIn("war_factory", built_types)

    def test_ai_unit_production(self):
        gs = GameState(difficulty=DIFFICULTY_NORMAL)
        gs.ai.resources = 1500.0
        # Ensure production buildings exist
        barracks = gs.spawn_building("barracks", 2200, 300, faction=FACTION_ENEMY)
        war_fac = gs.spawn_building("war_factory", 2100, 300, faction=FACTION_ENEMY)

        gs.ai._manage_production(gs)
        # Buildings should now have queued units
        self.assertTrue(len(barracks.queue) > 0 or barracks.current_unit is not None or
                        len(war_fac.queue) > 0 or war_fac.current_unit is not None)

    def test_ai_wave_attack_trigger(self):
        gs = GameState(difficulty=DIFFICULTY_NORMAL)
        # Spawn combat units for enemy
        for i in range(8):
            gs.spawn_unit("tank", 2000 + i * 20, 400, faction=FACTION_ENEMY)

        gs.ai.attack_timer = gs.ai.attack_interval + 1.0
        gs.ai.update(0.1, gs)

        # Units should have received orders to attack
        moving_units = [
            u for u in gs.units
            if u.faction == FACTION_ENEMY and u.state in ("attack_move", "move", "attack")
        ]
        self.assertGreaterEqual(len(moving_units), 5)

if __name__ == "__main__":
    unittest.main()
