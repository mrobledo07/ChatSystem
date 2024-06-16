import socket
import threading
import grpc
import private_chat_pb2
import private_chat_pb2_grpc
from grpc_server import serve
import queue

class Client:
    def __init__(self, username, nameserver):
        self.username = username
        self.ip_address = self.get_local_ip_address()
        self.port = self.get_available_port()
        self.nameserver = nameserver
        self.send_info_to_server()

        self.chat_stub = None  # Initialize chat_stub
        self.chat_queues = {}  # Dictionary to store chat queues
        self.chat_messages = {}  # Dictionary to store chat messages

        # Start the gRPC server in a separate thread
        self.server_thread = threading.Thread(target=serve, args=(self,), daemon=True)
        self.server_thread.start()

    def get_local_ip_address(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(("8.8.8.8", 80))
            ip_address = s.getsockname()[0]
        except Exception:
            ip_address = '127.0.0.1'
        finally:
            s.close()
        return ip_address

    def get_available_port(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind(("", 0))
        port = s.getsockname()[1]
        s.close()
        return port

    def send_info_to_server(self):
        self.nameserver.hset(self.username, mapping={
            "ip_address" : self.ip_address,
            "port" : self.port
        })

    def close(self):
        self.nameserver.delete(self.username)

    def connect(self, chat_key, ip_address, port):
        if chat_key == self.username:
            raise Exception("Cannot connect to yourself")
        try:
            channel = grpc.insecure_channel(f"{ip_address}:{port}")
            self.chat_stub = private_chat_pb2_grpc.PrivateChatServiceStub(channel)
            if chat_key not in self.chat_queues:
                self.chat_queues[chat_key] = queue.Queue()
                self.chat_messages[chat_key] = []
        except grpc.RpcError as e:
            raise Exception(f"Error connecting to server: {e}")

    def add_message(self, sender, receiver, message):
        try:
            message_obj = private_chat_pb2.Message(sender=sender, receiver=receiver, message=message)
            self.chat_stub.AddMessage(message_obj)
            self.store_message(message_obj)  # Store the message locally as well
        except grpc.RpcError as e:
            raise Exception(f"Error adding message: {e}")

    def store_message(self, message):
        chat_key = message.sender if message.sender != self.username else message.receiver
        if chat_key not in self.chat_queues:
            self.chat_queues[chat_key] = queue.Queue()
            self.chat_messages[chat_key] = []
        if chat_key == message.sender:
            self.chat_queues[chat_key].put(message)
        self.chat_messages[chat_key].append(f"{message.sender}: {message.message}")

    def get_new_message(self, receiver):
        chat_key = receiver
        if chat_key in self.chat_queues:
            return self.chat_queues[chat_key].get()  # This will block until a message is available
        else:
            print(f"[!] No chat found for receiver: {receiver}")
            return None

    def get_messages(self, receiver):
        chat_key = receiver
        return self.chat_messages.get(chat_key, [])
    
    def clear_chat(self, chat_id):
        del self.chat_messages[chat_id]
        del self.chat_queues[chat_id]
