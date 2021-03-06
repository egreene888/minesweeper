"""
solver.py

We've implemented a minesweeper game, now we need to make an AI to solve it
"""

from tkinter import *
from tkinter import ttk
from tkinter import font

import threading
import logging
import time
import random
import math
import itertools

import board

MOVE_TIME = 0.5
WATCHDOG_TIME = 0.2
POSSIBILITY_CAP = 20
NUM_RANDOM_GUESSES = 100000
STEP_DEBUG = False


class computerBoard(board.board):
    """
    Extend the board of the original minesweeper game to make it
    play well with an AI.
    """
    # Extend the constructor, gameOver, checkVictory and restart functions
    # to add a flag that tells us whether we've won.
    def __init__(self, rows, cols, mines):
        self.win = None
        return super().__init__(rows, cols, mines)

    def gameOver(self):
        self.win = False
        return super().gameOver()

    def checkVictory(self):
        victory = super().checkVictory()
        if victory:
            self.win = True
        return victory

    def restart(self):
        self.win = None
        return super().restart()

    # write helper functions to easily access the information available to
    # the user -- tile flag, tile cover,tile number.
    def isFlag(self, row, col):
        return self.isCovered(row, col) and self.tiles[row][col].flag

    def getNumber(self, row, col):
        if not self.isCovered(row, col):
            return self.tiles[row][col].number

    def isCovered(self, row, col):
        return self.tiles[row][col].covered

    def releaseWait(self):
        """ for debugging use only """

    # Extend the primaryClick, secondaryClick, and doubleClick methods
    # to add support for multi-threading.
class solver(object):
    """
    An object that handles solving the board and deals with the multithreading
    Comes with a basic guesser that will just guess randomly.
    """
    def __init__(self, game):
        """
        Template constructor for solvers.
        Saves the board as input and sets up the multithreading
        """
        self.board = game
        # create a separate thread to call the solve() function.
        self.solverThread = threading.Thread(target = self.solve, name = 'solver')
        self.solverThread.daemon = True

        # create a debugging condition that will pause execution of the solver
        # thread until the button is pressed.
        if STEP_DEBUG:
            self.waitForClick = threading.Event()
            self.stepDebugButton = Button(self.board.window, text = "STEP", command = self.releaseWait())
            self.stepDebugButton.grid(row = self.board.rows + 2, columnspan = self.board.cols)
        # also create a watchdog thread to keep up on whether the others
        # are alive.
        # self.watchdogThread = threading.Thread(target = self.checkThreads, name = 'watchdog')
        # self.watchdogThread.daemon = True
        return

    def start(self):
        """Gets the show on the road. Takes no arguments and returns the
        victory variable"""
        # if the solver board isn't in the ready-to-start state, restart it
        if not self.board.firstClick:
            self.board.restart()
            time.sleep(0.5)
        # start the solver thread
        self.solverThread.start()
        # back to the main thread-- run the actual game
        self.board.show()

        return self.board.win

    def solve(self):
        """
        Template solver function.
        Makes a guess at regular intervals specified by MOVE_TIME
        """
        guessCounter = 0
        while self.board.win is None:
            startGuess = time.time()
            stopGuess = startGuess + MOVE_TIME
            # get a list of guesses.
            # logging.info("Taking a guess")
            guesses, action = self.guess()
            for guess in guesses:
                if action == 'flag':
                    self.board.secondaryClick(*guess)
                elif action == 'click':
                    self.board.primaryClick(*guess)
                    # logging.info("returned from primaryClick")
                elif action == 'double':
                    self.board.doubleClick(*guess)
                else:
                    logging.warn("{} was a bad guess".format(guess))
                guessCounter += 1
            # implement a pause to wait for the user to click the button.
            if STEP_DEBUG:
                # if action == 'click':
                logging.info("waiting for user input \n\n")
                self.waitForClick.wait(timeout = 20)
                self.waitForClick.clear()
            # wait half a second.
            while time.time() < stopGuess:
                time.sleep(0.01)
            # logging.info(self.board.win)
        # idle until the board is restarted.
        # while(1):
        #     logging.info("idling until restart")
        #     try:
        #         exists = self.board.window.winfo_exists()
        #     except RuntimeError:
        #         exists = False
        #     if not exists:
        #         # self.board.tk.destroy()
        #         return
        #     if self.board.firstClick:
        #         break
        #     else:
        #         time.sleep(0.5)
        # once we're done, close the Tk window.
        self.win = self.board.win
        self.board.tk.quit()
        # kill the current thread if it's not somehow the main one
        if threading.current_thread() is not threading.main_thread():
            raise SystemExit
        return

    def guess(self):
        """
        Template guesser.
        Literally picks a tile at random from the covered tiles still on the
        board
        """
        while(1):
            guess = self.pickRandom()
            if self.board.isCovered(*guess) is True:
                return [guess], 'click'

    def pickRandom(self):
        """
        Utility function to pick a tile from the board at random
        """
        random.seed()
        guessPos = random.randint(0, self.board.tileCount - 1)
        # print(minePos)
        guessRow = guessPos // self.board.cols
        guessCol = guessPos % self.board.cols
        return (guessRow, guessCol)

    def lookForDoubleClick(self):
        """
        look for places where the number of flagged tiles is equal to the
        number of the tile. Then we can doubleClick on the tile.
        """
        for i in range(self.board.rows):
            for j in range(self.board.cols):
                if not self.board.isCovered(i, j) and self.board.getNumber(i, j) > 0:
                    neighbors = self.board.getNeighbors(i ,j)
                    # count the flagged and covered neighbors
                    flags = 0
                    coveredAndNotFlagged = 0
                    for neighbor in neighbors:
                        if self.board.isFlag(*neighbor):
                            flags += 1
                        elif self.board.isCovered(*neighbor):
                            coveredAndNotFlagged += 1
                    # if there are any covered neighbors that do not have
                    # flags, double-click on this tile
                    if self.board.getNumber(i, j) == flags and coveredAndNotFlagged > 0:
                        return (i, j)
        # if we looped through all the tiles and didn't find a suitable
        # candidate, return None
        return None

    def lookForFlag(self):
        """
        look for places where the number of covered
        tiles is equal to the number of the tile.
        Then we can flag the all the covered tiles
        """
        for i in range(self.board.rows):
            for j in range(self.board.cols):
                # check if uncovered and the number is not zero.
                if not self.board.isCovered(i, j) and self.board.getNumber(i, j) > 0:
                    neighbors = self.board.getNeighbors(i, j)
                    # check the number of covered tiles
                    covered = 0
                    # see if any of these tiles are also unflagged
                    neighborsToFlag = []
                    for neighbor in neighbors:
                        if self.board.isCovered(*neighbor):
                            covered += 1
                            if not self.board.isFlag(*neighbor):
                                neighborsToFlag.append(neighbor)
                    #check if this number is equal to the number on the tile
                    if (len(neighborsToFlag) != 0) and (covered == self.board.getNumber(i, j)):
                        return neighborsToFlag
        # if we looped through all the tiles and didn't find a suitable
        # candidate, return None
        return None

    def releaseWait(self):
        """for debugging use only"""
        self.waitForClick.set()


class BasicSolver(solver):
    """
    A first attempt at trying to figure out how to play minesweeper. Follows
    just a few basic rules.
    """
    def guess(self):
        """
        Follows a few simple rules
        1. The first guess (on a totally covered board) is random.
        2. If the number of covered neighbors is equal to the number of the tile,
        flag all the uncovered tiles
        """
        # take the first guess at random
        if self.board.firstClick is True:
            return [self.pickRandom()], 'click'
        # print("It's not the first guess")

        # First, look for places where the number of flagged tiles
        # is equal to the number of the tile. Then we can double-click and
        # clear all remaining covered tiles.
        guess = self.lookForDoubleClick()
        if guess is not None:
            return [guess], 'double'
        # If that didn't work, look for places where the number of covered
        # tiles is equal to the number of the tile.
        # Then we can flag the all the covered tiles
        guess = self.lookForFlag()
        if guess is not None:
            return guess, 'flag'
        # print("No obvious flags")
        # if we haven't solved it by now, just pick something at random.
        for _ in range(self.board.tileCount):
            guess = self.pickRandom()
            if self.board.isCovered(*guess) and not self.board.isFlag(*guess):
                logging.info("Picking {} at random".format(guess))
                return [guess], 'click'

class AdvancedSolver(solver):
    """
    A more advanced version of the solver. Uses some of the same basic
    techniques, but resorts to more sophisticated methods than guessing when
    those fail.
    """
    def __init__(self, game):
        """
        Modify the parent constructior to create an array of tile objects with
        information about each tile
        """
        super().__init__(game)
        self.solverTiles = []
        for i in range(self.board.rows):
            row = []
            for j in range(self.board.cols):
                row.append(solverTile(self.board, i, j))
            self.solverTiles.append(row)
        return
    def guess(self):
        # logging.info("Starting Guess Function")
        # take the first guess at random
        if self.board.firstClick is True:
            return [self.pickRandom()], 'click'
        # print("It's not the first guess")

        # First, look for places where the number of flagged tiles
        # is equal to the number of the tile. Then we can double-click and
        # clear all remaining covered tiles.
        # guess = self.lookForDoubleClick()
        # if guess is not None:
        #     return [guess], 'double'
        # If that didn't work, look for places where the number of covered
        # tiles is equal to the number of the tile.
        # Then we can flag the all the covered tiles
        # guess = self.lookForFlag()
        # if guess is not None:
        #     return guess, 'flag'
        # print("No obvious flags")
        # if we haven't solved it by now, try to use a probabilistic method
        # to guess which one works.
        guess = self.extendedAreaSearch()
        if guess is not None:
            return guess

        # if that doesn't work, pick at random.
        for _ in range(self.board.tileCount):
            guess = self.pickRandom()
            if self.board.isCovered(*guess) and not self.board.isFlag(*guess):
                logging.info("Picking {} at random".format(guess))
                return [guess], 'click'

        # if that hasn't worked, guess at random.

    def guessWithProbability(self):
        """
        Generates a guess by computing the probability that each tile is a bomb.
        Any tile that has a 0% probability can be cleared and any tile that
        has 100% probability can be flagged
        """
        # compute the nearby flags for every tile on the board. We'll need
        # it later.
        self.nearbyFlags = self.getNearbyFlags()
        # generate a list of all the tiles that *might* be bombs.
        suspiciousTiles = []
        # parallel list of just how supsicious the qualifiers are
        suspiciousness = []
        # count flags so we can find out how many mines there are
        flagCounter = 0
        # originally tried declaring all covered tiles as suspicious.
        # Let's try declaring only covered tiles adjacent to an uncovered tile
        for i in range(self.board.rows):
            for j in range(self.board.cols):
                if self.board.isCovered(i, j):
                    if self.board.isFlag(i, j):
                        flagCounter += 1
                    else:
                        neighbors = self.board.getNeighbors(i, j)
                        for n in neighbors:
                            if not self.board.isCovered(*n):
                                suspiciousTiles.append((i, j))
                                suspiciousness.append(0)
                                break
        numberOfMines = self.board.mines - flagCounter

        #Next, generate a list of Combinationss of these suspicious tiles.
        # note that this is very computationally intensive.
        # Might have to find a way to randomly generate a smaller number of
        # these and guess stochastically.
        # generator = stochasticCombinationGenerator(suspiciousTiles, numberOfMines)
        if len(suspiciousTiles) > POSSIBILITY_CAP:
            generator = possibilityGenerator(suspiciousTiles, stochastic = True)
        else:
            generator = possibilityGenerator(suspiciousTiles, stochastic = False)
        # count the number of viable guesses
        goodGuessCount = 0

        # logging.info("There are {} suspicious tiles and {} bombs".format(
        #     len(suspiciousTiles), numberOfMines))
        # logging.info("This equates to {} combinations".format(generator.count()))
        # logging.info("Generating {} possible bomb positions".format(num_samples))
        i = 0                               # loop iterator
        num_samples = generator.count()   # number of combinations to generate
        while i < num_samples: # generate random combinations
            combo = generator.next()
            if len(combo) <= numberOfMines:
                if self.isGoodGuess(combo):
                    goodGuessCount += 1
                    for mine in combo:
                        suspiciousness[suspiciousTiles.index(mine)] += 1
                # if i % 10000 == 0:
                #     logging.info("Generated {} possibilities, {} were good".format(
                #         i, goodGuessCount))
            i += 1

        # now loop through each suspicious tile and see if it has 0% or 100%
        # probability of being a bomb.
        clearTiles = []
        flagTiles = []
        for i in range(len(suspiciousTiles)):
            if suspiciousness[i] == 0:
                clearTiles.append(suspiciousTiles[i])
            elif suspiciousness[i] == goodGuessCount:
                flagTiles.append(suspiciousTiles[i])
        if len(clearTiles):
            logging.info("Found {} tiles (of {}) with 0% suspicion".format(len(clearTiles), len(suspiciousTiles)))
            return [clearTiles[0]], 'click'
        elif len(flagTiles):
            logging.info("Found {} tiles with 100% suspicion".format(len(flagTiles)))
            return [flagTiles[0]], 'flag'

        # If we haven't found a tile with 0% probability, then click the tile
        # with the lowest.
        lowestSuspicion  = min(suspiciousness)
        leastSuspiciousTile = suspiciousTiles[suspiciousness.index(lowestSuspicion)]
        logging.info("Least Suspicious tile is {}, with probability = {:.2%}%".format(
            leastSuspiciousTile, lowestSuspicion/ goodGuessCount))
        return [leastSuspiciousTile], 'click'

    def extendedAreaSearch(self):
        """
        Tries to do something similar to guessWithProbability() but
        pares down the number of possibilities for the guesses
        """
        # create lists of the uncovered, numbered tiles with unflagged,
        # covered tiles nearby,
        # as well as the covered tiles near uncovered tiles,
        # and the probability for each covered tile.
        # also count the number of flags on the board, we'll use that.
        # logging.info("Starting a new extended search")
        flagCounter = 0
        for i, j in itertools.product(range(self.board.rows), range(self.board.cols)):
            currentTile = self.solverTiles[i][j]
            if currentTile.clear is True:
                continue
            if self.board.isCovered(i, j):
                if self.board.isFlag(i, j):
                    flagCounter += 1
            else:
                currentTile.reset()
                # generate the list of nearby tiles that are covered and
                # not flagged
                # also find out how many mines are in those tiles.
                currentTile.minesToFind = self.board.getNumber(i, j)
                if currentTile.minesToFind == 0:
                    currentTile.clear = True
                    continue

                # remove all of the suspicous neighbors that aren't covered.
                suspiciousNeighbors = self.board.getNeighbors(i, j)
                k = 0
                while k < len(suspiciousNeighbors):
                    if not self.board.isCovered(*suspiciousNeighbors[k]):
                        del suspiciousNeighbors[k]
                    elif self.board.isFlag(*suspiciousNeighbors[k]):
                        # logging.info("found a mine")
                        currentTile.minesToFind -= 1
                        del suspiciousNeighbors[k]
                    else:
                        k += 1
                # end while
                # still suspicious tiles, we can clear them
                # if not self.board.isCovered(i, j):
                #     logging.info(" {} {} \n".format(currentTile.minesToFind, self.solverTiles[i][j].minesToFind))
                if currentTile.minesToFind == 0:
                    currentTile.clear = True
                    if len(suspiciousNeighbors) > 0:
                    # logging.info("marked {} as clear".format((i, j)))
                        # logging.info("found a double-clickable tile {}".format((i, j)))
                        return [(i, j)], 'double'
                # otherwise, if the number of suspicious neighbors is equal to
                # the number of mines to find, we can flag all of them as
                # mines
                elif currentTile.minesToFind == len(suspiciousNeighbors):
                    # logging.info("All neighbors of {} can be flagged".format((i, j)))
                    return suspiciousNeighbors, 'flag'
                for neighborRow, neighborCol in suspiciousNeighbors:
                    # logging.info("{} is a suspicious neighbor of {}".format((neighborRow, neighborCol), (i, j)))
                    self.solverTiles[neighborRow][neighborCol].suspicion = 0
                # otherwise, save all the suspicious neighbors for later.
                currentTile.suspiciousNeighbors = suspiciousNeighbors
        # end for i, j in rows, cols

        # if the number of flagged tiles is equal to the total number of
        # mines on the board, we can click on all the unflagged, covered tiles
        # and win the game.
        # Other logic will eventually take care of this but this is insurance
        # and also speeds things up a little.
        if flagCounter == self.board.mines:
            remainingCovered = []
            for i, j in itertools.product(range(self.board.rows), range(self.board.cols)):
                if self.board.isCovered(i, j):
                    remainingCovered.append((i, j))
            return remainingCovered, 'click'

        # If we make it this far, we now have the following info for every tile
        # on the board.
        # suspicious neighbors, missing mines,
        for i, j in itertools.product(range(self.board.rows), range(self.board.cols)):
            currentTile = self.solverTiles[i][j]

            # skip the clear tiles.
            if currentTile.clear is True:
                continue
            # also skip the tiles with no suspicious neighbors that are
            # somehow not clear?
            if len(currentTile.suspiciousNeighbors) == 0:
                continue
            # logging.info("\n\n")
            # logging.info("analyzing tile {}".format((i, j)))
            # logging.info("tile has {} missing mines".format(currentTile.minesToFind))
            # loop through every possible combination of mines.
            combinations = itertools.combinations(currentTile.suspiciousNeighbors, currentTile.minesToFind)
            goodCombos = []
            comboCounter = 0
            for combo in combinations:
                badCombo = False
                comboCounter += 1
                # get all the neighbors of the tiles in that combination.
                neighbors = self.board.getNeighbors(i, j)
                for tile in combo:
                    neighbors.extend(self.board.getNeighbors(*tile))
                # remove duplicates (elements are tuples so this should work)
                neighbors = list(set(neighbors))

                # check if each neighbor contradicts this combo.
                for (row, col) in neighbors:
                    neighborTile = self.solverTiles[row][col]
                    # the tile shouldn't be flagged clear
                    # there are still suspicious tiles nearby.
                    # if neighborTile.clear:
                    #     message = "A tile was marked clear that shouldn't have been: {}".format((row, col))
                    #     logging.info("\nTile Number = {}".format(self.board.getNumber(row, col)))
                    #     logging.info("\nMines to clear = {}".format(neighborTile.minesToFind))
                    #     raise RuntimeError(message)
                    # if the neighbor tile is covered, we can't get any info
                    if self.board.isCovered(row, col):
                        continue
                    # find how many of the mines in the combo are near the
                    # neighbor in question.
                    minesNearNeighbor = sum([self.isNear(tile, (row, col)) for tile in combo])
                    # if the number of nearby mines in the combo = number of
                    # missing mines for the neighbor, this combo is ok.
                    if minesNearNeighbor == neighborTile.minesToFind:
                        continue
                    # if there are more nearby mines than there are missing mines
                    # near the neighbor in question, abort.
                    elif minesNearNeighbor > neighborTile.minesToFind:
                        # logging.info("Combo {} is bad because it has too many mines near {}".format(combo,( row, col)))
                        badCombo = True
                        break
                    # count the suspicious tiles near the neighbor that aren't
                    # near the tile under consideration.
                    otherPossibleMines = 0
                    for tile in neighborTile.suspiciousNeighbors:
                        if tile not in currentTile.suspiciousNeighbors:
                            otherPossibleMines += 1
                    if minesNearNeighbor < neighborTile.minesToFind - otherPossibleMines:
                        # logging.info("Combo {} is bad because it has too few mines near {}".format(combo,( row, col)))
                        badCombo = True
                        break
                # end for (row, col) in neighbors
                # if we've gotten through all the above code without the
                # flag being set, then this is a good combo and we'll add it to
                # the list.
                if not badCombo:
                    # logging.info("combo {} is good".format(combo))
                    goodCombos.append(list(combo))
            # combo in combinations

            # logging.info("Analyzed {} combos".format(comboCounter))
            # logging.info("Found {} good combos".format(len(goodCombos)))
            if len(goodCombos) == 0:
                raise RuntimeError("Found zero possible ways to place mines near {}".format((i, j)))
            # check and see if there is a suspicious tile that's present in every combo
            inEveryCombo = lambda tile: sum([tile not in combo for combo in goodCombos])
            flagTiles = list(itertools.filterfalse(inEveryCombo, currentTile.suspiciousNeighbors))
            if len(flagTiles) > 0:
                # if there are any, click on them.
                # logging.info("Tile {} is in Every combo. Flagging".format(flagTiles))
                return flagTiles, 'flag'
            #
            # # similarly, check to see if there's a tile that's not present
            notInAnyCombo = lambda tile: sum([tile in combo for combo in goodCombos])
            clearTiles = list(itertools.filterfalse(notInAnyCombo, currentTile.suspiciousNeighbors))
            if len(clearTiles) > 0:
                # logging.info("Tile {} is in no combo. Clearing. ".format(clearTiles))
                return clearTiles, 'click'
            # otherwise store the good combos for later use.
            currentTile.combos = goodCombos
        # end for i, j in rows, columns

        # now we have the following information for every tile.
        # list of combinations that are viable
        minesOnBoard = self.board.mines - flagCounter
        # create a list of the tiles under consideration.
        tilesInFocus = []
        # create a parallel list of the iterators of these tiles.
        tileIterators = []
        for i, j in itertools.product(range(self.board.rows), range(self.board.cols)):
            # a tile should be added to the tilesInFocus if
            # it is not cleared
            # it has suspiciousNeighbors
            # it has a list of combos after it
            currentTile = self.solverTiles[i][j]
            if currentTile.clear:
                continue
            if currentTile.suspiciousNeighbors is None or len(currentTile.suspiciousNeighbors) == 0:
                continue
            tilesInFocus.append((i, j))
            tileIterators.append(0)
        # now we can generate all the combinations we need to work out which of
        # of the tiles is the lowest probability.

        goodComboCounter = 0
        # allCombosList = [self.solverTiles[i][j].combos for (i, j) in tilesInFocus]
        allCombosList = []
        for (i, j) in tilesInFocus:
            currentTile = self.solverTiles[i][j]
            # logging.info("Tile {} has combos {}".format((i, j), currentTile.combos))
            allCombosList.append(currentTile.combos)

        comboCounter = 0
        numCombos = 1
        for comboList in allCombosList:
            numCombos *= len(comboList)

        for wholeBoardCombo in itertools.product(*allCombosList):
            comboCounter += 1
            if comboCounter % 100000 == 0:
                logging.info("Analyzed {} whole board combos of {}".format(comboCounter, numCombos))
            # logging.info("wholeBoardCombo = {}\n, type ={}".format(wholeBoardCombo, type(wholeBoardCombo)))
            wholeBoardCombo = itertools.chain(*wholeBoardCombo)
            # remove duplicates (hacky but somehow effective)
            wholeBoardCombo = list(set(list(wholeBoardCombo)))

            # logging.info("wholeBoardCombo = {}\n, type ={}".format(wholeBoardCombo, type(wholeBoardCombo)))
            # check the combo
            # if the combo has more mines than the number on the board, it's not
            # valid.
            if len(wholeBoardCombo) > minesOnBoard:
                continue
            badCombo = False
            for (i, j) in tilesInFocus:
                currentTile = self.solverTiles[i][j]
                minesNearCurrentTile = sum([self.isNear((i, j), mine) for mine in wholeBoardCombo])
                if minesNearCurrentTile != currentTile.minesToFind:
                    badCombo = True
                    break
            # if our combination is still a possibility, we can increase
            # the suspicion on all the tiles in the combo.
            if not badCombo:
                goodComboCounter += 1
                for (i, j) in wholeBoardCombo:
                    self.solverTiles[i][j].suspicion += 1
        # end for currentCombo

        # Now we've calculated suspicion for all tiles, we can pick tiles with
        # either zero suspicion, 100% suspicion, or the lowest suspsicion.
        clearTiles = []
        flagTiles = []
        leastSuspiciousTile, lowestSuspicion = tilesInFocus[0], goodComboCounter
        for (i, j) in tilesInFocus:
            currentTile = self.solverTiles[i][j]
            for ii, jj in currentTile.suspiciousNeighbors:
                suspiciousTile = self.solverTiles[ii][jj]
                if  (suspiciousTile.clear) or (suspiciousTile.suspicion is None):
                    continue
                if suspiciousTile.suspicion == 0:
                    clearTiles.append((ii, jj))
                elif suspiciousTile.suspicion == goodComboCounter:
                    flagTiles.append((ii, jj))
                elif suspiciousTile.suspicion < lowestSuspicion:
                    # don't need to worry about lowest suspcion if tile has 0% or 100%
                    leastSuspiciousTile = (ii, jj)
                    lowestSuspicion = suspiciousTile.suspicion
            # end for
        # end for
        if len(clearTiles):
            # logging.info("Found {} tiles with 0% suspicion".format(len(clearTiles)))
            return clearTiles, 'click'
        elif len(flagTiles):
            # logging.info("Found {} tiles with 100% suspicion".format(len(flagTiles)))
            return flagTiles, 'flag'
        else:
            logging.info("Tile {} has the lowest suspicion at {:.1%}".format(
                leastSuspiciousTile, lowestSuspicion / goodComboCounter))
            return [leastSuspiciousTile], 'click'
        # That'll do it.
    # end def
    def getNearbyFlags(self):
        """
        returns a nested list of the number of nearby flags for every tile on
        the board
        """
        nearbyFlags = []
        for i in range(self.board.rows):
            row = []
            for j in range(self.board.cols):
                neighbors = self.board.getNeighbors(i, j)
                row.append(sum(self.board.isFlag(*n) for n in neighbors))
            nearbyFlags.append(row)
        return nearbyFlags

    def isGoodGuess(self, combo):
        """
        Checks whether a set of bomb positions contradicts the numbers visible
        on the board
        """
        for i in range(self.board.rows):
            for j in range(self.board.cols):
                if not self.board.isCovered(i, j):
                    # check the number of nearby bombs in this Combination
                    neighbors = self.board.getNeighbors(i, j)
                    suspects = sum([n in combo for n in neighbors])
                    if suspects + self.nearbyFlags[i][j] != self.board.getNumber(i, j):
                        return False

        return True

    def isNear(self, i1, j1, i2 = None, j2=None):
        if i2 is None:
            i2, j2 = j1
            i1, j1 = i1
        diff =  (abs(i1 - i2), abs(j1 - j2))
        if diff == (0, 1) or diff == (1, 0) or diff == (1, 1):
            return True
        else:
            return False

class solverTile(object):
    """
    A class to record properties of a tile that we suspect might have a bomb.
    """
    def __init__(self, board, i, j):
        self.board = board
        self.row = i
        self.col = j
        self.clear = False
        self.suspicion = None
        self.suspiciousNeighbors = []
        self.minesToFind = None
        self.combos = None

    def reset(self):
        """ Resets all the info for about the tiles surroundings """
        self.suspicion = None
        self.suspiciousNeighbors = []
        self.minesToFind = None
        self.combos = None


class Looper(object):
    def __init__(self, solverType):
        self.games = 0
        self.wins = 0
        self.losses = 0
        b = computerBoard(*board.EXPERT)
        while (1):
            try:
                s = solverType(b)
                win = s.start()
                time.sleep(10)
                self.games += 1
                if win is None:
                    pass
                elif win is True:
                    logging.info("VICTORY!")
                    self.wins += 1
                elif win is False:
                    logging.info("DEFEAT!")
                    self.losses += 1
            except KeyboardInterrupt:
                self.printLogs()
                break
    def printLogs(self):
        logging.info("Won: \t{}".format(self.wins))
        logging.info("Lost:\t{}".format(self.losses))
        logging.info("Games:\t{}".format(self.games))
        logging.info("Win pct:\t{:.f%}".format(self.wins / self.games))

    def __del__(self):
        self.printLogs()

class stochasticCombinationGenerator(object):
    """
    A class to generate random Combinations of a list
    """
    def __init__(self, L, samples):
        self.original = L
        self.samples = samples
        # set up rng
        random.seed()

    def next(self):
        """
        A method to generate the next Combination
        """
        return random.sample(self.original, k = self.samples)

class possibilityGenerator(object):
    """
    Given a list of tiles, generates all possibilities for which will be mines
    and which won't
    """
    def __init__(self, L, stochastic = False):
        self.original = L
        self.counter = 1
        self.formatSpecifier = '0'+ str(len(self.original)) + 'b'
        self.stochastic = stochastic
        if stochastic:
            random.seed()
            self.counter = -1

    def next(self):
        mines = []
        if self.counter.bit_length() <= len(self.original):
            # mask = self.counter.to_bytes(len(self.original), byteorder = 'big')
            if self.counter == -1:
                mask = format(random.getrandbits(len(self.original)), self.formatSpecifier)
            else:
                mask = format(self.counter, self.formatSpecifier)
                self.counter += 1
            # print(mask)
            for i in range(len(self.original)):
                if mask[i] == '1':
                    mines.append(self.original[i])

        return mines

    def count(self):
        if self.counter == -1:
            return NUM_RANDOM_GUESSES
        return 2**len(self.original)

def main():
    logging.basicConfig(format = "%(message)s", level = logging.INFO)
    # b = computerBoard(*board.EXPERT)
    # s = AdvancedSolver(b)
    # s.start()
    loops = Looper(AdvancedSolver)
if __name__ == "__main__":
    main()
