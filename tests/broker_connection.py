from kafka import KafkaProducer


def test_kafka_connection():
    try:
        producer = KafkaProducer(bootstrap_servers=["kafka:9092"])
        print("Kafka connection successful")
        producer.close()
    except Exception as e:
        print(f"Kafka connection failed: {e}")


if __name__ == "__main__":
    test_kafka_connection()
