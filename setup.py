#!/usr/bin/env python3
"""
Setup script for ESO Builds Tool.
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read the README file
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()

# Read requirements
requirements = []
with open("requirements.txt", "r") as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith("#"):
            requirements.append(line)

setup(
    name="eso-builds",
    version="1.0.0",
    author="Christopher Gentle",
    description="ESO Logs report analyzer and build tracker",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.9",
    install_requires=requirements,
    extras_require={
        "dev": [
            "flake8>=6.0.0",
            "mypy>=1.0.0",
            "pytest>=7.0.0",
            "black>=23.0.0",
            "isort>=5.12.0",
        ]
    },
    entry_points={
        "console_scripts": [
            "eso-builds=single_report_tool:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    keywords="eso elder-scrolls-online logs analysis builds",
    project_urls={
        "Bug Reports": "https://github.com/yourusername/eso-builds/issues",
        "Source": "https://github.com/yourusername/eso-builds",
    },
)
