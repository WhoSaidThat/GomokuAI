import random
import time
from threading import Event

import utils
import config
import operator
from game import Board
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
        self._feature = utils.extract_features(Board().board, config.pattern_file_name)
        self.CNN = cnn.CriticNN(len(self._feature))

    def think(self, game):
        import operator
        self._pattern = utils.extract_features(game.board.board, config.pattern_file_name)
        legal_moves = game.board.get_legal_moves()
        values_dict = {}
        tmp_board = game.board.board
        pattern_array = []
        for x, y in legal_moves:
            tmp_board[x][y] = game.current_player.stone_color
            pattern_array.append(utils.extract_features(tmp_board, config.pattern_file_name))
            #print(self._pattern)
            #print(value)
            tmp_board[x][y] = '.'

        values = self.CNN.run_value(pattern_array)
        for index, (x, y) in enumerate(legal_moves):
            #print(values[index])
            values_dict[(x, y)] = values[index]
        if game.current_player.stone_color == 'b':
            max_point = max(values_dict.items(), key=operator.itemgetter(1))[0]
        else:
            max_point = min(values_dict.items(), key=operator.itemgetter(1))[0]
        occurence = utils.pattern_occurrence(game.board.board, utils.file_to_patterns("pattern.txt"))
        print(occurence)
        print(max_point)
        print(values_dict[max_point])
        print(self.CNN.run_value([self._pattern])[0])

        return max_point

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
        self.mul_values = [10000, 8000, 1000, 1000, 900, 100, 400, 110, 100, 60, 5, 5, 50, 50, -10000, -8000, -1000, -1000, -900, -100, -400, -110, -100, -60, -5, -5, -50, -50]
        self._feature = utils.extract_features(Board().board, config.pattern_file_name)
        self.CNN = cnn.CriticNN(len(self._feature))
        self.load_pattern = utils.file_to_patterns("pattern.txt")

    def think(self, game):
        legal_moves = game.board.get_legal_nearby_moves(2) or [(7, 7)]
        values_dict = {}
        pattern_array = []
        white_will_win = 0
        black_will_win = 0
        max_point = (-1, -1)
        max_eval_move = (-1, -1)
        if game.current_player.stone_color == 'b':
            max_eval = -10000
        else:
            max_eval = 10000
        occurence = game.board.occurrence
        od_value = sum([a*b for a,b in zip(occurence, self.mul_values)])
        for x, y in legal_moves:
            b = Board(game.board)
            b.put_stone((x, y))
            pattern = b.get_features()
            print(pattern)
            pattern_array.append(pattern)
            self_value = sum([a*b for a, b in zip(b.occurrence, self.mul_values)])
            if game.current_player.stone_color == 'b':
                if self_value > max_eval:
                    max_eval = self_value
                    max_eval_move = (x, y)
                elif self_value == max_eval:
                    if random.randint(0,9) >= 4:
                        max_eval_move = (x, y)
            elif game.current_player.stone_color == 'w':
                if self_value < max_eval:
                    max_eval = self_value
                    max_eval_move = (x, y)
                elif self_value == max_eval:
                    if random.randint(0,9) >= 4:
                        max_eval_move = (x, y)

            state = b.get_state()
            if state == 1:
                print('b win')
                black_will_win = 1
                max_point = (x, y)
            elif state == 2:
                print('w win')
                white_will_win = 1
                max_point = (x, y)

        if max_eval_move == (-1, -1):
            max_eval_move = random.choice(legal_moves)

        values = self.CNN.run_value(pattern_array)
        value_set = set()
        for index, (x, y) in enumerate(legal_moves):
            values_dict[(x, y)] = values[index]
            value_set.add(values[index][0])

        if black_will_win == 0 and white_will_win == 0:
            if random.randint(0,9) >= 3 and len(value_set) >= 5:
                #print("set len:", len(value_set))
                if game.current_player.stone_color == 'b':
                    max_point = max(values_dict.items(), key=operator.itemgetter(1))[0]
                else:
                    max_point = min(values_dict.items(), key=operator.itemgetter(1))[0]
            else:
                max_point = max_eval_move
                #max_point = random.choice(legal_moves)
        b = Board(game.board)
        b.put_stone(max_point)
        self._feature = game.board.get_features()
        new_pattern = b.get_features()
        print(max_point)
        #print(values_dict[max_point])
        #print("new_pattern", new_pattern)
        #reward
        if black_will_win == 1:
            print("learning...reward 1")
            print(self.CNN.run_learning([[1.]], [self._feature], [new_pattern]))
        elif white_will_win == 1:
            print("learning...reward -1")
            print(self.CNN.run_learning([[-1.]], [self._feature], [new_pattern]))
        else:
            new_occurence = b.occurrence
            print("new_occur", new_occurence)
            self_occurence = game.board.occurrence
            self_value = sum([a*b for a,b in zip(self_occurence, self.mul_values)])
            new_value = sum([a*b for a,b in zip(new_occurence, self.mul_values)])
            print("self value:", self_value)
            print("new value:", new_value)
            if new_value > self_value:
                print("learning...reward 0.x")
                print(self.CNN.run_learning([[0.00001 * (new_value - self_value)]], [self._feature], [new_pattern]))
            elif new_value < self_value:
                print("learning...reward -0.x")
                print(self.CNN.run_learning([[0.00001 * (new_value - self_value)]], [self._feature], [new_pattern]))
            else:
                print("reward 0")
                print(self.CNN.run_learning([[0.]], [self._feature], [new_pattern]))
        return max_point


class ReinforceRandomPlayer(GomokuPlayer):
    def __init__(self, *args, **kwargs):
        super(ReinforceRandomPlayer, self).__init__(*args, **kwargs)
        self._move_event = Event()
        self._next_move = None
        self._pattern = [0] * config.pattern_num
        self.CNN = cnn.CriticNN(config.pattern_num)

    def think(self, game):
        max_point = random.choice(game.get_legal_nearby_moves(2))
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

class LearningTestPlayer(GomokuPlayer):
    def __init__(self, *args, **kwargs):
        super(LearningTestPlayer, self).__init__(*args, **kwargs)
        self._feature = utils.extract_features(Board().board, config.pattern_file_name)
        self.CNN = cnn.CriticNN(len(self._feature))
        self._pattern = [0] * len(self._feature)

    def think(self, game):
          if game.board.num_stone < len(game.test_move):
              max_point = game.test_move[game.board.num_stone]
              tmp_board = game.board.board
              self._pattern = utils.extract_features(tmp_board, config.pattern_file_name)
              #print("current pattern:", self._pattern)
              tmp_board[max_point[0]][max_point[1]] = game.current_player.stone_color
              new_pattern = utils.extract_features(tmp_board, config.pattern_file_name)
              #print("new pattern:", new_pattern)
              new_occurence = utils.pattern_occurrence(tmp_board, utils.file_to_patterns("pattern.txt"))
              print("new occur:", utils.pattern_occurrence(tmp_board, utils.file_to_patterns("pattern.txt")))
              #reward
              if new_occurence[10] >= 1:
                  print("learning...reward 1")
                  print(self.CNN.run_learning([[1.]], [self._pattern], [new_pattern]))
              else:
                  print("reward 0")
                  print(self.CNN.run_learning([[0.]], [self._pattern], [new_pattern]))
              return max_point
