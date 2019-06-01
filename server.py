import sys
import time
import aiohttp
import asyncio
import configparser
import re
import json


IN = "input"
OUT = "output"
SERVERS = ['Goloman', 'Hands', 'Holiday', 'Welsh', 'Wilkes']
PROPAGATION_MAP = {
    'Goloman': ['Hands', 'Holiday', 'Wilkes'],
    'Hands': ['Goloman', 'Wilkes'],
    'Holiday': ['Goloman', 'Welsh', 'Wilkes'],
    'Welsh': ['Holiday'],
    'Wilkes': ['Goloman', 'Hands', 'Holiday']
}
SERVER_PORT_MAP = {
    'Goloman': 12777,
    'Hands': 12778,
    'Holiday': 12779,
    'Welsh': 12780,
    'Wilkes': 12781
}
server_name = ""
clients= {}
log = []

# Config file used for secret stuff like the API Key
config = configparser.ConfigParser()
config.read('config.ini')


def main():
    # async with aiohttp.ClientSession() as session:
    if len(sys.argv) != 2:
        print("Invalid number of arguments!")
        print_usage()
        exit(1)

    global server_name 
    server_name = sys.argv[1]
    if server_name not in SERVERS:
        print("Invalid server name provided: {}".format(server_name))
        print_usage()
        exit(1)
    
    print("\n\nStarting server: {}...\n\n".format(server_name))

    loop = asyncio.get_event_loop()
    coro = asyncio.start_server(handle_event, '127.0.0.1', SERVER_PORT_MAP[server_name], loop=loop)
    server = loop.run_until_complete(coro)

    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass
    
    server.close()
    loop.run_until_complete(server.wait_closed())
    loop.close()

    print("\n\n{} going offline\n\nDumping log...".format(server_name))
    dump_log()


async def handle_event(reader, writer):
    data = await reader.read()
    message = data.decode()
    addr = writer.get_extra_info('peername')
    print(f"Receieved {message} from {addr}")
    

# Processes a message m received presumably from an async event.
# TODO field validation
async def handle_message(m, source, session):
    connection = "TODO_CONNECTION"
    log_message(IN, m, connection)
    t_received = time.time()

    if m.startswith('IAMAT '):
        handle_client_location(m, t_received, source)
    elif m.startswith('WHATSAT '):
        await handle_client_query(m, source, session)
    elif m.startswith('AT '):
        handle_propagation(m)
    else:
        print("\nUnknown message received: ", m)
        send_message(f"? {m}", [source])


# Process a client IAMAT location message m
def handle_client_location(m, t, source):
    m = m.strip()
    print("\nReceived location message: ", m)
    m_parse = m.split()

    if len(m_parse) != 4:
        send_message(f"? {m}", [source])
        return
    
    client_id = m_parse[1]
    client_location = m_parse[2]
    client_timestamp = float(m_parse[3])

    t_delta = t - client_timestamp
    t_prefix = '+' if t_delta >= 0 else '-'
    t_delta_s = t_prefix + str(t_delta)

    if not is_valid_location(client_location):
        send_message(f"? {m}", [source])
        return

    store_client_data(client_id, client_location, client_timestamp, t_delta_s)

    # Respond to client
    response = "AT {} {} {}".format(server_name, t_delta_s, m)
    send_message(response, [source])

    # Propagate location information
    propagate_list = \
        [SERVER_PORT_MAP[s] for s in PROPAGATION_MAP[server_name]]
    propagation = "AT {} {} {} {} {}" \
                  .format(server_name, t_delta_s, client_id, 
                          client_location, client_timestamp)
    send_message(propagation, propagate_list)
      

# Process client query m
async def handle_client_query(m, source, session):
    m = m.strip()
    print("\nReceived query: ", m)
    m_parse = m.split()
    
    if len(m_parse) != 4:
        send_message(f"? {m}", [source])
        return
    
    target_client = m_parse[1]
    radius = m_parse[2]
    max_results = m_parse[3]

    client_data = get_client_data(target_client)
    if not client_data:
        print(f"No client data for {target_client}")
        send_message(f"? {m}", [source])
        return
    
    try:
        lat, long = re.findall("[+-]{1}[0-9]+[.]*[0-9]+", 
                    client_data['location'])
    except:
        send_message(f"? {m}", [source])
        return

    gcpapi_res = await nearby_search(f"{lat},{long}", int(radius), 
                              int(max_results), session)
    
    if not gcpapi_res:
        send_message(f"? {m}", [source])
        return

    # Trim results to maximum
    results = gcpapi_res['results']
    gcpapi_res['results'] = results[0:min(int(max_results), len(results))]
    
    formatted_gcpapi_response = json.dumps(gcpapi_res, indent=4) + '\n'
    message_to_client = "AT {} {} {} {} {}\n{}" \
                        .format(client_data['server'], client_data['timedelta'],
                                target_client, client_data['location'], 
                                client_data['timestamp'], formatted_gcpapi_response)
    send_message(message_to_client, [source])


# Makes REST GET call to Google Places API nearby search
async def nearby_search(location, radius, max_count, session):
    output = "json"
    key = config['KEYS']['places_api_key']
    if radius < 0 or radius > 50 or max_count > 20 or max_count < 0:
        return None
    get_request = \
        "https://maps.googleapis.com/maps/api/place/nearbysearch/{}?key={}&location={}&radius={}" \
        .format(output, key, location, radius)
    return await fetch(session, get_request)

    
# Process propagation flood message m. Propagation messages should have form:
# AT [server] [timedelta] [client id] [location] [timestamp]
def handle_propagation(m):
    m = m.strip()
    print("Flood message received: ", m)
    m_parse = m.split()

    if len(m_parse) != 6:
        print("Invalid format for propagation message: too many entries.")
        return

    server = m_parse[1]
    timedelta = m_parse[2]
    client_id = m_parse[3]
    client_location = m_parse[4]
    timestamp = float(m_parse[5])

    # Check to see if we already have the latest client update
    last_client_report = get_client_data(client_id)
    if last_client_report and last_client_report['timestamp'] == timestamp:
        return
    
    # Otherwise store new data and propagate
    store_client_data(client_id, client_location, timestamp, timedelta, server)
    propagate_list = \
        [SERVER_PORT_MAP[s] for s in PROPAGATION_MAP[server_name]]
    send_message(m, propagate_list)


# Store reported client location
def store_client_data(c_id, location, timestamp, timedelta, server=None):
    if not server:
        server = server_name

    clients[c_id] = {
        "server": server,
        "location": location,
        "timestamp": timestamp,
        "timedelta": timedelta
    }


# Given the client id c, return the location of that client
def get_client_data(c):
    if c in clients:
        return clients[c]
    else:
        return None 


def is_valid_location(l):
    return len(re.findall("[+-]{1}[0-9]+[.]*[0-9]+", l)) == 2


# Send TCP message to another server or client. Sends to all nodes indicated by
# id in list d
def send_message(m, d):
    for target in d:
        log_message(OUT, m, target)
        print("\n{} sending message to {}: \n{}"
              .format(server_name, target, m))


# Save a message into the server log
def log_message(dir, m, connection):
    prefix = "INVALID_LOG_DIR" if dir != IN and dir != OUT \
             else "<<<" if dir == IN else ">>>"
    to_log = "{} {} {}".format(prefix, connection, m)
    
    # TODO: batch write LOG to a file at some point
    log.append(to_log)


# Print log contents to console 
def dump_log():
    for _ in log: print(_)
    print()


async def run_tests(session):
    print("Running tests...")

    # IAMAT valid 
    await handle_message("IAMAT kiwi.cs.ucla.edu +34.068930-118.445127 1520023934.918963997", "fake.source.com", session)
    # IAMAT valid with weird spaces
    await handle_message("IAMAT   kiwi.cs.ucla.edu    +34.068930-118.445127     1520023934.918963997", "fake.source.com", session)
    # Invalid IAMAT: too many entries
    await handle_message("IAMAT kiwi.cs.ucla.edu +34.068930-118.445127 1520023934.918963997 extraextra", "fake.source.com", session)
    # Invalid IAMAT: bad location
    await handle_message("IAMAT kiwi.cs.ucla.edu +34.068930118.445127 1520023934.918963997", "fake.source.com", session)

    # WHATSAT valid
    await handle_message("WHATSAT kiwi.cs.ucla.edu 10 1", "fake.source.com", session)

    # WHATSAT invalid radius 
    await handle_message("WHATSAT kiwi.cs.ucla.edu 10000 5", "fake.source.com", session)
    await handle_message("WHATSAT kiwi.cs.ucla.edu -1 5", "fake.source.com", session)

    # WHATSAT invalid maxcount 
    await handle_message("WHATSAT kiwi.cs.ucla.edu 10 50", "fake.source.com", session)
    await handle_message("WHATSAT kiwi.cs.ucla.edu 10 -1", "fake.source.com", session)

    # Propagation message valid
    await handle_message("AT kiwi.cs.ucla.edu +34.068930-118.445127 1520023934.918963997", "fake.source.com", session) 

    # Propagation message entry count different
    await handle_message("AT +34.068930-118.445127 1520023934.918963997", "fake.source.com", session) 

    # Unrecognized command
    await handle_message("MUFUFU hello", "fake.source.com", session)
    print("Done!")


def print_usage():
    print("\nUsage: python server.py [server_name]")
    print("Valid server names: 'Goloman', 'Hands', 'Holiday', 'Welsh', "
          "'Wilkes'")


async def fetch(session, url):
    async with session.get(url) as response:
        return await response.json()


if __name__ == "__main__":
    main()