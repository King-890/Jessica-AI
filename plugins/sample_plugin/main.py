class Plugin:
    def on_load(self):
        # Initialize resources if needed
        pass

    def on_event(self, name: str, payload=None):
        if name == "unity_error":
            # Example: react to Unity error events
            return {"action": "log", "message": "SamplePlugin observed unity_error"}
        return None

    def on_command(self, name: str, args=None):
        if name == "hello":
            return "SamplePlugin says hello!"
        return None