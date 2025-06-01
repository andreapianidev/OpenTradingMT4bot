#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Setup script for OpenMT4TradingBot Python components.
"""

from setuptools import setup, find_packages

setup(
    name="OpenMT4TradingBot",
    version="1.0.0",
    description="Python components for OpenMT4TradingBot - a hybrid MT4 + Python trading system",
    author="Immaginet Srl",
    author_email="info@immaginet.com",
    packages=find_packages(),
    install_requires=[
        "pandas>=2.0.0",
        "numpy>=1.20.0",
        "requests>=2.25.0",
        "schedule>=1.0.0",
        "pyarrow>=10.0.0",
        "python-dotenv>=1.0.0",
        "fastapi>=0.95.0",
        "uvicorn>=0.20.0",
        "pydantic>=2.0.0",
        "rich>=13.0.0",
    ],
    python_requires=">=3.8",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Financial and Insurance Industry",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
)
