import random
import threading
import time
import itertools
from tkinter import *
from tkinter import ttk
from tkinter import font

def randomChoicesTest():
    L = [['a', 'A'], ['b', 'B'], ['c', 'C']]
    print(random.choices(L, k=2))

def listMethodTest():
    L = ['a', 'b', 'c', 'd', 'e']
    for elt in itertools.combinations(L, 0):
        print(elt)

    return

def doubleAsterisk():
    t = (1, 4)
    print(dummyFunc(*t))

def foolWithFonts():
    root = Tk()
    window = ttk.Frame(root, padding=10)
    window.grid()

    fontNameList = font.names()
    print(fontNameList)
    fontList = [font.nametofont(name) for name in fontNameList]
    labels = []
    for i in range(len(fontList)):
        l = Label(window)
        l.configure(text = fontList[i].actual()['family'])
        l.configure(font = fontNameList[i])
        l.grid(row = i, column = 0)
        labels.append(l)

    fontFamilyList = font.families()
    print(fontFamilyList)
    for i in range(len(fontFamilyList)):
        l = Label(window)
        l.configure(text = fontFamilyList[i])
        l.configure(font = font.Font(family = fontFamilyList[i], size = 12))
        l.grid(row = i % 20, column = i // 20)
        labels.append(l)

    root.mainloop()

def foolwithBitmap():
    def makedarker():
        b1.configure(bitmap = 'gray25')
        b1.configure(compound = NONE)
        return

    root = Tk()
    window = ttk.Frame(root, padding=10)
    window.grid()
    b1 = Button(window, bitmap = 'gray12')
    b1.configure(text = '3', compound = CENTER)
    b2 = Button(window, bitmap = 'gray25')
    b1.configure(command = makedarker)

    b1.grid(row = 0, column = 0)
    b2.grid(row = 0, column = 1)

def threadExperiment():
    thread1 = threading.Thread(target = threadFunction, args = (1,))
    thread2 = threading.Thread(target = threadFunction, args = (2,))

    thread1.start()
    thread2.start()

def threadFunction(i):
    print("started thread {}".format(i))
    time.sleep(2)
    print("finished thread {}".format(i))
    return

def boolCounter():
    L = [12, 13, 14, 15]
    x = sum([isEven(a) for a in L])
    print(x)

def isEven(a):
    return bool(a % 2)

def permutations():
    L = ['a', 'b', 'c']
    p = list(range(0, len(L) + 1))
    i = 1
    print(L)
    while i < len(L):
        p[i] -= 1
        if i % 2 == 1:
            j = p[i]
        else:
            j = 0
        L[i], L[j] = L[j], L[i]
        print(p, i, j)
        print(L)
        i = 1
        while p[i] == 0:
            p[i] = i
            i += 1
def nextPerm(L):
    return

class possibilityGenerator(object):
    """
    Given a list of tiles, generates all possibilities for which will be mines
    and which won't
    """
    def __init__(self, L):
        self.original = L
        self.counter = 1

    def next(self):
        mines = []
        if self.counter.bit_length() <= len(self.original):
            # mask = self.counter.to_bytes(len(self.original), byteorder = 'big')
            formatSpecifier = '0'+ str(len(self.original)) + 'b'
            mask = format(self.counter, formatSpecifier)
            # print(mask)
            for i in range(len(self.original)):
                if mask[i] == '1':
                    mines.append(self.original[i])
            self.counter += 1
        return mines

    def hacky_next(self):
        mines = []
        if self.counter <= 2**len(self.original):
            mask = self.counter
            for i in range(len(self.original)):
                # print(i)
                if mask // 2**i:
                    mines.append(self.original[i])
                    mask -= 2**i
        self.counter += 1
        return mines

def generatePossibilities():
    L = ['a', 'b', 'c']

    startTime = time.time()
    for _ in range(int(1e6)):
        p = possibilityGenerator(L)
        for __ in range(8):
            p.next()
    print("First method completed in {} s".format(startTime - time.time()))

    startTime = time.time()
    for _ in range(int(1e6)):
        p = possibilityGenerator(L)
        for __ in range(8):
            p.hacky_next()
    print("Second method completed in {} s".format(startTime - time.time()))

def stringFormat():
    print("Number: {:.2%}".format(5.0))

def ifNone():
    if None:
        print("Hello World!")

def foolWithLambdas():
    list1 = range(10)
    list2 = range(9)
    list3 = range(3)
    metaList = [list1, list2, list3]

    queryList = [21, 8, 2]
    inEvery = lambda  q: sum([q not in L for L in metaList])
    inNone = lambda q: sum([q in L for L in metaList])
    # for query in queryList:
    x = list(itertools.filterfalse(inEvery, queryList))
    print(x)
    # for q in queryList:
    #     print(inEvery(q))
    y = list(itertools.filterfalse(inNone, queryList))
    print(y)

def foolWithNests():
    curse = [((0, 3),), ((1, 3),)]
    print(len(curse))
    print(len(curse[0]))

def foolWithRange():
    L = ['a', 'b', 'c', 'd', 'e']
    for i in range(len(L) - 1, 0, -1):
        print(L[i])

def unpacking():
    print(dummyFunc(2, 5))
    print(dummyFunc(*(2, 5)))
    print(dummyFunc((2, 5)))
    print(dummyFunc(2))


def dummyFunc(*args):
    print(args)
    try:
        a , b = args
    except ValueError: # not enough values to unpack
        try:
            a, b = args[0]
        except TypeError: # cannot unpack non-iterable int object
            a = args[0]
            b = 0

    return a + b

class dummyClass(object):
    a = None

    def setThing(self):
        if self.a is None:
            self.a = {'is': 'strange'}
    def speak(self):
        print(self.a)

    def check(self):
        self.five = 5
        for (key, value) in self.__dict__.items():
            print("{} : \t {}".format(key, value))
        # for thing in globals():
        #     print(thing)

def classVarTest():
    thing1 = dummyClass()
    thing1.speak()
    thing2 = dummyClass()
    thing1.setThing()
    thing2.speak()
    thing1.speak()

def destructorTest():
    obj = dummyClass()
    obj.fourteen = 14
    obj.check()

def main():
    destructorTest()

main()
