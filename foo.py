from game import GomokuGame
from player import *
import sys

if __name__ == '__main__':
    for i in range(100000000000000):
        print("--------------START: ", i, "------------------")
        game = GomokuGame(ReinforceAIBlackPlayer, ReinforceAIWhitePlayer)
        #game = GomokuGame(PlayRecordPlayer, PlayRecordPlayer)
        game.start()
        print("--------------END------------------")
