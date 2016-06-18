from game import GomokuGame
from player import *

if __name__ == '__main__':
    win_count = {1: 0, 2: 0}
    for i in range(3000):
        print("--------------START: ", i, "------------------")
        game = GomokuGame(ReinforceAIPlayer, ReinforceAIPlayer)
        #game = GomokuGame(PlayRecordPlayer, PlayRecordPlayer)
        game.start()
        win_count[game.winner] += 1
        
        print(".............WIN_CCOUNT...............")
        print("")
        print(">>", win_count)
        print("")
        print("--------------END------------------")
