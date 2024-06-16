import pika

class RabbitMQ:
    def __init__(self, username, server_ip):
        self.username = username
        self.server_ip = server_ip
        self.initialize()

    def connect(self):
        try:
            connection = pika.BlockingConnection(pika.ConnectionParameters(host=self.server_ip))
            channel = connection.channel()
            return channel
        except Exception as e:
            raise Exception(f"Connection to RabbitMQ failed: {e}")


    def initialize(self):
        try:
            channel = self.connect()

            # Group chat initialization
            channel.exchange_declare(exchange='group_chat', exchange_type='topic')

            # Chat discovery initialization
            channel.exchange_declare(exchange='discovery_requests', exchange_type='fanout')
            queue_requests = f'{self.username}:discovery_requests'
            channel.queue_declare(queue=queue_requests, durable=True)
            channel.queue_bind(exchange='discovery_requests', queue=queue_requests)
            channel.exchange_declare(exchange='discovery_responses', exchange_type='direct')
            queue_responses = f'{self.username}:discovery_responses'
            channel.queue_declare(queue=queue_responses, durable=True)
            channel.queue_bind(exchange='discovery_responses', queue=queue_responses, routing_key=self.username)

            # Insult channel initialization
            channel.exchange_declare(exchange='insults', exchange_type='fanout')
            channel.queue_declare(queue='insults_queue', durable=True)
            channel.queue_bind(exchange='insults', queue='insults_queue')

        except Exception as e:
            raise Exception(f"Initialization RabbitMQ failed: {e}")