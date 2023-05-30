from string import *
import json
import random
import traceback
import wcwidth
import tiktoken  # modified by oy3o to support count function in rust rather than convert to python

def tojson(o):
    return json.dumps(o, ensure_ascii=False)

def errString(e: Exception):
    try:
        return '\n'.join(traceback.format_exception(etype=type(e), value=e, tb=e.__traceback__))
    except:
        return str(e)

def remainder(n:int, d:int): return 0 if n==0 else (n%d or n)

def random_num(length: int = 5):
    return ''.join(random.choice(digits) for _ in range(length))

def random_hex(length: int = 32):
    return ''.join(random.choice('0123456789abcdef') for _ in range(length))

def random_word(length: int = 6):
    return ''.join(random.choice(digits + ascii_letters) for _ in range(length))

def string_width(text):
    """
    Return the width of a string in terminal columns.
    """
    if not text: return 0
    return wcwidth.wcswidth(text) 

def maxwidth(text, width):
    """
    Return a truncated version of a string that fits in a given width.
    """
    if string_width(text) > width:
        return split_bywidth(text,width-3)[0] + '...'
    return text

def split_bywidth(str:str, width:int):
    """
    Split a string into a list of substrings that have the same or less width.
    """
    list = []
    chunk = ''
    count = 0
    for c in str:
        cw = wcwidth.wcwidth(c)
        if count + cw > width:
            list.append(chunk)
            chunk = c
            count = cw
        else:
            chunk += c
            count += cw
    if chunk:
        list.append(chunk)
    if not list or count == width:
        list.append('')
    return list

def splitstrings_bywidth(lines:list[str], width:int, a:int=None, b:int=None):
    """
    Split a list of strings into a list of tuples containing substrings, line index and fragment index.
    """
    result = []
    a = 0 if a == None else max(0, min(a, len(lines)))
    b = len(lines) if b == None else min(b, len(lines))
    for i in range(a, b):
        line = lines[i]
        fragments = split_bywidth(line, width)
        for j in range(len(fragments)):
            text = fragments[j]
            result.append((text, i, j))
    return result


def split_first(args_text, spliter, nosp = False):
    try:
        i = args_text.index(spliter)
        return (args_text[:i], args_text[(i+len(spliter)) if nosp else i:].strip())
    except:
        return (args_text, '')

class Token:
    def __init__(self):
        self.enc = tiktoken.get_encoding('cl100k_base')

    def count(self, text: str, *, allowed_special=set()) -> int:
        try:
            return self.enc._core_bpe.count(text, allowed_special)
        except:
            return len(self.encode(text))
    
    def encode(self, text: str, *, allowed_special=set()) -> list:
        return self.enc._core_bpe.encode(text, allowed_special)
