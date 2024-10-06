# Change Data Capture
![alt text](/public/image.png)



In this guide, we will set up a Change Data Capture (CDC) pipeline using Debezium, Apache Kafka, and Apache Zookeeper, running across multiple Docker containers managed by a Docker Compose file named cdc_maintainer.yaml. 
This setup is intended for a production environment.

- Step 1: Create a docker compose file and write the following Service (cdc_maintainer.yaml)

```javascript
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

```mysql
    SHOW VARIABLES LIKE `log_bin`;
```

2. Check the Binlog Format, Debezium requires the binlog format to be set to ROW. You can check the current format with this 

```mysql
SHOW VARIABLES LIKE 'binlog_format';
```

3. Check the Binlog Row Image, the value should be FULL.

```mysql
SHOW VARIABLES LIKE 'binlog_row_image';
```

4. Check Server ID, We have to put the Server Id in both compose file as well as
the connector json api.

```mysql
SHOW VARIABLES LIKE 'server_id';
```

5. Check the hostname/ database server name of the Database:

```mysql
SELECT @@hostname;
```

More thing to do:

The Database Administrator Has to provide the following privilege:

- Global Privilege (Reload, Replication-Client, Replication-slave) [on user level]
- local Privilege (lock table, select)


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

```
curl -s http://<HOST_IP ADDRESS>:8083/connectors/cdc-connector/status
```

The simple response will be like
```javascript
{"name":"cdc-connector","connector":{"state":"RUNNING","worker_id":"172.18.0.6:8083"},"tasks":[{"id":0,"state":"RUNNING","worker_id":"172.18.0.6:8083"}],"type":"source"}
```

if the api shows the above response, now we are ready to test the pipeline.


- Step4: check Kafdrop ui: 

```javascript
<ip_address>:9000
```


