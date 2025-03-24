import pickle

from landscape import CLIENT_API
from landscape.client.diff import diff
from landscape.client.exchange import exchange_messages
from landscape.lib.process import ProcessInformation

PROCESS_INFO = ProcessInformation()
MAX_MESSAGE_COUNT = 1


def get_processes():
    ps = {}
    pis = (p for p in PROCESS_INFO.get_all_process_info() if p['state'] != b'X')

    for pi in pis:
        ps[pi['pid']] = pi

    return ps


def get_changes(pdiff):
    creates, updates, deletes = pdiff
    changes = {
        k + '-processes': list(v.values()) for k, v in
        (('add', creates), ('update', updates), ('kill', deletes))
        if v
    }
    return changes


def send_messages(messages, sequence, exchange_token, computer_id, host):
    payload = {
        'client-api': CLIENT_API,
        'sequence': sequence,
        'next-expected-sequence': 1,
        'messages': messages,
    }

    response = exchange_messages(
        payload,
        host + '/message-system',
        computer_id=computer_id,
        exchange_token=exchange_token,
    )

    return response.next_exchange_token, response.next_expected_sequence


def generate_message(prev_processes):
    message: dict[str, str | list] = {'type': 'active-process-info'}
    processes = get_processes()
    process_diff = diff(prev_processes, processes)
    changes = get_changes(process_diff)

    if changes:
        message.update(changes)
        return message, prev_processes

    return None, prev_processes


def main():
    with open('data.pickle', 'rb') as f:
        next_exchange_token, sequence = pickle.load(f)

    prev_processes = {}

    try:
        while True:
            messages = []
            for _ in range(MAX_MESSAGE_COUNT):
                message, prev_processes = generate_message(prev_processes)
                if message:
                    messages.append(message)

            next_exchange_token, sequence = send_messages(messages, sequence, next_exchange_token)
            # print((next_exchange_token, sequence))
    except Exception:
        with open('data.pickle', 'wb') as f:
            pickle.dump((next_exchange_token, sequence), f, pickle.HIGHEST_PROTOCOL)

if __name__ == '__main__':
    main()
