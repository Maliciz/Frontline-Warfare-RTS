"""
Procedural Military Audio Engine for Frontline: Steel Vanguard RTS
Generates rich military sound effects purely in-memory using NumPy and Pygame mixer.
Zero external audio file dependencies - 100% offline and standalone!
"""
import numpy as np
import pygame

class SoundEngine:
    def __init__(self):
        self.enabled = True
        self.volume = 0.8
        self.sounds = {}
        self.last_played = {}
        self.sample_rate = 44100
        
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=self.sample_rate, size=-16, channels=2, buffer=1024)
            self._init_procedural_sounds()
        except Exception as e:
            print(f"Warning: Audio initialization failed: {e}")
            self.enabled = False

    def _make_stereo(self, mono_arr):
        """Convert mono float array (-1.0 to 1.0) into int16 stereo array."""
        clipped = np.clip(mono_arr, -1.0, 1.0)
        int16_mono = (clipped * 32767).astype(np.int16)
        return np.column_stack((int16_mono, int16_mono))

    def _init_procedural_sounds(self):
        sr = self.sample_rate

        # 1. Rifle Shot
        t = np.linspace(0, 0.14, int(sr * 0.14), endpoint=False)
        noise = np.random.uniform(-1, 1, len(t))
        env = np.exp(-35 * t)
        body = np.sin(2 * np.pi * (240 - 120 * t) * t) * np.exp(-40 * t)
        rifle_mono = (0.7 * noise + 0.5 * body) * env
        self.sounds["rifle_shot"] = pygame.sndarray.make_sound(self._make_stereo(rifle_mono))

        # 2. Autocannon (IFV)
        t = np.linspace(0, 0.18, int(sr * 0.18), endpoint=False)
        noise = np.random.uniform(-0.8, 0.8, len(t))
        punch = np.sin(2 * np.pi * 180 * t) * np.exp(-30 * t)
        env = np.exp(-25 * t)
        ifv_mono = (0.5 * noise + 0.7 * punch) * env
        self.sounds["autocannon"] = pygame.sndarray.make_sound(self._make_stereo(ifv_mono))

        # 3. RPG Launch (whoosh & rocket blast)
        t = np.linspace(0, 0.38, int(sr * 0.38), endpoint=False)
        noise = np.random.uniform(-1, 1, len(t))
        whoosh_freq = 600 - 450 * (t / 0.38)
        sweep = np.sin(2 * np.pi * whoosh_freq * t)
        env = np.sin(np.pi * np.clip(t / 0.1, 0, 1) * 0.5) * np.exp(-8 * t)
        rpg_mono = (0.6 * noise + 0.4 * sweep) * env
        self.sounds["rpg_launch"] = pygame.sndarray.make_sound(self._make_stereo(rpg_mono))

        # 4. Tank Cannon Blast (Deep thunderous concussive punch)
        t = np.linspace(0, 0.65, int(sr * 0.65), endpoint=False)
        noise = np.random.uniform(-1, 1, len(t))
        sub = np.sin(2 * np.pi * 55 * t) * np.exp(-6 * t)
        punch = np.sin(2 * np.pi * (140 - 100 * t) * t) * np.exp(-18 * t)
        env = np.exp(-8 * t)
        tank_mono = (0.55 * noise * np.exp(-12 * t) + 0.7 * sub + 0.8 * punch) * env
        self.sounds["tank_cannon"] = pygame.sndarray.make_sound(self._make_stereo(tank_mono))

        # 5. Artillery Howitzer Shot
        t = np.linspace(0, 0.75, int(sr * 0.75), endpoint=False)
        noise = np.random.uniform(-0.9, 0.9, len(t))
        sub = np.sin(2 * np.pi * 42 * t) * np.exp(-5 * t)
        kick = np.sin(2 * np.pi * (110 - 80 * t) * t) * np.exp(-15 * t)
        env = np.exp(-6 * t)
        art_mono = (0.5 * noise * np.exp(-10 * t) + 0.85 * sub + 0.6 * kick) * env
        self.sounds["artillery_shot"] = pygame.sndarray.make_sound(self._make_stereo(art_mono))

        # 6. Artillery Falling Whistle
        t = np.linspace(0, 0.5, int(sr * 0.5), endpoint=False)
        freq = 1100 - 750 * (t / 0.5)
        env = (t / 0.5) * 0.5  # swells up
        whistle_mono = np.sin(2 * np.pi * freq * t) * env
        self.sounds["artillery_whistle"] = pygame.sndarray.make_sound(self._make_stereo(whistle_mono))

        # 7. Small Explosion
        t = np.linspace(0, 0.45, int(sr * 0.45), endpoint=False)
        noise = np.random.uniform(-1, 1, len(t))
        thump = np.sin(2 * np.pi * 90 * t) * np.exp(-15 * t)
        env = np.exp(-9 * t)
        exp_s_mono = (0.75 * noise + 0.5 * thump) * env
        self.sounds["explosion_small"] = pygame.sndarray.make_sound(self._make_stereo(exp_s_mono))

        # 8. Large Explosion (Heavy Vehicle / Building collapse)
        t = np.linspace(0, 0.9, int(sr * 0.9), endpoint=False)
        noise = np.random.uniform(-1, 1, len(t))
        sub_rumble = np.sin(2 * np.pi * 48 * t) * np.exp(-4.5 * t)
        impact = np.sin(2 * np.pi * 120 * t) * np.exp(-22 * t)
        env = np.exp(-5 * t)
        exp_l_mono = (0.7 * noise * np.exp(-7 * t) + 0.8 * sub_rumble + 0.9 * impact) * env
        self.sounds["explosion_large"] = pygame.sndarray.make_sound(self._make_stereo(exp_l_mono))

        # 9. FPV Drone High-Pitch Electric Motor Buzz
        t = np.linspace(0, 0.28, int(sr * 0.28), endpoint=False)
        motor1 = np.sin(2 * np.pi * 320 * t)
        motor2 = np.sin(2 * np.pi * 640 * t)
        pwm_mod = 0.5 + 0.5 * np.sin(2 * np.pi * 60 * t)
        drone_mono = (0.5 * motor1 + 0.5 * motor2) * pwm_mod * 0.4
        self.sounds["drone_buzz"] = pygame.sndarray.make_sound(self._make_stereo(drone_mono))

        # 10. Anti-Air Flak / Rapid Double Crack
        t = np.linspace(0, 0.22, int(sr * 0.22), endpoint=False)
        noise = np.random.uniform(-0.8, 0.8, len(t))
        tone = np.sin(2 * np.pi * 320 * t) * np.exp(-25 * t)
        flak_mono = (0.7 * noise + 0.4 * tone) * np.exp(-20 * t)
        self.sounds["flak_shot"] = pygame.sndarray.make_sound(self._make_stereo(flak_mono))

        # 11. Tread / Engine Rumble
        t = np.linspace(0, 0.35, int(sr * 0.35), endpoint=False)
        diesel = np.sin(2 * np.pi * 58 * t) + 0.4 * np.sin(2 * np.pi * 116 * t)
        squeak = 0.2 * np.sin(2 * np.pi * 880 * t) * (np.sin(2 * np.pi * 7 * t) > 0.7)
        tread_mono = (diesel + squeak) * 0.35
        self.sounds["tread_rumble"] = pygame.sndarray.make_sound(self._make_stereo(tread_mono))

        # 12. Radio Command Acknowledge ("Roger / Target locked")
        t = np.linspace(0, 0.12, int(sr * 0.12), endpoint=False)
        tone = np.sin(2 * np.pi * 880 * t) * 0.3
        click = np.random.uniform(-0.4, 0.4, len(t)) * np.exp(-40 * t)
        ack_mono = (tone + click) * np.exp(-20 * t)
        self.sounds["order_ack"] = pygame.sndarray.make_sound(self._make_stereo(ack_mono))

        # 13. Unit Deployed Chime ("Unit Ready")
        t = np.linspace(0, 0.25, int(sr * 0.25), endpoint=False)
        n1 = np.sin(2 * np.pi * 659 * t) * np.exp(-15 * t) * (t < 0.12)
        n2 = np.sin(2 * np.pi * 880 * (t - 0.12)) * np.exp(-15 * (t - 0.12)) * (t >= 0.12)
        ready_mono = (n1 + n2) * 0.4
        self.sounds["unit_ready"] = pygame.sndarray.make_sound(self._make_stereo(ready_mono))

        # 14. Capture Success Chime
        t = np.linspace(0, 0.45, int(sr * 0.45), endpoint=False)
        n1 = np.sin(2 * np.pi * 523 * t) * np.exp(-12 * t) * (t < 0.15)
        n2 = np.sin(2 * np.pi * 659 * (t - 0.15)) * np.exp(-12 * (t - 0.15)) * ((t >= 0.15) & (t < 0.30))
        n3 = np.sin(2 * np.pi * 784 * (t - 0.30)) * np.exp(-12 * (t - 0.30)) * (t >= 0.30)
        capture_mono = (n1 + n2 + n3) * 0.5
        self.sounds["capture_complete"] = pygame.sndarray.make_sound(self._make_stereo(capture_mono))

        # 15. Alert Klaxon (Under Attack)
        t = np.linspace(0, 0.4, int(sr * 0.4), endpoint=False)
        freq = 660 + 220 * np.sin(2 * np.pi * 8 * t)
        alert_mono = np.sin(2 * np.pi * freq * t) * 0.4 * np.exp(-2 * t)
        self.sounds["alert_siren"] = pygame.sndarray.make_sound(self._make_stereo(alert_mono))

        # 16. Victory Fanfare
        t = np.linspace(0, 1.1, int(sr * 1.1), endpoint=False)
        c1 = np.sin(2 * np.pi * 523 * t) * (t < 0.25)
        c2 = np.sin(2 * np.pi * 659 * t) * ((t >= 0.25) & (t < 0.50))
        c3 = np.sin(2 * np.pi * 784 * t) * ((t >= 0.50) & (t < 0.75))
        c4 = (np.sin(2 * np.pi * 1046 * t) + 0.5 * np.sin(2 * np.pi * 523 * t)) * (t >= 0.75) * np.exp(-3 * (t - 0.75))
        vic_mono = (c1 + c2 + c3 + c4) * 0.4
        self.sounds["victory"] = pygame.sndarray.make_sound(self._make_stereo(vic_mono))

        # 17. Defeat Theme
        t = np.linspace(0, 0.9, int(sr * 0.9), endpoint=False)
        d1 = np.sin(2 * np.pi * 440 * t) * (t < 0.3)
        d2 = np.sin(2 * np.pi * 415 * t) * ((t >= 0.3) & (t < 0.6))
        d3 = np.sin(2 * np.pi * 370 * t) * (t >= 0.6) * np.exp(-3 * (t - 0.6))
        def_mono = (d1 + d2 + d3) * 0.4
        self.sounds["defeat"] = pygame.sndarray.make_sound(self._make_stereo(def_mono))

        # Set default volumes
        for snd in self.sounds.values():
            snd.set_volume(self.volume)

    def play(self, name, min_interval=0.06):
        """Play sound with optional throttling to prevent audio clipping."""
        if not self.enabled or name not in self.sounds:
            return
        now = pygame.time.get_ticks() / 1000.0
        last = self.last_played.get(name, 0.0)
        if now - last < min_interval:
            return
        self.last_played[name] = now
        try:
            self.sounds[name].play()
        except Exception:
            pass

    def toggle_sound(self):
        self.enabled = not self.enabled
        return self.enabled

    def set_volume(self, vol):
        self.volume = max(0.0, min(1.0, vol))
        for snd in self.sounds.values():
            snd.set_volume(self.volume)
