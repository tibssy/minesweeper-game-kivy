from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.lang import Builder


Builder.load_file('layout.kv')


class MainLayout(BoxLayout):
    pass


class MinesweeperApp(App):
    def build(self):
        return MainLayout()


if __name__ == "__main__":
    MinesweeperApp().run()