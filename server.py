import sys
import time
import configparser


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
server_name = ""
clients= {}
log = []

# Config file used for secret stuff like the API
config = configparser.ConfigParser()
config.read('config.ini')


def main():
    # Parse args for server name
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
    run_tests()

    print("\n\n{} going offline\n\nDumping log...".format(server_name))
    for _ in log: print(_)
    print()


# Processes a message m received presumably from an async event.
def handle_message(m):
    connection = "TODO_CONNECTION"
    log_message(IN, m, connection)
    t_received = time.time()

    if m.startswith('IAMAT '):
        handle_client_location(m, t_received)
    elif m.startswith('WHATSAT '):
        handle_client_query(m)
    elif m.startswith('AT '):
        handle_propagation(m)
    else:
        print("Unknown message received")


# Process a client location message m
def handle_client_location(m, t):
    m = m.strip()
    print("Received location message: ", m)
    print("Receipt time: ", t)
    m_parse = m.split()

    if len(m_parse) != 4:
        print("Invalid format for location message: too many entries.")
        return
    
    # TODO: validate these 3 fields
    client_id = m_parse[1]
    client_location = m_parse[2]
    client_timestamp = float(m_parse[3])

    store_client_data(client_id, client_location, client_timestamp)

    t_delta = t - client_timestamp
    t_prefix = '+' if t_delta >= 0 else '-'
    t_delta_s = t_prefix + str(t_delta)

    # Respond to client
    response = "AT {} {} {}".format(server_name, t_delta_s, m)
    send_message(response, [client_id])

    # Propagate location information
    propagation = "AT {} {} {}".format(client_id, client_location, client_timestamp)
    send_message(propagation, PROPAGATION_MAP[server_name])
      

# Process client query m
def handle_client_query(m):
    m = m.strip()
    print("Received query: ", m)
    m_parse = m.split()
    
    if len(m_parse) != 4:
        print("Invalid format for location message: too many entries.")
        return
    
    # TODO: validate these 3 fields
    target_client = m_parse[1]
    radius = m_parse[2]
    max_results = m_parse[3]

    # TODO check bounds of max_results

    print("Not ready to handle queries yet")


# Process propagation flood message m. Propagation messages should have form:
# AT [client id] [location] [timestamp]
def handle_propagation(m):
    m = m.strip()
    print("Flood message received: ", m)
    m_parse = m.split()

    if len(m_parse) != 4:
        print("Invalid format for propagation message: too many entries.")
        return

    client_id = m_parse[1]
    client_location = m_parse[2]
    timestamp = float(m_parse[3])

    # Check to see if we already have the latest client update
    last_client_report = get_client_data(client_id)
    if last_client_report and last_client_report['timestamp'] == timestamp:
        return
    
    # Otherwise store new data and propagate
    store_client_data(client_id, client_location, timestamp)
    send_message(m, PROPAGATION_MAP[server_name])


# Send TCP message to another server or client. Sends to all nodes indicated by
# id in list d
def send_message(m, d):
    for target in d:
        log_message(OUT, m, target)
        print("\n{} sending message to {}: \n{}"
              .format(server_name, target, m))


# Store reported client location
def store_client_data(c_id, location, timestamp):
    clients[c_id] = {
        "location": location,
        "timestamp": timestamp 
    }


# Given the client id c, return the location of that client
def get_client_data(c):
    if c in clients:
        return clients[c]
    else:
        return None 
    

# Save a message into the server log
def log_message(dir, m, connection):
    prefix = "INVALID_LOG_DIR" if dir != IN and dir != OUT \
             else "<<<" if dir == IN else ">>>"
    to_log = "{} {} {}".format(prefix, connection, m)
    
    # TODO: batch write LOG to a file at some point
    log.append(to_log)


def run_tests():
    handle_message("IAMAT kiwi.cs.ucla.edu +34.068930-118.445127 1520023934.918963997")
    # handle_message("IAMAT   kiwi.cs.ucla.edu    +34.068930-118.445127     1520023934.918963997")
    # handle_message("WHATSAT kiwi.cs.ucla.edu 10 5")
    # handle_message("AT Goloman +0.263873386 kiwi.cs.ucla.edu +34.068930-118.445127 1520023934.918963997")
    # handle_message("MUFUFU hello")


def print_usage():
    print("\nUsage: python server.py [server_name]")
    print("Valid server names: 'Goloman', 'Hands', 'Holiday', 'Welsh', "
          "'Wilkes'")


if __name__ == "__main__":
    main()