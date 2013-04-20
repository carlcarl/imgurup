from setuptools import setup

setup(
    name='imgur-upload',
    description='Upload to imgur using API(v3). Support authorization, CLI and KDE dialog upload',
    long_description=open('README.rst').read(),
    version='0.0.2',
    author='carlcarl',
    author_email='carlcarlking@gmail.com',
    url='https://github.com/carlcarl/imgur-upload',
    packages=[],
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
