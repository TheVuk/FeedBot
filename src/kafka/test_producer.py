import os
import sys
from time import sleep
from json import dumps
from kafka import KafkaProducer



#returned_value = os.system("kafka-topics --create --zookeeper localhost:2181 --replication-factor 1 --partitions 1 --topic %s" % str(1))
#print(returned_value)

producer = KafkaProducer(bootstrap_servers=['127.0.0.1:9092'],
                         value_serializer=lambda x:
                         dumps(x).encode('utf-8'))


for e in range(10):
    data = {'number1': e+1, 'number2': 44.3, 'number3': "sdsdsd", 'number4': 121212}
    #data = {'Price': str(price), 'Timestamp': str(timestamp), 'tottrade': str(tottrade), 'VWAP': str(VWAP)}

    producer.send(str("1"), value=data)
    sleep(1)

