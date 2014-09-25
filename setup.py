from setuptools import setup, find_packages

setup(
    name="besnappy",
    version="0.1.0",
    url='http://github.com/westerncapelabs/besnappy',
    license='BSD',
    description="An unofficial client library for the BeSnappy HTTP API.",
    long_description=open('README.rst', 'r').read(),
    author='Western Cap Labs',
    author_email='devops@westerncapelabs.com',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'requests>=2',
    ],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: POSIX',
        'Programming Language :: Python',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: System :: Networking',
    ],
)
