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

    def learn(self, game, move):
        tmp_board = game.get_current_board()
        tmp_board[move[0]][move[1]] = game.current_player.stone_color
        new_pattern = utils.scan_patterns(tmp_board, config.pattern_file_name)
        if new_pattern[10] == 1:
            self.CNN.run_learning([[1.]], [self._pattern], [new_pattern])
        else:
            self.CNN.run_learning([[0.]], [self._pattern], [new_pattern])


class GuiPlayer(GomokuPlayer):
    def __init__(self, *args, **kwargs):
        super(GuiPlayer, self).__init__(*args, **kwargs)
        self._move_event = Event()
        self._next_move = None
        self.CNN = cnn.CriticNN(config.pattern_num)

    def think(self, game):
        self._pattern = utils.scan_patterns(game._board, config.pattern_file_name)
        print(self._pattern)
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
        self.CNN = cnn.CriticNN(config.pattern_num)

    def think(self, game):
        import operator
        self._pattern = utils.scan_patterns(game._board, config.pattern_file_name)
        print(self._pattern)
        legal_moves = game.get_legal_nearby_moves()
        values_dict = {}
        tmp_board = game.get_current_board()
        pattern_array = []
        for x, y in legal_moves:
            tmp_board[x][y] = game.current_player.stone_color
            pattern_array.append(utils.scan_patterns(game._board, config.pattern_file_name))
            #print(self._pattern)
            #print(value)
            tmp_board[x][y] = '.'

        values = self.CNN.run_value(pattern_array)
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


class ReinforceAIBlackPlayer(ReinforceAIPlayer):
    def think(self, game):
        legal_moves = game.get_legal_nearby_moves()
        values_dict = {}
        tmp_board = game.get_current_board()
        pattern_array = []
        max_point = None
        for x, y in legal_moves:
            tmp_board[x][y] = game.current_player.stone_color
            new_pattern = utils.scan_patterns(tmp_board, config.pattern_file_name)
            pattern_array.append(new_pattern)

            # rule: if 5 in a row --> choose that!
            if new_pattern[10] >= 1:
                max_point = (x, y)
                break
            tmp_board[x][y] = '.'

        if not max_point:
            if random.random() < 0.25:
                print("random")
                max_point = random.choice(legal_moves)
            else:
                values = self.CNN.run_value(pattern_array)
                for index, (x, y) in enumerate(legal_moves):
                    values_dict[(x, y)] = values[index]
                max_point = max(values_dict.items(), key=operator.itemgetter(1))[0]

        self.learn(game, max_point)
        
        print("MAX_POINT:", max_point)
        return max_point


class ReinforceAIWhitePlayer(ReinforceAIPlayer):
    def think(self, game):
        legal_moves = game.get_legal_nearby_moves()
        values_dict = {}
        tmp_board = game.get_current_board()
        pattern_array = []
        best_point = None
        for x, y in legal_moves:
            tmp_board[x][y] = game.current_player.stone_color
            new_pattern = utils.scan_patterns(tmp_board, config.pattern_file_name)
            pattern_array.append(new_pattern)
            # rule: if 5 in a row --> choose that!
            tmp_board[x][y] = '.'
            if new_pattern[21] >= 1:
                best_point = (x, y)
                break

        if not best_point:
            if random.random() < 0.25:
                print("random")
                best_point = random.choice(legal_moves)
            else:    
                values = self.CNN.run_value(pattern_array)
                for index, (x, y) in enumerate(legal_moves):
                    values_dict[(x, y)] = values[index]
                best_point = min(values_dict.items(), key=operator.itemgetter(1))[0]

        self.learn(game, best_point)

        print("best_POINT:", best_point)
        return best_point


class ReinforceRandomPlayer(GomokuPlayer):
    def __init__(self, *args, **kwargs):
        super(ReinforceRandomPlayer, self).__init__(*args, **kwargs)
        self._move_event = Event()
        self._next_move = None
        self._pattern = [0] * config.pattern_num
        self.CNN = cnn.CriticNN(config.pattern_num)

    def think(self, game):
        max_point = random.choice(game.get_legal_nearby_moves())
        tmp_board = game.get_current_board()
        self._pattern = utils.scan_patterns(game._board, config.pattern_file_name)
        tmp_board[max_point[0]][max_point[1]] = game.current_player.stone_color
        new_pattern = utils.scan_patterns(tmp_board, config.pattern_file_name)
        
        if new_pattern[10] == 1:
            print("learning...reward 1")
            print(self.CNN.run_learning([[1.]], [self._pattern], [new_pattern]))
        else:
            print("reward 0")
            print(self.CNN.run_learning([[0.]], [self._pattern], [new_pattern]))
        return max_point

class PlayRecordPlayer(GomokuPlayer):
    def __init__(self, *args, **kwargs):
        super(PlayRecordPlayer, self).__init__(*args, **kwargs)
        self._move_event = Event()
        self._next_move = None
        self._pattern = [0] * config.pattern_num
        self.CNN = cnn.CriticNN(config.pattern_num)
        self._step = []
        with open('play_record.txt', 'r') as f:
            for line in f:
                x = int(line.split(',')[0])
                y = int(line.split(',')[1].split('\n')[0])
                self._step.append((x, y))

    def think(self, game):
        self.learn(game, self._step[game.moves])
        return self._step[game.moves]

