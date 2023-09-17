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

            # make file hidden

    except Exception as e:
        pass


setup(
    name="npmnuke",
    version=__version__,
    description="Remove all node_modules folders from a directory",
    author="cuire",
    author_email="garwes@icloud.com",
    entry_points={"console_scripts": ["npmnuke=npmnuke.main:main"]},
    packages=find_packages(),
    python_requires=">=3.10",
)

put_npmnukeignore_in_home_directory()
