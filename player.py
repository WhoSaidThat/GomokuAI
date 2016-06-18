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

    def learn(self, game, move):
        current_feature = game.board.get_features(game)
        next_board = Board(game.board)
        next_board.put_stone(move)
        next_feature = next_board.get_features(game)
        
        if next_board.get_state() and self.player_num == 1:
            print("reward 1")
            print(game.CNN.run_learning([[1.]], [current_feature], [next_feature]))
        else:
            print("reward 0")
            print(game.CNN.run_learning([[0.]], [current_feature], [next_feature]))

    def set_player_num(self, player_num):
        self.player_num = player_num


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

        self.learn(game, self._next_move)
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
        self._random_first_place_rate = 0.2
        self._random_rate = 0.1
        self._nearby2_rate = 0.7


    def think(self, game):
        print(".........START THINKING", game.moves, "........")
        print("")
        next_moves = self._get_next_moves(game)
        algo_func = max if self.player_num == 1 else min
        best_move = self._get_best_move(game, next_moves, algo_func)
        self.learn(game, best_move)

        print(">>CURRENT_PLAYER:", self.player_num, "STONE:", self.stone_color)
        print(">>BEST_MOVE", best_move)
        print("")
        print("..............................")

        return best_move

    def _get_best_move(self, game, next_moves, algo_func=max):
        next_boards = self._get_next_boards(game, next_moves)
        next_feature_list = self._get_next_feature_list(game, next_boards)
        best_move = self._get_move_by_rules(next_moves, next_boards)
        
        if not best_move:
            values = game.CNN.run_value(next_feature_list)
            best_value = -1 * algo_func(-999999, 999999)
            best_move = next_moves[0]

            for move, value in zip(next_moves, values):
                tmp_val = algo_func(best_value, value[0])
                if tmp_val != best_value:
                    best_value = tmp_val
                    best_move = move
            print(">>VALUE:", best_value, "PLAYER", self.player_num)

        return best_move

    def _get_move_by_rules(self, next_moves, next_boards):
        for move, board in zip(next_moves, next_boards):
            if board.get_state():
                print(">>RULE_WIN!")
                return move

        if random.random() < self._random_rate:
            print(">>RANDOM!")
            return random.choice(next_moves)

        return None

    def _get_next_boards(self, game, next_moves):
        board_list = []
        for move in next_moves:
            next_board = Board(game.board)
            next_board.put_stone(move)
            board_list.append(next_board)
        return board_list

    def _get_next_feature_list(self, game, next_boards):
        feature_list = []
        for board in next_boards:
            feature_list.append(board.get_features(game))
        return feature_list

    def _get_next_moves(self, game):
        if random.random() < self._nearby2_rate:
            next_moves = game.board.get_legal_nearby_moves(2)
        else:
            next_moves = game.board.get_legal_nearby_moves(1)

        if not next_moves:
            if random.random() < self._random_first_place_rate:
                next_moves = [random.choice(game.board.get_legal_moves())]
            else:
                next_moves = [(7, 7)]
        return next_moves


class PlayRecordPlayer(GomokuPlayer):
    def __init__(self, *args, **kwargs):
        super(PlayRecordPlayer, self).__init__(*args, **kwargs)
        self._move_event = Event()
        self._step = []
        with open('play_record.txt', 'r') as f:
            for line in f:
                x = int(line.split(',')[0])
                y = int(line.split(',')[1].split('\n')[0])
                self._step.append((x, y))
        print("STEP", self._step)

    def think(self, game):
        print("moves", game.moves)
        print("QQ", self._step[game.moves])
        self.learn(game, self._step[game.moves])
        return self._step[game.moves]


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
