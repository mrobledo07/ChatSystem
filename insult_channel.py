
class InsultChannel:
    def __init__(self, rabbitmq):
        self.rabbitmq = rabbitmq

    def publish_insult(self, insult):
        try:
            channel = self.rabbitmq.connect()
            channel.basic_publish(exchange='insults', routing_key='', body=insult)
        except Exception as e:
            raise Exception(e)
        
    def consume_insults(self, callback, stop_event):
        def handle_insult(ch, method, properties, body):
            if stop_event.is_set():
                ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
                ch.stop_consuming()  # Stop consuming
            else:
                callback(body.decode())
                ch.basic_ack(delivery_tag=method.delivery_tag)

        try:
            channel = self.rabbitmq.connect()
            channel.basic_qos(prefetch_count=1)
            channel.basic_consume(queue='insults_queue', on_message_callback=handle_insult)
            channel.start_consuming()
        except Exception as e:
            raise Exception(e)