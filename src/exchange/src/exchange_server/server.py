import asyncio
import logging
import os
import pickle

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
logger = logging.getLogger(__name__)


async def client_connected(_, writer: asyncio.StreamWriter):  # noqa: ANN001
    if QUEUE.empty():
        writer.close()
        await writer.wait_closed()
        print("NO MORE DATA TO SERVE")  # noqa: T201
        return

    r = await QUEUE.get()
    print(f"SERVING {r}")  # noqa: T201
    pickled = pickle.dumps(r, pickle.HIGHEST_PROTOCOL)
    writer.write(pickled)
    await writer.drain()
    writer.close()
    await writer.wait_closed()


async def serve(results: list):
    for r in results:
        await QUEUE.put(r)

    port = os.getenv("LANDSCAPE_LOCUST_EXCHANGE_SERVER_PORT", "9999")
    server = await asyncio.start_server(client_connected, "0.0.0.0", port)

    logger.info("Listening on port %s with %d computers queued", port, QUEUE.qsize())

    async with server:
        await server.serve_forever()


def main():
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s"
    )

    host = os.getenv("LANDSCAPE_LOCUST_EXCHANGE_SERVER_DB_HOST", "localhost")
    db_name = os.getenv(
        "LANDSCAPE_LOCUST_EXCHANGE_SERVER_DB_NAME", "landscape-test-main"
    )
    user = os.getenv("LANDSCAPE_LOCUST_EXCHANGE_SERVER_DB_USER", "landscape")
    password = os.getenv("LANDSCAPE_LOCUST_EXCHANGE_SERVER_DB_PASSWORD", "landscape")
    port = os.getenv("LANDSCAPE_LOCUST_EXCHANGE_SERVER_DB_PORT", "5432")

    conn = psycopg2.connect(
        database=db_name, user=user, password=password, port=port, host=host
    )
    cur = conn.cursor()
    cur.execute(COMPUTER_QUERY)

    results = []
    for x in cur.fetchall():
        secure_id = x[0].tobytes()
        next_exchange_token = x[1].tobytes() if x[1] else None
        next_expected_sequence = x[2]
        insecure_id = x[3]

        results.append(
            (
                secure_id,
                next_exchange_token,
                next_expected_sequence,
                insecure_id,
            )
        )

    conn.close()
    asyncio.run(serve(results))


if __name__ == "__main__":
    main()
