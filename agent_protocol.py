# agent_protocol.py
class AgentProtocol:
    def __init__(self):
        self.messages = {}

    def send(self, sender: str, receiver: str, content: dict):
        print(f"\n📨 [A2A] {sender} → {receiver}")
        self.messages[receiver] = content

    def receive(self, agent_name: str):
        return self.messages.get(agent_name, {})
