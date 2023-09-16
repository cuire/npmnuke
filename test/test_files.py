import os
import tempfile
from collections.abc import Iterator
from pathlib import Path

import pytest

from npmnuke.main import calculate_size, find_node_modules_dirs, remove_node_modules

if os.name == "nt":
    import _winapi


@pytest.fixture(autouse=True)
def tmpdir() -> None:
    with tempfile.TemporaryDirectory() as tmpdirname:
        tmpdir = Path(tmpdirname)
        yield tmpdir


def test_find_node_modules_dirs(tmpdir: Path) -> None:
    node_modules_dir = tmpdir / f"node_modules"
    node_modules_dir.mkdir(parents=True, exist_ok=True)

    node_modules_dirs = list(find_node_modules_dirs(tmpdir))

    assert len(node_modules_dirs) == 1

    assert node_modules_dirs[0].name == tmpdir.name


def test_find_node_modules_dirs_in_multiple_folders(tmpdir: Path) -> None:
    FOLDER_COUNT = 3

    for i in range(FOLDER_COUNT):
        node_modules_dir = tmpdir / str(i) / f"node_modules"
        node_modules_dir.mkdir(parents=True, exist_ok=True)

    node_modules_dirs = list(find_node_modules_dirs(tmpdir))

    assert len(node_modules_dirs) == FOLDER_COUNT

    found = [False] * FOLDER_COUNT

    # folders can be found in any order
    for dir in node_modules_dirs:
        found[int(dir.name)] = True

    assert all(found)


def test_find_node_modules_in_empty_folder(tmpdir: Path) -> None:
    node_modules_dirs = list(find_node_modules_dirs(tmpdir))

    assert len(node_modules_dirs) == 0


def test_find_node_modules_in_nested_folder(tmpdir: Path) -> None:
    node_modules_dir = tmpdir / "nested" / "node_modules"
    node_modules_dir.mkdir(parents=True, exist_ok=True)

    node_modules_dirs = list(find_node_modules_dirs(tmpdir))

    assert len(node_modules_dirs) == 1

    assert node_modules_dirs[0].name == "nested"


def test_find_node_modules_ingnores_nested_node_modules(tmpdir: Path) -> None:
    nested_node_modules_dir = tmpdir / "node_modules" / "node_modules" / "node_modules"
    nested_node_modules_dir.mkdir(parents=True, exist_ok=True)

    node_modules_dirs = list(find_node_modules_dirs(tmpdir))

    assert len(node_modules_dirs) == 1

    assert node_modules_dirs[0].name == tmpdir.name


def test_find_node_modules_dirs_ignores_dot_folders_by_default(tmpdir: Path) -> None:
    dot_node_modules = tmpdir / ".dot" / "node_modules"
    dot_node_modules.mkdir(parents=True, exist_ok=True)

    node_modules_dirs = list(find_node_modules_dirs(tmpdir))

    assert len(node_modules_dirs) == 0


def test_find_node_modules_dirs_does_not_ignore_dot_folders(tmpdir: Path) -> None:
    dot_node_modules = tmpdir / ".dot" / "node_modules"
    dot_node_modules.mkdir(parents=True, exist_ok=True)

    node_modules_dirs = list(find_node_modules_dirs(tmpdir, ignore_dot=False))

    assert len(node_modules_dirs) == 1

    assert node_modules_dirs[0].name == ".dot"


def test_find_node_modules_dirs_ignores_folders_in_ignore_set(
    tmpdir: Path,
) -> None:
    node_modules_dir = tmpdir / "AppData" / "node_modules"
    node_modules_dir.mkdir(parents=True, exist_ok=True)

    node_modules_dirs = list(find_node_modules_dirs(tmpdir, ignore_set={"AppData"}))

    assert len(node_modules_dirs) == 0


def test_find_node_modules_itertor(tmpdir: Path) -> None:
    node_modules_dir = tmpdir / f"node_modules"
    node_modules_dir.mkdir(parents=True, exist_ok=True)

    node_modules_dirs_iter = find_node_modules_dirs(tmpdir)

    assert isinstance(node_modules_dirs_iter, Iterator)


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


@pytest.mark.skipif("nt" == os.name, reason="Windows does not support symlinks")
def test_remove_node_modules_ignores_symlinks(tmpdir: Path) -> None:
    node_modules_dir = tmpdir / "node_modules"
    node_modules_dir.mkdir(parents=True, exist_ok=True)
    hello = node_modules_dir / "hello"
    hello.touch()
    hello.write_text("a" * 1024)

    ignored_dir = tmpdir / "ignored_dir"
    ignored_dir.mkdir(parents=True, exist_ok=True)

    symlink = node_modules_dir / "symlink"
    symlink.symlink_to(ignored_dir)
    symlink.touch()

    assert symlink.is_symlink()

    ignored_file = symlink / "ignored_file"
    ignored_file.touch()
    ignored_file.write_text("a" * 1024)

    remove_node_modules(tmpdir)

    assert not node_modules_dir.exists()

    assert ignored_dir.exists()


@pytest.mark.skipif("nt" != os.name, reason="Windows specific test")
def test_remove_node_modules_ignores_junctions(tmpdir: Path) -> None:
    node_modules_dir = tmpdir / "node_modules"
    node_modules_dir.mkdir(parents=True, exist_ok=True)
    hello = node_modules_dir / "hello"
    hello.touch()
    hello.write_text("a" * 1024)

    ignored_dir = tmpdir / "ignored_dir"
    ignored_dir.mkdir(parents=True, exist_ok=True)

    ignored_file = ignored_dir / "ignored_file"
    ignored_file.touch()
    ignored_file.write_text("a" * 1024)

    _winapi.CreateJunction(str(ignored_dir), str(node_modules_dir / "junction"))

    remove_node_modules(tmpdir)

    assert not node_modules_dir.exists()

    assert ignored_dir.exists()


def test_calculate_size(tmpdir: Path) -> None:
    node_modules_dir = tmpdir / f"node_modules"
    node_modules_dir.mkdir(parents=True, exist_ok=True)

    # file with 1 KB of data
    file = node_modules_dir / "file.txt"
    file.touch()
    file.write_text("a" * 1024, encoding="ASCII")

    size = calculate_size(tmpdir)

    assert size == pytest.approx(1 / 1024, 0.0001)


def test_calculate_size_with_multiple_files(tmpdir: Path) -> None:
    node_modules_dir = tmpdir / f"node_modules"
    node_modules_dir.mkdir(parents=True, exist_ok=True)

    # file with 1 KB of data
    file = node_modules_dir / "file.txt"
    file.touch()
    file.write_text("a" * 1024, encoding="ASCII")

    # file with 2 KB of data
    file = node_modules_dir / "file2.txt"
    file.touch()
    file.write_text("a" * 2048, encoding="ASCII")

    size = calculate_size(tmpdir)

    assert size == pytest.approx(3 / 1024, 0.0001)


def test_calculate_size_with_nested_folders(tmpdir: Path) -> None:
    node_modules_dir = tmpdir / "nested" / "node_modules"
    node_modules_dir.mkdir(parents=True, exist_ok=True)

    # file with 1 KB of data
    file = node_modules_dir / "file.txt"
    file.touch()
    file.write_text("a" * 1024, encoding="ASCII")

    size = calculate_size(tmpdir)

    assert size == pytest.approx(1 / 1024, 0.0001)


def test_calculate_size_with_multiple_folders(tmpdir: Path) -> None:
    FOLDER_COUNT = 3

    for i in range(FOLDER_COUNT):
        node_modules_dir = tmpdir / str(i) / "node_modules"
        node_modules_dir.mkdir(parents=True, exist_ok=True)

        # file with 1 KB of data
        file = node_modules_dir / "file.txt"
        file.touch()
        file.write_text("a" * 1024, encoding="ASCII")

    size = calculate_size(tmpdir)

    assert size == pytest.approx(3 / 1024, 0.0001)


@pytest.mark.skipif("nt" == os.name, reason="Windows does not support symlinks")
def test_calculate_size_dont_follow_symlinks(tmpdir: Path) -> None:
    """
    Test to make sure that pnpm links are not included in the size calculation.
    """
    node_modules_dir = tmpdir / "node_modules"
    node_modules_dir.mkdir(parents=True, exist_ok=True)
    hello = node_modules_dir / "hello"
    hello.touch()
    hello.write_text("a" * 1024)

    # dir outside of scanned folder
    ignored_dir = tmpdir / "ignored_dir"
    ignored_dir.mkdir(parents=True, exist_ok=True)

    symlink = node_modules_dir / "symlink"
    symlink.symlink_to(ignored_dir)
    symlink.touch()

    assert symlink.is_symlink()

    ignored_file = symlink / "ignored_file"
    ignored_file.touch()
    ignored_file.write_text("a" * 1024)

    size = calculate_size(node_modules_dir)

    assert size == pytest.approx(1 / 1024, 0.0001)


def test_calculate_size_raises_error_on_non_existing_folder(tmpdir: Path) -> None:
    invalid_path = tmpdir / "invalid_path"
    with pytest.raises(FileNotFoundError):
        calculate_size(invalid_path)


@pytest.mark.skipif("nt" != os.name, reason="Windows specific test")
def test_calculate_size_ignores_windows_junctions(tmpdir: Path) -> None:
    node_modules_dir = tmpdir / "node_modules"
    node_modules_dir.mkdir(parents=True, exist_ok=True)
    hello = node_modules_dir / "hello"
    hello.touch()
    hello.write_text("a" * 1024)

    ignored_dir = tmpdir / "ignored_dir"
    ignored_dir.mkdir(parents=True, exist_ok=True)

    ignored_file = ignored_dir / "ignored_file"
    ignored_file.touch()
    ignored_file.write_text("a" * 1024)

    _winapi.CreateJunction(str(ignored_dir), str(node_modules_dir / "junction"))

    size = calculate_size(node_modules_dir)

    assert size == pytest.approx(1 / 1024, 0.0001)
