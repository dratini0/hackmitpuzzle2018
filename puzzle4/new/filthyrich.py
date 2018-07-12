#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-

import wallet
import miner
from crypto import generate_keys, sign
from constants import REWARD
from blockchain import Transaction, Block, get_genisis
from utils import gen_uuid, get_route
import datetime
from random import randint
import json

STORE = "cf5b92b688f85838bb6b31cc14ed26a69850af2ac0263e8b0294548e9a3de48a"
ITERS = 1000

def mine_till_submit(txns):
    while True:
        chain = miner.load_blockchain()
        b = Block(
            timestamp = datetime.datetime.now(),
            transactions = txns,
            previous_hash = chain.head.hash_block()
        )
        miner.mine_till_found(b)
        try:
            resp = get_route('add', data=str(b))
            if resp['success']:
                print("Block added!")
                if miner.load_blockchain().head.hash_block() == b.hash_block():
                    print("Success!")
                    return
                else:
                    print("Got beaten")
            else:
                print "Couldn't add block:", resp['message']
        except Exception as e:
            print(e)

def construct_and_mine(txns, previous):
    b = Block(
        timestamp = datetime.datetime.now(),
        transactions = txns,
        previous_hash = previous.hash_block()
    )
    miner.mine_till_found(b)
    return b

def paySomeone(public, private, target, amount):
    txn = Transaction(
        id = gen_uuid(),
        owner = public,
        receiver = target,
        coins = amount,
        signature = None
    )
    txn.signature = sign(txn.comp(), private)
    return txn

wallets = (generate_keys(), generate_keys())
json.dump({"public": wallets[0][1], "private": wallets[0][0]}, open("walletA.json", "w"))
json.dump({"public": wallets[1][1], "private": wallets[1][0]}, open("walletB.json", "w"))
print(repr(wallets))

blocksToSubmit = []

#mine initial block
reward = Transaction(
    id = gen_uuid(),
    owner = "mined",
    receiver = wallets[0][1],
    coins = REWARD,
    signature = ""
)
lastBlock = construct_and_mine([reward], get_genisis())
blocksToSubmit.append(lastBlock)

balances = (10, 0)

for i in range(ITERS):
    weight = randint(10, 20)
    txns = [paySomeone(wallets[0][1], wallets[0][0], wallets[1][1], balances[0]) for _ in range(weight)]
    lastBlock = construct_and_mine(txns, lastBlock)
    blocksToSubmit.append(lastBlock)
    wallets = (wallets[1], wallets[0])
    balances = (balances[1] + weight * balances[0], balances[0] * (1 - weight))

print(balances)
lastBlock = construct_and_mine([paySomeone(wallets[0][1], wallets[0][0], STORE, balances[0])], lastBlock)
blocksToSubmit.append(lastBlock)

open("filthyrich.jq", "w").writelines(map(str, blocksToSubmit))

exit()

for block in blocksToSubmit:
    try:
        resp = get_route('add', data=str(block))
        if resp['success']:
            print("Block added!")
        else:
            print "Couldn't add block:", resp['message']
    except Exception as e:
        print(e)
