
"""
I'm making a python program to play minesweeper
"""

from tkinter import *
from tkinter import ttk
from tkinter import font

import random

IMAGE_GRAPHICS = True
if IMAGE_GRAPHICS:
    from PIL import ImageTk, Image

TILE_SIZE = 18

GAME_MESSAGE = "Clear all the mines"
LOSE_MESSAGE = "Game Over"
WIN_MESSAGE = "VICTORY!"
RESTART_MESSAGE = "New Game"

BEGINNER = (9, 9, 10)
INTERMEDIATE = (16, 16, 40)
EXPERT = (16, 40, 99)


# if __name__ == '__main__':
#     root = Tk()

root = Tk()


class Board(object):
    """
    The board of a minesweeper game.
    Consists of a rows and columns of tiles (tkinter buttons)
    Plus an info box and a restart button
    """
    def __init__(self, rows, cols = None, mines = None):
        """
        Takes three arguments-- rows, columns, mines
        Note that three pre-defined levels can be accessed using the
        BEGINNER, INTERMEDIATE, and EXPERT flags
        """
        # do some argument parsing.
        self._parseArgs(rows, cols, mines)
        self.tileCount = self.rows * self.cols
        self.tiles = None # will be initialized in self.initGUI()
        # some implementations of minesweeper decide the mine positions
        # when the board is first generated. But the original Microsoft
        # implementation has it so that the first tile will always have no
        # mines in neighboring tiles. So a flag for the first tile to click.
        self.firstClick = True
        self.victory = None

        # set up the GUI elements
        # create a window
        # self.root = Tk()
        self.window = ttk.Frame(root, padding=10)

        # set a theme for the window
        # options are 'winnative', 'clam', 'alt', 'default', 'classic',
        # 'vista', 'xpnative'
        # self.style = ttk.Style()
        # self.style.theme_use('winnative')

        self._initTiles()
        self._initWindow()
        # actually show the window
        # self.show()

    def _initWindow(self):
        """
        Sets the basic settings for the window and the background
        """

        # create a frame for all the info outside the game itself.
        self.infoFrame = ttk.Frame(self.window, padding = 5)

        # create an info box to display messages to the user
        self.infoBox = Label(self.infoFrame)
        self.infoBox.grid(row = 0)
        self.infoBox.configure(text = GAME_MESSAGE)

        # create a restart button
        restartButton = Button(self.window)
        restartButton.configure(text = RESTART_MESSAGE)
        restartButton.configure(command = self.restart)
        restartButton.grid(row = 1)

        # grid the infoBox window
        self.infoFrame.grid()
        return

    def _initTiles(self):
        """
        Initializes the grid of tiles
        """
        self.tileWindow = ttk.Frame(self.window, padding = 5)
        self.tiles = TileGrid(self.tileWindow, self.rows, self.cols)
        # bind the tiles to the function
        for i in range(self.rows):
            for j in range(self.cols):
                leftClick = lambda ii = i, jj = j: self.primaryClick(ii, jj)
                rightClick = lambda event, ii = i, jj = j: self.secondaryClick(ii, jj)
                doubleClick = lambda event, ii= i, jj = j: self.doubleClick(ii, jj)
                self.tiles[i][j].configure(command = leftClick)
                self.tiles[i][j].bind(sequence = "<Button-2>", func = rightClick)
                self.tiles[i][j].bind(sequence = "<Button-3>", func = rightClick)
                self.tiles[i][j].bind(sequence = "<Double-Button-1>", func = doubleClick)

        self.tileWindow.grid()
        return

    def primaryClick(self, i, j):
        """
        The actions you take when a tile has a left-click.
        """
        # if all the tiles are covered, set the positions for all the mines
        if self.firstClick:
            self.layMines(i, j)
            self.firstClick = False
        # if the tile has a flag, or if the tile is already uncovered,
        # the primary click does nothing.
        elif (self.tiles[i][j].flag) or (self.tiles[i][j].covered is False):
            return
        # if the tile is unflagged and has a mine, then you lose.
        # Call the game over function.
        if self._checkGameOver(i, j):
            return
        # if none of the above conditions is satisfied, then uncover the tile
        self.tiles[i][j].covered = False
        # we will already have computed the number for the tile in the
        # laymines() method. We only need to check it here.
        if self.tiles[i][j].number == 0:
            # if there are no mines nearby, automatically uncover all the
            # nearby tiles.
            zeroNeighbors = [(i, j)]
            while len(zeroNeighbors) > 0:
                currentZero = zeroNeighbors.pop(0)
                # get the neighbors for the first element in the queue
                newNeighbors = self.getNeighbors(*currentZero)
                for n in newNeighbors:
                    # if the neighbor is covered, uncovrer it
                    if self.tiles[n].covered:
                        self.tiles[n].covered = False
                        self.tiles[n].updateGUI()
                        # if the number is zero, add it to the queue so we can
                        # uncover all of its neighbors later.
                        if self.tiles[n].number == 0:
                            zeroNeighbors.append(n)

        # check for victory
        self._checkVictory()
        # at the end of the routine, update the tile's graphics
        self.tiles[i][j].updateGUI()
        return

    def secondaryClick(self, i, j):
        """
        the actions when a tile has a right-click
        """
        # if a tile is uncovered, don't flag it
        if self.tiles[i][j].covered is False:
            # shouldn't be possible to get into a state where tile.flag is
            # True, but just in case
            self.tiles[i][j].flag = False
        # otherwise, toggle the flag
        else:
            self.tiles[i][j].flag = not self.tiles[i][j].flag
        self.tiles[i][j].updateGUI()

        self._checkVictory()

        return

    def doubleClick(self, i, j):
        """
        The actions taken when a tile is double-clicked
        """
        # if a tile is covered, a double click will count the same as single
        if self.tiles[i][j].covered:
            self.primaryClick(i, j)
            return
        if self.tiles[i][j].number > 0:
            # get the indices of all the neighbors of the double-clicked cell.
            neighbors = self.getNeighbors(i, j)
            # count the flags near the tile in question.
            flags = sum([self.tiles[n].flag for n in neighbors])
            # check if the number of flags is equal to the number of mines
            if flags == self.tiles[i][j].number:
                # if it is, then primary click on every neighbor.
                # go ahead and click on flagged and uncovered tiles. It's fine.
                for n in neighbors:
                    self.primaryClick(*n)
        return

    def layMines(self, clickRow, clickCol):
        """
        Decides which tiles should be mines and lays them there.
        """
        # set up randomness
        random.seed()
        mineCount = 0
        # we need to randomly generate a positon for a mine, check that it's a
        # good position, and repeat until we've generated the correct number
        # of good mines.
        while mineCount < self.mines:
            mineRow = random.randrange(self.rows)
            mineCol = random.randrange(self.cols)
            # if the generated mine position is the first tile clicked, it's
            # no good.
            if mineRow == clickRow and mineCol == clickCol:
                continue
            # if it's a neighbor of the first tile clicked, also no good.
            elif (mineRow, mineCol) in self.getNeighbors(clickRow, clickCol):
                continue
            # if there's already a mine in that position, it's no good.
            elif (self.tiles[mineRow][mineCol].mine):
                continue
            # otherwise, it's a good tile. Set the mine flag and
            # add one to the mine count.
            else:
                self.tiles[mineRow][mineCol].mine = True
                mineCount += 1
                # increment the number for each nearby tile.
                mineNeighbors = self.getNeighbors(mineRow, mineCol)
                for n in mineNeighbors:
                    if not self.tiles[n].mine:
                        self.tiles[n].number += 1
        return

    def _checkGameOver(self, row, col):
        """
        When we trip a mine, the game is over. Put all the logic that happens
        here.
        """
        # if we have a mine
        if self.tiles[row, col].mine is False:
            return False
        else:
            # put a game over message in the infoBox
            self.infoBox.configure(text = LOSE_MESSAGE)

            # show the mine as exploded
            self.tiles[row, col].exploded = True

            # disable all the tiles
            # show the mines
            for i in range(self.rows):
                for j in range(self.cols):
                    # uncover the mines
                    if self.tiles[i][j].mine:
                        self.tiles[i][j].covered = False
                        self.tiles[i][j].updateGUI()
                    elif self.tiles[i][j].flag:
                        self.tiles[i][j].exploded = True
                        self.tiles[i][j].updateGUI()
            self.victory= False
            return True

    def _checkVictory(self):
        # if there is any tile on the board that is covered and has a mine,
        # there's no victory yet.
        for i in range(self.rows):
            for j in range(self.cols):
                if (self.tiles[i][j].mine is False) and (self.tiles[i][j].covered is True):
                    return False

        # Put a Victory message in the info box
        self.victory= True
        self.infoBox.configure(text = WIN_MESSAGE)
        # flag all the mines and disable all the tiles
        for i in range(self.rows):
            for j in range(self.cols):
                if self.tiles[i][j].mine is True:
                    self.tiles[i][j].flag = True
                # update the GUI for every tile.
                self.tiles[i][j].updateGUI()
        return True

    def restart(self):
        """
        if the restart button is pressed, then, well, restart.
        calls both GUI functions and data functions.
        """
        for i in range(self.rows):
            for j in range(self.cols):
                self.tiles[i][j].reset()
                self.tiles[i][j].updateGUI()

        self.infoBox.configure(text = GAME_MESSAGE)
        self.firstClick = True
        self.victory = None
        return

    def getNeighbors(self, i, j):
        """
        returns all the tiles adjacent to tiles[i, j]
        """
        neighbors = set()
        for row in range(i-1, i+2):
            if row < 0 or row >= self.rows:
                continue
            for col in range(j-1, j+2):
                if row == i and col == j:
                    continue
                elif col < 0 or col >= self.cols:
                    continue
                else:
                    neighbors.add((row, col))
        return neighbors

    def show(self):
        self.window.grid()
        self.window.mainloop()

    def addUserInput(self, row = 3):
        """
        Adds a user input to the board.
        For debugging use only.
        """
        waitButton = Button(self.infoFrame)
        waitButton.configure(text = "Next Move")
        waitButton.configure(command = self.releaseWait)
        waitButton.grid(row = row, columnspan = self.cols)

        return

    def releaseWait(self):
        """
        Sets the self.wait variable
        """
        self.hold = False

        return

    def _parseArgs(self, rows, cols, mines):
        """
        The constructor can be called in one of three ways.
        board((rows, cols, mines)) -- all arguments in a tuple
        board(rows, cols, mines) -- arguments as three ints
        board(code) -- uses a string to specify difficulty level.

        This function works out which is being used and sets the values
        of self.rows, self.cols, and self.mines accordingly.
        """
        # case where args are three ints
        errorMessage = """
        The constructor can be called in one of three ways.

        board((rows, cols, mines)) -- all arguments in a tuple
        board(rows, cols, mines) -- arguments as three ints
        board(code) -- uses a string to specify difficulty level.

        Where the string can be
        "BEGINNER" -- \t9x9, 10 mines,
        "INTERMEDIATE"-- \t16x16, 40 mines, or
        "EXPERT" -- \t16x40, 99 mines
        """
        if cols is not None and mines is not None:
                # default case
            self.rows = rows
            self.cols = cols
            self.mines = mines
            return
        difficultyLevel = 0
        # case where a string is passed in
        if isinstance(rows, str):
            difficulties = ["BEGINNER", "INTERMEDIATE", "EXPERT"]
            try:
                difficultyLevel = difficulties.index(rows)
            except ValueError:
                # passed arg is a string but not a valid difficulty
                raise boardError(message)
        # case where a tuple or list is passed in
        else:
            try:
                self.rows, self.cols, self.mines = rows
                return
            except ValueError:
                # not enough values to unpack (or too many)
                raise boardError(message)
            except TypeError:
                # cannot unpack non-iterable object
                difficultyLevel = rows
        # case where an int is passed in
        if difficultyLevel == 1:
            self.rows, self.cols, self.mines = BEGINNER
        elif difficultyLevel == 2:
            self.rows, self.cols, self.mines = INTERMEDIATE
        elif difficultyLevel == 3:
            self.rows, self.cols, self.mines = EXPERT
        else:
            raise boardError(message)
        return

    def __getitem__(self, i, j):
        """
        Makes it easier to deal with lists of (i, j) tuples
        """
        return self.tiles[i][j]

class TileGrid(object):
    """
    An holder to manage a large grid of tile objects
    """
    def __init__(self, window, rows, cols):
        # create a nested list for the tile data structure.
        # call the setup function on each tile.
        self.rows = rows
        self.cols = cols
        self.tiles = []
        for i in range(rows):
            row = []
            for j in range(cols):
                # create the tile and initialize GUI
                tile = Tile(window, i, j)
                row.append(tile)
            self.tiles.append(row)

    def __getitem__(self, i, j = None):
        """
        Allow fetching items using the grid[i, j] or grid[*pair]
        where pair = (i, j), in addition to grid[i][j]
        Does not allow grid[pair]
        """
        # we're going to use leap-before-you-look coding here
        try:
            return self.tiles[i][j]
        except TypeError: # list indices must be integers or slice
            if j is None:
                try:
                    i, j = i
                    return self.tiles[i][j]
                except TypeError: # Cannot unpack non-iterable int
                    return self.tiles[i]

class Tile(Button):
    """
    An extension of the Tkinter Button class that suits our purposes
    """

    # create class variables to correspond to the GUI settings for every
    # state the tile could be in.

    if IMAGE_GRAPHICS:
        image_file_locations = {
            0: 'graphics/uncovered.png',
            1: 'graphics/one.png',
            2: 'graphics/two.png',
            3: 'graphics/three.png',
            4: 'graphics/four.png',
            5: 'graphics/five.png',
            6: 'graphics/six.png',
            7: 'graphics/seven.png',
            8: 'graphics/eight.png',
            'bad_flag' : 'graphics/bad_mine.png',
            'covered' : 'graphics/covered.png',
            'exploded' : 'graphics/exploded.png',
            'flag' : 'graphics/flag.png',
            'mine' : 'graphics/mine.png',
            'question' : 'graphics/question.png',
            'blank' : 'graphics/blank.png',
        }
        tile_images = {}
        for (key, fileLocation) in image_file_locations.items():
            with Image.open(fileLocation) as importedImage:
                importedImage = importedImage.resize((TILE_SIZE, TILE_SIZE),
                    resample = Image.BILINEAR)
                tile_images.update({key: ImageTk.PhotoImage(importedImage)})
        tile_images.setdefault(tile_images['covered'])

        configs = {
            'default':{
                'state': 'normal',
                'image': tile_images['covered'],
                'height': TILE_SIZE-2, 'width': TILE_SIZE -2,
                'relief' : 'flat',
                'borderwidth' : 0,
                'background': 'gray75',
                'padx' : 0, 'pady': 0,
            },
            'flag' : {
                'image': tile_images['flag'],
                'relief' : 'raised',
            },
            'bad flag' : {
                'image': tile_images['bad_flag'],
                'relief' : 'solid',
            },
            'mine' : {
                'image': tile_images['mine'],
                'relief' : 'raised',
            },
            'exploded': {
                'image': tile_images['exploded'],
                'relief' : 'solid',
            },
            'covered': {
                'image': tile_images['covered'],
                'relief' : 'raised',
            },
            'uncovered' : {
                'image':  tile_images[0],
                'relief' : 'flat',
                'activebackground': 'gray75',
        }
    }

    else:
        default_font = font.Font(family = 'terminal', weight = 'bold')
        configs = {
            'default':{
                'state': 'normal',
                'bitmap' : 'gray25', 'text' : ' ', 'compound' : CENTER,
                'height': 14, 'width': 14,
                'relief' : 'raised',
                'font' : 'default_font',
                # 'borderwidth' : 0,
                # 'padx' : 1, 'pady': 1,
            },
            'flag' : {
                'bitmap' : 'warning', 'text' : ' ', 'compound' : CENTER,
                'relief' : 'raised',
            },
            'bad flag' : {
                'bitmap' : 'warning', 'text' : ' ', 'compound' : CENTER,
                'background' : 'red',
                'relief' : 'flat',
            },
            'mine' : {
                'bitmap' : 'error', 'text' : ' ', 'compound' : CENTER,
                'relief' : 'flat',
            },
            'exploded': {
                'bitmap' : 'error', 'text' : ' ', 'compound' : CENTER,
                'background' : 'red',
                'relief' : 'raised',
            },
            'covered': {
                'bitmap' : 'gray25', 'text' : ' ', 'compound' : CENTER,
                'relief' : 'raised',
            },
            'uncovered' : {
                'bitmap' : 'gray12', 'text' : ' ', 'compound' : CENTER,
                'relief' : 'sunken',
            }
        }


    def __init__(self, window, i, j):
        super().__init__(window)
        self.i = i
        self.j = j
        # print(str(self.parent()))
        # using the same procedure for start and reset helps avoid issues
        self.reset()

        self.grid(row = i, column = j)

        return

    def reset(self):
        """ instructions for resetting after the "new game" button is pressed"""
        # set up data fields
        self.covered = True     # tile is covered or uncovered
        self.mine = False       # tile has a mine
        self.flag = False       # user places flag to indicate a mine
        self.number = 0         # number of mines in adjacent tiles
        self.exploded = False   # whether or not the tile has been struck.

        self.configure(self.configs['default'])

    def updateGUI(self):
        """
        Update the GUI after every action.
        """
        # if the tile is flagged it looks like a covered tile with a flag
        # IDEA: different graphics for the first mine tripped.
        if self.flag:
            if self.exploded:
                stateString = 'bad flag'
            else:
                stateString = 'flag'
        else:
            if self.covered:
                stateString = 'covered'
            else:
                if self.mine:
                    if self.exploded:
                        stateString = 'exploded'
                    else:
                        stateString = 'mine'
                else:
                    stateString = 'uncovered'

        self.configure(self.configs[stateString])
        if stateString == 'uncovered':
            if IMAGE_GRAPHICS:
                self.configure(image = self.tile_images[self.number])
            else:
                if self.number > 0:
                    self.configure(text = str(self.number))
        return

class boardError(Exception):
    """
    An error type for dealing with problems that occur with the board
    """
    def __init__(self, message):
        self.message = message

    def __str__(self):
        return self.message

class ImageDisplayGrid(object):
    """
    A class to inspect the graphics. Not used in the final product
    """
    imageFiles =  ['graphics/uncovered.png',
        'graphics/one.png',
        'graphics/two.png',
        'graphics/three.png',
        'graphics/four.png',
        'graphics/five.png',
        'graphics/six.png',
        'graphics/seven.png',
        'graphics/eight.png',
        'graphics/bad_mine.png',
        'graphics/covered.png',
        'graphics/exploded.png',
        'graphics/flag.png',
        'graphics/mine.png',
        'graphics/question.png',
        'graphics/blank.png']
    filters = [Image.NEAREST, Image.BOX, Image.BILINEAR, Image.HAMMING,
        Image.BICUBIC, Image.LANCZOS]

    imSize = 100

    def __init__(self):
        self.window = ttk.Frame(root, padding = 10)
        self.window.grid()
        self.labels = []
        self.experiments = []
        for i in range(len(self.imageFiles)):
            newExperiment = ResizeExperiment(self.imageFiles[i], self.imSize)
            row = []
            for (j, filter) in enumerate(newExperiment.filters):
                newLabel = Label(self.win)
                configs = {'image' : newExperiment[filter],
                    'height' : self.imSize, 'width' : self.imSize,
                    'padx' : 5, 'pady': 5,
                }
                newLabel.configure(configs)
                newLabel.grid(row = i, column = j, rowspan = 1, columnspan = 1)
                row.append(newLabel)
            self.labels.append(row)
            self.experiments.append(newExperiment)
        return

class ResizeExperiment(object):
    filters = [Image.NEAREST, Image.BOX, Image.BILINEAR, Image.HAMMING,
        Image.BICUBIC, Image.LANCZOS]
    def __init__(self, filename, imsize):
        self.asDict = {}
        with Image.open(filename) as f:
            self.original = f
            for i in range(len(self.filters)):
                resizedImage = self.original.resize((imsize, imsize), resample = self.filters[i])
                self.asDict.update({self.filters[i] : ImageTk.PhotoImage(resizedImage)})

    def __getitem__(self, key):
        return self.asDict[key]

    def __len__(self):
        return len(self.asDict)

def test():
    tester = ImageDisplayGrid()
    root.mainloop()

def main():
    b = Board(BEGINNER)
    b.show()
    # test()

if __name__ == "__main__":
    main()
