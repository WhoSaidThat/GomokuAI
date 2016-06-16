import random
import time
from threading import Event

import utils
import config
import operator
import rl_network.critic_network as cnn


class GomokuPlayer:
    def __init__(self, stone_color):
        if stone_color.lower() not in ['w', 'b']:
            raise Exception('stone_color should be "w" or "b"')
        self.stone_color = stone_color.lower()

    def think(self, game):
        """Return next move."""
        return None


class GuiPlayer(GomokuPlayer):
    def __init__(self, *args, **kwargs):
        super(GuiPlayer, self).__init__(*args, **kwargs)
        self._move_event = Event()
        self._next_move = None

    def think(self, game):
        # wait until move event set
        self._move_event.clear()
        self._move_event.wait()
        self._move_event.clear()
        return self._next_move

    def make_move(self, move):
        self._next_move = move
        self._move_event.set()


class GuiTestPlayer(GomokuPlayer):
    def __init__(self, *args, **kwargs):
        super(GuiTestPlayer, self).__init__(*args, **kwargs)
        self._move_event = Event()
        self._next_move = None
        self._pattern = [0] * config.pattern_num
        self.CNN = cnn.CriticNN(config.pattern_num)

    def think(self, game):
        import operator
        self._pattern = utils.extract_features(game.board.board, config.pattern_file_name)
        print(self._pattern)
        legal_moves = game.get_legal_moves()
        values_dict = {}
        tmp_board = game.get_current_board()
        pattern_array = []
        for x, y in legal_moves:
            tmp_board[x][y] = game.current_player.stone_color
            pattern_array.append(utils.extract_features(game.board.board, config.pattern_file_name))
            #print(self._pattern)
            #print(value)
            tmp_board[x][y] = '.'

        values = self.CNN.run_value(pattern_array)[0]
        for index, (x, y) in enumerate(legal_moves):
            print(values[index])
            values_dict[(x, y)] = values[index]
        max_point = max(values_dict.items(), key=operator.itemgetter(1))[0]
        print(max_point)
        print(values_dict[max_point])

        # wait until move event set
        self._move_event.clear()
        self._move_event.wait()
        self._move_event.clear()
        return self._next_move

    def make_move(self, move):
        self._next_move = move
        self._move_event.set()


class RandomAIPlayer(GomokuPlayer):
    def think(self, game):
        time.sleep(0.1)
        return random.choice(game.get_legal_moves())


class ReinforceAIPlayer(GomokuPlayer):
    def __init__(self, *args, **kwargs):
        super(ReinforceAIPlayer, self).__init__(*args, **kwargs)
        self._move_event = Event()
        self._next_move = None
        self._pattern = [0] * config.pattern_num
        self.CNN = cnn.CriticNN(config.pattern_num)

    def think(self, game):
        legal_moves = game.get_legal_nearby_moves(1)
        values_dict = {}
        tmp_board = game.get_current_board()
        pattern_array = []
        for x, y in legal_moves:
            tmp_board[x][y] = game.current_player.stone_color
            pattern_array.append(utils.extract_features(game.board.board, config.pattern_file_name))
            tmp_board[x][y] = '.'

        values = self.CNN.run_value(pattern_array)
        for index, (x, y) in enumerate(legal_moves):
            values_dict[(x, y)] = values[index]
        max_point = max(values_dict.items(), key=operator.itemgetter(1))[0]
        tmp_board[max_point[0]][max_point[1]] = game.current_player.stone_color
        self._pattern = utils.extract_features(game.board.board, config.pattern_file_name)
        new_pattern = utils.extract_features(tmp_board, config.pattern_file_name)
        #print(max_point)
        #print(values_dict[max_point])
        #reward
        if new_pattern[10] == 1:
            print("learning...reward 1")
            print(self.CNN.run_learning([[1.]], [self._pattern], [new_pattern]))
        else:
            print("reward 0")
            print(self.CNN.run_learning([[0.]], [self._pattern], [new_pattern]))
        return max_point


class ReinforceRandomPlayer(GomokuPlayer):
    def __init__(self, *args, **kwargs):
        super(ReinforceRandomPlayer, self).__init__(*args, **kwargs)
        self._move_event = Event()
        self._next_move = None
        self._pattern = [0] * config.pattern_num
        self.CNN = cnn.CriticNN(config.pattern_num)

    def think(self, game):
        max_point = random.choice(game.get_legal_nearby_moves(1))
        tmp_board = game.get_current_board()
        self._pattern = utils.extract_features(game.board.board, config.pattern_file_name)
        tmp_board[max_point[0]][max_point[1]] = game.current_player.stone_color
        new_pattern = utils.extract_features(tmp_board, config.pattern_file_name)
        #reward
        if new_pattern[10] == 1:
            print("learning...reward 1")
            print(self.CNN.run_learning([[1.]], [self._pattern], [new_pattern]))
        else:
            print("reward 0")
            print(self.CNN.run_learning([[0.]], [self._pattern], [new_pattern]))
        return max_point
