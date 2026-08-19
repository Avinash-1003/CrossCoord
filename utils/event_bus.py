import asyncio
from collections import defaultdict

class EventBus:
    """
    Asynchronous Pub/Sub Event Bus for Distributed Multi-Agent Communication.
    Simulates a message broker (like MQTT or RabbitMQ) in a single async process.
    """
    def __init__(self):
        self.subscribers = defaultdict(list)
        self.message_queue = asyncio.Queue()
        self._running = False

    def subscribe(self, topic: str, callback):
        """Register a callback for a specific topic."""
        self.subscribers[topic].append(callback)

    async def publish(self, topic: str, payload: dict):
        """Publish a message to a topic."""
        await self.message_queue.put((topic, payload))

    async def run_broker(self):
        """Continuously pulls messages from the queue and dispatches to subscribers."""
        self._running = True
        print("[EventBus] Broker started.")
        while self._running:
            topic, payload = await self.message_queue.get()
            
            # Dispatch to all subscribers
            for callback in self.subscribers.get(topic, []):
                if asyncio.iscoroutinefunction(callback):
                    asyncio.create_task(callback(payload))
                else:
                    callback(payload)
                    
            self.message_queue.task_done()

    def stop(self):
        self._running = False
        print("[EventBus] Broker stopped.")

# Global singleton for convenience in this simulation
bus = EventBus()
