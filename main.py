from kivy.app import App
from kivy.uix.screenmanager import ScreenManager
from kivy.lang import Builder
from kivy.core.window import Window
from kivy.properties import StringProperty, ListProperty, ColorProperty
from kivy.animation import Animation

from colorsys import hls_to_rgb

from configurations import Hue, DarkTheme, LightTheme, GameMode, Icons


Builder.load_file('layout.kv')


if Window._is_desktop:
    Window.size = 500, 1000


class MainLayout(ScreenManager):
    primary_background = ColorProperty([47/255, 41/255, 34/255, 1])
    secondary_background = ColorProperty([0.1,0.1,0.1,1])
    primary_accent = ColorProperty([254/255, 209/255, 153/255, 1])
    secondary_accent = ColorProperty([254/255, 209/255, 153/255, 1])
    theme = StringProperty('dark')
    color = StringProperty('orange')


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

    def toggle_screen(self):
        if self.current == 'main_screen':
            self.transition.mode = 'pop'
            self.transition.direction = 'up'
            self.current = 'game_screen'

        else:
            self.transition.mode = 'push'
            self.transition.direction = 'down'
            self.current = 'main_screen'


class MinesweeperApp(App):


    def build(self):
        return MainLayout()


if __name__ == "__main__":
    MinesweeperApp().run()