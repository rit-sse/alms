from setuptools import setup, find_packages


setup(
    name='alms',
    version='0.2.0',
    packages=find_packages(),
    entry_points={
        'console_scripts':
            ['alms=src.main:main']
    }
)
