class AgentMessage:
    def __init__(self, sender, content, metadata=None):
        self.sender = sender
        self.content = content
        self.metadata = metadata or {}

    def to_dict(self):
        return {
            "sender": self.sender,
            "content": self.content,
            "metadata": self.metadata
        }
