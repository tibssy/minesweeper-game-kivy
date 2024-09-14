from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.screenmanager import ScreenManager
from kivy.lang import Builder
from kivy.core.window import Window
from kivy.factory import Factory


Builder.load_file('layout.kv')


if Window._is_desktop:
    Window.size = 500, 1000


class MainLayout(ScreenManager):
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
    is_desktop = Window._is_desktop

    def build(self):
        print(self.is_desktop)
        return MainLayout()


if __name__ == "__main__":
    MinesweeperApp().run()