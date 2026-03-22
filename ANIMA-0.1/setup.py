from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="anima-llm",
    version="0.1.0",
    author="Spyder Group",
    author_email="dev@spyderglobalgroup.com",
    description="Adaptive Neural Identity & Memory Architecture – emotional intelligence layer for LLMs",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/SpyderGroup/anima",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Intended Audience :: Developers",
    ],
    python_requires=">=3.9",
    install_requires=[
        "google-generativeai>=0.8.0",
    ],
    extras_require={
        "dev": ["pytest", "black", "ruff"]
    },
    entry_points={
        "console_scripts": [
            "anima=anima.cli:main",
        ]
    },
)
