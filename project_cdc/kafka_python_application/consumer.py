from confluent_kafka import Consumer, KafkaException, KafkaError

# Kafka configuration
conf = {
    'bootstrap.servers': '<IP_ADDRESS>:9092',   # Kafka broker address
    'group.id': 'my_consumer_group',         # Consumer group
    'auto.offset.reset': 'earliest'          # Start reading at the earliest available message
}

# Create Consumer instance
consumer = Consumer(conf)

# Kafka topic
topic = 'try-topic'

# Subscribe to the Kafka topic
consumer.subscribe([topic])

# Function to handle message processing
def consume_messages(consumer):
    try:
        while True:
            msg = consumer.poll(timeout=1.0)  # Poll for messages with a 1 second timeout
            if msg is None:
                continue
            if msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    # End of partition, continue polling
                    print(f"Reached end of partition {msg.partition()}")
                elif msg.error():
                    raise KafkaException(msg.error())
            else:
                # Process message
                print(f"Received message: {msg.value().decode('utf-8')}")
    except KeyboardInterrupt:
        print("Consumer stopped.")
    finally:
        # Close down the consumer cleanly
        consumer.close()

if __name__ == '__main__':
    consume_messages(consumer)
