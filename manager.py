"""
Pixel Scenes Plugin for LEDMatrix

Animated pixel-art scenes designed primarily for 128x32 LED matrices.
"""

import math
import time
import random
from typing import Dict, Any

from src.plugin_system.base_plugin import BasePlugin


class PixelScenes(BasePlugin):

    def __init__(self, plugin_id: str, config: Dict[str, Any],
                 display_manager, cache_manager, plugin_manager):

        super().__init__(
            plugin_id,
            config,
            display_manager,
            cache_manager,
            plugin_manager
        )

        self.animation_speed = float(config.get("animation_speed", 1.0))

        self.start_time = time.time()

        # Fixed stars so they don't randomly jump around every frame.
        rng = random.Random(12832)

        self.stars = [
            (
                rng.randrange(0, max(1, self.display_manager.width)),
                rng.randrange(0, max(1, self.display_manager.height // 2)),
                rng.randrange(0, 3)
            )
            for _ in range(28)
        ]

        self.logger.info(
            "Pixel Scenes initialized for %dx%d display",
            self.display_manager.width,
            self.display_manager.height
        )

    def update(self) -> None:
        """No external data required."""
        self.last_update = time.time()

    def display(self, force_clear: bool = False) -> bool:
        """Render one frame of the retro horizon animation."""

        try:
            width = self.display_manager.width
            height = self.display_manager.height

            elapsed = (time.time() - self.start_time) * self.animation_speed

            self.display_manager.clear()

            draw = self.display_manager.draw

            # ---------------------------------------------------------
            # STAR FIELD
            # ---------------------------------------------------------

            for x, y, phase in self.stars:

                twinkle = int(elapsed * 3 + phase) % 3

                if twinkle == 0:
                    color = (70, 70, 110)
                elif twinkle == 1:
                    color = (150, 150, 210)
                else:
                    color = (255, 255, 255)

                draw.point((x, y), fill=color)

            # ---------------------------------------------------------
            # RETRO SUN
            # ---------------------------------------------------------

            sun_x = width // 2
            sun_y = max(7, height // 3)
            sun_radius = max(5, min(9, height // 4))

            # Outer glow
            draw.ellipse(
                (
                    sun_x - sun_radius - 1,
                    sun_y - sun_radius - 1,
                    sun_x + sun_radius + 1,
                    sun_y + sun_radius + 1
                ),
                fill=(90, 20, 80)
            )

            # Sun
            draw.ellipse(
                (
                    sun_x - sun_radius,
                    sun_y - sun_radius,
                    sun_x + sun_radius,
                    sun_y + sun_radius
                ),
                fill=(255, 80, 100)
            )

            # Bright center
            draw.ellipse(
                (
                    sun_x - sun_radius + 2,
                    sun_y - sun_radius + 2,
                    sun_x + sun_radius - 2,
                    sun_y + sun_radius - 2
                ),
                fill=(255, 150, 50)
            )

            # Horizontal sun bands
            for offset in range(-sun_radius + 2, sun_radius, 3):
                y = sun_y + offset

                if y > sun_y:
                    draw.line(
                        (sun_x - sun_radius, y,
                         sun_x + sun_radius, y),
                        fill=(60, 0, 40)
                    )

            # ---------------------------------------------------------
            # HORIZON
            # ---------------------------------------------------------

            horizon_y = max(height // 2, 17)

            draw.line(
                (0, horizon_y, width - 1, horizon_y),
                fill=(255, 40, 180)
            )

            # ---------------------------------------------------------
            # MOVING FLOOR GRID
            # ---------------------------------------------------------

            bottom = height - 1
            center_x = width // 2

            # Perspective lines
            for bottom_x in range(-32, width + 33, 16):
                draw.line(
                    (center_x, horizon_y,
                     bottom_x, bottom),
                    fill=(80, 40, 180)
                )

            # Animated horizontal grid lines
            grid_phase = (elapsed * 5.0) % 6.0

            for i in range(7):
                distance = i * 3 + grid_phase

                # Perspective spacing gets wider toward the viewer.
                y = horizon_y + int((distance * distance) / 12)

                if horizon_y < y < height:
                    draw.line(
                        (0, y, width - 1, y),
                        fill=(40, 80, 180)
                    )

            # ---------------------------------------------------------
            # MOVING SHOOTING PIXEL
            # ---------------------------------------------------------

            shooting_x = int((elapsed * 25) % (width + 20)) - 10
            shooting_y = 4

            if 0 <= shooting_x < width:
                draw.line(
                    (
                        max(0, shooting_x - 5),
                        shooting_y,
                        shooting_x,
                        shooting_y
                    ),
                    fill=(255, 255, 255)
                )

            self.display_manager.update_display()

            return True

        except Exception as exc:
            self.logger.error(
                "Pixel Scenes display error: %s",
                exc,
                exc_info=True
            )
            return False

    def get_display_duration(self) -> float:
        return float(self.config.get("display_duration", 20.0))

    def validate_config(self) -> bool:
        if not super().validate_config():
            return False

        if self.animation_speed <= 0:
            self.logger.error("animation_speed must be greater than zero")
            return False

        return True

    def get_info(self) -> Dict[str, Any]:
        info = super().get_info()

        info.update({
            "scene": "retro_horizon",
            "animation_speed": self.animation_speed,
            "resolution": (
                f"{self.display_manager.width}x"
                f"{self.display_manager.height}"
            )
        })

        return info
