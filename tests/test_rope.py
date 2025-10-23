from game.rope import Rope

def test_rope_moves_right_with_right_pull():
    r = Rope(200, 100)
    start = r.pos
    r.apply_pull(left_pull=0, right_pull=5)
    assert r.pos > start

def test_rope_moves_left_with_left_pull():
    r = Rope(200, 100)
    start = r.pos
    r.apply_pull(left_pull=5, right_pull=0)
    assert r.pos < start

def test_rope_clamps_bounds_left():
    r = Rope(200, 100)
    r.pos = r.min_x
    r.apply_pull(left_pull=10, right_pull=0)
    assert r.pos == r.min_x

def test_rope_clamps_bounds_right():
    r = Rope(200, 100)
    r.pos = r.max_x
    r.apply_pull(left_pull=0, right_pull=10)
    assert r.pos == r.max_x