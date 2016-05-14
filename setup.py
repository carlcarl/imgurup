from setuptools import setup
from setuptools import find_packages

setup(
    name='imgurup',
    description='Upload to imgur using API(v3). Support CLI, KDE,Zenity(GTK) and Mac dialog upload. And you can also use your account to upload :).',
    long_description=open('README.rst').read(),
    version='1.7.0',
    author='carlcarl',
    author_email='carlcarlking@gmail.com',
    url='https://github.com/carlcarl/imgurup',
    packages=find_packages(),
    license='MIT',
    package_data={
        'imgurup': ['data/*'],
    },
    entry_points={
        'console_scripts': [
            'img = imgurup:main',
        ]
    },

    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: End Users/Desktop',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
        'Operating System :: MacOS :: MacOS X',
        'Operating System :: POSIX',
        'Operating System :: Unix',
        'Topic :: Utilities',
        'Topic :: Software Development :: Libraries',
    ],
)
