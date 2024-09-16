import socket

def get_IP_address():
    hostname = socket.gethostname()
    IPAddr = socket.gethostbyname(hostname)

    return IPAddr