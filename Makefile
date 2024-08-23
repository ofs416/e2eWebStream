# Variables
WORKER_COUNT ?= 3
SPARK_PACKAGES = org.apache.spark:spark-sql-kafka-0-10_2.12:3.1.2

build:
	docker-compose build

down:
	docker-compose down --volumes --remove-orphans

run:
	make down && docker-compose up

run-scaled:
	make down && docker-compose up --scale spark-worker=$(WORKER_COUNT)

run-d:
	make down && docker-compose up -d

stop:
	docker-compose stop

submit:
	docker exec spark-master spark-submit --packages $(SPARK_PACKAGES) --master spark://spark-master:7077 ./apps/$(app)

rm-results:
	rm -r book_data/results/*