import threading

class ChatDiscovery:
    def __init__(self, rabbitmq):
        self.rabbitmq = rabbitmq
        self.discovery_thread = threading.Thread(target=self.listen_for_discovery_requests, daemon=True)
        self.discovery_thread.start()
     
    def publish_discovery_event(self):
            try:
                channel = self.rabbitmq.connect()
                channel.basic_publish(exchange='discovery_requests', routing_key='', body=self.rabbitmq.username)
            except Exception as e:
                raise Exception(e)

    def listen_for_discovery_requests(self):
        def callback(ch, method, properties, body):
                requester = body.decode()
                if requester != self.rabbitmq.username:
                    self.respond_to_discovery_request(requester)
        try:
                channel = self.rabbitmq.connect()
                queue_requests = f'{self.rabbitmq.username}:discovery_requests'
                channel.queue_purge(queue=queue_requests)
                channel.basic_consume(queue=queue_requests, on_message_callback=callback, auto_ack=True)
                channel.start_consuming()
        except Exception as e:
            print(f"Error: {e}")

    def respond_to_discovery_request(self, requester_username):
        try:
            channel = self.rabbitmq.connect()
            channel.basic_publish(exchange='discovery_responses', routing_key=requester_username, body=self.rabbitmq.username)
        except Exception as e:
            print(f"Error: {e}")

    def listen_for_responses(self, callback, stop_event):
        def wrapper(ch, method, properties, body):
                if stop_event.is_set():
                    ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
                    ch.stop_consuming()    
                else:
                    callback(body.decode())
                    ch.basic_ack(delivery_tag=method.delivery_tag)
        try:    
            channel = self.rabbitmq.connect()
            queue_responses = f'{self.rabbitmq.username}:discovery_responses'
            channel.queue_purge(queue=queue_responses)
            channel.basic_consume(queue=queue_responses, on_message_callback=wrapper)
            channel.start_consuming()
        except Exception as e:
            print(f"Error: {e}")

    def stop_consuming(self):
        try:
            channel = self.connect()
            channel.basic_publish(exchange='discovery_responses', routing_key=self.rabbitmq.username, body='stop')
        except Exception as e:
            print(f"Error: {e}")