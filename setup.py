from __future__ import annotations
from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name='caniscrape',
    version='1.0.0',
    author='Zaid Ahmed',
    author_email='zaahme18@gmail.com',
    description='Analyze website anti-bot protections before you scrape',
    long_description=long_description,
    long_description_content_type="text/markdown",
    url='https://github.com/ZA1815/caniscrape',
    packages=find_packages(),
    license='MIT',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Programming Language :: Python :: 3.13'
    ],
    python_requires='>=3.9',
    install_requires=[
        'click>=8.0.0',
        'rich>=13.0.0',
        'aiohttp>=3.8.0',
        'beautifulsoup4>=4.11.0',
        'playwright>=1.40.0',
        'curl-cffi>=0.5.0',
        'requests>=2.28.0',
        'aiohttp-socks>=0.7.0',
        'capsolver>=1.0.7',
        '2captcha-python>=1.5.1',
    ],
    entry_points={
        'console_scripts': [
            'caniscrape=caniscrape.cli:cli',
        ],
    },
)