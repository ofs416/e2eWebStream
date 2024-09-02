# Variables
WORKER_COUNT ?= 3
SPARK_PACKAGES = 'org.apache.kafka:kafka-clients:3.7.0,org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.1,org.apache.spark:spark-streaming-kafka-0-10_2.12:3.5.1,org.apache.spark:spark-token-provider-kafka-0-10_2.12:3.5.1'

build:
	docker compose build

down:
	docker compose down --volumes --remove-orphans

run:
	make down && docker compose up

run-scaled:
	make down && docker compose up --scale spark-worker=$(WORKER_COUNT)

run-d:
	make down && docker compose up -d

stop:
	docker compose stop

submit:
	docker exec spark-master spark-submit --packages $(SPARK_PACKAGES) --master spark://spark-master:7077 ./apps/spark_stream.py