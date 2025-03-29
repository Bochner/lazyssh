#!/usr/bin/env python3
"""
LazySSH - A comprehensive SSH toolkit for managing connections and tunnels.
"""
from setuptools import setup, find_packages

# Get the long description from the README file
with open("README.md", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="lazyssh",
    version="1.1.1",
    author="Bochner",
    author_email="lazyssh@example.com",
    description="A comprehensive SSH toolkit for managing connections and tunnels",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Bochner/lazyssh",
    project_urls={
        "Bug Tracker": "https://github.com/Bochner/lazyssh/issues",
        "Documentation": "https://github.com/Bochner/lazyssh",
        "Source Code": "https://github.com/Bochner/lazyssh",
    },
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    python_requires=">=3.11",
    entry_points={
        "console_scripts": [
            "lazyssh=lazyssh.__main__:main",
        ],
    },
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: System Administrators",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.11",
        "Operating System :: POSIX :: Linux",
        "Environment :: Console",
        "Topic :: System :: Networking",
        "Topic :: System :: Systems Administration",
    ],
    keywords="ssh, tunnel, proxy, socks, terminal, connection, management",
)