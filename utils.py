# Utility module for gomoku game.
import re


def in_board(x, y):
    """Check if the given position is in the board."""
    return (0 <= x < 15) and (0 <= y < 15)


def str_to_board(string):
    string = string.strip()
    return [list(row) for row in string.split()]


def file_to_board(file):
    with open(file) as f:
        return [list(line.strip()) for line in f]


def diagonal_line(board, x, y, direction):
    """Return the board layout on the diagonal line of the given position.

    :param board: 2D array of board info.
    :param x: x coordinate.
    :param y: y coordinate.
    :param direction: Should be '\\' or '/'
    :return: A list containing board info of the given direction on (x, y)
    """
    l = []
    if direction == '\\':
        while in_board(x, y):
            x -= 1
            y -= 1
        x += 1
        y += 1
        while in_board(x, y):
            l.append(board[x][y])
            x += 1
            y += 1
    elif direction == '/':
        while in_board(x, y):
            x -= 1
            y += 1
        x += 1
        y -= 1
        while in_board(x, y):
            l.append(board[x][y])
            x += 1
            y -= 1
    else:
        raise Exception(r"direction should be either '/' or '\\'")
    return l


def extract_features(board, patterns):
    """Return a list of the occurrence of patterns.
    :param board: List representation of the board.
    :param patterns: Pattern list or the file name from which to read the patterns.
    :return: A list of features. Each pattern has 5 + 2 features, except for patterns with 5 same-color stones in a row,
             which only have 1 + 2 patterns.
    """
    if isinstance(patterns, str):
        patterns = file_to_patterns(patterns)

    occurrence = pattern_occurrence(board, patterns)
    feature = []

    for p, o in zip(patterns, occurrence):
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

    # count the stones on the board to determine who is next to move
    num_stone = 0
    for row in board:
        for stone in row:
            if stone != '.':
                num_stone += 1
    for o in occurrence:
        if o == 0:
            feature += [0, 0]
        else:
            if num_stone % 2 == 0:  # black to move
                feature += [1, 0]
            else:                   # white to move
                feature += [0, 1]
    return feature


def pattern_occurrence(board, patterns):
    occurrence = [0] * len(patterns)

    lines = []
    # get horizontal lines
    lines += [''.join(raw) for raw in board]
    # get vertical lines
    lines += [''.join(raw) for raw in zip(*board)]
    # get '\' lines
    # we start from the first row then the first column
    for c in range(15):
        line = ''.join(diagonal_line(board, c, 0, '\\'))
        lines.append(line)
    for r in range(1, 15):
        line = ''.join(diagonal_line(board, 0, r, '\\'))
        lines.append(line)
    # get '/' lines
    # we start from the first row then the last column
    for c in range(15):
        line = ''.join(diagonal_line(board, 0, c, '/'))
        lines.append(line)
    for r in range(1, 15):
        line = ''.join(diagonal_line(board, r, 14, '/'))
        lines.append(line)

    for i, p in enumerate(patterns):
        for line in lines:
            _p = p.replace('.', '\.')
            occurrence[i] += len(re.findall(r'(?=(%s))' % _p, line))
            if p != p[::-1]:
                occurrence[i] += len(re.findall(r'(?=(%s))' % _p, line[::-1]))
    return occurrence


def file_to_patterns(f):
    with open(f) as file:
        patterns = [line.strip() for line in file]
    return patterns


def get_state(board):
    """Return board state. 0: none, 1: black, 2: white, 3: board full"""
    for row in range(15):
        for col in range(15):
            for color in ['b', 'w']:
                if board[row][col] == color:
                    win_flag = [1, 1, 1, 1]
                    for i in range(1, 5):
                        if row + i >= 15 or board[row + i][col] != color:
                            win_flag[0] = 0
                        if col + i >= 15 or board[row][col + i] != color:
                            win_flag[1] = 0
                        if row + i >= 15 or col + i >= 15 or board[row + i][col + i] != color:
                            win_flag[2] = 0
                        if row + i >= 15 or col - i < 0 or board[row + i][col - i] != color:
                            win_flag[3] = 0
                    if any(win_flag):
                        return ['b', 'w'].index(color) + 1
    return 0
