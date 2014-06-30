#!/usr/bin/env python
from bitcoinrpc.authproxy import AuthServiceProxy
import curses, time, Queue 

def init(config):
    rpcuser = config.get('rpc', 'rpcuser')
    rpcpassword = config.get('rpc', 'rpcpassword')
    rpcip = config.get('rpc', 'rpcip')
    rpcport = config.get('rpc', 'rpcport')

    rpcurl = "http://" + rpcuser + ":" + rpcpassword + "@" + rpcip + ":" + rpcport
    rpchandle = AuthServiceProxy(rpcurl, None, 500)

    return rpchandle

def stop(interface_queue):
    interface_queue.put({'stop': 1})

def loop(interface_queue, rpc_queue, config):
    # TODO: add some error checking for failed connection, json error, broken config
    rpchandle = init(config)

    last_update = time.time() - 2
    
    try:
        info = rpchandle.getinfo()
        interface_queue.put({'getinfo': info})
    except:
        stop(interface_queue)
        return 1

    prev_blockcount = 0
    while 1:
        try:
            s = rpc_queue.get(False)
        except Queue.Empty:
            s = {}

        if 'stop' in s:
            break

        elif 'getblockhash' in s:
            try:
                blockhash = rpchandle.getblockhash(s['getblockhash'])
                block = rpchandle.getblock(blockhash)
                interface_queue.put({'getblock': block})
            except: pass

        elif 'getblock' in s:
            try:
                block = rpchandle.getblock(s['getblock'])
                interface_queue.put({'getblock': block})
            except: pass

        elif 'txid' in s:
            try:
                raw_tx = rpchandle.getrawtransaction(s['txid'])
                decoded_tx = rpchandle.decoderawtransaction(raw_tx)
                interface_queue.put(decoded_tx)
            except: pass

        if (time.time() - last_update) > 2:
            try:
                nettotals = rpchandle.getnettotals()
                connectioncount = rpchandle.getconnectioncount()
                blockcount = rpchandle.getblockcount()

                interface_queue.put({'getnettotals' : nettotals})
                interface_queue.put({'getconnectioncount' : connectioncount})
                interface_queue.put({'getblockcount' : blockcount})
            except: pass

            try:
                balance = rpchandle.getbalance()
                interface_queue.put({'getbalance' : balance})
            except: pass

            if (prev_blockcount != blockcount): # minimise RPC calls
                if prev_blockcount == 0:
                    lastblocktime = {'lastblocktime': 0}
                else:
                    lastblocktime = {'lastblocktime': time.time()}
                interface_queue.put(lastblocktime)

                try:
                    blockhash = rpchandle.getblockhash(blockcount)
                    block = rpchandle.getblock(blockhash)
                    interface_queue.put({'getblock': block})

                    prev_blockcount = blockcount
                except: pass

                try:
                    difficulty = rpchandle.getdifficulty()
                    interface_queue.put({'getdifficulty': difficulty})
                except: pass

                try:
                    nethash144 = rpchandle.getnetworkhashps(144)
                    nethash2016 = rpchandle.getnetworkhashps(2016)
                    interface_queue.put({'getnetworkhashps': {'blocks': 144, 'value': nethash144}})
                    interface_queue.put({'getnetworkhashps': {'blocks': 2016, 'value': nethash2016}})
                except: pass


            last_update = time.time()

        time.sleep(0.05) # TODO: investigate a better way to idle CPU
