from kafka import KafkaConsumer
import sys
from json import loads
consumer = KafkaConsumer(
     str(sys.argv[1]),
     bootstrap_servers=['127.0.0.1:9092'],
     auto_offset_reset='earliest',
     enable_auto_commit=True,
     group_id='algobots',
     value_deserializer=lambda x: loads(x.decode('utf-8')))


for message in consumer:
    message = message.value
    print(message)
