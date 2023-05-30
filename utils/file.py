import pathlib
import json

def mktree(tree, base=''):
    for path in tree:
        if type(path) == str:
            fullpath = base + path
            if not fullpath.endswith('/'):
                fullpath += '/'
            pathlib.Path(fullpath).mkdir(exist_ok=True)
            if type(tree) == list:
                continue
            subtree = tree.get(path)
            if subtree:
                mktree(subtree, fullpath)
        else:
            mktree(path, base)

def trytouch(path, content=''):
    try:
        pathlib.Path(path).touch(exist_ok=False)
        pathlib.Path(path).write_text(content)
    except Exception as e:
        return e

def write_text(path: str, content: str):
    pathlib.Path(path).write_text(content)

def read_text(path: str):
    return pathlib.Path(path).read_text(encoding='utf-8')

def unlink(path: str):
    pathlib.Path(path).unlink()

def io(path: str):
    return open(path, encoding='utf-8')

def loads(path: str):
    with open(path, encoding='utf-8') as io:
        return json.load(io)

def dumps(o, path: str):
    with open(path, encoding='utf-8') as io:
        return json.dump(o, io,ensure_ascii=False)
