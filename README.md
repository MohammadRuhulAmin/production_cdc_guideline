# Change Data Capture
Date: September,18, 2025
![alt text](/public/image2.png)
## Setup and Installation CDC pipeline IN (Kafka) Stand Alone Mode :

- prerequisites: 
  - Linux Operating System
  - Docker 
  - Kafka
  

In this guide, we will set up a Change Data Capture (CDC) pipeline using Debezium, Apache Kafka, and Apache Zookeeper, running across multiple Docker containers managed by a Docker Compose file named cdc_maintainer.yaml. 
This setup is intended for a production environment.

- Step 1: Create a docker compose file and write the following Service (cdc_maintainer.yaml), Here for configuring the 
environment variables we have to use `KAFKA_` `ZOOKEEPER_` prefix. In kafka documentation there is a environment variable 
called `advertised.listeners` we will use `KAFKA + "_" + ADVERTISED + "_" + LISTENERS` (replace the `.` separator with `_`)

If you are new please visit:
- [Debezium Tutorial](https://debezium.io/documentation/reference/3.0/tutorial.html)
- [kafka](https://kafka.apache.org/)


```bash
version: 1.0.0
services:
  zookeeper:
    image: confluentinc/cp-zookeeper:5.5.3
    environment:
      ZOOKEEPER_CLIENT_PORT: 2181
    volumes:
      - ./zkafka_data/zookeeper/zk-data:/var/lib/zookeeper/data
      - ./zkafka_data/zookeeper/zk-txn-logs:/var/lib/zookeeper/log

  kafka:
    image: confluentinc/cp-enterprise-kafka:5.5.3
    links:
      - zookeeper
    environment:
      KAFKA_ZOOKEEPER_CONNECT: "zookeeper:2181"
      KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://<IP_ADDRESS>:9092 #  IP ADDRESS OF HOST MACHINE
      KAFKA_BROKER_ID: 1
      KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR: 1
      KAFKA_JMX_PORT: 9991
      # custom configuration 
      #KAFKA_AUTO_CREATE_TOPICS_ENABLE: false
      #KAFKA_LOG_RETENTION_MINUTES: 5
    ports:
      - 9092:9092
    volumes:
      - ./zkafka_data/kafka:/var/lib/kafka/data

  kafdrop:
    image: obsidiandynamics/kafdrop
    restart: "no"
    ports:
      - "9000:9000"
    environment:
      KAFKA_BROKERCONNECT: "<IP_ADDRESS>:9092" # BIND HOST IP ADDRESS WITH THE PORT 
    depends_on:
      - "kafka"

  connect:
    image: quay.io/debezium/connect:1.9
    ports:
      - 8083:8083
    links:
      - kafka
    environment:
      - BOOTSTRAP_SERVERS=kafka:9092
      - GROUP_ID=1
      - CONFIG_STORAGE_TOPIC=my_connect_configs
      - OFFSET_STORAGE_TOPIC=my_connect_offsets
      - STATUS_STORAGE_TOPIC=my_connect_statuses
      - CONNECTOR_CLASS=io.debezium.connector.mysql.MySqlConnector
      # MySQL connection details
      - DATABASE_HOSTNAME=<DATABASE_IP_ADDRESS> # database host IP address
      - DATABASE_PORT=3306
      - DATABASE_USER= 
      - DATABASE_PASSWORD=
      - DATABASE_SERVER_ID=1 # EXECUTEABLE SQL COMMAND:(SHOW VARIABLES LIKE 'server_id';)
      - DATABASE_SERVER_NAME=stg-mysql-8-db # EXECUTABLE SQL COMMAND (SELECT @@HOSTNAME;)
      - DATABASE_HISTORY_KAFKA_TOPIC=schema-changes.cdc_log

  schema-registry:
    image: confluentinc/cp-schema-registry:5.5.3
    environment:
      - SCHEMA_REGISTRY_KAFKASTORE_CONNECTION_URL=zookeeper:2181
      - SCHEMA_REGISTRY_HOST_NAME=schema-registry
      - SCHEMA_REGISTRY_LISTENERS=http://schema-registry:8081,http://<IP_ADDRESS>:8081 # IP ADDRESS OF HOST MACHINE 
    ports:
      - 8081:8081
    depends_on: [zookeeper, kafka]


```

- Step2: Before running the containers we have to follow, several things from the database end.

1. Check binary log if it is enable or not. If it is off then, need to contact database administrator to make it Enable / ON.

```bash
    SHOW VARIABLES LIKE `log_bin`;
```

2. Check the Binlog Format, Debezium requires the binlog format to be set to ROW. You can check the current format with this 

```bash
SHOW VARIABLES LIKE 'binlog_format';
```

3. Check the Binlog Row Image, the value should be FULL.

```bash
SHOW VARIABLES LIKE 'binlog_row_image';
```

4. Check Server ID, We have to put the Server Id in both compose file as well as
the connector json api.

```bash
SHOW VARIABLES LIKE 'server_id';
```

5. Check the hostname/ database server name of the Database:

```bash
SELECT @@hostname;
```

More thing to do:

The Database Administrator Has to provide the following least privilege To the user credential:

- Global Privilege (Reload, Replication-Client, Replication-slave) [on user level]
- Object Level privileged  (lock table, select)

To get All the privileges: 

```SQL
CREATE USER 'user'@'MACHINE_IP_ADDRESS' IDENTIFIED BY 'user_PASSWORD';
GRANT ALL ON *.* TO 'user'@'MACHINE_IP_ADDRESS';
```

if the configuration is not fulfilled, the database configuration for CDC is not ready.

- Step3: Now Lets Run the docker command:

```javascript
docker compose -f cdc_maintainer.yaml up
```

After running the container we have to add the debezium connector with the mysql
server by POST API:

POST API URL:
```javascript
http://<HOST_IP_ADDRESS>:8083/connectors
```

```javascript
{
    "name": "cdc-connector", /* name of the connector*/
    "config": {
      "connector.class": "io.debezium.connector.mysql.MySqlConnector",
      "tasks.max": "1",
      "database.hostname": "", /* Database Host IP Address*/
      "database.port": "3306",
      "database.user": "",
      "database.password": "",
      "database.server.id": "1",  /* DATABASE QUERY (SHOW VARIABLES LIKE 'server_id'; )  */
      "database.server.name": "", /* DATABASE QUERY (SELECT @@hostname;) */  
      "table.include.list":"mutation_barisal.cdc_log", /* DATABASE_NAME.TABLE_NAME */
      "database.history.kafka.bootstrap.servers": "<HOST_IP_ADDRESS>:9092",
      "database.history.kafka.topic": "schema-changes.cdc_log", /* TOPIC NAME */
      "database.allowPublicKeyRetrieval": "true", /* ALLOW PUBLIC RETRIEVAL */
      "database.useSSL": "false", /* SSL FALSE */
      "name": "cdc-connector"
    }
  }

```

After exposing the URL, It will response  200/201 status code.


- Step3: To Check the connection status using the curl command:

```bash
/* for checking the status of the connector*/
curl -s http://<HOST_IP_ADDRESS>:8083/connectors/cdc-connector/status

/** for restarting the connector */
curl -X POST http://<HOST_IP_ADDRESS>:8083/connectors/cdc-connector/restart

```

if you want to delete the connector, you will have to get the worker_id of the connector from the status json,
from ```curl -s http://<HOST_IP_ADDRESS>:8083/connectors/cdc-connector/status```
the response:

The simple response will be like
```javascript
{"name":"cdc-connector","connector":{"state":"RUNNING","worker_id":"172.18.0.6:8083"},"tasks":[{"id":0,"state":"RUNNING","worker_id":"172.18.0.6:8083"}],"type":"source"}
```

if the api shows the above response, now we are ready to test the pipeline.


In order to delete cdc-connector just use this:

```javascript
curl -X DELETE http://<worker_id>:<worker_port>/connectors/cdc-connector
/*Example: */
curl -X DELETE http://172.18.0.6:8083/connectors/cdc-connector
```

you will find the below response when you curl the status api again:

```javascript 
{"error_code":404,"message":"No status found for connector cdc-connector"}
```




- Step4: check Kafdrop ui: 

```javascript
<ip_address>:9000
```


The basic configuration of the debezium-kafka has been established. In this setup, 
by default all the records of the table will be captured and it will be sent  to the 
kafka queue. If we want to disable this debezium read mode and only want to sent data to 
the queue when (Insert, update, delete) will be performed, we have to add a property
in the connector json. 

the property is: 

```bash
     "snapshot.mode": "schema_only",
```

so the json looks like the following:


```javascript
{
    "name": "cdc-connector", /* name of the connector*/
    "config": {
      "connector.class": "io.debezium.connector.mysql.MySqlConnector",
      "tasks.max": "1",
      "database.hostname": "", /* Database Host IP Address*/
      "database.port": "3306",
      "database.user": "",
      "database.password": "",
      "database.server.id": "1",  /* DATABASE QUERY (SHOW VARIABLES LIKE 'server_id'; )  */
      "database.server.name": "", /* DATABASE QUERY (SELECT @@hostname;) */  
      "table.include.list":"mutation_barisal.cdc_log", /* DATABASE_NAME.TABLE_NAME */
      "database.history.kafka.bootstrap.servers": "<HOST_IP_ADDRESS>:9092",
      "database.history.kafka.topic": "schema-changes.cdc_log", /* TOPIC NAME */
      "database.allowPublicKeyRetrieval": "true", /* ALLOW PUBLIC RETRIEVAL */
      "database.useSSL": "false", /* SSL FALSE */
      "snapshot.mode": "schema_only",
      "name": "cdc-connector"
    }
  }

```

Now the more interesting part comes, Whatif i want to capture those records which are only inserted, or only deleted
or only updated.

## Kafka configuration in more details:

- To clear kafka queue after every certain time: 

```bash
  KAFKA_LOG_RETENTION_MINUTES: 5
  KAFKA_LOG_RETENTION_HOURS: 1
  KAFKA_LOG_RETENTION_MS: 12
```

- Not to allow create a topic from any producer/ consumer: 

```bash 
  KAFKA_AUTO_CREATE_TOPICS_ENABLE: false # by default it will be true
```
- Not to allow delete topic: 

```bash
  KAFKA_DELETE_TOPIC_ENABLE: false
```

- To specify the size of the topic : 

```bash
KAFKA_LOG_RETENTION_BYTES: 1073741824  # 1 GB
```
Kafka can generate a significant amount of data over time, especially in high-throughput scenarios. By setting a limit on the size of logs, 
```KAFKA_LOG_RETENTION_BYTES``` 
helps prevent the Kafka broker from consuming excessive disk space. 
Once the log for a partition reaches the specified size,
Kafka will start deleting the oldest segments of the log to make room for new data.

## Setting Up Kafka Cluster :

Using a Kafka cluster instead of a standalone Kafka instance for capturing data from a large database offers several advantages, particularly around scalability, reliability, and fault tolerance:

  - Scalability: A Kafka cluster allows for horizontal scaling by distributing data and load across multiple brokers. Each broker can handle a portion of the database's data capture process, making it possible to manage high-throughput, large datasets more efficiently.
  - High Availability: With a single Kafka instance (standalone mode), if it goes down, the entire data capture process stops. A Kafka cluster ensures that multiple brokers replicate data across partitions, so if one broker fails, the others can continue processing with minimal interruption.
  - Improved Throughput: Kafka clusters enable parallel processing of partitions, which is especially useful for large databases. You can allocate specific topics and partitions to different brokers, improving data ingestion speed and supporting high-velocity data capture without bottlenecks.
  - Fault Tolerance: Kafka clusters use replication to store copies of each partition on multiple brokers. This redundancy ensures data isn't lost if a single broker experiences issues, which is crucial for mission-critical, large-scale databases.
  - Data Durability: With Kafka’s distributed architecture, messages are replicated to ensure durability. This setup makes data capture more resilient to unexpected system failures and helps to prevent data loss when dealing with high-volume data from large databases.
  - Efficient Resource Utilization: By distributing processing across multiple nodes, a Kafka cluster can manage memory, CPU, and network resources more effectively than a standalone setup, reducing the risk of overloading a single machine.

Overall, a Kafka cluster provides a robust and resilient setup suited to handle the demands of capturing and processing data from large, high-volume databases, which would be challenging for a standalone Kafka instance to support effectively.


### [Kafka Cluster Setup Docker Compose file](https://github.com/MohammadRuhulAmin/docker_tutorial/blob/main/docker_file/cdc_cluster_setup/cdc_cluster_maintainer.yaml)

Md. Ruhul Amin
ETL Engineer
Business Automation Ltd.


