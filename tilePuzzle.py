"""
While I was making a Python program to play minesweeper, I got an idea for a
side quest of sorts. Start with a random assortment of black and white tiles,
and then click on them until they're all black.
"""

from tkinter import *
from tkinter import ttk
import random

# import numpy as np
COVERED_TILE = 'gray12'
FLAGGED_TILE = 'gray75'

class board(object):
    """
    The board of a minesweeper game
    """
    def __init__(self, rows, cols, mines):
        self.rows = rows
        self.cols = cols
        self.tileCount = rows * cols
        self.mines = mines
        self.firstClick = True

        self.initGUI()
        self.layMines()

        self.show()

    def restart(self):
        self.restartGUI()
        self.layMines()

        return
    def layMines(self):
        """
        Decides which tiles should be mines and lays them there.
        """
        # set up randomness
        random.seed()
        minePos = random.choices(range(self.rows * self.cols), k=self.mines)
        for mine in minePos:
            minei = mine // self.cols
            minej = mine % self.cols
            self.tiles[minei][minej].flag = True

        self.updateGUI()
        return
    def checkVictory(self):
        for row in self.tiles:
            for tile in row:
                if tile.flag is True:
                    return False
        # write a victory messag ein the info box
        self.infoBox.configure(text = "VICTORY!")
        # disable all the tiles
        for row in self.tiles:
            for tile in row:
                tile.configure(state = "disabled")
        return  True

    def primaryClick(self, i, j):
        """
        The actions you take when a tile has a left-click.
        """
        self.tiles[i][j].flag = not self.tiles[i][j].flag
        for loc in self._getNeighbors(i, j):
            self.tiles[loc[0]][loc[1]].flag = not self.tiles[loc[0]][loc[1]].flag
        self.updateGUI()
        self.checkVictory()

    def initGUI(self):
        self.tk = Tk()
        self.window = ttk.Frame(self.tk, padding=10)
        self.window.grid()

        self.tiles = []
        for i in range(self.rows):
            row = []
            for j in range(self.cols):
                tile = Tile(self.window)
                tile.create(i, j)
                tile.configure(command = lambda ii=i,jj=j: self.primaryClick(ii, jj))
                row.append(tile)
            self.tiles.append(row)

        self.updateGUI()

        # create an info box
        self.infoBox = Label(self.window)
        self.infoBox.grid(row = self.rows, columnspan = self.cols + 1)
        # self.infoBox.configure(text = "Turn all the tiles white to win the game")
        # create a new game button.
        self.newGameBox = Button(self.window, command = self.restart)
        self.newGameBox.configure(text = "Restart")
        self.newGameBox.grid(row = self.rows + 1, columnspan = self.cols)
        return

    def updateGUI(self):
        for i in range(self.rows):
            for j in range(self.cols):
                self.tiles[i][j].updateGUI()

    def restartGUI(self):
        for i in range(self.rows):
            for j in range(self.cols):
                self.tiles[i][j].create(i, j)

    def _getNeighbors(self, i, j):
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

class Tile(Button):
    """
    An extension of the Tkinter Button class that suits our purposes
    """
    def create(self, i, j):
        self.i = i
        self.j = j

        self.revealed = False
        self.mine = False
        self.flag = False
        self.number = None

        # self.configure(command = self.click)
        self.GUISetup()

    def GUISetup(self):
        """
        Move all the setup for the GUI properties to this function
        """
        self.configure(bitmap  = COVERED_TILE)
        self.configure(height = 12, width = 12)
        self.configure(state = "normal")
        self.grid(row = self.i, column = self.j)

        return

    def updateGUI(self):
        """
        Update the GUI after every action
        """
        if self.flag == False:
            self.configure(bitmap = COVERED_TILE)
        else:
            self.configure(bitmap = FLAGGED_TILE)
def main():
    b = board(4, 4, 4)

main()
