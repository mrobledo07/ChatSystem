import socket

def discover_server_ip():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    message = b'DISCOVERY_REQUEST'
    broadcast_address = ('<broadcast>', 37020)
    
    while True:
        sock.sendto(message, broadcast_address)
        try:
            sock.settimeout(2)
            data, addr = sock.recvfrom(1024)
            if data.startswith(b'SERVER_IP:'):
                server_ip = data.split(b':')[1].decode('utf-8')
                return server_ip
        except socket.timeout:
            continue