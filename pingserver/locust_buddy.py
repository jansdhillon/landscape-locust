import asyncio
import os
import pickle

from constants import BUDDY_PORT
import psycopg2

COMPUTER_QUERY = """SELECT
    computer.secure_id,
    computer_status.next_exchange_token,
    computer_status.next_expected_sequence,
    computer.insecure_id
FROM computer
JOIN computer_status ON computer.id = computer_status.computer_id
"""

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

    server = await asyncio.start_server(client_connected, "0.0.0.0", BUDDY_PORT)

    async with server:
        await server.serve_forever()


def main():
    db_name = os.getenv("LANDSCAPE_LOCUST_DB_NAME") or "landscape-test-main"
    user = os.getenv("LANDSCAPE_LOCUST_DB_USER") or "landscape"
    password = os.getenv("LANDSCAPE_LOCUST_DB_PASSWORD") or "landscape"

    conn = psycopg2.connect(database=db_name, user=user, password=password)
    cur = conn.cursor()
    cur.execute(COMPUTER_QUERY)

    results = []
    for x in cur.fetchall():
        secure_id = x[0].tobytes()
        next_exchange_token = x[1].tobytes() if x[1] else None
        next_expected_sequence = x[2]
        insecure_id = x[3]

        results.append((
            secure_id,
            next_exchange_token,
            next_expected_sequence,
            insecure_id,
        ))

    conn.close()
    asyncio.run(serve(results))


if __name__ == "__main__":
    main()
