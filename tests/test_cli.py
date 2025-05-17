import importlib
import sys
import types
from pathlib import Path

import pytest
from click.testing import CliRunner


def _create_stubs():
    rich = types.ModuleType("rich")
    console = types.ModuleType("console")
    markup = types.ModuleType("markup")
    text = types.ModuleType("text")

    class DummyHighlighter:
        def __call__(self, text):
            return text

    class Console:
        def __init__(self, *args, **kwargs):
            self.highlighter = DummyHighlighter()
            self.width = 80

        def print(self, *args, **kwargs):
            pass

    class Text(str):
        def __new__(cls, content="", *args, **kwargs):
            return str.__new__(cls, content)

        def stylize(self, style):
            pass

        def __iadd__(self, other):
            return Text(str(self) + str(other))

        @classmethod
        def from_markup(cls, markup, **kwargs):
            return Text(markup)

    console.Console = Console
    console.RenderableType = object
    markup.escape = lambda text: text
    text.Text = Text

    rich.console = console
    rich.markup = markup
    rich.text = text

    pygments = types.ModuleType("pygments")
    util = types.ModuleType("util")
    class ClassNotFound(Exception):
        pass
    util.ClassNotFound = ClassNotFound

    stubs = {
        "rich": rich,
        "rich.console": console,
        "rich.markup": markup,
        "rich.text": text,
        "pygments": pygments,
        "pygments.util": util,
    }
    return stubs


@pytest.fixture(autouse=True)
def stub_dependencies(monkeypatch):
    stubs = _create_stubs()
    for name, module in stubs.items():
        sys.modules.setdefault(name, module)
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
    yield
    for name in stubs:
        sys.modules.pop(name, None)
    sys.path = [p for p in sys.path if p != str(Path(__file__).resolve().parents[1] / "src")]


def test_version_output():
    main = importlib.import_module("rich_cli.__main__").main
    runner = CliRunner()
    result = runner.invoke(main, ["--version"])
    assert result.exit_code == 0
    assert "1.8.0" in result.output


def test_read_resource(tmp_path):
    main = importlib.import_module("rich_cli.__main__")
    sample = tmp_path / "sample.txt"
    sample.write_text("hello world")
    text, lexer = main.read_resource(str(sample), "text")
    assert text == "hello world"
    assert lexer == "text"


def test_line_range():
    main = importlib.import_module("rich_cli.__main__")
    assert main._line_range(3, None, 10) == (1, 3)
    assert main._line_range(None, 2, 10) == (10, 11)
    with pytest.raises(SystemExit):
        main._line_range(1, 1, 10)

