"""
test.py

A tester that will
-- create a tester object (an extension of the board class)
-- create a list of test scenarios.
-- run the a solver object through the tests
"""
from tkinter import *
from tkinter import ttk
from tkinter import filedialog, messagebox

import re
import threading

import board
from board import root
import solver

import logging
if __name__ == "__main__":
    # if we're importing this in another module, don't configure the logging.
    # that way it won't actually do any logging.
    logging.basicConfig(format = "%(message)s", level = logging.INFO)

class tester(object):
    """
    An object to hold the boards we need to do the testing, the solver we're
    testing, and to record the success/failure info
    """
    # board_names = ['one.txt']
    board_names = ['one.txt', 'two.txt', 'clear.txt']
    tests_dir = './tests/basic/'

    def __init__(self, solverClass):
        """
        Takes as input a class of solver, and creates a solver for various
        boards.
        """
        self.testList = self.loadFiles()

        for i, boardToSolve in enumerate(self.testList):
            # TODO: Gather more info and statistics about the tests.
            solverInstance = solverClass(boardToSolve)
            logging.info("testing board {}".format(self.board_names[i]))
            # make the solver not loop forever.
            solverInstance.repeat = False
            solverInstance.start()
            if boardToSolve.victory:
                logging.info("Correctly solved board {}".format(self.board_names[i]))
            else:
                logging.info("Failed board {}".format(self.board_names[i]))

            # close the board window.
            try:
                boardToSolve.window.destroy()
            # potentially over-general except clause, should probably do something about that. 
            except : # can't invoke "destroy" command: application has been destroyed
                # fail silently
                pass
        return

    def loadFiles(self):
        testList = []
        for filename in self.board_names:
            newBoard = testBoard(self.tests_dir + filename)
            testList.append(newBoard)
        return testList

class testBoard(board.Board):
    """
    An extension of the board class that doesn't lay mines at random, but
    instead loads them from a file.
    """
    def __init__(self, filename = None):
        self.fromFile(filename)
        super().__init__(self.rows, self.cols, len(self.initialMineList))
        self.firstClick = False
        self.layMines()


    def fromFile(self, filename):
        """
        Load the information from a file.
        """
        with open(filename) as f:
            lines = f.readlines()

        # kinda banking on there being only one of each line.
        for line in lines:
            if re.match("Size", line):
                sizeString = line
            elif re.match("Mines", line):
                self.initialMineList = toTiles(line)
            elif re.match("Flags", line):
                self.initialFlagList = toTiles(line)
            elif re.match("Uncovered", line):
                self.initialUncoveredList = toTiles(line)

        assert(sizeString)
        size = toTiles(sizeString)
        self.rows, self.cols = size[0]

        return

    def fromList(self, mineString, uncoveredString):
        """
        Takes two lists-- one with all the tiles that have mines, the other
        with all the tiles that are uncovered.
        """
        # TODO
        pass

    def layMines(self, *_):
        """
        Lays all the mines and flags, uncovers tiles
        """
        for mineTile in self.initialMineList:
            self.tiles[mineTile].mine = True

        for flagTile in self.initialFlagList:
            self.tiles[flagTile].mine = True
            self.tiles[flagTile].flag = True

        for uncoveredTile in self.initialUncoveredList:
            if not self.tiles[uncoveredTile].mine:
                self.tiles[uncoveredTile].covered = False

        # assign the numbers correctly
        for i in range(self.rows):
            for j in range(self.rows):
                if self.tiles[i][j].mine:
                    for neighbor in self.getNeighbors(*mineTile):
                        if not self.tiles[neighbor].mine:
                            self.tiles[neighbor].number += 1

        # check for incompatible combinations of flag, tile, and covered.
        self.checkForLoadErrors()

        for i in range(self.rows):
            for j in range(self.cols):
                self.tiles[i][j].updateGUI()

    def _checkVictory(self):
        """
        Overwrite the method to check victory, a successful test is different
        from a test in game.
        """
        # the test is successful if all of the flags from the loaded test board
        # are actually flagged by the solver
        for i in range(self.rows):
            for j in range(self.cols):
                if self.tiles[i][j].mine:
                    if not self.tiles[i][j].flag:
                        return False
        # Put a Victory message in the info box
        self.victory= True
        self.infoBox.configure(text = board.WIN_MESSAGE)

        return True

    def checkForLoadErrors(self):
        for i in range(self.rows):
            for j in range(self.cols):
                tile = self.tiles[i][j]
                errorMessage = ""
                if tile.mine:
                    if not tile.covered:
                        errorMessage += "Mines Must be covered\n"
                if tile.flag:
                    if not tile.mine:
                        errorMessage += "Mines must be covered"
                    if not tile.covered:
                        errorMessage += "Flagged tiles must be covered\n"
                if errorMessage:
                    errorMessage = "Problem with loaded board at tile {}".format((tile.i, tile.j))

class testCreator(board.Board):
    """
    A tool to create a tests for the board class.
    Pulls up a window and allows you to assign and unassign mines/covered tiles
    """

    valid_entry_dict = {
        'highlightbackground' : 'SystemWindow',
        'highlightthickness' :  0,
        'highlightcolor': 'black',
        'width': 6,
    }
    invalid_entry_dict = {
        'highlightbackground' : 'red',
        'highlightthickness' :  1,
        'highlightcolor': 'red',
        'width': 6,
    }

    def __init__(self, rows = 5, cols = 5):
        """
        Initializes the tester object
        -- Creates window to specify the number of rows and columns
        -- Creates a window to show the number of mines
        -- Creates a grid of tiles (defaults to 5x5)
        """

        self.rows = rows
        self.cols = cols
        # create a window to contain all the other elements
        self.window = ttk.Frame(root, padding = 30)
        self.window.configure(height = "3 in", width = "4 in")
        self.window.grid_propagate(0)
        self.window.grid()
        self.initEntryWindow()
        self.initTileGrid()
        self.initSaveWindow()

        # grid all the windows here so the geometry is managed properly.
        self.entryWindow.grid(row = 0)
        self.tileWindow.grid(row = 1)
        self.saveWindow.grid(row = 2)
        # now grid the entry window.

        return

    def initEntryWindow(self):
        # create a window with entry boxes
        self.entryWindow = ttk.Frame(self.window, padding = 5)

        # create a variable to hold the value of the rows.
        self.rowInput = StringVar()
        self.rowInput.set(self.rows)
        # create an entry box and a label for it.
        self.rowLabel = ttk.Label(self.entryWindow, text = "Rows: ")
        self.rowEntry = Entry(self.entryWindow,
            textvariable = self.rowInput)
        self.rowEntry.configure(validate = 'focusout',
            validatecommand = (root.register(self.updateRows),  '%P',))
        self.rowEntry.configure(self.valid_entry_dict)
        # set up validation.
        self.colInput = StringVar()
        self.colInput.set(self.cols)
        self.colLabel = ttk.Label(self.entryWindow, text = "Columns: ")
        self.colEntry = Entry(self.entryWindow,
            textvariable = self.colInput)
        self.colEntry.configure(validate = 'focusout',
            validatecommand = (root.register(self.updateCols), '%P'))
        self.colEntry.configure(self.valid_entry_dict)

        # manage the geometry.
        self.rowLabel.grid(row = 0, column = 0)
        self.rowEntry.grid(row = 0, column = 1)
        self.colLabel.grid(row = 1, column = 0)
        self.colEntry.grid(row = 1, column = 1)

        return

    def initTileGrid(self):
        # create a grid with tiles in it.
        self.tileWindow = ttk.Frame(self.window, padding = 5)
        self.tiles = board.TileGrid(self.tileWindow, self.rows, self.cols)
        for i in range(self.rows):
            for j in range(self.cols):
                self.bindTile(i, j)

        return

    def bindTile(self, i, j):
        # bind the tiles so that things happen when you click on them.
        tile = self.tiles[i][j]
        # bindFunction = lambda  ii=i, jj=j: self.toggleMine(ii, jj)
        # tile.configure(command = bindFunction)
        bindFunction = lambda event, ii = i, jj = j: self.toggleMine(ii, jj)
        tile.bind(sequence = "<Button-1>", func = bindFunction)

        bindFunction = lambda event, ii = i, jj = j: self.toggleFlag(ii, jj)
        tile.bind(sequence = "<Button-2>", func = bindFunction)
        tile.bind(sequence = "<Button-3>", func = bindFunction)

        bindFunction = lambda event, ii = i, jj = j: self.toggleCovered(ii, jj)
        tile.bind(sequence = "<Control-Button-1>", func = bindFunction)
        return

    def updateRows(self, newString):

        # don't update while the user is actively changing things.
        if self.validateNumber(newString):
            self.rows = int(newString)
            self.rowEntry.configure(self.valid_entry_dict)

            # update the number of rows in the grid
            if self.rows > self.tiles.rows:
                # add more tile objects to the grid.
                for i in range(self.tiles.rows, self.rows):
                    newRow = []
                    for j in range(self.cols):
                        newTile = board.Tile(self.tileWindow, i, j)
                        newRow.append(newTile)
                    self.tiles.tiles.append(newRow)
                # bind the keypress events to the newly created tiles.
                for i in range(self.tiles.rows, self.rows):
                    for j in range(self.cols):
                        self.bindTile(i, j)
            elif self.rows < self.tiles.rows:
                # destroy the tile objects in the extra rows
                for i in range(self.rows, self.tiles.rows):
                    for j in range(self.cols):
                        self.tiles[i][j].destroy()
                    del self.tiles[i][:]
            self.tiles.rows = self.rows

            return True
        else:
            self.rowEntry.configure(self.invalid_entry_dict)
            return False

    def updateCols(self, newString):
        if self.validateNumber(newString):
            self.cols = int(newString)
            self.colEntry.configure(self.valid_entry_dict)

            # update the number of columns in the grid GUI
            if self.cols > self.tiles.cols:
                # add more tile objects
                for i in range(self.rows):
                    for j in range(self.tiles.cols, self.cols):
                        newTile = board.Tile(self.tileWindow, i, j)
                        self.tiles[i].append(newTile)
                for i in range(self.rows):
                    for j in range(self.tiles.cols, self.cols):
                        self.bindTile(i, j)
            elif self.cols < self.tiles.cols:
                for i in range(self.rows):
                    for j in range(self.cols, self.tiles.cols):
                        self.tiles[i][j].destroy()
                    del self.tiles[i][self.cols:self.tiles.cols]
            self.tiles.cols = self.cols
            return True
        else:
            self.colEntry.configure(self.invalid_entry_dict)
            return False

    def validateNumber(self, numberString):
        # let's try-catch this
        try:
            number = int(numberString)
        except ValueError: # invalid literal
            return False
        return number >= 2 and number < 100

    def toggleMine(self, i, j):
        tile = self.tiles[i][j]
        if tile.flag:
            return
        tile.mine = not tile.mine
        # a tile is always uncovered if it's a mine
        tile.covered = not tile.mine
        # count the numbers for every non-mine tile
        for neighbor in self.getNeighbors(i, j):
            neighborTile = self.tiles[neighbor]
            neighborTile.number += 1 if tile.mine else -1
            neighborTile.updateGUI()
        tile.updateGUI()
        return

    def toggleFlag(self, i, j):
        tile = self.tiles[i][j]
        if not tile.covered:
            return

        tile.flag = not tile.flag
        tile.mine = tile.flag
        tile.updateGUI()

        for neighbor in self.getNeighbors(i, j):
            neighborTile = self.tiles[neighbor]
            neighborTile.number += 1 if tile.mine else -1
            neighborTile.updateGUI()
        return

    def toggleCovered(self, i, j):
        tile = self.tiles[i][j]
        if tile.mine or tile.flag:
            return
        tile.covered = not tile.covered
        tile.updateGUI()
        return

    def show(self):
        root.mainloop()
        return

    def initSaveWindow(self):
        """
        Creates buttons to save and load
        """
        self.saveWindow = ttk.Frame(self.window, padding = 10)

        self.saveButton = Button(self.saveWindow, text = "Save", command = self.save)
        self.saveButton.grid(row = 0)

        self.loadButton = Button(self.saveWindow, text = "Load", command = self.load)
        self.loadButton.grid(row = 0, column = 1)

        return

    def save(self):
        # first half of the problem-- write to string.
        saveString = ""
        saveString += "Size: ({}, {})\n".format(self.rows, self.cols)

        mineString = "Mines: "
        flagString = "Flags: "
        uncoveredString = "Uncovered: "

        for i in range(self.rows):
            for j in range(self.cols):
                if self.tiles[i][j].mine:
                    mineString += "({}, {})".format(i, j)
                if self.tiles[i][j].flag:
                    flagString += "({}, {})".format(i, j)
                if not self.tiles[i][j].covered:
                    uncoveredString += "({}, {})".format(i, j)

        saveString += mineString + '\n'
        saveString += flagString + '\n'
        saveString += uncoveredString + '\n'

        try:
            with filedialog.asksaveasfile(mode='w',initialdir = "./tests") as f:
                f.write(saveString)
        except AttributeError: # user closed window
            return
        return

    def load(self, filename = None):

        # allow a filename to be passed just to save time with testing.
        if filename is None:
            try:
                with filedialog.askopenfile(mode = 'r', initialdir = "./tests") as f:
                    lines = f.readlines()
            except AttributeError: # user exited the window.
                # messagebox.showerror(message = "Failed to Load")
                # honestly just fail silently
                return
            except FileNotFoundError as e:
                # Error name is self-explanatory, although I feel like you'd
                # have to be trying to generate it.
                messagebox.showerror(title = e)
                return

        else:
            with open(filename) as f:
                lines = f.readlines()

        for line in lines:
            if re.match("Size", line):
                sizeString = line
            elif re.match("Mines", line):
                mineString = line
            elif re.match("Flags", line):
                flagString = line
            elif re.match("Uncovered", line):
                uncoveredString = line
        # make sure that we read that successfully
        try:
            assert(sizeString and mineString and flagString and uncoveredString)
        except NameError: # name 'mineString' is not defined
            messagebox.showerror(title = "Could not read info from file")
            return
        except AssertionError:
            messagebox.showerror(title = "String was empty")

        size = toTiles(sizeString)
        assert(len(size) == 1) # should be a list with one tuple.

        self.rows, self.cols = size[0]

        self.tileWindow.destroy()
        self.initTileGrid()
        self.tileWindow.grid(row = 1)

        mines = toTiles(mineString)
        uncovereds = toTiles(uncoveredString)
        for uncovered in uncovereds:
            self.toggleCovered(*uncovered)

        flags = toTiles(flagString)
        for flag in flags:
            self.toggleFlag(*flag)

        for mine in mines:
            self.toggleMine(*mine)

        return

def toTiles(string):
    """
    Helper function to convert a string in the format
    "(1, 2), (3, 5)" to a tuple
    """
    tupleString = r"\((?P<row>\d+),\s(?P<col>\d+)\)"
    tiles = []
    matches = re.finditer(tupleString, string)
    # will simply iterate over an empty list (that is, pass) if no matches.
    for match in matches:
        tiles.append((int(match['row']), int(match['col'])))

    return tiles

def add_debug(window, name = 'main'):
    activate = lambda event: print("Entering the window: {}".format(name))
    deactivate = lambda event: print("Leaving the window: {}".format(name))
    destroy = lambda event: print("Destroying the window: {}".format(name))
    window.bind(sequence = "<FocusIn>", func = activate)
    window.bind(sequence = "<FocusOut>", func = deactivate)
    window.bind(sequence = "<Destroy>", func = destroy)

    return

def test():
    # load a file.
    t = testCreator()
    t.load("./tests/test.txt")

def main():
    # t = testCreator()
    # t.show()
    t = tester(solver.BasicSolver)

if __name__ == "__main__":
    main()
