import ast
import inspect
import textwrap

from project import gui

def test_default_mode_is_gpu():
    """_create_widgetsでGPUが初期選択となっているかを検証する。"""
    source = textwrap.dedent(inspect.getsource(gui.BacktesterGUI._create_widgets))
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and getattr(node.func, 'attr', '') == 'StringVar':
            for kw in node.keywords:
                if kw.arg == 'value' and isinstance(kw.value, ast.Constant):
                    assert kw.value.value == 'gpu'
                    return
    assert False, "StringVar default value not set to 'gpu'"
