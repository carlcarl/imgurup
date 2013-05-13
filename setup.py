from setuptools import setup
from setuptools import find_packages

setup(
    name='imgurup',
    description='Upload to imgur using API(v3). Support CLI, KDE and Mac dialog upload. And you can also use your account to upload :).',
    long_description=open('README.rst').read(),
    version='0.1.1',
    author='carlcarl',
    author_email='carlcarlking@gmail.com',
    url='https://github.com/carlcarl/imgurup',
    packages=find_packages(),
    license='MIT',
    entry_points={
        'console_scripts': [
            'img = imgurup:main',
        ]
    },

    classifiers=[
        'Development Status :: 4 - Beta',
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
