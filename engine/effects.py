"""
Tactical RTS Visual Effects, Particles, Tracers, Craters, and Smoke
"""
import math
import random
import pygame

class Particle:
    def __init__(self, x, y, vx, vy, color, radius, lifetime, shrink=True, gravity=0.0):
        self.x = float(x)
        self.y = float(y)
        self.vx = float(vx)
        self.vy = float(vy)
        self.color = color
        self.radius = float(radius)
        self.initial_radius = float(radius)
        self.lifetime = float(lifetime)
        self.age = 0.0
        self.shrink = shrink
        self.gravity = gravity
        self.dead = False

    def update(self, dt):
        self.age += dt
        if self.age >= self.lifetime:
            self.dead = True
            return
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.vy += self.gravity * dt
        if self.shrink:
            progress = self.age / self.lifetime
            self.radius = max(0.5, self.initial_radius * (1.0 - progress))

    def render(self, surface, camera):
        sx, sy = camera.world_to_screen(self.x, self.y)
        if camera.is_visible(self.x, self.y, int(self.radius) + 4):
            pygame.draw.circle(surface, self.color, (sx, sy), max(1, int(self.radius)))

class Crater:
    def __init__(self, x, y, radius=18):
        self.x = float(x)
        self.y = float(y)
        self.radius = radius
        self.lifetime = 45.0  # lasts 45 seconds on battlefield
        self.age = 0.0
        self.dead = False

    def update(self, dt):
        self.age += dt
        if self.age >= self.lifetime:
            self.dead = True

    def render(self, surface, camera):
        if not camera.is_visible(self.x, self.y, self.radius):
            return
        sx, sy = camera.world_to_screen(self.x, self.y)
        alpha = max(0.2, 1.0 - (self.age / self.lifetime))
        color = (25, 23, 20)
        pygame.draw.circle(surface, color, (sx, sy), self.radius)
        pygame.draw.circle(surface, (15, 14, 12), (sx, sy), int(self.radius * 0.6))

class TrackMark:
    """Tread marks left by tanks and armored vehicles."""
    def __init__(self, x, y, angle, length=12):
        self.x = x
        self.y = y
        self.angle = angle
        self.length = length
        self.lifetime = 20.0
        self.age = 0.0
        self.dead = False

    def update(self, dt):
        self.age += dt
        if self.age >= self.lifetime:
            self.dead = True

    def render(self, surface, camera):
        if not camera.is_visible(self.x, self.y, self.length):
            return
        sx, sy = camera.world_to_screen(self.x, self.y)
        dx = math.cos(self.angle) * self.length * 0.5
        dy = math.sin(self.angle) * self.length * 0.5
        # Perpendicular track offset
        px = -math.sin(self.angle) * 7.0
        py = math.cos(self.angle) * 7.0
        color = (35, 32, 28)
        # Left and right track segments
        pygame.draw.line(surface, color, (sx + px - dx, sy + py - dy), (sx + px + dx, sy + py + dy), 2)
        pygame.draw.line(surface, color, (sx - px - dx, sy - py - dy), (sx - px + dx, sy - py + dy), 2)

class FloatingText:
    """Floating tactical text (damage, +EXP, +Resources, Capture)."""
    def __init__(self, x, y, text, color=(255, 255, 255), lifetime=1.2):
        self.x = float(x)
        self.y = float(y)
        self.text = text
        self.color = color
        self.lifetime = lifetime
        self.age = 0.0
        self.dead = False

    def update(self, dt):
        self.age += dt
        self.y -= 25.0 * dt
        if self.age >= self.lifetime:
            self.dead = True

    def render(self, surface, camera, font):
        if not camera.is_visible(self.x, self.y, 40):
            return
        sx, sy = camera.world_to_screen(self.x, self.y)
        txt_surf = font.render(self.text, True, self.color)
        surface.blit(txt_surf, (sx - txt_surf.get_width() // 2, sy))

class EffectManager:
    def __init__(self):
        self.particles = []
        self.craters = []
        self.tracks = []
        self.texts = []

    def add_muzzle_flash(self, x, y, angle, color=(255, 220, 100), count=6):
        for _ in range(count):
            spread = angle + random.uniform(-0.35, 0.35)
            speed = random.uniform(80, 220)
            vx = math.cos(spread) * speed
            vy = math.sin(spread) * speed
            life = random.uniform(0.06, 0.14)
            r = random.uniform(2, 5)
            self.particles.append(Particle(x, y, vx, vy, color, r, life))

    def add_explosion(self, x, y, radius=35, is_large=False):
        # Add ground crater
        self.craters.append(Crater(x, y, radius=int(radius * 0.65)))

        # Fire and spark particles
        num_sparks = 45 if is_large else 25
        for _ in range(num_sparks):
            ang = random.uniform(0, 2 * math.pi)
            spd = random.uniform(40, 280 if is_large else 180)
            vx = math.cos(ang) * spd
            vy = math.sin(ang) * spd
            col = random.choice([(255, 240, 120), (255, 140, 30), (240, 60, 20), (120, 120, 120)])
            life = random.uniform(0.25, 0.7 if is_large else 0.45)
            sz = random.uniform(3, 8 if is_large else 5)
            self.particles.append(Particle(x, y, vx, vy, col, sz, life, shrink=True))

        # Heavy smoke puffs that rise
        num_smoke = 20 if is_large else 10
        for _ in range(num_smoke):
            ang = random.uniform(0, 2 * math.pi)
            spd = random.uniform(15, 60)
            vx = math.cos(ang) * spd
            vy = math.sin(ang) * spd - random.uniform(15, 45)  # smoke drifts up
            gray = random.randint(45, 95)
            col = (gray, gray, gray)
            life = random.uniform(0.8, 1.8 if is_large else 1.2)
            sz = random.uniform(6, 14 if is_large else 9)
            self.particles.append(Particle(x, y, vx, vy, col, sz, life, shrink=False))

    def add_rocket_smoke(self, x, y):
        vx = random.uniform(-10, 10)
        vy = random.uniform(-10, 10)
        gray = random.randint(180, 220)
        self.particles.append(Particle(x, y, vx, vy, (gray, gray, gray), random.uniform(2, 4), 0.35))

    def add_track_mark(self, x, y, angle):
        if len(self.tracks) > 250:
            self.tracks.pop(0)
        self.tracks.append(TrackMark(x, y, angle))

    def add_floating_text(self, x, y, text, color=(255, 255, 255)):
        self.texts.append(FloatingText(x, y, text, color))

    def update(self, dt):
        for p in self.particles:
            p.update(dt)
        self.particles = [p for p in self.particles if not p.dead]

        for c in self.craters:
            c.update(dt)
        self.craters = [c for c in self.craters if not c.dead]

        for t in self.tracks:
            t.update(dt)
        self.tracks = [t for t in self.tracks if not t.dead]

        for txt in self.texts:
            txt.update(dt)
        self.texts = [txt for txt in self.texts if not txt.dead]

    def render_ground(self, surface, camera):
        """Render craters and track marks on the ground level (under units)."""
        for c in self.craters:
            c.render(surface, camera)
        for t in self.tracks:
            t.render(surface, camera)

    def render_air(self, surface, camera, font=None):
        """Render particles, smoke, and floating text above units."""
        for p in self.particles:
            p.render(surface, camera)
        if font:
            for txt in self.texts:
                txt.render(surface, camera, font)
