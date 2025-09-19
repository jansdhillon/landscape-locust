import asyncio
import pickle

import psycopg2

COMPUTER_QUERY = '''SELECT
    computer.secure_id,
    computer_status.next_exchange_token,
    computer_status.next_expected_sequence,
    computer.insecure_id
FROM computer
JOIN computer_status ON computer.id = computer_status.computer_id
'''

QUEUE = asyncio.Queue()


async def client_connected(_, writer):
    if QUEUE.empty():
        writer.close()
        await writer.wait_closed()
        print("NO MORE DATA TO SERVE")
        return

    r = await QUEUE.get()
    print(f"SERVING {r}")
    pickled = pickle.dumps(r, pickle.HIGHEST_PROTOCOL)
    writer.write(pickled)
    await writer.drain()
    writer.close()
    await writer.wait_closed()


async def serve(results):
    for r in results:
        await QUEUE.put(r)

    server = await asyncio.start_server(client_connected, '0.0.0.0', 9999)

    async with server:
        await server.serve_forever()


def main():
    conn = psycopg2.connect('dbname=landscape-test-main')
    cur = conn.cursor()
    cur.execute(COMPUTER_QUERY)

    results = []
    for x in cur.fetchall():
        si = x[0].tobytes()
        net = x[1].tobytes() if x[1] else None
        ii = x[3]

        results.append((si, net, x[2], ii))

    conn.close()
    asyncio.run(serve(results))


if __name__ == '__main__':
    main()
