#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from requests import post
import json
from itertools import *
from math import *
from random import Random

ENDPOINT = "https://gerry.hackmirror.icu/u/dratini0_cfb7da/"
FILE = "voters.json"

data = json.load(open(FILE, "r"))
data = (data["voters_by_block"]["party_A"], data["voters_by_block"]["party_B"])
population = sum(data[0]) + sum(data[1])
n = 10
D = 20
SVP = .6 # straightVoteProbability
goalMetrics = (0, 10.0, 1.68e12, -0.074 * population)
weights = (1, 1, 1, 1)

SEED = "VPIPwCFEBpwxrLW9TZ4dDXTFVF1VN6U+JOS+3xjN"
ITERS = int(1e7)

#avgDsize = n * n // D
#solution = (tuple(frozenset(range(i, i+avgDsize)) for i in range(0, n * n, avgDsize)), tuple(d // avgDsize for d in range(n * n)))
state = [0,] * (n * n)

def change(state, cell, newDistrict):
    ret = state.copy()
    ret[cell] = newDistrict
    return ret

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
    firstEmpty = next(iter(set(range(D)).difference(set(state))), None)
    for i in range(n * n):
        candidates = set()
        ownDistrict = state[i]
        for neighbour in adjacent(i):
            candidates.add(state[neighbour])
        candidates.discard(ownDistrict)
        if firstEmpty is not None:
            candidates.add(firstEmpty)
        for candidate in candidates:
            yield change(state, i, candidate)

def evaluate(state):
    pops = [[0, 0] for i in range(D)]
    for district, aPop, bPop in zip(state, *data):
        pops[district][0] += aPop
        pops[district][1] += bPop

    hasEmpty = 0
    aDistricts = 0.
    DPI = 0.
    EEG = 0.

    for aVoters, bVoters in pops:
        if aVoters == 0 and bVoters == 0:
            hasEmpty += 1
            continue

        # aVotes = aVoters_A + bVoters_A = Bin(aVoters, SVP) + Bin(bVoters, 1 - SVP) ~=
        # ~= N(aVoters * SVP, aVoters * SVP * (1 - SVP)) + N(bVoters * (1 - SVP), bVoters * SVP * (1 - SVP)) =
        # = N(aVoters * SVP + bVoters * (1 - SVP), (aVoters + bVoters) * SVP * (1 - SVP))
        # pWin = P(aVotes > (aVoters + bVoters) / 2) = 1 - F_aVoters((aVoters + bVoters) / 2) =
        # = 1 - 1 / 2 * (1 + erf(((aVoters + bVoters) / 2 - aVoters * SVP - bVoters * (1 - SVP)) / sqrt(2 * (aVoters + bVoters) * SVP * (1 - SVP)))) =
        # = 1 / 2 * (1 + erf((aVoters * SVP + bVoters * (1 - SVP) - (aVoters + bVoters) / 2) / sqrt(2 * (aVoters + bVoters) * SVP * (1 - SVP)))))
        pWin = (1 + erf((aVoters * SVP + bVoters * (1 - SVP) - (aVoters + bVoters) / 2) / sqrt(2 * (aVoters + bVoters) * SVP * (1 - SVP)))) / 2
        aDistricts += pWin

        DPI += (aPop + bPop - population/D) * (aPop + bPop - population/D)

        # EEG = pWin (E[aVotes | Win] - pop/2 - E[bVotes | Win]) + (1 - pWin) (E[aVotes | ~Win] - E[bVotes | ~Win] + pop/2) =
        # = E[aVotes] - E[bVotes] - pWin * pop/2 + (1 - pWin) * pop/2 =
        # = 2 E[aVotes] - pop - pWin * pop/2 + pop/2 - pWin * pop/2 =
        # = 2 E[aVotes] - pop/2 - pWin * pop = 2 E[aVoters] - pop * (pWin + 0.5)
        EEG += 2 * (aVoters * SVP + bVoters * (1 - SVP)) - (aVoters + bVoters) * (pWin + 0.5)

    return hasEmpty, aDistricts, DPI, EEG

startMetrics = evaluate(state)

def energy(s):
    metrics = evaluate(s)
    return sum(max(0, (current - goal) / (start - goal)) * weight for current, start, goal, weight in zip(metrics, startMetrics, goalMetrics, weights))

def temperature(proportion):
    return 1 - proportion

def P(oldEnergy, newEnergy, temp):
    if newEnergy < oldEnergy: return 1
    else: return exp((oldEnergy - newEnergy) / temp)

rng = Random()
rng.seed(SEED)
print(seed)
currentEnergy = energy(state)
for i in range(ITERS):
    if i % 1000 == 0:
        print(i, currentEnergy)
    if currentEnergy <= 0:
        break
    temp = temperature(i/ITERS)
    nextState = rng.choice(list(neighbours(state)))
    nextStateEnergy = energy(nextState)
    if rng.random() < P(currentEnergy, nextStateEnergy, temp):
        state = nextState
        currentEnergy = nextStateEnergy

solution = [[] for i in range(D)]
for block, district in enumerate(state):
    solution[district].append(block)
print(json.dumps(solution))
print(post(ENDPOINT, data={"json": json.dumps(solution)}).text)
