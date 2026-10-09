"""
Unit tests for Frontline Warfare Combat and Ballistics
"""
import unittest
import math
from engine.config import FACTION_PLAYER, FACTION_ENEMY
from engine.game_state import GameState

class TestCombat(unittest.TestCase):
    def setUp(self):
        self.gs = GameState()

    def test_direct_fire_damage(self):
        attacker = self.gs.spawn_unit("ifv", 1000, 1000, faction=FACTION_PLAYER)
        defender = self.gs.spawn_unit("rifleman", 1100, 1000, faction=FACTION_ENEMY)
        initial_hp = defender.hp

        attacker.issue_attack(defender)
        for _ in range(30):
            self.gs.update(0.016)
            if defender.hp < initial_hp:
                break

        self.assertLess(defender.hp, initial_hp)

    def test_fpv_drone_kamikaze_strike(self):
        drone = self.gs.spawn_unit("fpv_drone", 1000, 1000, faction=FACTION_PLAYER)
        tank = self.gs.spawn_unit("tank", 1080, 1000, faction=FACTION_ENEMY)
        initial_tank_hp = tank.hp

        drone.issue_attack(tank)
        for _ in range(40):
            self.gs.update(0.016)
            if drone.dead:
                break

        self.assertTrue(drone.dead)
        self.assertLess(tank.hp, initial_tank_hp)

    def test_anti_air_interception(self):
        drone = self.gs.spawn_unit("fpv_drone", 1000, 1000, faction=FACTION_PLAYER)
        aa = self.gs.spawn_unit("aa_vehicle", 1180, 1000, faction=FACTION_ENEMY)
        drone.issue_attack(aa)

        for _ in range(50):
            self.gs.update(0.016)
            if drone.dead:
                break

        # Drone should be shot down while AA survives undamaged or nearly undamaged
        self.assertTrue(drone.dead)
        self.assertEqual(aa.hp, aa.max_hp)

    def test_artillery_min_range(self):
        art = self.gs.spawn_unit("artillery", 1000, 1000, faction=FACTION_PLAYER)
        target_close = self.gs.spawn_unit("rifleman", 1050, 1000, faction=FACTION_ENEMY)
        art.issue_attack(target_close)

        # Distance is 50px, which is below min_range (150px)
        # Artillery should back away or not fire directly at point-blank
        self.assertEqual(art.reload_timer, 0.0)

if __name__ == "__main__":
    unittest.main()
