#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from requests import post
import json
from itertools import *

ENDPOINT = "https://gerry.hackmirror.icu/u/dratini0_cfb7da/"
FILE = "voters.json"

data = json.load(open(FILE, "r"))
n = 10
D = 20
avgDsize = n * n // D

#solution = (tuple(frozenset(range(i, i+avgDsize)) for i in range(0, n * n, avgDsize)), tuple(d // avgDsize for d in range(n * n)))
state = ((frozenset(range(n*n)),) + tuple(frozenset() for i in range(D - 1)), (0,) * (n * n))

def change(state, cell, newDistrict):
    return (tuple(district.union({cell}) if i == newDistrict else district.difference({cell}) for i, district in enumerate(state[0])),
            tuple(currentDistrict if i != cell else newDistrict for i, currentDistrict in enumerate(state[1])))

def adjacent(cell):
    if cell % n > 0:
        yield cell - 1
    if cell % n < n - 1:
        yield cell + 1
    if cell // n > 0:
        yield cell - n
    if cell // n < n - 1:
        yield cell + n

def neighbours(state):
    yield state #?
    firstEmpty = next((i for i, district in enumerate(state[0]) if len(district) == 0), None)
    for i in range(n * n):
        candidates = set()
        ownDistrict = state[1][i]
        for neighbour in adjacent(i):
            candidates.add(state[1][neighbour])
        candidates.discard(ownDistrict)
        if firstEmpty is not None:
            candidates.add(firstEmpty)
        for candidate in candidates:
            yield change(state, i, candidate)

for i in neighbours(state):
    print(i)

solution = []
print(post(ENDPOINT, data={"json": json.dumps(solution)}).text)
print(json.dumps(solution))
