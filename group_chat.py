import pika

class GroupChat:
    def __init__(self, rabbitmq):
        self.subscriptions = {}
        self.messages = {}
        self.rabbitmq = rabbitmq
        
    def subscribe(self, group_id):
        try:
            channel = self.rabbitmq.connect()
            queue_name = f'{self.rabbitmq.username}:{group_id}'
            channel.queue_declare(queue=queue_name, durable=True)
            channel.queue_bind(exchange='group_chat', queue=queue_name, routing_key=f'*.{group_id}.*')
            self.messages[group_id] = []
            self.subscriptions[group_id] = queue_name
        except Exception as e:
            raise Exception(e) 

    def send_message(self, group_id, message):
        try:
            channel = self.rabbitmq.connect()
            channel.basic_publish(
                exchange='group_chat',
                routing_key=f'{self.rabbitmq.username}.{group_id}.msg',
                body=f'{self.rabbitmq.username}: {message}',
                properties=pika.BasicProperties(delivery_mode=2) # make message persistent
            )
            self.messages[group_id].append(f"{self.rabbitmq.username}: {message}")
        except Exception as e:
            raise Exception(e)

    def receive_messages(self, group_id, callback, stop_event):
        queue_name = self.subscriptions.get(group_id)
       
        def wrapper_callback(ch, method, properties, body):
            if stop_event.is_set():
                ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
                ch.stop_consuming()
            else:
                message = body.decode()
                if not message.startswith(self.rabbitmq.username):
                    self.messages[group_id].append(message)
                    callback(message)
                ch.basic_ack(delivery_tag=method.delivery_tag)

        try:
            channel = self.rabbitmq.connect()
            channel.basic_consume(queue=queue_name, on_message_callback=wrapper_callback)
            channel.start_consuming()
        except Exception as e:
            print(f"Error receiving messages. Try to connect again: {e}")

    def is_subscribed(self, group_id):
        return group_id in self.subscriptions

    def get_messages(self, group_id):
        return self.messages.get(group_id, []).copy()
    
    def delete_queues(self):
        try:
            channel = self.rabbitmq.connect()
            for queue in self.subscriptions.values():
                channel.queue_delete(queue)
        except Exception as e:
            print(f"Error deleting queues: {e}")