from collections import defaultdict


class EventBus:
    def __init__(self):
        self.subscriptions = defaultdict(list)

    def subscribe(self, event_type, callback):
        self.subscriptions[event_type].append(callback)

    def publish(self, event_type, data=None):
        for callback in self.subscriptions[event_type]:
            try:
                callback(data)
            except Exception as e:
                print(f"Event handler failed: {e}")


event_bus = EventBus()
