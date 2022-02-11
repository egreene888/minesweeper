"""
I'm making a python program to play minesweeper
"""

from tkinter import *
from tkinter import ttk
from tkinter import font

import random

# import numpy as np
COVERED_TILE = 'gray25'
UNCOVERED_TILE = 'gray12'
FLAGGED_TILE = 'warning'
MINE_TILE = 'error'

GAME_MESSAGE = "Clear all the mines"
LOSE_MESSAGE = "Game Over"
WIN_MESSAGE = "VICTORY!"
RESTART_MESSAGE = "New Game"

BEGINNER = (9, 9, 10)
INTERMEDIATE = (16, 16, 40)
EXPERT = (16, 40, 99)

class board(object):
    """
    The board of a minesweeper game.
    Consists of a rows and columns of tiles (tkinter buttons)
    Plus an info box and a restart button
    """
    def __init__(self, rows, cols, mines):
        """
        Takes either a 'level' 'beginner', 'intermediate', 'expert'
        or a custom three arguments rows, columns, mines
        If both are passed, custom arguments will take precedence.
        """
        self.rows = rows
        self.cols = cols
        self.mines = mines

        self.tileCount = self.rows * self.cols
        self.tiles = None # will be initialized in self.initGUI()
        # some implementations of minesweeper decide the mine positions
        # when the board is first generated. But the original Microsoft
        # implementation has it so that the first tile will always have no
        # mines in neighboring tiles. So a flag for the first tile to click.
        self.firstClick = True

        # separate the initialization of the tiles for GUI features and
        # underlying data features
        self.initGUI()
        self.initData()
        # actually show the window
        # self.show()

    def __getitem__(self, i, j):
        """
        Makes it much easier to deal with lists of (i, j) tuples
        """
        return self.tiles[i][j]

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
        elif self.tiles[i][j].flag or self.tiles[i][j].covered is False:
            return
        # if the tile is unflagged and has a mine, then you lose.
        # Call the game over function.
        elif self.tiles[i][j].mine:
            self.gameOver()
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
                    if self.__getitem__(*n).covered is True:
                        self.__getitem__(*n).covered = False
                        self.__getitem__(*n).updateGUI()
                        # if the number is zero, add it to the queue so we can
                        # uncover all of its neighbors later.
                        if self.__getitem__(*n).number == 0:
                            zeroNeighbors.append(n)


        # check for victory
        self.checkVictory()
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
            # remove all the flagged tiles from this list, and count them in
            # the process.
            flags = 0
            loopIndex = 0
            while loopIndex < len(neighbors):
                n = neighbors[loopIndex]
                if self.__getitem__(*n).flag is True:
                    flags += 1
                    neighbors.pop(loopIndex)
                else:
                    loopIndex += 1
            # check if the number of flags is equal to the number of mines
            if flags == self.tiles[i][j].number:
                # if it is, then primary click on every unflagged neighbor.
                for n in neighbors:
                    self.primaryClick(*n)

            # be sure to update the GUI
        self.updateGUI()
        return

    def initData(self):
        """
        Once GUI setup is done, initialize the data fields for every tile and
        bind the functions of the old tile to the new tile.
        """
        for i in range(self.rows):
            for j in range(self.cols):
                # perform all of the new tile setup
                self.tiles[i][j].DataSetup()
                # bind the commands to the tile
                leftClick = lambda ii=i, jj=j: self.primaryClick(ii, jj)
                rightClick = lambda event, ii = i, jj = j: self.secondaryClick(ii, jj)
                doubleClick = lambda event, ii= i, jj = j: self.doubleClick(ii, jj)
                self.tiles[i][j].configure(command = leftClick)
                self.tiles[i][j].bind(sequence = "<Button-2>", func = rightClick)
                self.tiles[i][j].bind(sequence = "<Button-3>", func = rightClick)
                self.tiles[i][j].bind(sequence = "<Double-Button-1>", func = doubleClick)
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
            minePos = random.randint(0, self.tileCount - 1)
            # print(minePos)
            mineRow = minePos // self.cols
            mineCol = minePos % self.cols
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
                # print(mineCount)
        # now compute the number that goes on each tile.
        # this is easier than doing it on the fly with every click.
        for i in range(self.rows):
            for j in range(self.cols):
                # compute the numbers for each tile
                self.tiles[i][j].number = 0
                for neighbor in self.getNeighbors(i, j):
                    if self.tiles[neighbor[0]][neighbor[1]].mine == True:
                        self.tiles[i][j].number += 1
        return

    def gameOver(self):
        """
        When we trip a mine, the game is over. Put all the logic that happens
        here.
        """
        # put a game over message in the infoBox
        self.infoBox.configure(text = LOSE_MESSAGE)

        # disable all the tiles
        # show the mines
        for i in range(self.rows):
            for j in range(self.cols):
                # disable all the tiles on the board
                self.tiles[i][j].configure(state = 'disabled')
                # uncover the mines
                if self.tiles[i][j].mine:
                    self.tiles[i][j].covered = False

    def checkVictory(self):
        # if there is any tile on the board that is covered and has a mine,
        # there's no victory yet.
        for row in self.tiles:
            for tile in row:
                if tile.mine is False and tile.covered is True:
                    return False
        # Put a Victory message in the info box
        self.infoBox.configure(text = WIN_MESSAGE)
        # flag all the mines
        for row in self.tiles:
            for tile in row:
                if tile.mine is True:
                    tile.flag = True

        return True

    def restart(self):
        """
        if the restart button is pressed, then, well, restart.
        calls both GUI functions and data functions.
        """
        for i in range(self.rows):
            for j in range(self.cols):
                self.tiles[i][j].GUISetup(i, j)
                self.tiles[i][j].DataSetup()

        self.infoBox.configure(text = GAME_MESSAGE)
        self.firstClick = True
        self.updateGUI()
        return

    def initGUI(self):
        """
        This function initializes all the GUI features for the whole board
        Note that data initilization is done in initData()
        """
        # set up a Tk root, window
        self.tk = Tk()
        self.window = ttk.Frame(self.tk, padding=10)
        self.window.grid()

        # bind the window to a method that will kill the whole program
        # when it closes.
        self.tk.bind(sequence = "<Destroy>", func = self.kill)

        # create a nested list for the tile data structure.
        # call the setup function on each tile.
        self.tiles = []
        for i in range(self.rows):
            row = []
            for j in range(self.cols):
                tile = Tile(self.window)
                tile.GUISetup(i, j)
                row.append(tile)
            self.tiles.append(row)

        # create and set up an info box
        self.infoBox = Label(self.window)
        self.infoBox.grid(row = self.rows, columnspan = self.cols)
        self.infoBox.configure(text = GAME_MESSAGE)

        # create and set up a "New Game" button
        restartButton = Button(self.window)
        restartButton.configure(text = RESTART_MESSAGE)
        restartButton.configure(command = self.restart)
        restartButton.grid(row = self.rows + 1, columnspan = self.cols)
        return

    def updateGUI(self):
        for i in range(self.rows):
            for j in range(self.cols):
                self.tiles[i][j].updateGUI()

    def getNeighbors(self, i, j):
        """
        returns all the tiles adjacent to tiles[i, j]
        """
        neighbors = []
        for row in range(i-1, i+2):
            if row < 0 or row >= self.rows:
                continue
            for col in range(j-1, j+2):
                if row == i and col == j:
                    continue
                elif col < 0 or col >= self.cols:
                    continue
                else:
                    neighbors.append((row, col))
        return neighbors

    def show(self):
        self.tk.mainloop()
    def kill(self, event):
        # self.tk.destroy()
        # raise RuntimeError("User closed the window")

        return

class Tile(Button):
    """
    An extension of the Tkinter Button class that suits our purposes
    """
    def DataSetup(self):
        self.covered = True     # tile is covered or uncovered
        self.mine = False       # tile has a mine
        self.flag = False       # user places flag to indicate a mine
        self.number = None      # number of mines in adjacent tiles

        self.configure(state = 'normal')
        # self.GUISetup()

        return

    def GUISetup(self, row, col):
        """
        Move all the setup for the GUI properties to this function
        """
        # set the GUI to reflect all tiles are covered at startup
        self.configure(bitmap  = COVERED_TILE)
        self.configure(height = 12, width = 12)
        self.configure(text = " ", compound = CENTER)
        tileFont = font.Font(family = 'terminal', size = 10)
        self.configure(font = tileFont)
        self.grid(row = row, column = col)

        return

    def updateGUI(self):
        """
        Update the GUI after every action
        """
        # if the tile is flagged it looks like a covered tile with a flag
        if self.flag:
            self.configure(bitmap = FLAGGED_TILE)
        else:
            if self.covered:
                self.configure(bitmap = COVERED_TILE)
                self.configure(text = " ")
            else:
                if self.mine:
                    self.configure(bitmap = MINE_TILE)
                else:
                    self.configure(state = 'disabled')
                    if self.number == 0:
                        self.configure(bitmap = UNCOVERED_TILE)
                    else:
                        self.configure(bitmap = UNCOVERED_TILE,
                            text = str(self.number),
                            compound = CENTER)
def main():
    b = board(*EXPERT)

if __name__ == "__main__":
    main()
