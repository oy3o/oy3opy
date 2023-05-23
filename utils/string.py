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

def random_num(length: int = 5):
    return ''.join(random.choice(digits) for _ in range(length))

def random_hex(length: int = 32):
    return ''.join(random.choice('0123456789abcdef') for _ in range(length))

def random_word(length: int = 6):
    return ''.join(random.choice(digits + ascii_letters) for _ in range(length))

def string_width(text):
    return wcwidth.wcswidth(text) 

def maxwidth(text, width):
    if len(text) > width:
        return text[:width-3]+ '...'
    return text
def uni_snippets(s,w):
    list = []
    chunk = ''
    count = 0
    for c in s:
        cw = wcwidth.wcwidth(c)
        if count + cw > w:
            list.append((chunk, random_word()))
            chunk = c
            count = cw
        else:
            chunk += c
            count += cw
    if chunk:
        list.append((chunk, random_word()))
    if not list or count == w:
        list.append(('', random_word()))
    return list

def snippet_index(s,ss):
    for i, x in enumerate(s):
        if x[1] == ss[1]:
            return i

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
