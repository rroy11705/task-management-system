"""
RabbitMQ client for publishing and consuming events.
"""

import os
import json
import pika
import asyncio
from typing import Dict, Any

class RabbitMQClient:
    """
    Client for interacting with RabbitMQ.
    """
    def __init__(self):
        self.url = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/")
        self.connection = None
        self.channel = None
        self._connection_lock = asyncio.Lock()
        self._connected = False

    async def connect(self):
        """
        Connect to RabbitMQ and set up channel.
        """
        async with self._connection_lock:
            if self._connected:
                return
            
            try:
                # Connect to RabbitMQ
                connection_params = pika.URLParameters(self.url)
                self.connection = pika.BlockingConnection(connection_params)
                self.channel = self.connection.channel()
                
                # Declare exchange
                self.channel.exchange_declare(
                    exchange='tenant_events',
                    exchange_type='topic',
                    durable=True
                )
                
                self._connected = True
                print("Connected to RabbitMQ")
            except Exception as e:
                print(f"Failed to connect to RabbitMQ: {str(e)}")
                self._connected = False
                # Re-raise to let the caller handle the error
                raise

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

    async def publish_event(self, event_type: str, payload: Dict[str, Any]):
        """
        Publish an event to RabbitMQ.
        """
        if not self._connected:
            await self.connect()
        
        try:
            # Add timestamp to payload
            message = {
                "event_type": event_type,
                "payload": payload,
            }
            
            # Convert to JSON
            message_json = json.dumps(message)
            
            # Publish message
            self.channel.basic_publish(
                exchange='tenant_events',
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
            # Try to reconnect for next time
            self._connected = False
            # Re-raise to let the caller handle the error
            raise

# Create a global instance of the RabbitMQ client
rabbitmq_client = RabbitMQClient()