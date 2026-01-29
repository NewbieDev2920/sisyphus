
class StateChange:
    def __init__(self, past_state : State, new_state : State):
        self.past_state = past_state
        self.new_state = new_state