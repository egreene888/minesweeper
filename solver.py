"""
solver.py

We've implemented a minesweeper game, now we need to make an AI to solve it
This edition re-writes and re-factors some of the code.

Author: Evan Greene
Date: 2022-02-28
"""
import board
import random
import threading
from collections import deque
import time
from itertools import combinations

import logging
# if __name__ == "__main__":
    # if we're importing this in another module, don't configure the logging.
    # that way it won't actually do any logging.
logging.basicConfig(format = "%(message)s", level = logging.INFO)

# timer strategies
INSTANT = 0
QUICK_MOVE = 1
SLOW_MOVE = 2
USER_INPUT = 3

# don't make guesses as fast as the computer can, use a timer.
MOVE_TIME = 0.5

class Solver(object):
    """
    This class serves as an interface between the board object and the
    logic of the solver. Sets up the threading and defines an API for the
    interaction.

    Other solvers will have this solver as a base class.
    """

    repeat = True
    timing = SLOW_MOVE

    def __init__(self, game):
        self.board = game
        self.queue = SolverQueue([])
        # create a separate thread to call the solve() function.
        self.solverThread = threading.Thread(target = self.solve, name = 'solver')
        self.solverThread.daemon = True

        if self.timing == USER_INPUT:
            self.board.addUserInput()
            self.board.hold = True

    def start(self):
        """
        Invokes the start of the threads for the game and the solver
        """
        # # if the solver board isn't in the ready-to-start state, restart it
        # if not self.board.firstClick:
        #     self.board.restart()
        #     time.sleep(MOVE_TIME)

        # start the solver thread
        self.solverThread.start()

        self.board.show()
        return

    def solve(self):
        """
        Gets the show on the road.
        Performs all the moves in the queue. When the queue is empty, calls the
        guess function to get more, until the victory variable is set.

        Takes no arguments and returns the victory variable
        """
        while True:
            self.victory = None
            while self.victory is None:

                # start the timer.
                startTime = time.time()
                stopTime = startTime + MOVE_TIME

                if len(self.queue) == 0:
                    try:
                        self.guess()
                        self.validateQueue()
                    except SolverError as e:
                        # try to fail cleanly.
                        self.board.window.quit()
                        raise SystemExit from e
                        
                    if self.timing == QUICK_MOVE:
                        waitUntil(stopTime)

                nextGuess = self.queue.popleft()
                if nextGuess.getAction() == 'click':
                    self.board.primaryClick(*nextGuess.getTile())
                elif nextGuess.getAction() == 'flag':
                    if not self.isFlag(*nextGuess.getTile()):
                        self.board.secondaryClick(*nextGuess.getTile())
                elif nextGuess.getAction() == 'double':
                    self.board.doubleClick(*nextGuess.getTile())

                self.victory = self.board.victory

                if self.timing == SLOW_MOVE:
                    waitUntil(stopTime)
                elif self.timing == USER_INPUT:
                    self.board.hold = True
                    while self.board.hold:
                        time.sleep(0.01)
            # end while self.victory is None

            # once the game is complete (victory or failure), check the
            # loopForever variable
            if self.repeat:
                if self.timing != INSTANT:
                    # wait for a human to hit the restart button.
                    while not self.board.firstClick:
                        time.sleep(MOVE_TIME)
                # reset before going back into the loop.
                self.reset()
            else:
                # break out of the while loop and exit the thread.
                break
        # end while
        # once we're done, close the Tk window.
        self.board.window.quit()
        # kill the current thread if it's not somehow the main one
        if threading.current_thread() is not threading.main_thread():
            raise SystemExit

        return
    # end def solve

    def guess(self):
        """
        This is a template function. It guesses at random from among all the
        tiles that are covered.

        Takes no input and returns None; only the self.queue variable will
        be modified.

        Implementations of actual solvers will overwrite
        """

        while True:
            guessRow = random.randrange(self.board.rows)
            guessCol = random.randrange(self.board.cols)

            if self.isCovered(guessRow, guessCol):
                self.queue.add(guessRow, guessCol, 'click')
                return

    def user_guess(self):
        """
        gets a guess from the user
        """
        row = int(input("Enter the Row: "))
        col = int(input("Enter the Column: "))
        action = input("Enter the action: ")
        self.queue.add(row, col, action)
        return

    def validateQueue(self):
        """
        A helper function for debugging. Makes sure the action and the tile
        are valid guesses
        """
        for item in self.queue:
            # The way this will work is that there is a string for the error
            # message. Rather than raise at each check, add to the error message.
            # Then check the string at the end to decide whether to raise.
            # Allows multiple problems to be caught in one error message.
            message = ""
            # check that the row and column are within the board.
            if (item.row < 0) or (item.row > self.board.rows):
                message += "Guessed Row must be in range {} to {} \n".format(0, self.board.rows)
            if (item.col < 0) or (item.row > self.board.rows):
                message += "Guessed Column must be in range {} to {} \n".format(0, self.board.cols)
            if item.action not in ['click', 'double', 'flag']:
                message += "Invalid action {} \n".format('\'' + item.action + '\'')
            if self.isFlag(*item.getTile()):
                if item.action == 'click':
                    message += "Cannot click a flagged tile \n"
                elif item.action == 'double':
                    message += "Cannot double-click a flagged tile \n"
                elif item.action == 'flag':
                    message += "Cannot un-flag already flagged tile \n"
            elif item.action == 'click':
                if not self.isCovered(*item.getTile()):
                    message += "Tile cannot be clicked on if uncovered \n"
            elif item.action == 'flag':
                if not self.isCovered(*item.getTile()):
                    message += "Tile cannot be flagged if uncovered \n"
            elif item.action == 'double':
                if self.isCovered(*item.getTile()):
                    message += "Cannot double-click on a covered tile\n"
                # check if we're double-clicking on a tile with no nearby mines
                for neighbor in self.board.getNeighbors(*item.getTile()):
                    if self.isCovered(*neighbor):
                        break
                else:
                    message += "Cannot double click: No covered tiles nearby \n"

            if message:
                message = "Invalid Guess {}: \n".format(item.getTile()) + message
                raise SolverError(message)
                break
        # end for
        return
    # end def validateQueue

    def pickRandom(self):
        """
        Utility function to pick a tile from the board at random
        """
        random.seed()
        guessPos = random.randint(0, self.board.tileCount - 1)
        guessRow = guessPos // self.board.cols
        guessCol = guessPos % self.board.cols
        return (guessRow, guessCol)

    def reset(self):
        """
        Deletes all the stored information about the state of the board.
        """
        self.queue = SolverQueue([])

    # solving should use these three functions for information about the
    # state of the board, not any info on the board object directly.
    # No peeking!
    def isCovered(self, row, col):
        """ Helper function to find whether a board tile is covered """
        return self.board.tiles[row][col].covered

    def isFlag(self, row, col):
        """ Helper function to find whether a board tile is flagged """
        return self.isCovered(row, col) and self.board.tiles[row][col].flag

    def getNumber(self, row, col):
        """ Helper function to find how many times are near a tile """
        if not self.isCovered(row, col):
            return self.board.tiles[row][col].number
        else:
            message = "Cannot get number for {}: is covered".format((row, col))
            raise SolverError(message)

    def getNeighbors(self, row, col):
        """
        I keep calling this function my mistake, so I created it.
        Calls self.board.getNeighbors()
        """
        return self.board.getNeighbors(row, col)

class BasicSolver(Solver):
    """
    Extends the solver class

    Overwrites the guess method so that it can actually play minesweeper
    """

    def __init__(self, game):
        """
        Extend the constructor to add the solver tile data, which keeps track
        of what the solver knows about a tile.
        """
        super().__init__(game)

        logging.info("Initialized solver")
        self.grid = SolverGrid(game)
        return

    def guess(self):
        """
        Applies two basic rules then guesses if that's unsuccessful
        """
        if self.board.firstClick:
            self.queue.add(*self.pickRandom(), 'click')
            return

        # gather the basic info for each tile needed to make a decision.
        self.gatherTileInfo()

        self.guessWithBasicRules()

        if len(self.queue):
            return

        self.guessAtRandom()
        logging.info("Guessed {} at random".format(self.queue[0].getTile()))
        return

    def guessWithBasicRules(self):
        """
        Applies 2 basic rules.
        1.  If the number on an uncovered tile is equal to the number of
        covered tiles around it, flag all of them as bombs.
        2. If the number on an uncovered tile is equal to the number of flags
        nearby, click on all the remaining uncovered tiles, if any.
        """
        for i in range(self.board.rows):
            for j in range(self.board.cols):
                tile = self.grid[i, j]
                # if a tile has been marked as clear, it's because there is
                # nothing interesting to find here.
                if tile.clear:
                    continue
                if self.isCovered(i, j):
                    continue
                # if the number of neighbor flags is equal to the number of the tile,
                # we can double-click the tile
                if self.getNumber(i, j) == tile.nearbyFlags:
                    # don't bother if there are no neighbors to flag
                    if tile.nearbyCovered > tile.nearbyFlags:
                        self.queue.add(i, j, 'double')
                        return
                # if the nearby covered tiles is equal to the number of the tile
                # flag all the tiles that aren't already flagged.
                elif self.getNumber(i, j) == tile.nearbyCovered:
                    for neighbor in tile.neighbors:
                        if self.isCovered(*neighbor):
                            if not self.isFlag(*neighbor):
                                self.queue.add(*neighbor, 'flag')
                # if there are too few uncovered tiles to meet the number of mines,
                # that's an error.
                elif self.getNumber(i, j) < tile.nearbyFlags:
                    message = "Error near tile {}: too many flags.".format((i, j))
                    raise SolverError(message)
        return

    def guessAtRandom(self):
        """
        Guesses from among the tiles that are covered and adjacent to an
        uncovered tile. If there are no such tiles, guesses at random from
        among all covered tiles.
        """
        guessableTiles = []
        for i in range(self.board.rows):
            for j in range(self.board.cols):
                tile = self.grid[i, j]
                if tile.clear:
                    continue
                # do not guess any tiles that are already uncovered
                if not self.isCovered(i, j):
                    continue
                # do not guess any flagged tiles.
                if self.isFlag(i, j):
                    continue

                # if the covered tile has at least one uncovered tile
                # then it becomes guessable.
                for neighbor in tile.neighbors:
                    if not self.isCovered(*neighbor):
                        guessableTiles.append((i, j))
                        break
        # if we haven't found any guessable tiles, all the covered tiles are
        # then guessable.
        if len(guessableTiles) == 0:
            for i in range(self.board.rows):
                for j in range(self.board.cols):
                    # do not guess any tiles that are already uncovered
                    if not self.isCovered(i, j):
                        continue
                    # do not guess any tiles that are flagged
                    if self.isFlag(i, j):
                        continue
                    guessableTiles.append((i, j))

        randomTile = random.choice(guessableTiles)
        self.queue.add(*randomTile, 'click')
        return

    def gatherTileInfo(self):
        """
        Finds the following data for a given tile.
        -- Number of nearby flagged tiles
        -- Number of nearby covered tiles
        -- A list of the tile's neighbors
        -- Whether the tile should be marked clear
            (no covered, unflagged neighbor tiles)
        """
        for i in range(self.grid.rows):
            for j in range(self.grid.cols):
                tile = self.grid[i, j]

                if tile.clear:
                    continue

                if tile.neighbors is None:
                    tile.neighbors = self.getNeighbors(i, j)

                if self.isCovered(i, j):
                    continue

                # count the nearby flagged tiles
                # count the nearby covered tiles.
                tile.nearbyCovered = 0
                tile.nearbyFlags = 0
                for ni, nj in tile.neighbors:
                    if self.isCovered(ni, nj):
                        tile.nearbyCovered += 1
                        if self.isFlag(ni, nj):
                            tile.nearbyFlags += 1
                # check if the tile should be clear.
                if tile.nearbyCovered == tile.nearbyFlags:
                    if tile.nearbyCovered == self.getNumber(i, j):
                        tile.clearTile()
                    else:
                        message = "Tile {} was has {} flags nearby. ".format(
                            (i, j), tile.nearbyFlags)
                        raise SolverError(message)

        return

    def reset(self):
        """
        Deletes all the stored information about the state of the board.
        """
        self.grid = SolverGrid(self.board)
        self.queue = SolverQueue([])

class AdvancedSolver(BasicSolver):
    """
    This solver allows for more advanced solutions of minesweeper by
    accounting for second neighbors (neighbors of neighbors) when deciding
    which tiles near a given uncovered tiles can be bombs.
    """

    def guess(self):
        """
        Applies two rules
        -- If the number on a tile is equal to the number of covered tiles
            nearby, then flag all the covered tiles nearby.
        -- If the number on the tile is equal to the number of flagged tiles
            nearby, double-click the tile to uncover any nearby covered tiles.
        If the above rules cannot be applied, considers every possible
        combination of mines that could be placed around every tile.
        -- If a combination places too many or too few mines near a neighboring
            tile, then it is not a viable combination.
        -- If a tile has only one viable combination of mines, flag the tiles
            corresponding to that combination.
        If the above rules cannot be used to make a guess, consider every
        board-wide meta-combination of combinations.
        -- If a meta-combination has more mines than the total number of mines
            on the board, it's not viable.
        -- If a meta-combination places too many or too few mines near a
            particular tile, it's not viable.
        -- For each viable meta-combination, increment a suspicion value for
            every mine in the meta-combination
        -- Once every combination has been analyzed, flag all the tiles that
            have 100% suspicion, and clear all the tiles that have 0% suspicion
        -- If that fails, clear the tile with the lowest suspicion.
        """
        if self.board.firstClick:
            self.queue.add(*self.pickRandom(), 'click')
            return

        # gather the basic info for each tile needed to make a decision.
        # use a simple formula to make a guess
        self.gatherNeighborInfo()
        self.guessWithBasicRules()

        if len(self.queue):
            return

        # use a more complicated formula to make a guess
        self.gatherSecondNeighborInfo()
        self.advancedGuess()

        # finally, use the very computationally-intense method to make a guess
        # IDEA: put this in another thread and use a watchdog to kill it after
        # it runs for too long.
        self.calculateSuspicions()
        self.guessFromSuspicions()

        if len(self.queue):
            return

        leastSuspiciousTile = None
        lowestSuspicion = 0
        for i in range(self.grid.rows):
            for j in range(self.grid.rows):
                tile = self.grid[i][j]
                if tile.suspicion == 0:
                    self.queue.add(i, j, 'click')
                elif tile.suspicion == self.comboCounter:
                    self.queue.add(i, j, 'flag')
                else:
                    leastSuspicousTile = (i, j)
                    lowestSuspicion = tile.suspicion

        if len(self.queue) == 0:
            self.queue.add(*leastSuspicousTile, 'click')
            return

        self.guessAtRandom()
        logging.info("Guessed {} at random".format(self.queue[0].getTile()))
        return

    def advancedGuess(self):
        for i in range(self.board.rows):
            for j in range(self.board.cols):
                tile = self.grid[i, j]

                # look for tiles in every good combination and in no
                # good combination.
                definitelyMines = tile.suspiciousNeighbors
                definitelyClear = tile.suspiciousNeighbors

                for combo in tile.goodCombos:
                    # Any tile not in the current combo is not definitely a mine
                    definitelyMines.intersection_update(combo)
                    # definitelyMines &= combo
                    # remove any tile in the current combo from inNoCombo
                    definitelyClear.difference_update(combo)
                    # definitelyClear -= combo
                    # this might speed things up a bit.
                    if len(inEveryCombo) == 0 and len(inNoCombo) == 0:
                        break

                # checking that the sets are empty is actually unnecessary
                # if they are empty the for loop won't do anything.
                for mine in definitelyMines:
                    self.queue.add(*mine, 'flag')

                for clearTile in definitelyClear:
                    self.queue.add(*clearTile, 'click')

    def guessFromSuspicions(self):
        self.guessAtRandom()
        return

    def gatherNeighborInfo(self):
        """
        Finds the following data for every tile.
        -- Number of nearby flagged tiles
        -- Number of nearby covered tiles
        -- A list of the tile's neighbors
        -- A list of *suspicious* neighbors* (covered but not flagged)
        -- Whether the tile should be marked clear (no suspicious neighbors)
        Also counts the number of flags on the board.
        """
        # start a counter for the flags on the board.
        self.grid.flagCounter = 0
        for i in range(self.board.rows):
            for j in range(self.board.cols):
                tile = self.grid[i][j]
                if tile.clear:
                    continue

                if tile.neighbors is None:
                    tile.neighbors = self.getNeighbors(i, j)

                if self.isCovered(i, j):
                    if self.isFlag(i, j):
                        self.grid.flagCounter += 1
                    continue


                # the suspicious neighbors are a list of tiles that are
                # both covered and not flagged. Will come in handly later.
                tile.suspiciousNeighbors = set()
                tile.nearbyCovered = 0
                tile.nearbyFlags = 0
                for neighbor in tile.neighbors:
                    if self.isCovered(*neighbor):
                        tile.nearbyCovered += 1
                        if self.isFlag(*neighbor):
                            tile.nearbyFlags += 1
                        else:
                            tile.suspiciousNeighbors.add(neighbor)
                if len(tile.suspiciousNeighbors) == 0:
                    tile.clearTile()

        return

    def gatherSecondNeighborInfo(self):
        """
        Calculates the following information for every tile
        -- A list of the viable combinations of suspicious tiles.
        """
        # generate the list of suspicious neighbors
        for i in range(self.board.rows):
            for j in range(self.board.cols):
                tile = self.grid[i][j]

                if tile.clear:
                    continue

                if self.isCovered(i, j):
                    continue

                # create an iterator of all the combinations of mines.
                missingMines = tile.nearbyCovered - tile.nearbyFlags
                comboIterator = itertools.combinations(tile.suspiciousNeighbors, missingMines)

                # create a list of good combinations.
                tile.goodCombos = []

                # create a list of all the second neighbors (neighbors of neighbors)
                secondNeighbors = tile.neighbors
                for neighbor in tile.neighbors:
                    secondNeighbors.update(self.grid[neighbor].neighbors)

                # iterate through all the combinations.
                for combo in comboIterator:
                    badCombo = False
                    for neighbor in secondNeighbors:
                        # no real useful information from covered tiles.
                        if self.isCovered(*neighbor):
                            continue
                        neighborTile = self.grid[neighbor]
                        # find the number of missing mines near this tile
                        # should not be zero.
                        missingMines = neighborTile.nearbyCovered - neighborTile.nearbyFlags
                        # the combo is a set of mines near the tile in focus.
                        # check how many mines this combo puts near this neighbor
                        minesNearNeighbor = neighborTile.suspiciousNeighbors.intersection(combo)
                        # check how many mines are "missing" near the neighbor
                        # if there are too many mines, this isn't a good combo.
                        if len(minesNearNeighbor) > missingMines:
                            break
                        # check if this combo puts too *few* mines near a neighbor
                        remainingSuspiciousNeighbors = neighborTile.suspiciousNeighbors - combo
                        if len(remainingSuspiciousNeighbors) < missingMines - len(minesNearNeighbor):
                            break
                    else:
                        tile.goodCombos.append(combo)

    def calculateSuspicions(self):
        """
        Calculates a suspicion value associated with each tile
        """
        pass

class SolverGrid(object):
    """
    A class to store and access the SolverTile object associated with all the
    tiles on the board.
    """
    def __init__(self, board):
        """
        Takes the board as input and initializes all of the data objects
        """
        self.rows = board.rows
        self.cols = board.cols

        self.tiles = []
        for i in range(self.rows):
            row = []
            for j in range(self.cols):
                newTile = SolverTile()
                row.append(newTile)
            self.tiles.append(row)
        return

    def __getitem__(self, i, j = None):
        """
        Will allow grid[i, j], grid[i][j] and grid[(i, j)]
        """
        try:
            return self.tiles[i][j]
        except TypeError: # list indices must be integers or slice
            if j is None:
                try:
                    i, j = i
                    return self.tiles[i][j]
                except TypeError: # Cannot unpack non-iterable int
                    return self.tiles[i]

class SolverTile(object):
    """
    A class to hold info that we gather about a particular tile as we gather it
    """
    def __init__(self):
        """
        Always have the clear field, but everything else will be initialized
        and destroyed as needed
        """
        self.clear = False
        self.neighbors = None

    def clearTile(self):
        """
        Set the clear flag to false and destroy all other variables
        """
        # This is kinda hacky but let's see how it goes.
        contents = list(self.__dict__)
        for key in contents:
                self.__delattr__(key)
        self.clear = True
        return

class SolverQueue(deque):
    """
    Extends the collections.deque by adding methods to
    -- add a QueueItem object without calling its constructor
    -- prevent duplicate tiles from being added to the queue
    """
    def add(self, row, column, action = 'click'):
        """
        Checks whether a function is already in the queue. Returns False if it
        is, adds the object and returns True if it isn't.
        """
        if (row, column) in self:
            return False
        else:
            self.append(QueueItem(row, column, action))
            return True
# end class SolverQueue

class QueueItem(object):
    """
    A helper class to manage the list of names from the solver.
    """
    def __init__(self, row, column, action = 'click'):
        self.row = row
        self.col = column
        self.action = action
        return

    def __eq__(self, other):
        """
        Should work on another QueueItem or a (row, column) tuple
        Compares on row and column, NOT on action.
        """
        # try the case where the object is a QueueItem or something
        # resembling it.
        try:
            return other.row == self.row and other.col == self.col
        # try the case where the object is a tuple.
        except AttributeError:
            row, column, *_ = other
            return row == self.row and column == self.col

    def getTile(self):
        return (self.row, self.col)

    def getAction(self):
        return self.action
# end class QueueItem

class SolverError(Exception):
    """
    An error type for dealing with problems that occur with the board
    Allows me to put error messages and distinguish between logical errors and
    syntax or other Runtime Errors.
    """
    def __init__(self, message):
        self.message = message

    def __str__(self):
        return self.message

def waitUntil(endTime):
    """
    Probably not function-worthy
    """
    currentTime = time.time()
    if currentTime < endTime:
        time.sleep(endTime - currentTime)
    return

def test():
    """
    Kind of a playground to test smaller bits of code
    """
    b = board.Board(board.BEGINNER)
    s = BasicSolver(b)
    coords = (2, 3)
    print(s.grid[coords])
    print(s.grid[(2, 3)])
    print(s.grid[2, 3])

def main():
    # test()
    b = board.Board(board.BEGINNER)
    s = AdvancedSolver(b)
    s.start()
if __name__ == '__main__':
    main()
