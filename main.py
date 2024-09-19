from typing import List, Callable, Optional, Tuple
from functools import partial
from colorsys import hls_to_rgb
import numpy as np
from collections import deque
from threading import Thread

from kivy.app import App
from kivy.uix.screenmanager import ScreenManager
from kivy.lang import Builder
from kivy.core.window import Window
from kivy.properties import StringProperty, ListProperty, ColorProperty, NumericProperty
from kivy.animation import Animation
from kivy.uix.widget import Widget
from kivy.factory import Factory
from kivy.clock import Clock
from kivy.graphics import Rectangle, Color, RoundedRectangle
from kivy.core.text import Label as CoreLabel

from configurations import Hue, DarkTheme, LightTheme, GameSize, GameMode, Icons


Builder.load_file('layout.kv')


if Window._is_desktop:
    Window.size = 500, 1000


class GameLogic:
    def __init__(
            self,
            cols: int = 10,
            rows: int = 10,
            number_of_mines: int = 10
    ):
        self.cols = cols
        self.rows = rows
        self.number_of_mines = number_of_mines
        self.game_matrix = np.zeros((self.rows, self.cols), dtype=np.uint8)
        self.mask = np.ones((3, 3), dtype=int)
        self.initialize_mines()

    def initialize_mines(self) -> None:
        matrix = self.game_matrix.copy()

        random_mines = np.random.choice(self.game_matrix.size, self.number_of_mines, replace=False)

        for mine in random_mines:
            mask = self.mask.copy()
            mask[1, 1] = 9
            pos_y, pos_x = divmod(mine, self.cols)
            pos_y, pos_x = pos_y - 1, pos_x - 1

            if pos_x < 0:
                mask = mask[:, 1:]
                pos_x = 0
            elif pos_x > self.cols - 3:
                mask = mask[:, :-1]

            if pos_y < 0:
                mask = mask[1:, :]
                pos_y = 0
            elif pos_y > self.rows - 3:
                mask = mask[:-1, :]

            new_matrix = self.game_matrix.copy()
            new_matrix[
                pos_y:pos_y + mask.shape[0],
                pos_x:pos_x + mask.shape[1]
            ] = mask
            matrix += new_matrix

        self.game_matrix = matrix

    def validate_flags(self, flags: set) -> bool:
        positions = map(tuple, np.argwhere(self.game_matrix >= 9).tolist())
        return not bool(set.difference(set(positions), flags))

    def get_connected_component(self, position: list | tuple):
        zero_positions = np.argwhere(self.game_matrix == 0)
        zeros = np.zeros_like(self.game_matrix, dtype=np.uint8)
        zero_set = set(map(tuple, zero_positions))
        component = np.array([position])

        queue = deque([position])
        visited = set()
        visited.add(position)

        directions = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]

        while queue:
            current = queue.popleft()

            for direction in directions:
                new_position = (current[0] + direction[0], current[1] + direction[1])

                if new_position in zero_set and new_position not in visited:
                    visited.add(new_position)
                    queue.append(new_position)
                    component = np.vstack([component, new_position])

        for pos in component:
            pos_start = np.clip(pos - 1, 0, [self.rows - 1, self.cols - 1])
            pos_end = np.clip(pos + 1, 0, [self.rows - 1, self.cols - 1])

            zeros[pos_start[0]:pos_end[0] + 1, pos_start[1]:pos_end[1] + 1] = 1

        return np.argwhere(zeros)


class MainLayout(ScreenManager):
    primary_background = ColorProperty([47/255, 41/255, 34/255, 1])
    secondary_background = ColorProperty([76/255,65/255,51/255,1])
    primary_accent = ColorProperty([245/255, 162/255, 61/255, 1])
    secondary_accent = ColorProperty([254/255, 209/255, 153/255, 1])
    theme = StringProperty('dark')
    color = StringProperty('orange')
    game_size = StringProperty('medium')
    difficulty = StringProperty('easy')

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_game_size(self.game_size)

    def toggle_dark_mode(self, theme):
        self.theme = theme.lower()
        self.set_color_theme(self.color)

    def set_color_theme(self, color):
        self.color = color.lower()
        hue = Hue[color.upper()].value / 360
        modes = {
            'dark': {
                'PRIMARY_BACKGROUND': DarkTheme.PRIMARY_BACKGROUND.value,
                'SECONDARY_BACKGROUND': DarkTheme.SECONDARY_BACKGROUND.value,
                'PRIMARY_ACCENT': DarkTheme.PRIMARY_ACCENT.value,
                'SECONDARY_ACCENT': DarkTheme.SECONDARY_ACCENT.value
            },
            'light': {
                'PRIMARY_BACKGROUND': LightTheme.PRIMARY_BACKGROUND.value,
                'SECONDARY_BACKGROUND': LightTheme.SECONDARY_BACKGROUND.value,
                'PRIMARY_ACCENT': LightTheme.PRIMARY_ACCENT.value,
                'SECONDARY_ACCENT': LightTheme.SECONDARY_ACCENT.value
            }
        }

        primary_background = [*hls_to_rgb(hue, *modes[self.theme]['PRIMARY_BACKGROUND'][::-1]), 1]
        secondary_background = [*hls_to_rgb(hue, *modes[self.theme]['SECONDARY_BACKGROUND'][::-1]), 1]
        primary_accent = [*hls_to_rgb(hue, *modes[self.theme]['PRIMARY_ACCENT'][::-1]), 1]
        secondary_accent = [*hls_to_rgb(hue, *modes[self.theme]['SECONDARY_ACCENT'][::-1]), 1]

        animate = Animation(
            primary_background=primary_background,
            secondary_background=secondary_background,
            primary_accent=primary_accent,
            secondary_accent=secondary_accent,
            duration=1,
            transition='out_expo'
        )
        animate.start(self)

    def set_game_size(self, size):
        self.game_size = size.lower()
        cols, rows = GameSize[size.upper()].value
        self.ids.game_board.cols = cols
        self.ids.game_board.rows = rows




    def toggle_screen(self):
        if self.current == 'main_screen':
            self.transition.mode = 'pop'
            self.transition.direction = 'up'
            self.current = 'game_screen'

        else:
            self.transition.mode = 'push'
            self.transition.direction = 'down'
            self.current = 'main_screen'


class GameBoard(Widget):
    rows = NumericProperty(16)
    cols = NumericProperty(8)
    gap = NumericProperty(5)
    background_color = ColorProperty([0.4, 0.4, 0.4])
    color = ColorProperty([0, 0, 0, 1])

    def __init__(
            self,
            press_time=1,
            on_release=None,
            **kwargs
    ):
        super().__init__(**kwargs)
        self.press_time = press_time
        self.is_long_press = False
        self.on_release = on_release
        self.squares = {}
        self.bind(size=self.update_board, pos=self.update_board)
        self.bind(rows=self.update_board, cols=self.update_board)
        self.draw_board()

    def update_board(self, *args):
        self.canvas.clear()
        self.draw_board()

    def draw_board(self):
        square_width = (self.width - self.gap * (self.cols + 1)) / self.cols
        square_height = (self.height - self.gap * (self.rows + 1)) / self.rows

        with self.canvas:
            for row in range(self.rows):
                for col in range(self.cols):
                    self._draw_square(row, col, square_width, square_height)

    def _draw_square(self, row, col, square_width, square_height):
        x, y = self._calculate_square_position(row, col, square_width, square_height)
        square_data = self.squares.get((row, col), {})
        background_color = square_data.get('background_color', self.background_color)

        Color(*background_color)
        RoundedRectangle(pos=(x, y), size=(square_width, square_height), radius=[5])
        self._draw_square_text(square_data, x, y, square_width, square_height)

    def _calculate_square_position(self, row, col, square_width, square_height):
        x = col * (square_width + self.gap) + self.gap + self.pos[0]
        y = row * (square_height + self.gap) + self.gap + self.pos[1]
        return x, y

    def _draw_square_text(self, square_data, x, y, square_width, square_height):
        text = square_data.get('text')
        if text:
            color = square_data.get('color', (1, 1, 1, 1))
            self.draw_text(text, color, x, y, square_width, square_height)

    def draw_text(self, text, color, x, y, square_width, square_height):
        label = CoreLabel(text=text, font_size=min(square_width, square_height) * 0.8, bold=True, color=color)
        label.refresh()
        text_size = label.texture.size
        text_x = x + (square_width - text_size[0]) / 2
        text_y = y + (square_height - text_size[1]) / 2

        with self.canvas.after:
            Rectangle(texture=label.texture, pos=(text_x, text_y), size=text_size)

    def set_square(self, row, col, background_color=None, text=None, color=(1, 1, 1, 1)):
        if background_color is None:
            background_color = self.background_color
        self.squares[(row, col)] = {'background_color': background_color, 'text': text, 'color': color}
        self.update_board()

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            self.is_long_press = False
            Clock.schedule_once(partial(self._set_long_press, touch), self.press_time)
            touch.grab(self)
            return True

    def on_touch_up(self, touch):
        if touch.grab_current is self:
            touch.ungrab(self)
            if not self.is_long_press:
                # self._trigger_callback()
                self.set_square(*self._get_touch_on_grid(touch), (0, 0, 0, 0))
            return True

    def _set_long_press(self, touch, dt=0):
        if touch.time_end == -1:
            self.is_long_press = True
            # self._trigger_callback()
            self.set_square(*self._get_touch_on_grid(touch), (0.2, 0.2, 0.8, 1))

    def _get_touch_on_grid(self, touch):
        local_x, local_y = self.to_local(touch.ox, touch.oy, relative=True)
        return int(local_y / self.height * self.rows), int(local_x / self.width * self.cols)

    def _trigger_callback(self):
        if callable(self.on_release):
            self.on_release(self)



class BoardButton(Widget):
    def __init__(
            self,
            press_time=1,
            on_release=None,
            **kwargs
    ):
        super().__init__(**kwargs)
        self.press_time = press_time
        self.is_long_press = False
        self.on_release = on_release


    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            self.is_long_press = False
            Clock.schedule_once(partial(self._set_long_press, touch), self.press_time)
            touch.grab(self)
            return True

    def on_touch_up(self, touch):
        if touch.grab_current is self:
            touch.ungrab(self)
            if not self.is_long_press:
                self._trigger_callback()
            return True

    def _set_long_press(self, touch, dt=0):
        if touch.time_end == -1:
            self.is_long_press = True
            self._trigger_callback()

    def _trigger_callback(self):
        if callable(self.on_release):
            self.on_release(self)



class MinesweeperApp(App):
    def build(self):
        return MainLayout()


    def build_game(self):
        pass
        print(self.root.game_size)
        width, height = GameSize[self.root.game_size.upper()].value

        game = GameLogic(
            cols=width,
            rows=height,
            number_of_mines=10
        )
        print(game.game_matrix)
        # self.root.ids.game_grid.cols = width
        #
        # for id in range(width * height):
        #     button = BoardButton()
        #     button.radius = 5
        #     button.color = self.root.primary_accent if id % 2 else self.root.secondary_accent
        #     button.on_release = self.set_button
        #     self.root.ids.game_grid.add_widget(button)


    def set_button(self, instance):
        instance.color = (0,1,0,1) if instance.is_long_press else (1,0,0,1)


if __name__ == "__main__":
    MinesweeperApp().run()