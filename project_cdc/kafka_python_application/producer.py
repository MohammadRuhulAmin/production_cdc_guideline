from kafka import KafkaProducer
import json
import time

# Kafka Producer Configuration
producer = KafkaProducer(
    bootstrap_servers='<HOST_IP_ADDRESS>:9092',  # Change to your Kafka broker address
    value_serializer=lambda v: json.dumps(v).encode('utf-8')  # Serialize data to JSON format
)


def produce_data():
    # Sample data to send to Kafka
    data = {
        "id": 1,
        "name": "Ruhul Amin",
        "age": 30,
        "profession": "Software Engineer"
    }

    while True:
        try:
            
            producer.send('try-topic', value=data)
            print(f"Data sent: {data}")
            time.sleep(5)  # Wait 5 seconds before sending the next message
        except Exception as e:
            print(f"Error sending data: {e}")


if __name__ == "__main__":
    produce_data()
