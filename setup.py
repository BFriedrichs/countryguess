import setuptools
import re

def get_long_description():
    with open('README.md', 'r') as f:
        return f.read()

def get_var(name):
    with open('countryguess/__init__.py') as f:
        content = f.read()
        match = re.search(rf'''^{name}\s*=\s*['"]([^'"]*)['"]''',
                          content, re.MULTILINE)
        if match:
            return match.group(1)
        else:
            raise RuntimeError(f'Unable to find {name}')


setuptools.setup(
    name=get_var('__project_name__'),
    version=get_var('__version__'),
    author=get_var('__author__'),
    author_email=get_var('__author_email__'),
    description=get_var('__description__'),
    url=get_var('__homepage__'),
    long_description=get_long_description(),
    long_description_content_type='text/markdown',
    packages=setuptools.find_packages(),
    classifiers=[
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
    ],
    python_requires='>=3.8',
    install_requires=[
    ],
    package_data={
        get_var('__project_name__'): [
            '_countrydata.json',
        ]
    },
    entry_points={'console_scripts': ['countryguess = countryguess._cli:run']},
)
