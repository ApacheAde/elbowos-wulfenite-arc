#!/usr/bin/env python3
"""Wulfenite Arc — neon artillery arcade for ElbowOS."""
from __future__ import annotations

import math
import os
import random
import subprocess
import sys

import pygame

W, H = 1080, 1920
FPS = 30
TITLE = "WULFENITE ARC"
HANDLE = "x.com/ElbowOS"
VOID = (12, 6, 22)
PLUM = (42, 12, 58)
INK = (28, 10, 40)
AMBER = (255, 164, 36)
TANG = (255, 92, 28)
GOLD = (255, 214, 72)
LIME = (168, 255, 80)
VIOLET = (176, 84, 255)
MAG = (255, 64, 168)
CYAN = (72, 230, 255)
PEARL = (255, 244, 230)
G = 980.0
POWER = 1180.0


class Spark:
    __slots__ = ("x", "y", "vx", "vy", "life", "col", "r")

    def __init__(self, x, y, vx, vy, life, col, r=5):
        self.x, self.y, self.vx, self.vy = x, y, vx, vy
        self.life, self.col, self.r = life, col, r


class Shard:
    __slots__ = ("x", "y", "vx", "vy", "r")

    def __init__(self, x, y, vx, vy):
        self.x, self.y, self.vx, self.vy = x, y, vx, vy
        self.r = 11


class Ore:
    __slots__ = ("x", "y", "vx", "r", "phase", "kind", "hp")

    def __init__(self, x, y, vx, kind):
        self.x, self.y, self.vx, self.kind = x, y, vx, kind
        self.r = 34 if kind == "core" else 26
        self.hp = 2 if kind == "core" else 1
        self.phase = random.random() * math.tau


class Game:
    def __init__(self, record: bool):
        self.record = record
        self.surf = pygame.Surface((W, H))
        self.clock = pygame.time.Clock()
        self.font_lg = pygame.font.Font(None, 64)
        self.font_md = pygame.font.Font(None, 42)
        self.font_sm = pygame.font.Font(None, 28)
        self.score = 0
        self.reset()

    def reset(self) -> None:
        self.t = 0.0
        self.cx = W * 0.5
        self.ang = math.radians(90)
        self.cool = 0.0
        self.combo = 1
        self.ores: list[Ore] = []
        self.shots: list[Shard] = []
        self.sparks: list[Spark] = []
        self.stars = [[random.uniform(0, W), random.uniform(80, 1500),
                       random.uniform(1.2, 3.2)] for _ in range(90)]
        self.flash = 0.0
        self.seed_ores()

    def seed_ores(self) -> None:
        self.ores.clear()
        for i in range(9):
            y = 260 + i * 118
            vx = random.choice((-1, 1)) * random.uniform(70, 160)
            x = random.uniform(80, W - 80)
            kind = "core" if i % 3 == 0 else "chunk"
            self.ores.append(Ore(x, y, vx, kind))

    def burst(self, x, y, col, n=16) -> None:
        for _ in range(n):
            a = random.random() * math.tau
            spd = random.uniform(80, 420)
            self.sparks.append(Spark(x, y, math.cos(a) * spd, math.sin(a) * spd,
                                     random.uniform(0.18, 0.45), col, random.randint(3, 8)))

    def fire(self) -> None:
        if self.cool > 0:
            return
        self.cool = 0.28
        vx = math.cos(self.ang) * POWER
        vy = -math.sin(self.ang) * POWER
        muzzle = 78
        sx = self.cx + math.cos(self.ang) * muzzle
        sy = 1688 - math.sin(self.ang) * muzzle
        self.shots.append(Shard(sx, sy, vx, vy))
        self.burst(sx, sy, AMBER, 8)

    def aim_auto(self) -> None:
        if not self.ores:
            return
        best_ang, best_err = self.ang, 1e9
        for ore in self.ores:
            lead = 0.55
            tx = ore.x + ore.vx * lead
            ty = ore.y
            for deg in range(28, 153, 3):
                a = math.radians(deg)
                vx, vy = math.cos(a) * POWER, -math.sin(a) * POWER
                x, y = self.cx + math.cos(a) * 78, 1688 - math.sin(a) * 78
                hit = False
                err = 1e9
                for _ in range(90):
                    x += vx / FPS
                    y += vy / FPS
                    vy += G / FPS
                    if y > 1760 or x < -40 or x > W + 40:
                        break
                    d = math.hypot(x - tx, y - ty)
                    if d < err:
                        err = d
                    if d < ore.r + 16:
                        hit = True
                        err = 0
                        break
                if hit and err <= best_err:
                    best_err, best_ang = err, a
                elif err < best_err - 40:
                    best_err, best_ang = err, a
        self.ang = best_ang
        self.cx += (max(140, min(W - 140, self.cx + math.cos(self.ang) * 12)) - self.cx) * 0.2

    def autoplay(self) -> None:
        self.aim_auto()
        if self.cool <= 0 and self.ores:
            self.fire()

    def handle(self, ev) -> None:
        if ev.type != pygame.KEYDOWN:
            return
        if ev.key in (pygame.K_LEFT, pygame.K_a):
            self.ang = min(math.radians(155), self.ang + math.radians(6))
        elif ev.key in (pygame.K_RIGHT, pygame.K_d):
            self.ang = max(math.radians(25), self.ang - math.radians(6))
        elif ev.key in (pygame.K_q,):
            self.cx = max(120, self.cx - 48)
        elif ev.key in (pygame.K_e,):
            self.cx = min(W - 120, self.cx + 48)
        elif ev.key in (pygame.K_SPACE, pygame.K_w):
            self.fire()
        elif ev.key == pygame.K_r:
            self.score = 0
            self.reset()

    def update(self, dt: float) -> None:
        self.t += dt
        self.flash = max(0.0, self.flash - dt)
        self.cool = max(0.0, self.cool - dt)
        keys = pygame.key.get_pressed() if not self.record else None
        if keys:
            if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                self.ang = min(math.radians(155), self.ang + 1.8 * dt)
            if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                self.ang = max(math.radians(25), self.ang - 1.8 * dt)
            if keys[pygame.K_q]:
                self.cx = max(120, self.cx - 280 * dt)
            if keys[pygame.K_e]:
                self.cx = min(W - 120, self.cx + 280 * dt)
        if self.record:
            self.autoplay()
        for o in self.ores:
            o.x += o.vx * dt
            o.phase += 3.2 * dt
            if o.x < 50 and o.vx < 0:
                o.vx *= -1
            if o.x > W - 50 and o.vx > 0:
                o.vx *= -1
        live_s: list[Shard] = []
        for sh in self.shots:
            sh.vy += G * dt
            sh.x += sh.vx * dt
            sh.y += sh.vy * dt
            if -40 < sh.x < W + 40 and sh.y < 1760:
                live_s.append(sh)
            else:
                if sh.y >= 1760:
                    self.burst(sh.x, 1754, TANG, 10)
        self.shots = live_s
        kept: list[Ore] = []
        for o in self.ores:
            struck = False
            remain: list[Shard] = []
            for sh in self.shots:
                if math.hypot(sh.x - o.x, sh.y - o.y) < o.r + sh.r:
                    o.hp -= 1
                    self.burst(o.x, o.y, GOLD if o.kind == "core" else MAG, 18)
                    self.flash = 0.1
                    struck = True
                else:
                    remain.append(sh)
            self.shots = remain
            if o.hp <= 0:
                pts = 40 if o.kind == "core" else 15
                self.score += pts * self.combo
                self.combo = min(9, self.combo + 1)
                self.burst(o.x, o.y, AMBER, 26)
                y = o.y
                vx = -o.vx if random.random() < 0.5 else o.vx
                kind = "core" if random.random() < 0.28 else "chunk"
                kept.append(Ore(random.choice((-40, W + 40)), y, vx * random.uniform(0.8, 1.3), kind))
            else:
                if struck:
                    self.combo = max(1, self.combo)
                kept.append(o)
        self.ores = kept
        if not self.shots and self.cool <= 0 and random.random() < 0.002:
            self.combo = 1
        live_p: list[Spark] = []
        for sp in self.sparks:
            sp.life -= dt
            if sp.life <= 0:
                continue
            sp.x += sp.vx * dt
            sp.y += sp.vy * dt
            sp.vy += 240 * dt
            live_p.append(sp)
        self.sparks = live_p
        for st in self.stars:
            st[1] += (8 + st[2] * 6) * dt
            if st[1] > 1600:
                st[1] = 90
                st[0] = random.uniform(0, W)

    def hexagon(self, s, cx, cy, r, col, width=0):
        pts = []
        for i in range(6):
            a = math.tau * i / 6 + 0.2
            pts.append((int(cx + math.cos(a) * r), int(cy + math.sin(a) * r)))
        pygame.draw.polygon(s, col, pts, width)

    def draw(self, s: pygame.Surface) -> None:
        s.fill(VOID)
        pygame.draw.rect(s, PLUM, (0, 0, W, 210))
        pygame.draw.rect(s, INK, (0, 1720, W, 200))
        for x, y, r in self.stars:
            pygame.draw.circle(s, (90, 40, 120), (int(x), int(y)), max(1, int(r)))
        pygame.draw.rect(s, (64, 22, 18), (0, 1710, W, 16))
        pygame.draw.rect(s, AMBER, (0, 1710, W, 3))
        for o in self.ores:
            wob = 4 * math.sin(o.phase)
            col = GOLD if o.kind == "core" else MAG
            self.hexagon(s, o.x, o.y + wob, o.r + 4, col, 0)
            self.hexagon(s, o.x, o.y + wob, o.r - 6, PEARL if o.kind == "core" else VIOLET, 0)
            self.hexagon(s, o.x, o.y + wob, o.r + 4, AMBER, 3)
        for sh in self.shots:
            pygame.draw.circle(s, AMBER, (int(sh.x), int(sh.y)), 13)
            pygame.draw.circle(s, PEARL, (int(sh.x - 3), int(sh.y - 3)), 5)
            pygame.draw.circle(s, TANG, (int(sh.x - sh.vx * 0.02), int(sh.y - sh.vy * 0.02)), 7)
        pygame.draw.rect(s, (40, 16, 28), (int(self.cx - 70), 1698, 140, 48), border_radius=16)
        pygame.draw.rect(s, AMBER, (int(self.cx - 70), 1698, 140, 48), 3, border_radius=16)
        pygame.draw.circle(s, TANG, (int(self.cx), 1710), 28)
        pygame.draw.circle(s, GOLD, (int(self.cx), 1710), 28, 3)
        bx = self.cx + math.cos(self.ang) * 86
        by = 1688 - math.sin(self.ang) * 86
        pygame.draw.line(s, (80, 24, 16), (int(self.cx), 1704), (int(bx), int(by) + 8), 26)
        pygame.draw.line(s, AMBER, (int(self.cx), 1698), (int(bx), int(by)), 18)
        pygame.draw.circle(s, PEARL, (int(bx), int(by)), 10)
        for sp in self.sparks:
            pygame.draw.circle(s, sp.col, (int(sp.x), int(sp.y)), max(1, int(sp.r * sp.life * 2.6)))
        if self.flash > 0:
            fl = pygame.Surface((W, H), pygame.SRCALPHA)
            fl.fill((255, 140, 40, int(70 * self.flash / 0.12)))
            s.blit(fl, (0, 0))
        title = self.font_lg.render(TITLE, True, AMBER)
        s.blit(title, title.get_rect(center=(W // 2, 54)))
        handle = self.font_sm.render(HANDLE, True, GOLD)
        s.blit(handle, handle.get_rect(center=(W // 2, 104)))
        hud = self.font_md.render(f"SCORE  {self.score}    x{self.combo}", True, LIME)
        s.blit(hud, hud.get_rect(center=(W // 2, 154)))
        hint = self.font_sm.render("A/D aim   Q/E slide   SPACE fire   R reset   x.com/ElbowOS", True, VIOLET)
        s.blit(hint, hint.get_rect(center=(W // 2, H - 40)))

    def play(self) -> None:
        screen = pygame.display.set_mode((W, H))
        pygame.display.set_caption(TITLE)
        running = True
        while running:
            dt = self.clock.tick(FPS) / 1000.0
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT or (ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE):
                    running = False
                else:
                    self.handle(ev)
            self.update(dt)
            self.draw(self.surf)
            screen.blit(self.surf, (0, 0))
            pygame.display.flip()

    def record_mp4(self, path: str) -> None:
        cmd = [
            "ffmpeg", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
            "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
            "-an", "-c:v", "libx264", "-pix_fmt", "yuv420p",
            "-crf", "20", "-preset", "fast", "-movflags", "+faststart", path,
        ]
        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
        frames = FPS * 15
        for i in range(frames):
            self.update(1.0 / FPS)
            self.draw(self.surf)
            proc.stdin.write(pygame.image.tostring(self.surf, "RGB"))
            if i % 30 == 0:
                print(f"frame {i}/{frames}", flush=True)
        proc.stdin.close()
        rc = proc.wait()
        if rc != 0:
            raise SystemExit(f"ffmpeg failed: {rc}")
        print("wrote", path)


def main() -> None:
    record = "--record" in sys.argv or os.environ.get("ELBOWOS_RECORD") == "1"
    play = "--play" in sys.argv
    if record or not play:
        os.environ["SDL_VIDEODRIVER"] = "dummy"
        os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
    pygame.init()
    pygame.font.init()
    g = Game(record or not play)
    if record or not play:
        out = os.environ.get("ELBOWOS_MP4", "/home/workdir/artifacts/WULFENITE_ARC_ElbowOS.mp4")
        g.record_mp4(out)
    else:
        g.play()
    pygame.quit()


if __name__ == "__main__":
    main()
