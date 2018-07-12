#!/usr/bin/env python3

from requests import get, post
from math import *
from random import choice, random

from user import USER

def toNode(r, c, gridH, gridW):
    return r * gridW + c

def toCoord(node, gridH, gridW):
    return ((node - node % gridW) // gridW, node % gridW)

def endpoint(name):
    return "https://gps.hackmirror.icu/api/{}?user={}".format(name, USER)

def reset():
    post(endpoint("reset"))

def getPosition():
    ret = get(endpoint("position")).json()
    ret.update(get(endpoint("time")).json())
    return ret

def getMap():
    return get(endpoint("map")).json()["graph"]

def getProbability():
    return get(endpoint("probability")).json()["probability"]

def unpackPositionLike(position, gridH, gridW):
    if "message" in position:
        print(position["message"])
    return position["time"], toNode(position["row"], position["col"], gridH, gridW)


def move(fromNode, toNode, gridH, gridW):
    y1, x1 = toCoord(fromNode, gridH, gridW)
    y2, x2 = toCoord(toNode, gridH, gridW)

    if x1 == x2:
        if y1 + 1 == y2:
            direction = "down"
        elif y1 - 1 == y2:
            direction = "up"
        else:
            raise Exception
    elif y1 == y2:
        if x1 + 1 == x2:
            direction = "right"
        elif x1 - 1 == x2:
            direction = "left"
        else:
            raise Exception
    else:
        raise Exception

    return post(endpoint("move") + "&move=" + direction).json()

class Node(object):
    pass

def dijkstras(graph, goal):
    for node in graph:
        node.cost = inf
    graph[goal].cost = 0

    changed = True

    while changed:
        changed = False
        for node in graph:
            for outNode in node.out:
                candidateCost = graph[outNode].cost + graph[outNode].penalty + 1
                if candidateCost < node.cost:
                    changed = True
                    node.next = outNode
                    node.cost = candidateCost

def simulate(graph, p, time, start, goal, iterations):
    success = outatime = stuck = 0
    for i in range(iterations):
        current = start
        timeLeft = time
        while True:
            if current == goal:
                success += 1
                break
            if graph[current].next == -1:
                stuck += 1
                break
            if timeLeft == 0:
                outatime += 1
                break
            if random() < p:
                current = choice(graph[current].out)
            else:
                current = graph[current].next
            timeLeft -= 1
    return success / iterations, outatime / iterations, stuck / iterations

def main():
    reset()
    adjacency = getMap()
    graph = []
    for i in adjacency:
        obj = Node()
        obj.out = i
        obj.penalty = 0
        obj.next = -1
        graph.append(obj)
    
    p = getProbability()

    gridH = gridW = int(sqrt(len(adjacency)))

    time, current = unpackPositionLike(getPosition(), gridH, gridW)

    goal = len(adjacency) - 1

    print("Nodes: {} Probability: {} Start: {} Goal: {} Time: {}".format(len(adjacency), p, current, goal, time))

    dijkstras(graph, goal)
    print(graph[current].cost)
    print("Before optimization: Success: {:.2%} Outatime: {:.2%} Stuck: {:.2%}".format(*simulate(graph, p, time, current, goal, 10000)))

    for node in graph:
        if node.cost == inf:
            node.penalty_ = [500]
        else:
            node.penalty_ = [0]
    
    for i in range(20):
        for node in graph:
            penalty = 0
            for outNode in node.out:
                penalty += graph[outNode].penalty_[i] * p / len(node.out)
            node.penalty_.append(penalty)

    for node in graph:
        node.penalty = sum(node.penalty_)

    dijkstras(graph, goal)

    #print([node.penalty for node in graph])

    print(graph[current].cost)
    print("After optimization: Success: {:.2%} Outatime: {:.2%} Stuck: {:.2%}".format(*simulate(graph, p, time, current, goal, 10000)))

    while current != goal:
        if time <= 0:
            print("Outatime")
            exit()
        if graph[current].next == -1:
            print("Stuck")
            exit()
        # print("{} -> {} ({}, {} -> {}, {})".format(current, graph[current].next, *(toCoord(current, gridH, gridW) + toCoord(graph[current].next, gridH, gridW))))
        time, current = unpackPositionLike(move(current, graph[current].next, gridH, gridW), gridH, gridW)

if __name__ == "__main__":
    main()
