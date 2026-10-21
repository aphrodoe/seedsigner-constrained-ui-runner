"""Everything under src/ must import on MicroPython, which has no `typing`.

CPython always has `typing`, so an unguarded import passes every other test and
only fails on the device -- text_renderer.py shipped one for two months that way.

The check is static because the runtime one can't be done faithfully on CPython:
blocking `typing` there fails on every annotation, which CPython evaluates when a
function is defined and MicroPython never evaluates at all. So this enforces the
two rules MicroPython actually imposes:

1. every `typing` import sits inside a `try` that catches ImportError;
2. names taken from `typing` appear only in annotations.

Separately, the files the device renders through may import only modules stock
MicroPython ships: status.py used `textwrap` and the bridge `base64`, neither of
which exists there. And they may not pad with str.center/ljust/rjust or
"{:<n}"/"{:^n}", which MicroPython measures in UTF-8 bytes (see text_helpers.center).
"""
import ast
import pathlib
import re

import pytest

SRC = pathlib.Path(__file__).resolve().parent.parent / "src"
FILES = sorted(p for p in SRC.rglob("*.py"))
TYPING_NAMES = {"List", "Dict", "Any", "Optional", "Tuple", "Union", "Callable", "Set"}


def _is_typing_import(node):
    if isinstance(node, ast.Import):
        return any(a.name == "typing" for a in node.names)
    if isinstance(node, ast.ImportFrom):
        return node.module == "typing"
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
        return (node.func.id == "__import__" and node.args
                and isinstance(node.args[0], ast.Constant) and node.args[0].value == "typing")
    return False


def _catches_import_error(try_node):
    for h in try_node.handlers:
        if h.type is None:
            return True
        names = h.type.elts if isinstance(h.type, ast.Tuple) else [h.type]
        if any(isinstance(n, ast.Name) and n.id in ("ImportError", "Exception") for n in names):
            return True
    return False


def _unguarded_typing_imports(tree):
    guarded = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Try) and _catches_import_error(node):
            for stmt in node.body:
                guarded.update(id(n) for n in ast.walk(stmt))
    return [n.lineno for n in ast.walk(tree) if _is_typing_import(n) and id(n) not in guarded]


def _typing_names_outside_annotations(tree):
    in_annotation = set()
    for node in ast.walk(tree):
        anns = []
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            a = node.args
            anns += [x.annotation for x in a.posonlyargs + a.args + a.kwonlyargs]
            anns += [a.vararg and a.vararg.annotation, a.kwarg and a.kwarg.annotation, node.returns]
        elif isinstance(node, ast.AnnAssign):
            anns.append(node.annotation)
        for ann in filter(None, anns):
            in_annotation.update(id(n) for n in ast.walk(ann))
    return [n.lineno for n in ast.walk(tree)
            if isinstance(n, ast.Name) and n.id in TYPING_NAMES
            and isinstance(n.ctx, ast.Load) and id(n) not in in_annotation]


@pytest.mark.parametrize("path", FILES, ids=lambda p: str(p.relative_to(SRC.parent)))
def test_typing_imports_are_guarded(path):
    assert _unguarded_typing_imports(ast.parse(path.read_text())) == []


@pytest.mark.parametrize("path", FILES, ids=lambda p: str(p.relative_to(SRC.parent)))
def test_typing_names_only_in_annotations(path):
    assert _typing_names_outside_annotations(ast.parse(path.read_text())) == []


# From `help('modules')` on the v1.27 ESP32 build, plus our own packages.
# gpiozero is imported only on the Pi branch of the bridge; ssd1306 is the
# micropython-lib driver on the device branch.
MPY_MODULES = {
    "_thread", "binascii", "collections", "errno", "framebuf", "gc", "io", "json",
    "machine", "math", "micropython", "os", "re", "select", "struct", "sys", "time",
    "typing", "src", "seedsigner", "gpiozero", "ssd1306",
}
DEVICE_FILES = sorted(
    [p for p in (SRC / "renderers").rglob("*.py")]
    + [SRC / "screen_state.py", SRC / "constrained_text_screens.py"]
    + list((SRC / "drivers").glob("*_mpy.py"))
)


def _imported_modules(tree):
    for n in ast.walk(tree):
        if isinstance(n, ast.Import):
            yield from ((a.name.split(".")[0], n.lineno) for a in n.names)
        elif isinstance(n, ast.ImportFrom) and n.level == 0 and n.module:
            yield n.module.split(".")[0], n.lineno


@pytest.mark.parametrize("path", DEVICE_FILES, ids=lambda p: str(p.relative_to(SRC.parent)))
def test_device_path_imports_exist_on_micropython(path):
    missing = [(m, line) for m, line in _imported_modules(ast.parse(path.read_text())) if m not in MPY_MODULES]
    assert missing == []


PADDING = re.compile(r"\.(center|ljust|rjust)\(|\{[^}]*:[<^]")


@pytest.mark.parametrize("path", DEVICE_FILES, ids=lambda p: str(p.relative_to(SRC.parent)))
def test_device_path_pads_by_characters(path):
    hits = [i for i, line in enumerate(path.read_text().splitlines(), 1) if PADDING.search(line)]
    assert hits == []


def test_padding_helpers_match_cpython():
    from src.renderers.text_helpers import center, ljust
    for text in ("", "x", "ab", "abc", "\u2713 Success!", "longer than width"):
        for width in range(12):
            assert center(text, width) == text.center(width)
            assert ljust(text, width) == text.ljust(width)
