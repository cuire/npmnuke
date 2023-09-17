from pathlib import Path

from setuptools import find_packages, setup

from npmnuke import __version__


def put_npmnukeignore_in_home_directory() -> None:
    try:
        with open(".npmnukeignore-template", "r") as f:
            template = f.read()

        ignore_file = Path.home() / ".npmnukeignore"
        if not ignore_file.exists():
            with open(ignore_file, "w") as f:
                f.write(template)

    except Exception as e:
        pass


setup(
    name="npmnuke",
    version=__version__,
    description="Remove all node_modules folders from a directory",
    long_description=Path("README.md").read_text(encoding="utf-8"),
    author="cuire",
    author_email="garwes@icloud.com",
    entry_points={"console_scripts": ["npmnuke=npmnuke.main:main"]},
    packages=find_packages(),
    install_requires=Path("requirements.txt").read_text(encoding="utf-8").split("\n"),
    python_requires=">=3.10",
)

put_npmnukeignore_in_home_directory()
