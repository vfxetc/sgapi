from setuptools import setup, find_packages

setup(

    name='sgapi',
    version='0.1-dev',
    description='Low-level Shotgun API',
    url='http://github.com/westernx/sgapi',
    
    packages=find_packages(exclude=['build*', 'tests*']),
    
    author='Mike Boers',
    author_email='sgapi@mikeboers.com',
    license='BSD-3',
    
    install_requires=[
        'requests',
    ],

    classifiers=[
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
    
)
