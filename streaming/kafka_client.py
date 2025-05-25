from confluent_kafka import Producer, Consumer, KafkaError
import json
import socket
from typing import Dict, Any, List, Callable, Optional
import threading
import time

from core.config import settings


class KafkaClient:
    """
    Kafka client for message streaming.
    
    Provides:
    - Producer for sending messages
    - Consumer for receiving messages
    - Topic management
    """
    
    def __init__(self):
        """Initialize Kafka client with configuration from settings."""
        self.bootstrap_servers = ",".join(settings.KAFKA_BOOTSTRAP_SERVERS)
        self.producer_config = {
            'bootstrap.servers': self.bootstrap_servers,
            'client.id': socket.gethostname()
        }
        self.consumer_config = {
            'bootstrap.servers': self.bootstrap_servers,
            'group.id': 'fastapi_app',
            'auto.offset.reset': 'earliest'
        }
        
        # Initialize producer
        self.producer = Producer(self.producer_config)
        
        # Active consumers
        self.consumers: Dict[str, Dict[str, Any]] = {}
        
        # Flag to control consumer threads
        self.running = True
    
    def produce(self, topic: str, key: str, value: Dict[str, Any]) -> None:
        """
        Produce a message to a Kafka topic.
        
        Args:
            topic: Kafka topic
            key: Message key
            value: Message value (will be JSON serialized)
        """
        try:
            self.producer.produce(
                topic=topic,
                key=key,
                value=json.dumps(value).encode('utf-8'),
                callback=self._delivery_report
            )
            # Trigger any available delivery callbacks
            self.producer.poll(0)
        except Exception as e:
            print(f"Error producing message: {e}")
    
    def _delivery_report(self, err, msg) -> None:
        """
        Callback for message delivery reports.
        
        Args:
            err: Error (if any)
            msg: Message that was produced
        """
        if err is not None:
            print(f"Message delivery failed: {err}")
        else:
            print(f"Message delivered to {msg.topic()} [{msg.partition()}]")
    
    def flush(self) -> None:
        """
        Wait for all messages in the producer queue to be delivered.
        """
        self.producer.flush()
    
    def create_consumer(self, consumer_id: str, topics: List[str], 
                        message_handler: Callable[[str, Dict[str, Any]], None]) -> None:
        """
        Create a new Kafka consumer.
        
        Args:
            consumer_id: Unique consumer identifier
            topics: List of topics to subscribe to
            message_handler: Callback function for handling messages
        """
        if consumer_id in self.consumers:
            raise ValueError(f"Consumer with ID {consumer_id} already exists")
        
        # Create consumer with unique group ID
        consumer_config = self.consumer_config.copy()
        consumer_config['group.id'] = f"{consumer_config['group.id']}_{consumer_id}"
        
        consumer = Consumer(consumer_config)
        consumer.subscribe(topics)
        
        # Store consumer
        self.consumers[consumer_id] = {
            'consumer': consumer,
            'topics': topics,
            'handler': message_handler,
            'thread': None
        }
        
        # Start consumer thread
        thread = threading.Thread(
            target=self._consume_loop,
            args=(consumer_id,),
            daemon=True
        )
        thread.start()
        
        self.consumers[consumer_id]['thread'] = thread
    
    def _consume_loop(self, consumer_id: str) -> None:
        """
        Consumer loop for processing messages.
        
        Args:
            consumer_id: Consumer identifier
        """
        if consumer_id not in self.consumers:
            return
        
        consumer = self.consumers[consumer_id]['consumer']
        handler = self.consumers[consumer_id]['handler']
        
        try:
            while self.running:
                msg = consumer.poll(1.0)
                
                if msg is None:
                    continue
                
                if msg.error():
                    if msg.error().code() == KafkaError._PARTITION_EOF:
                        # End of partition event - not an error
                        continue
                    else:
                        print(f"Consumer error: {msg.error()}")
                        continue
                
                # Parse message
                try:
                    key = msg.key().decode('utf-8') if msg.key() else None
                    value = json.loads(msg.value().decode('utf-8'))
                    
                    # Call handler
                    handler(key, value)
                except Exception as e:
                    print(f"Error processing message: {e}")
        finally:
            consumer.close()
    
    def delete_consumer(self, consumer_id: str) -> None:
        """
        Delete a Kafka consumer.
        
        Args:
            consumer_id: Consumer identifier
        """
        if consumer_id in self.consumers:
            # Close consumer
            self.consumers[consumer_id]['consumer'].close()
            # Remove from active consumers
            del self.consumers[consumer_id]
    
    def close(self) -> None:
        """
        Close all consumers and the producer.
        """
        self.running = False
        
        # Close all consumers
        for consumer_id in list(self.consumers.keys()):
            self.delete_consumer(consumer_id)
        
        # Flush and close producer
        self.producer.flush()


# Singleton instance
kafka_client = KafkaClient()
