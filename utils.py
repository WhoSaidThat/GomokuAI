# Utility module for gomoku game.
import re


def in_board(x, y):
    """Check if the given position is in the board."""
    return (0 <= x < 15) and (0 <= y < 15)


def str_to_board(str):
    return [list(row) for row in str.split()]


def file_to_board(file):
    with open(file) as f:
        return [list(line.strip()) for line in f]


def diagonal_line(board, x, y, direction):
    """Return the board layout on a diagonal line.

    :param board: 2D array of board info.
    :param x: Starting x coordinate.
    :param y: Starting y coordinate.
    :param direction: Should be '\\' or '/'
    :return: A list containing board info along the given direction starting from (x, y)
    """
    l = []
    if direction == '\\':
        while in_board(x, y):
            l.append(board[x][y])
            x += 1
            y += 1
    elif direction == '/':
        while in_board(x, y):
            l.append(board[x][y])
            x -= 1
            y += 1
    else:
        raise Exception(r"direction should be either '/' or '\\'")
    return l


def scan_patterns(board, pattern_file):
    """Return a list of the occurrence of patterns.
    :param board: List representation of the board.
    :param pattern_file: The file to read the patterns.
    :return: A list of features. Each pattern has 5 + 2 features, except for patterns with 5 same-color stones in a row,
    which only have 1 + 2 patterns.
    """
    with open(pattern_file) as file:
        patterns = [line.strip() for line in file]
    occurrence = [0] * len(patterns)
    feature = []

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
        line = ''.join(diagonal_line(board, c, 0, '/'))
        lines.append(line)
    for r in range(1, 15):
        line = ''.join(diagonal_line(board, 14, r, '/'))
        lines.append(line)

    for i, p in enumerate(patterns):
        for line in lines:
            if 'b' in p:
                _p = p.replace('.', '[^b]')
            elif 'w' in p:
                _p = p.replace('.', '[^w]')
            occurrence[i] += len(re.findall(r'(?=(%s))' % _p, line))

        # special case: five same-color stones in a raw
        if 'bbbbb' in p or 'wwwww' in p:
            if occurrence[i] > 0:
                feature += [1]
            else:
                feature += [0]
            continue

        if occurrence[i] == 0:
            feature += [0, 0, 0, 0, 0]
        elif occurrence[i] == 1:
            feature += [1, 0, 0, 0, 0]
        elif occurrence[i] == 2:
            feature += [1, 1, 0, 0, 0]
        elif occurrence[i] == 3:
            feature += [1, 1, 1, 0, 0]
        elif occurrence[i] == 4:
            feature += [1, 1, 1, 1, 0]
        elif occurrence[i] >= 5:
            feature += [1, 1, 1, 1, (occurrence[i]-4)/2]

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
