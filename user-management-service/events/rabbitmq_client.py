"""
RabbitMQ client for publishing and consuming events with retry logic.
"""

import os
import json
import pika
import asyncio
import time
from typing import Dict, Any, Optional, Callable

class RabbitMQClient:
    """
    Client for interacting with RabbitMQ with improved connection retry logic.
    """
    def __init__(self):
        self.url = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/")
        self.connection = None
        self.channel = None
        self._connection_lock = asyncio.Lock()
        self._connected = False
        self.max_retries = 10
        self.retry_delay = 3  # seconds

    async def connect(self):
        """
        Connect to RabbitMQ and set up channel with retry logic.
        """
        async with self._connection_lock:
            if self._connected:
                return
            
            retries = 0
            while retries < self.max_retries:
                try:
                    print(f"Attempting to connect to RabbitMQ at {self.url} (attempt {retries + 1}/{self.max_retries})")
                    # Connect to RabbitMQ
                    connection_params = pika.URLParameters(self.url)
                    self.connection = pika.BlockingConnection(connection_params)
                    self.channel = self.connection.channel()
                    
                    # Declare exchanges
                    self.channel.exchange_declare(
                        exchange='user_events',
                        exchange_type='topic',
                        durable=True
                    )
                    
                    self._connected = True
                    print("Successfully connected to RabbitMQ")
                    return
                except Exception as e:
                    retries += 1
                    print(f"Failed to connect to RabbitMQ: {str(e)}")
                    if retries >= self.max_retries:
                        print("Maximum retry attempts reached. Could not connect to RabbitMQ.")
                        raise
                    
                    wait_time = self.retry_delay * retries
                    print(f"Waiting {wait_time} seconds before retrying...")
                    await asyncio.sleep(wait_time)

    async def close(self):
        """
        Close connection and channel.
        """
        async with self._connection_lock:
            if self.connection:
                try:
                    self.connection.close()
                    self._connected = False
                    print("Disconnected from RabbitMQ")
                except Exception as e:
                    print(f"Error closing RabbitMQ connection: {str(e)}")

    async def ensure_connection(self):
        """
        Ensure there is a connection to RabbitMQ before performing operations.
        """
        if not self._connected:
            await self.connect()

    async def publish_event(self, event_type: str, payload: Dict[str, Any]):
        """
        Publish an event to RabbitMQ with automatic reconnection.
        
        Args:
            event_type: Type of event (used as routing key)
            payload: Event payload
            
        Raises:
            Exception: If publishing fails after reconnection attempts
        """
        await self.ensure_connection()
        
        try:
            # Add timestamp to payload
            message = {
                "event_type": event_type,
                "payload": payload,
                "timestamp": time.time()
            }
            
            # Convert to JSON
            message_json = json.dumps(message)
            
            # Determine exchange based on event type
            exchange = 'user_events'
            
            # Publish message
            self.channel.basic_publish(
                exchange=exchange,
                routing_key=event_type,
                body=message_json,
                properties=pika.BasicProperties(
                    delivery_mode=2,  # make message persistent
                    content_type='application/json'
                )
            )
            
            print(f"Published event {event_type}")
        except Exception as e:
            print(f"Error publishing event: {str(e)}")
            # Mark as disconnected and try to reconnect next time
            self._connected = False
            # Try to reconnect once
            try:
                await self.connect()
                # Try publishing again
                message = {
                    "event_type": event_type,
                    "payload": payload,
                    "timestamp": time.time()
                }
                message_json = json.dumps(message)
                exchange = 'user_events'
                
                self.channel.basic_publish(
                    exchange=exchange,
                    routing_key=event_type,
                    body=message_json,
                    properties=pika.BasicProperties(
                        delivery_mode=2,
                        content_type='application/json'
                    )
                )
                print(f"Published event {event_type} after reconnection")
            except Exception as reconnect_error:
                print(f"Failed to reconnect and publish: {str(reconnect_error)}")
                raise

# Create a global instance of the RabbitMQ client
rabbitmq_client = RabbitMQClient()