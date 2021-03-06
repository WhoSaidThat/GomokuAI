from threading import Thread
import time

import kivy
from kivy.app import App
from kivy.clock import mainthread
from kivy.graphics import Color, Line
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.image import Image
from kivy.uix.label import Label

from game import GomokuGame, BoardUpdateEvent, GameOverEvent, MoveEvent
from player import GuiPlayer, RandomAIPlayer, ReinforceAIPlayer, GuiTestPlayer, ReinforceRandomPlayer
from rl_network.critic_network import CriticNN
from utils import file_to_patterns, extract_features

kivy.require('1.9.1')


class BoardLayout(FloatLayout):
    """The main layout for gomoku game."""
    def __init__(self, **kwargs):
        super(BoardLayout, self).__init__(**kwargs)
        self.add_widget(Image(source='img/wood.jpg', keep_ratio=False, allow_stretch=True))
        self.board_grid = BoardGrid(pos_hint={'center_x': 0.5})
        self.add_widget(self.board_grid)

    def on_size(self, instance, val):
        side = min(instance.size)
        self.board_grid.size = (side, side)


class BoardGrid(GridLayout):
    """The grid that holds all stones."""
    def __init__(self, **kwargs):
        super(BoardGrid, self).__init__(**kwargs)
        self.size_hint = (None, None)
        self.rows = self.cols = 15
        self.last_stone = None
        for row in range(15):
            for col in range(15):
                self.add_widget(Stone((row, col)))

    def on_size(self, instance, val):
        self.draw_grid()

    def on_pos(self, instance, val):
        self.draw_grid()

    @mainthread
    def update_stone(self, event):
        n = event.move[0] * 15 + event.move[1]
        # The children seems to be reversed...
        stone = self.children[224-n]
        stone.show_stone(event.stone_color)
        if self.last_stone:
            self.last_stone.remove_dot()
        self.last_stone = stone

    def board_value_listener(self, event):
        return
        patterns = file_to_patterns('pattern.txt')
        feature = extract_features(event.board.board, patterns)
        cnn = CriticNN(len(feature))
        children = []
        features = []
        for pos, next_board in event.board.enumerate_next_board():
            n = pos[0] * 15 + pos[1]
            stone = self.children[224-n]
            if stone.has_stone():
                continue
            else:
                children.append(stone)
                feature = extract_features(next_board, patterns)
                features.append(feature)
        for child, v in zip(children, cnn.run_value(features)):
            child.show_value(v[0])

    def draw_grid(self):
        self.canvas.before.clear()
        with self.canvas.before:
            delta = self.height / self.rows
            padding_y = delta / 2
            padding_x = delta / 2

            # draw white lines
            Color(1, 1, 1, .8)
            for i in range(15):
                x0, y0 = self.x + padding_x, self.y + padding_y + i * delta + 1
                x1, y1 = self.x + self.width - padding_x, self.y + padding_y + i * delta + 1
                Line(points=[x0, y0, x1, y1], width=1)

                x0, y0 = self.x + padding_x + i * delta + 1, self.y + padding_y
                x1, y1 = self.x + padding_x + i * delta + 1, self.y + self.height - padding_y
                Line(points=[x0, y0, x1, y1], width=1)

            # draw black lines
            Color(0, 0, 0, 1)
            for i in range(15):
                x0, y0 = self.x + padding_x, self.y + padding_y + i * delta
                x1, y1 = self.x + self.width - padding_x, self.y + padding_y + i * delta
                Line(points=[x0, y0, x1, y1], width=2)

                x0, y0 = self.x + padding_x + i * delta, self.y + padding_y
                x1, y1 = self.x + padding_x + i * delta, self.y + self.height - padding_y
                Line(points=[x0, y0, x1, y1], width=2)

            dot = [(3, 3), (11, 3), (7, 7), (3, 11), (11, 11)]
            for x, y in dot:
                x = self.x + x * delta + padding_x
                y = self.y + y * delta + padding_y
                Line(width=delta/12, circle=(x, y, 0))


class Stone(FloatLayout):
    def __init__(self, move, **kwargs):
        super(Stone, self).__init__(**kwargs)
        self.move = move
        self.stone_img = Image(size_hint=(.9, .9),
                               pos_hint={'center_x': 0.5, 'center_y': 0.5})
        self.label = Label(pos_hint={'center_x': 0.5, 'center_y': 0.5})
        self.bind(on_touch_up=self.click)
        self.add_widget(self.label)

    def click(self, instance, touch):
        if self.collide_point(touch.x, touch.y):
            print('click', self.move)
            current_player = App.get_running_app().game.current_player
            if hasattr(current_player, 'make_move'):
                current_player.make_move(self.move)

    def show_stone(self, color):
        self.funbind('on_touch_up', self.click)
        if color == 'b':
            self.stone_img.source = 'img/black_dot.png'
            self.add_widget(self.stone_img)
        elif color == 'w':
            self.stone_img.source = 'img/white_dot.png'
            self.add_widget(self.stone_img)

    def remove_dot(self):
        self.stone_img.source = self.stone_img.source.replace('_dot', '')

    def has_stone(self):
        return self.stone_img in self.children

    def show_value(self, value):
        self.label.text = str(value)

    def remove_value(self):
        self.remove_widget(self.label)


class GomokuApp(App):
    def __init__(self, **kwargs):
        super(GomokuApp, self).__init__(**kwargs)
        self.layout = BoardLayout()
        # self.game = GomokuGame(GuiPlayer, GuiPlayer)
        # self.game = GomokuGame(GuiTestPlayer, GuiTestPlayer)
        self.game = GomokuGame(ReinforceAIPlayer, ReinforceAIPlayer)
        # self.game = GomokuGame(RandomAIPlayer, RandomAIPlayer)

    def build(self):
        self.game.set_event_callback(self.callback)
        return self.layout

    def on_start(self):
        Thread(target=self.game.start, daemon=True).start()

    @mainthread
    def callback(self, event):
        if isinstance(event, MoveEvent):
            self.layout.board_grid.update_stone(event)
        elif isinstance(event, BoardUpdateEvent):
            self.layout.board_grid.board_value_listener(event)
        elif isinstance(event, GameOverEvent):
            self.stop()


if __name__ == '__main__':
    GomokuApp().run()
