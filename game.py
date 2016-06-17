import copy
import re
from utils import diagonal_line, file_to_patterns, pattern_occurrence


class GomokuGame:
    def __init__(self, player1_cls, player2_cls):
        self.board = Board(patterns=file_to_patterns('pattern.txt'))
        self.players = [player1_cls('b'), player2_cls('w')]
        self._event_callback = lambda event: None
        self.moves = 0
        self._event_callback = None
        self.test_move = [(7, 7), (3, 2), (7, 8), (2, 4), (7, 9), (7, 2), (7, 10), (11, 2), (7, 11)]

    def start(self):
        state = self.board.get_state()
        while state == 0:
            move = self.current_player.think(self)
            self._event_callback(MoveEvent(self.current_player.stone_color, move))

            self.board.put_stone(move)
            self._event_callback(BoardUpdateEvent(self.board))

            state = self.board.get_state()

        print('GG')
        if state == 1:
            self._event_callback(GameOverEvent('b'))
        elif state == 2:
            self._event_callback(GameOverEvent('w'))
        elif state == 3:
            self._event_callback(GameOverEvent())

    @property
    def current_player(self):
        return self.players[self.board.num_stone % 2]

    def set_event_callback(self, func):
        self._event_callback = func


class MoveEvent:
    def __init__(self, stone_color, move):
        self.stone_color = stone_color
        self.move = move


class BoardUpdateEvent:
    def __init__(self, board):
        self.board = board


class GameOverEvent:
    def __init__(self, winner=None):
        self.winner = winner


class Board:
    def __init__(self, board=None, patterns=[]):
        if isinstance(board, Board):
            self._board = board.board
            self._patterns = copy.deepcopy(board._patterns)
            self.occurrence = copy.deepcopy(board.occurrence)
        else:
            self._board = copy.deepcopy(board) or [['.'] * 15 for _ in range(15)]
            self._patterns = patterns
            self.occurrence = pattern_occurrence(self._board, patterns)

    def __repr__(self):
        s = ''
        for row in self._board:
            s += ''.join(row) + '\n'
        return s

    def get_legal_moves(self):
        moves = []
        for row in range(15):
            for col in range(15):
                if self._board[row][col] is '.':
                    moves.append((row, col))
        return moves

    def is_legal_move(self, move):
        return self._board[move[0]][move[1]] == '.'

    @property
    def num_stone(self):
        num = 0
        for r in range(15):
            for c in range(15):
                if self._board[r][c] != '.':
                    num += 1
        return num

    @property
    def board(self):
        """Return a copy of self._board"""
        return copy.deepcopy(self._board)

    def put_stone(self, pos):
        """
        First call to this method will place a black stone on the given position and second call
        will place a white stone, and so on.

        This method also updates the pattern occurrence.
        """
        if not self.is_legal_move(pos):
            raise Exception('Illegal move')

        row, col = pos
        o1 = self._get_occurrence_at(pos)
        self._board[row][col] = self.get_next_stone_color()
        o2 = self._get_occurrence_at(pos)
        self.occurrence = [o + y - x for o, x, y in zip(self.occurrence, o1, o2)]

    def get_next_stone_color(self):
        return ['b', 'w'][self.num_stone % 2]

    def get_legal_nearby_moves(self, nearby_length=1):
        """
        This gives nearby moves within the nearby_length
        (ex. nearby_length=1 --> would search for current_place-1 ~ current_place+1
        --> 3*3 area )

        Return None if there's no move.
        """
        moves = []
        for row, col in self.get_legal_moves():
            if not self._is_nearby_empty(nearby_length, row, col):
                moves.append((row, col))

        return moves or None

    def _is_nearby_empty(self, nearby_length, row, col):
        for r in range(row-nearby_length, row+nearby_length+1):
            for c in range(col-nearby_length, col+nearby_length+1):
                if r < 0 or c < 0 or r >= 15 or c >= 15:
                    continue
                if self._board[r][c] is not '.':
                    return False
        return True

    def enumerate_next_board(self):
        """Enumerate all possible next board.
        :return: A list of (move, board_in_list).
        """
        nb = []
        for move in self.get_legal_moves():
            next_board = Board(self)
            next_board.put_stone(move)
            nb.append((move, next_board.board))
        return nb

    def get_state(self):
        """Return board state. 0: none, 1: black, 2: white, 3: board full"""
        for row in range(15):
            for col in range(15):
                for color in ['b', 'w']:
                    if self._board[row][col] == color:
                        win_flag = [1, 1, 1, 1]
                        for i in range(1, 5):
                            if row + i >= 15 or self._board[row + i][col] != color:
                                win_flag[0] = 0
                            if col + i >= 15 or self._board[row][col + i] != color:
                                win_flag[1] = 0
                            if row + i >= 15 or col + i >= 15 or self._board[row + i][col + i] != color:
                                win_flag[2] = 0
                            if row + i >= 15 or col - i < 0 or self._board[row + i][col - i] != color:
                                win_flag[3] = 0
                        if any(win_flag):
                            return ['b', 'w'].index(color) + 1
        return 3 if not self.get_legal_moves() else 0

    def _get_occurrence_at(self, pos):
        x, y = pos
        occurrence = [0] * len(self._patterns)

        lines = [''.join(self._board[x]),
                 ''.join(list(zip(*self._board))[y]),
                 ''.join(diagonal_line(self._board, x, y, '\\')),
                 ''.join(diagonal_line(self._board, x, y, '/'))]

        for i, p in enumerate(self._patterns):
            for line in lines:
                _p = p.replace('.', '\.')
                occurrence[i] += len(re.findall(r'(?=(%s))' % _p, line))
                if p != p[::-1]:
                    occurrence[i] += len(re.findall(r'(?=(%s))' % _p, line[::-1]))
        return occurrence

    def get_features(self):
        feature = []

        for p, o in zip(self._patterns, self.occurrence):
            if 'bbbbb' in p or 'wwwww' in p:
                if o > 0:
                    feature += [1]
                else:
                    feature += [0]
                continue

            if o == 0:
                feature += [0, 0, 0, 0, 0]
            elif o == 1:
                feature += [1, 0, 0, 0, 0]
            elif o == 2:
                feature += [1, 1, 0, 0, 0]
            elif o == 3:
                feature += [1, 1, 1, 0, 0]
            elif o == 4:
                feature += [1, 1, 1, 1, 0]
            elif o >= 5:
                feature += [1, 1, 1, 1, (o-4)/2]

        for o in self.occurrence:
            if o == 0:
                feature += [0, 0]
            else:
                if self.num_stone % 2 == 0:  # black to move
                    feature += [1, 0]
                else:                   # white to move
                    feature += [0, 1]
        return feature

if __name__ == '__main__':
    from utils import extract_features, file_to_patterns, str_to_board
    import random
    b = Board(patterns=file_to_patterns('pattern.txt'))
    for i in range(100):
        b.put_stone(random.choice(b.get_legal_moves()))
    print(b)
    print(b.get_features())
    print(extract_features(b.board, file_to_patterns('pattern.txt')))
    assert b.get_features() == extract_features(b.board, file_to_patterns('pattern.txt'))
