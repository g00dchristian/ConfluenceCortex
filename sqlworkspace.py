import sqlite3
import asyncio
import websockets

#conn = sqlite3.connect(':memory') - RAM memory

# conn = sqlite3.connect('tradelog.db')
# c = conn.cursor()
# SQL='''SELECT UUID, SYMBOL, STRATEGY, Trade_List.Clip_Size FROM Trade_List
# 	WHERE Trade_List.Status = "Open"'''

# c.execute(SQL)
# for entry in c.fetchall():
# 	print(entry)

# conn.commit()
# conn.close()


async def hello():
    async with websockets.connect(
            'ws://localhost:8765') as websocket:
        name = input("What's your name? ")

        await websocket.send(name)
        print(f"> {name}")

        greeting = await websocket.recv()
        print(f"< {greeting}")

asyncio.get_event_loop().run_until_complete(hello())