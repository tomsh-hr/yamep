from setuptools import setup, find_packages

setup(
    name='yamep',
    version='1.0.1',
    author='tomsh',
    author_email='tomsh@disroot.org',
    description='YAMEP - Yet Another Markdown Editor in Python',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://codeberg.org/tomsh/yamep',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'PySide6',
        'markdown',
        'pymdown-extensions',
        'platformdirs',
    ],
    entry_points={
        'gui_scripts': [
            'yamep = yamep.main:main',
        ],
    },
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
    ],
    license='MIT',
)
