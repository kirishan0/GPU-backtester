from project.engine.state import RunState, init_states


def test_runstate_default():
    state = init_states()
    assert state.position_side is None
    d = state.to_dict()
    state2 = RunState.from_dict(d)
    assert state2 == state
