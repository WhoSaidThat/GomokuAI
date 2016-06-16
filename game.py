import copy


class GomokuGame:
    def __init__(self, player1_cls, player2_cls):
        self.board = Board()
        self.players = [player1_cls('b'), player2_cls('w')]
        self._event_callback = lambda event: None

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
    def __init__(self, board=None):
        self._board = copy.deepcopy(board) or [['.'] * 15 for _ in range(15)]

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
        """
        if not self.is_legal_move(pos):
            raise Exception('Illegal move')

        row, col = pos
        self._board[row][col] = self.get_next_stone_color()

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
        :return: Generator that generates tuple (move, board_in_list).
        """
        for move in self.get_legal_moves():
            next_board = Board(self._board)
            next_board.put_stone(move)
            yield move, next_board.board

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
