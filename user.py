import shelve
from dataclasses import dataclass
from typing import Tuple

from config import db_name
storage = shelve.open(db_name, writeback=True)


@dataclass
class User:
    number: str = ''
    mode: str = ''
    level: int = 0
    history: Tuple = ()
    next_move_man: bool = True

def get_or_create_user(id):
    return storage.get(str(id), User())

def save_user(id, user):
    storage[str(id)] = user

def del_user(id):
    if str(id) in storage:
        del storage[str(id)]
