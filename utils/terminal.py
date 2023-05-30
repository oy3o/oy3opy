from oy3opy import *
from curses import *
import curses
import re

color_code = {
    'black': 30,
    'grey': 90,
    'red': 91,
    'green': 92,
    'yellow': 93,
    'blue': 94,
    'magenta': 95,
    'cyan': 96,
    'white': 97
}

bgcolor_code = {
    'black': 40,
    'grey': 100,
    'red': 101,
    'green': 102,
    'yellow': 103,
    'blue': 104,
    'magenta': 105,
    'cyan': 106,
    'white': 107,
}

color_map = {
    30: COLOR_BLACK,
    90: COLOR_BLACK,
    91: COLOR_RED,
    92: COLOR_GREEN,
    93: COLOR_YELLOW,
    94: COLOR_BLUE,
    95: COLOR_MAGENTA,
    96: COLOR_CYAN,
    97: COLOR_WHITE,
}

bgcolor_map = {
    40: COLOR_BLACK,
    100: COLOR_BLACK,
    101: COLOR_RED,
    102: COLOR_GREEN,
    103: COLOR_YELLOW,
    104: COLOR_BLUE,
    105: COLOR_MAGENTA,
    106: COLOR_CYAN,
    107: COLOR_WHITE,
}

curses_map = {
    None: 'None',
    COLOR_BLACK: 'black',
    COLOR_RED: 'red',
    COLOR_GREEN: 'green',
    COLOR_YELLOW: 'yellow',
    COLOR_BLUE: 'blue',
    COLOR_MAGENTA: 'magenta',
    COLOR_CYAN: 'cyan',
    COLOR_WHITE: 'white',
}

COLOR_PAIRS = {
    (None,None): A_NORMAL,
}

def color(text, color, bgcolor=None):
    return f'\033[{color_code[color]}{(";" + str(bgcolor_code[bgcolor])) if bgcolor else ""}m{text}\033[0m'


def colorpair_id(color_pair):
    if color_pair not in COLOR_PAIRS:
        init_pair(100+len(COLOR_PAIRS), *color_pair)
        COLOR_PAIRS[color_pair] = 100+len(COLOR_PAIRS) 
    return COLOR_PAIRS[color_pair]

ansi = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')

def extactAnsi(ansi):
    color = COLOR_WHITE
    bgcolor = COLOR_BLACK
    numbers = re.findall('\d\d+', ansi)
    for number in numbers:
        number = int(number)
        if number in color_map:
            color = color_map[number]
        elif number in bgcolor_map:
            bgcolor = bgcolor_map[number]
    return (color, bgcolor)

def extactText(text):
    texts = ansi.split(text)
    codes = ansi.findall(text)
    fragments = [(texts[0], A_NORMAL)] if texts[0] else []
    for i in range(len(codes)):
        if texts[i+1]: fragments.append((texts[i+1], colorpair_id(extactAnsi(codes[i]))))
    return fragments


class _CursesWindow: ...

def __initscr()->_CursesWindow:
    curses.stdscr = Proxy(initscr(), WindowHandler)
    return curses.stdscr

@wraps(newwin)
def __newwin(*args,**kwds)->_CursesWindow:
    return Proxy(newwin(*args, **kwds), WindowHandler)

curses.__start_color = False
def __start_color():
    start_color()
    curses.__start_color = True

curses.initscr = __initscr
curses.newwin = __newwin
curses.start_color = __start_color

class WindowHandler:
    def getattr(self, name):
        if name == 'addstr':
            return bind(addstr, self)
        elif name == 'derwin':
            return bind(derwin, self)
        return getattr(self, name)

def addstr(self:object, y:int, x: int, str: str, attr:int=0)->_CursesWindow:...
@overload
def addstr(self:object, str: str, attr:int=0)->_CursesWindow:...
addstr = template(addstr)
@addstr.register
def _(self:object, y:int, x: int, str: str, attr:int=0):
    if curses.__start_color and has_colors() and attr>0:
        cts = iter(extactText(str))
        self.addstr(y, x, *next(cts))
        for ct in cts:
            self.addstr(*ct)
    else:
        self.addstr(y, x, ''.join(ansi.split(str)), attr)

@addstr.register
def _(self:object, str: str, attr:int=0):
    if curses.__start_color and has_colors() and attr>0:
        for ct in iter(extactText(str)): self.addstr(*ct)
    else:
        self.addstr(''.join(ansi.split(str)), attr)

@overload
def derwin(self:object, nlines: int, ncols: int, begin_y: int, begin_x: int)->_CursesWindow:...
@overload
def derwin(self:object, begin_y: int, begin_x: int)->_CursesWindow:...
derwin = template(derwin)
@derwin.register
def _(self:object, nlines: int, ncols: int, begin_y: int, begin_x: int):
    return Proxy(self.derwin(nlines, ncols, begin_y, begin_x), WindowHandler)
@derwin.register
def _(self:object, begin_y: int, begin_x: int):
    return Proxy(self.derwin(begin_y, begin_x), WindowHandler)
