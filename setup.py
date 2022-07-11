from distutils.core import setup

exec(open('src/nanocli/version.py').read())

setup(
    name='nanocli',
    version=__version__,
    packages=['nanocli'],
    package_dir={'nanocli': 'src/nanocli'},
    install_requires=[
        'pyserial',
        'numpy>=1.18',
    ],
    license='Creative Commons Attribution-Noncommercial-Share Alike license',
    long_description=open('README.md').read(),
    entry_points={
        'console_scripts': [
            'nanocli = nanocli:main',
        ]
    },
)
