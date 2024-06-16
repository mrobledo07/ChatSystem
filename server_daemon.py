import socket


def get_local_ip_address():
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(("8.8.8.8", 80))
            ip_address = s.getsockname()[0]
        except Exception:
            ip_address = '127.0.0.1'
        finally:
            s.close()
        return ip_address

def respond_to_discovery():
    server_ip = get_local_ip_address()
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(('', 37020))
        
    while True:
        try:
            data, addr = sock.recvfrom(1024)
            if data == b'DISCOVERY_REQUEST':
                sock.sendto(f'SERVER_IP:{server_ip}'.encode('utf-8'), addr)
                print(f"Sent the server IP to {addr}")
        except KeyboardInterrupt:
            break

if __name__ == "__main__":
    print("Listening to broadcast nameserver requests...")
    respond_to_discovery()
