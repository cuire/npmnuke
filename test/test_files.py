import tempfile
from pathlib import Path

import pytest

from npmnuke.main import find_node_modules_dirs, remove_node_modules


@pytest.fixture(autouse=True)
def tmpdir() -> None:
    with tempfile.TemporaryDirectory() as tmpdirname:
        tmpdir = Path(tmpdirname)
        yield tmpdir


def test_find_node_modules_dirs(tmpdir: Path) -> None:
    node_modules_dir = tmpdir / f"node_modules"
    node_modules_dir.mkdir(parents=True, exist_ok=True)

    node_modules_dirs = find_node_modules_dirs(tmpdir)

    assert len(node_modules_dirs) == 1

    assert node_modules_dirs[0].name == tmpdir.name


def test_find_node_modules_dirs_in_multiple_folders(tmpdir: Path) -> None:
    FOLDER_COUNT = 3

    for i in range(FOLDER_COUNT):
        node_modules_dir = tmpdir / str(i) / f"node_modules"
        node_modules_dir.mkdir(parents=True, exist_ok=True)

    node_modules_dirs = find_node_modules_dirs(tmpdir)

    assert len(node_modules_dirs) == FOLDER_COUNT

    found = [False] * FOLDER_COUNT

    # folders can be found in any order
    for dir in node_modules_dirs:
        found[int(dir.name)] = True

    assert all(found)


def test_find_node_modules_in_empty_folder(tmpdir: Path) -> None:
    node_modules_dirs = find_node_modules_dirs(tmpdir)

    assert len(node_modules_dirs) == 0


def test_find_node_modules_in_nested_folder(tmpdir: Path) -> None:
    node_modules_dir = tmpdir / "nested" / "node_modules"
    node_modules_dir.mkdir(parents=True, exist_ok=True)

    node_modules_dirs = find_node_modules_dirs(tmpdir)

    assert len(node_modules_dirs) == 1

    assert node_modules_dirs[0].name == "nested"


def test_find_node_modules_ingnores_nested_node_modules(tmpdir: Path) -> None:
    nested_node_modules_dir = tmpdir / "node_modules" / "node_modules" / "node_modules"
    nested_node_modules_dir.mkdir(parents=True, exist_ok=True)

    node_modules_dirs = find_node_modules_dirs(tmpdir)

    assert len(node_modules_dirs) == 1

    assert node_modules_dirs[0].name == tmpdir.name


def test_remove_node_modules(tmpdir: Path) -> None:
    node_modules_dir = tmpdir / f"node_modules"
    node_modules_dir.mkdir(parents=True, exist_ok=True)

    for i in range(10):
        module = node_modules_dir / f"module_{i}"
        module.mkdir(parents=True, exist_ok=True)

    remove_node_modules(tmpdir)

    assert not node_modules_dir.exists()


def test_remove_node_modules_in_nested_folder(tmpdir: Path) -> None:
    nested_dir = tmpdir / "nested"
    nested_dir.mkdir(parents=True, exist_ok=True)

    node_modules_dir = nested_dir / "node_modules"
    node_modules_dir.mkdir(parents=True, exist_ok=True)

    for i in range(10):
        module = node_modules_dir / f"module_{i}"
        module.mkdir(parents=True, exist_ok=True)

    remove_node_modules(nested_dir)

    assert not node_modules_dir.exists()


def test_remove_node_modules_in_nested_folder_with_files(tmpdir: Path) -> None:
    nested_dir = tmpdir / "nested"
    nested_dir.mkdir(parents=True, exist_ok=True)

    node_modules_dir = nested_dir / "node_modules"
    node_modules_dir.mkdir(parents=True, exist_ok=True)

    file = node_modules_dir / "file.txt"
    file.touch()

    remove_node_modules(nested_dir)

    assert not node_modules_dir.exists()


def test_remove_node_modules_return_size(tmpdir: Path) -> None:
    node_modules_dir = tmpdir / f"node_modules"
    node_modules_dir.mkdir(parents=True, exist_ok=True)

    # file with 1 KB of data
    file = node_modules_dir / "file.txt"
    file.touch()
    file.write_text("a" * 1024, encoding="ASCII")

    remove_node_modules(tmpdir)

    assert not node_modules_dir.exists()
