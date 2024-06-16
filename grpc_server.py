import grpc
from concurrent import futures
import private_chat_pb2_grpc
import private_chat_pb2

class PrivateChatServicer(private_chat_pb2_grpc.PrivateChatServiceServicer):
    def __init__(self, client):
        self.client = client

    def AddMessage(self, message, context):
        self.client.store_message(message)
        response = private_chat_pb2.google_dot_protobuf_dot_empty__pb2.Empty()
        return response

def serve(client):
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    private_chat_pb2_grpc.add_PrivateChatServiceServicer_to_server(PrivateChatServicer(client), server)
    server.add_insecure_port(f'{client.ip_address}:{client.port}')
    server.start()
    server.wait_for_termination()