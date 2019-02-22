from setuptools import setup

setup(
    name='tough',
    version='0.1',
    author='Ovunc Cetin',
    author_email='ovunccetin@gmail.com',
    description='A fault tolerance library designed for Python.',
    license='Apache',
    packages=['toughpy'],
    extras_require={
        'dev': [
            'pytest>=3'
        ]
    },
    classifiers=[
        'Development Status :: 1 - Planning',
        'Topic :: Utilities',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7'
    ],
    setup_requires=['pytest-runner'],
    tests_require=['pytest', 'behave'],
    install_requires=['six']
)
