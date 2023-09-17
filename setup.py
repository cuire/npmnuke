from setuptools import find_packages, setup

from npmnuke import __version__

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
