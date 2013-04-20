from setuptools import setup

setup(
    name='imgur-upload',
    description='',
    long_description=open('README.md').read(),
    version='0.0.1',
    author='carlcarl',
    author_email='carlcarlking@gmail.com',
    url='https://github.com/carlcarl/imgur-upload',
    packages=[''],
    license='MIT',
    entry_points={
        'console_scripts': [
            'img = imgur_upload:main',
        ]
    },

    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: End Users/Desktop',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
        'Operating System :: MacOS :: MacOS X',
        'Operating System :: POSIX',
        'Operating System :: Unix',
        'Topic :: Utilities',
        'Topic :: Software Development :: Libraries',
    ]
)
