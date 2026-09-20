import math
import random
import time
from typing import Any, Dict

from src.plugin_system.base_plugin import BasePlugin


class PixelScenes(BasePlugin):
    """Animated pixel-art scenes for a 128x32 LED matrix."""

    SCENES = (
        "synthwave",
        "lightning",
        "arcade",
        "mardi_gras",
        "american_flag",
        "halloween",
        "christmas",
        "lsu_game_day",
    )

    def __init__(
        self,
        plugin_id,
        config,
        display_manager,
        cache_manager,
        plugin_manager,
    ):
        super().__init__(
            plugin_id,
            config,
            display_manager,
            cache_manager,
            plugin_manager,
        )

        self.display_duration = float(config.get("display_duration", 20))
        self.animation_speed = float(config.get("animation_speed", 1.0))
        self.scene_mode = config.get("scene_mode", "random")

        self.start_time = time.time()
        self.last_update = 0

        self.width = getattr(display_manager, "width", 128)
        self.height = getattr(display_manager, "height", 32)

        self.active_scene = None
        self.last_scene = None

        self.stars = self._make_stars(30)

        # Lightning state
        self.next_lightning = 0
        self.lightning_until = 0
        self.lightning_points = []

        # Arcade state
        self.arcade_stars = self._make_stars(18)

        # Mardi Gras particles
        rng = random.Random(504)
        self.confetti = [
            [
                rng.randrange(self.width),
                rng.randrange(self.height),
                rng.randrange(1, 4),
                rng.randrange(3),
            ]
            for _ in range(30)
        ]

        self.logger.info(
            "Pixel Scenes initialized - %dx%d, mode=%s",
            self.width,
            self.height,
            self.scene_mode,
        )

    def _make_stars(self, count):
        rng = random.Random(12832)
        return [
            (
                rng.randrange(self.width),
                rng.randrange(max(1, self.height // 2)),
                rng.random() * math.pi * 2,
            )
            for _ in range(count)
        ]

    def _enabled_scenes(self):
        enabled = []

        for scene in self.SCENES:
            key = f"enable_{scene}"
            if self.config.get(key, True):
                enabled.append(scene)

        return enabled or ["synthwave"]

    def _choose_scene(self):
        enabled = self._enabled_scenes()

        if self.scene_mode in self.SCENES:
            if self.scene_mode in enabled:
                return self.scene_mode
            return enabled[0]

        choices = enabled[:]

        # Avoid showing the same random scene twice when possible.
        if len(choices) > 1 and self.last_scene in choices:
            choices.remove(self.last_scene)

        return random.choice(choices)

    def _ensure_scene(self, force_clear=False):
        if self.active_scene is None or force_clear:
            self.active_scene = self._choose_scene()
            self.last_scene = self.active_scene
            self.start_time = time.time()

            self.logger.info("Pixel Scenes selected scene: %s", self.active_scene)

    def update(self):
        self.last_update = time.time()

    def display(self, force_clear=False) -> bool:
        try:
            self._ensure_scene(force_clear)

            self.display_manager.clear()

            now = time.time()
            t = (now - self.start_time) * self.animation_speed
            if self.active_scene == "lightning":
                self._draw_lightning(t, now)
            elif self.active_scene == "arcade":
                self._draw_arcade(t)
            elif self.active_scene == "mardi_gras":
                self._draw_mardi_gras(t)
            elif self.active_scene == "american_flag":
                self._draw_american_flag(t)
            elif self.active_scene == "halloween":
                self._draw_halloween(t)
            elif self.active_scene == "christmas":
                self._draw_christmas(t)
            elif self.active_scene == "lsu_game_day":
                self._draw_lsu_game_day(t)
            else:
                self._draw_synthwave(t)
            self.display_manager.update_display()
            return True

        except Exception as exc:
            self.logger.exception("Pixel Scenes display error: %s", exc)
            return False

    # ----------------------------------------------------------
    # SYNTHWAVE
    # ----------------------------------------------------------

    def _draw_synthwave(self, t):
        draw = self.display_manager.draw
        w, h = self.width, self.height

        # Stars
        for x, y, phase in self.stars:
            pulse = math.sin(t * 3.0 + phase)
            c = 100 if pulse < 0 else 220
            draw.point((x, y), fill=(c, c, c))

        horizon = 18

        # Retro sun
        cx = w // 2
        cy = 12
        radius = 8

        for r in range(radius, 1, -1):
            ratio = r / radius
            color = (
                255,
                int(70 + 90 * (1 - ratio)),
                int(20 + 80 * (1 - ratio)),
            )
            draw.ellipse(
                (cx - r, cy - r, cx + r, cy + r),
                fill=color,
            )

        # Horizontal cuts through sun
        for yy in (11, 14, 16):
            draw.line((cx - radius, yy, cx + radius, yy), fill=(0, 0, 0))

        # Horizon
        draw.line((0, horizon, w - 1, horizon), fill=(255, 0, 170))

        # Perspective road/grid
        vanishing_x = w // 2

        for bottom_x in range(-32, w + 33, 16):
            draw.line(
                (vanishing_x, horizon, bottom_x, h - 1),
                fill=(50, 80, 255),
            )

        offset = (t * 10) % 5

        y = horizon + 2 + offset
        while y < h:
            distance = max(1, y - horizon)
            spacing_boost = int(distance / 5)
            draw.line((0, int(y), w - 1, int(y)), fill=(90, 0, 180))
            y += 3 + spacing_boost

        # Shooting pixel
        sx = int((t * 30) % (w + 20)) - 10
        sy = 5 + int(2 * math.sin(t * 2))
        draw.line((sx - 5, sy, sx, sy), fill=(80, 80, 255))
        draw.point((sx, sy), fill=(255, 255, 255))

    # ----------------------------------------------------------
    # LIGHTNING STORM
    # ----------------------------------------------------------

    def _new_lightning(self, now):
        rng = random.Random(time.time_ns())

        x = rng.randrange(15, max(16, self.width - 15))
        y = 0
        points = [(x, y)]

        while y < self.height - 4:
            y += rng.randrange(3, 7)
            x += rng.randrange(-7, 8)
            x = max(2, min(self.width - 3, x))
            points.append((x, min(y, self.height - 1)))

        self.lightning_points = points
        self.lightning_until = now + 0.16
        self.next_lightning = now + rng.uniform(1.2, 3.8)

    def _draw_lightning(self, t, now):
        draw = self.display_manager.draw
        w, h = self.width, self.height

        # Moving rain
        for i in range(35):
            x = (i * 29 + int(t * 20)) % w
            y = (i * 13 + int(t * 28)) % h
            draw.line((x, y, x - 1, min(h - 1, y + 2)), fill=(20, 70, 130))

        # Cloud bank
        for x in range(-5, w + 10, 11):
            yy = 4 + ((x // 11) % 3)
            draw.ellipse((x, yy, x + 16, yy + 7), fill=(22, 22, 40))

        if now >= self.next_lightning:
            self._new_lightning(now)

        if now <= self.lightning_until and len(self.lightning_points) > 1:
            # Brief sky flash
            draw.rectangle((0, 0, w - 1, h - 1), outline=(70, 70, 110))

            for a, b in zip(self.lightning_points[:-1], self.lightning_points[1:]):
                draw.line((a[0], a[1], b[0], b[1]), fill=(255, 255, 255))

            # Small branch
            mid = self.lightning_points[len(self.lightning_points) // 2]
            draw.line(
                (mid[0], mid[1], mid[0] + 8, min(h - 1, mid[1] + 5)),
                fill=(130, 150, 255),
            )

        # Ground
        draw.line((0, h - 3, w - 1, h - 3), fill=(20, 80, 40))

    # ----------------------------------------------------------
    # RETRO ARCADE
    # ----------------------------------------------------------

    def _draw_arcade(self, t):
        draw = self.display_manager.draw
        w, h = self.width, self.height

        # Star field moving left
        for x0, y, phase in self.arcade_stars:
            x = int((x0 - t * (12 + phase)) % w)
            brightness = 100 + int((phase / (math.pi * 2)) * 120)
            draw.point((x, y), fill=(brightness, brightness, brightness))

        # Pixel spaceship
        ship_x = 14
        ship_y = int(h / 2 + math.sin(t * 2.3) * 6)

        ship = [
            (0, 0), (1, 0), (2, 0),
            (3, -1), (4, -1),
            (3, 1), (4, 1),
            (5, 0),
        ]

        for px, py in ship:
            draw.rectangle(
                (
                    ship_x + px * 2,
                    ship_y + py * 2,
                    ship_x + px * 2 + 1,
                    ship_y + py * 2 + 1,
                ),
                fill=(40, 220, 255),
            )

        # Engine flame
        flame = 2 + int((math.sin(t * 15) + 1))
        draw.line(
            (ship_x - flame, ship_y, ship_x - 1, ship_y),
            fill=(255, 80, 20),
        )

        # Laser
        laser_x = int((t * 55) % (w + 30))
        if laser_x > ship_x + 12:
            draw.line(
                (laser_x, ship_y, min(w - 1, laser_x + 7), ship_y),
                fill=(50, 255, 80),
            )

        # Asteroids
        for i in range(4):
            ax = int((w + 30 - (t * (16 + i * 3) + i * 34)) % (w + 40))
            ay = 5 + ((i * 9) % 23)
            size = 2 + (i % 2)

            draw.rectangle(
                (ax - size, ay - size, ax + size, ay + size),
                outline=(180, 120, 60),
            )

    # ----------------------------------------------------------
    # MARDI GRAS
    # ----------------------------------------------------------

    def _draw_mardi_gras(self, t):
        draw = self.display_manager.draw
        w, h = self.width, self.height

        colors = [
            (100, 20, 180),   # purple
            (30, 180, 60),    # green
            (255, 190, 20),   # gold
        ]

        # Animated confetti
        for index, particle in enumerate(self.confetti):
            x0, y0, speed, color_index = particle

            x = int((x0 + math.sin(t + index) * 5) % w)
            y = int((y0 + t * speed * 5) % h)

            draw.point((x, y), fill=colors[color_index])

        # Bead strands
        for strand in range(3):
            base_y = 7 + strand * 8
            color = colors[strand]

            for x in range(0, w, 5):
                yy = int(base_y + math.sin((x / 10.0) + t * 2 + strand) * 2)
                draw.ellipse((x, yy, x + 2, yy + 2), fill=color)

        # Central fleur-de-lis inspired pixel symbol
        cx = w // 2
        cy = h // 2

        gold = (255, 190, 20)

        pixels = [
            (0, -7),
            (-1, -6), (0, -6), (1, -6),
            (-2, -5), (0, -5), (2, -5),
            (-3, -4), (-1, -4), (0, -4), (1, -4), (3, -4),
            (-2, -3), (-1, -3), (0, -3), (1, -3), (2, -3),
            (-1, -2), (0, -2), (1, -2),
            (0, -1),
            (-4, 0), (-3, 0), (-2, 0), (-1, 0),
            (0, 0),
            (1, 0), (2, 0), (3, 0), (4, 0),
            (-2, 1), (-1, 1), (0, 1), (1, 1), (2, 1),
            (-1, 2), (0, 2), (1, 2),
            (0, 3), (0, 4), (0, 5),
            (-2, 5), (-1, 5), (0, 5), (1, 5), (2, 5),
        ]

        for px, py in pixels:
            draw.rectangle(
                (
                    cx + px * 2,
                    cy + py,
                    cx + px * 2 + 1,
                    cy + py,
                ),
                fill=gold,
            )

    # ----------------------------------------------------------
    # AMERICAN FLAG
    # ----------------------------------------------------------

    def _draw_american_flag(self, t):
        draw = self.display_manager.draw
        w, h = self.width, self.height

        red = (220, 20, 30)
        white = (235, 235, 225)
        blue = (20, 45, 130)

        # 13 stripes compressed into the 32-pixel-high display.
        for y in range(h):
            stripe = int((y * 13) / h)
            base_color = red if stripe % 2 == 0 else white

            for x in range(w):
                # Horizontal wave that becomes slightly stronger
                # toward the fly end of the flag.
                strength = 0.7 + (x / max(1, w - 1)) * 2.2
                wave = int(
                    math.sin((x * 0.13) - (t * 4.0)) * strength
                )

                source_y = y + wave

                if source_y < 0 or source_y >= h:
                    continue

                source_stripe = int((source_y * 13) / h)
                color = red if source_stripe % 2 == 0 else white

                # Subtle moving highlight/shadow gives the flag
                # a cloth-like appearance.
                shade = math.sin((x * 0.13) - (t * 4.0))

                if shade > 0.55:
                    color = tuple(min(255, c + 18) for c in color)
                elif shade < -0.55:
                    color = tuple(max(0, c - 30) for c in color)

                draw.point((x, y), fill=color)

        # Blue canton: roughly traditional flag proportions,
        # adapted to the tiny 128x32 canvas.
        canton_w = int(w * 0.40)
        canton_h = int(h * 0.54)

        for y in range(canton_h):
            for x in range(canton_w):
                strength = 0.7 + (x / max(1, w - 1)) * 2.2
                wave = int(
                    math.sin((x * 0.13) - (t * 4.0)) * strength
                )

                yy = y + wave

                if 0 <= yy < h:
                    draw.point((x, yy), fill=blue)

        # Pixel-star field.
        #
        # At 32 pixels high we cannot render recognizable 5-point
        # stars at realistic scale, so bright pixels create the
        # visual impression of the star field.
        rows = 9

        for row in range(rows):
            stars = 6 if row % 2 == 0 else 5

            for col in range(stars):
                if stars == 6:
                    sx = 4 + col * 8
                else:
                    sx = 8 + col * 8

                sy = 2 + row * 2

                if sx >= canton_w or sy >= canton_h:
                    continue

                strength = 0.7 + (sx / max(1, w - 1)) * 2.2
                wave = int(
                    math.sin((sx * 0.13) - (t * 4.0)) * strength
                )

                sy += wave

                if 0 <= sy < h:
                    draw.point((sx, sy), fill=(255, 255, 255))

        # Dark left edge gives the impression that the flag
        # is attached to a pole just outside the display.
        draw.line((0, 0, 0, h - 1), fill=(80, 80, 80)) 





    # ----------------------------------------------------------
    # HALLOWEEN
    # ----------------------------------------------------------

    def _draw_halloween(self, t):
        draw = self.display_manager.draw
        w, h = self.width, self.height

        orange = (255, 90, 0)
        yellow = (255, 210, 30)
        purple = (90, 20, 130)
        white = (220, 220, 230)

        # Moon
        draw.ellipse((w - 25, 2, w - 10, 17), fill=(150, 150, 110))
        draw.ellipse((w - 21, 1, w - 8, 14), fill=(0, 0, 0))

        # Drifting stars
        for i in range(15):
            x = (i * 23 + int(t * 3)) % w
            y = 2 + ((i * 7) % 12)
            draw.point((x, y), fill=purple)

        # Pumpkin
        cx = w // 2
        cy = 20

        draw.ellipse((cx - 13, cy - 8, cx + 13, cy + 8), fill=orange)
        draw.ellipse((cx - 9, cy - 8, cx + 9, cy + 8), outline=(180, 45, 0))
        draw.rectangle((cx - 2, cy - 12, cx + 2, cy - 8), fill=(40, 130, 40))

        # Eyes
        draw.polygon(
            [(cx - 8, cy - 3), (cx - 3, cy - 3), (cx - 5, cy + 1)],
            fill=yellow,
        )
        draw.polygon(
            [(cx + 3, cy - 3), (cx + 8, cy - 3), (cx + 5, cy + 1)],
            fill=yellow,
        )

        # Animated mouth
        glow = yellow if int(t * 4) % 2 == 0 else (180, 80, 0)

        for x in range(cx - 8, cx + 9, 4):
            draw.rectangle((x, cy + 4, x + 2, cy + 6), fill=glow)

        # Ghost drifting across display
        gx = int((t * 15) % (w + 25)) - 12
        gy = 8 + int(math.sin(t * 2) * 3)

        draw.ellipse((gx - 5, gy - 5, gx + 5, gy + 5), fill=white)
        draw.rectangle((gx - 5, gy, gx + 5, gy + 6), fill=white)

        draw.point((gx - 2, gy - 1), fill=(0, 0, 0))
        draw.point((gx + 2, gy - 1), fill=(0, 0, 0))


    # ----------------------------------------------------------
    # CHRISTMAS
    # ----------------------------------------------------------

    def _draw_christmas(self, t):
        draw = self.display_manager.draw
        w, h = self.width, self.height

        # Snow
        for i in range(32):
            x = (i * 31 + int(math.sin(t + i) * 5)) % w
            y = int((i * 11 + t * (4 + i % 3)) % h)
            draw.point((x, y), fill=(180, 210, 255))

        # Ground snow
        draw.rectangle((0, h - 4, w - 1, h - 1), fill=(180, 210, 230))

        cx = w // 2

        # Tree
        draw.polygon(
            [(cx, 3), (cx - 10, 17), (cx + 10, 17)],
            fill=(20, 130, 45),
        )
        draw.polygon(
            [(cx, 8), (cx - 15, 24), (cx + 15, 24)],
            fill=(15, 110, 35),
        )
        draw.rectangle((cx - 2, 24, cx + 2, 29), fill=(110, 60, 20))

        # Star
        star = (255, 220, 40)
        draw.point((cx, 1), fill=star)
        draw.line((cx - 2, 3, cx + 2, 3), fill=star)
        draw.line((cx, 1, cx, 5), fill=star)

        # Blinking lights
        colors = [
            (255, 30, 30),
            (255, 210, 20),
            (30, 100, 255),
            (220, 30, 220),
        ]

        lights = [
            (-4, 9), (4, 11),
            (-8, 15), (0, 15), (8, 16),
            (-11, 21), (-4, 20), (4, 22), (11, 20),
        ]

        phase = int(t * 4)

        for i, (dx, dy) in enumerate(lights):
            color = colors[(i + phase) % len(colors)]
            draw.rectangle(
                (cx + dx, dy, cx + dx + 1, dy + 1),
                fill=color,
            )


    # ----------------------------------------------------------
    # LSU GAME DAY
    # ----------------------------------------------------------

    def _draw_lsu_game_day(self, t):
        draw = self.display_manager.draw
        w, h = self.width, self.height

        purple = (70, 20, 120)
        gold = (255, 190, 20)
        white = (245, 245, 245)

        # Animated purple/gold background bands
        offset = int(t * 20) % 32

        for x in range(-32, w + 32, 32):
            xx = x + offset
            draw.polygon(
                [(xx, 0), (xx + 16, 0), (xx - 2, h - 1), (xx - 18, h - 1)],
                fill=purple,
            )
            draw.polygon(
                [(xx + 16, 0), (xx + 32, 0), (xx + 14, h - 1), (xx - 2, h - 1)],
                fill=gold,
            )

        # Dark center panel for readability
        cx = w // 2
        draw.rectangle((cx - 27, 5, cx + 27, 27), fill=(15, 5, 25))
        draw.rectangle((cx - 27, 5, cx + 27, 27), outline=gold)

        # Pixel LSU letters
        patterns = {
            "L": [
                "100",
                "100",
                "100",
                "100",
                "111",
            ],
            "S": [
                "111",
                "100",
                "111",
                "001",
                "111",
            ],
            "U": [
                "101",
                "101",
                "101",
                "101",
                "111",
            ],
        }

        scale = 3
        letter_width = 3 * scale
        spacing = 3
        total_width = letter_width * 3 + spacing * 2
        start_x = cx - total_width // 2
        start_y = 8

        for letter_index, letter in enumerate(("L", "S", "U")):
            ox = start_x + letter_index * (letter_width + spacing)

            for row, pattern in enumerate(patterns[letter]):
                for col, bit in enumerate(pattern):
                    if bit == "1":
                        x1 = ox + col * scale
                        y1 = start_y + row * scale
                        draw.rectangle(
                            (x1, y1, x1 + scale - 1, y1 + scale - 1),
                            fill=gold if letter_index != 1 else white,
                        )

        # Pulsing corner pixels
        pulse = gold if int(t * 5) % 2 == 0 else purple
        draw.rectangle((2, 2, 5, 5), fill=pulse)
        draw.rectangle((w - 6, 2, w - 3, 5), fill=pulse)
        draw.rectangle((2, h - 6, 5, h - 3), fill=pulse)
        draw.rectangle((w - 6, h - 6, w - 3, h - 3), fill=pulse)



    def get_display_duration(self):
        return self.display_duration

    def validate_config(self) -> bool:
        try:
            duration = float(self.config.get("display_duration", 20))
            speed = float(self.config.get("animation_speed", 1.0))

            return (
                5 <= duration <= 300
                and 0.25 <= speed <= 4.0
            )
        except (TypeError, ValueError):
            return False

    def get_info(self) -> Dict[str, Any]:
        return {
            "name": "Pixel Scenes",
            "version": "0.4.1",
            "active_scene": self.active_scene or "not selected",
            "scene_mode": self.scene_mode,
            "resolution": f"{self.width}x{self.height}",
        }
