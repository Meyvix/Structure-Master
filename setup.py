"""
Stracture-Master - Setup Configuration
A comprehensive tool for project structure analysis, generation, and documentation.
"""

from setuptools import setup, find_packages
import os

# Read requirements
def read_requirements():
    req_path = os.path.join(os.path.dirname(__file__), 'requirements.txt')
    with open(req_path, 'r', encoding='utf-8') as f:
        requirements = []
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                # Handle platform-specific dependencies
                if ';' in line:
                    requirements.append(line)
                else:
                    requirements.append(line)
        return requirements

# Read README for long description
def read_readme():
    readme_path = os.path.join(os.path.dirname(__file__), 'README.md')
    if os.path.exists(readme_path):
        with open(readme_path, 'r', encoding='utf-8') as f:
            return f.read()
    return ''

setup(
    name='Stracture-Master',
    version='1.0.0',
    author='Stracture-Master Team',
    author_email='info@Stracture-Master.dev',
    description='A comprehensive tool for project structure analysis, generation, and documentation',
    long_description=read_readme(),
    long_description_content_type='text/markdown',
    url='https://github.com/Stracture-Master/Stracture-Master',
    packages=find_packages(where='src'),
    package_dir={'': 'src'},
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Build Tools',
        'Topic :: Software Development :: Documentation',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Operating System :: OS Independent',
        'Environment :: Console',
        'Environment :: X11 Applications :: Qt',
        'Environment :: Web Environment',
    ],
    python_requires='>=3.9',
    install_requires=read_requirements(),
    extras_require={
        'dev': [
            'pytest>=7.4.0',
            'pytest-cov>=4.1.0',
            'black>=23.0.0',
            'flake8>=6.0.0',
            'mypy>=1.5.0',
        ],
        'docs': [
            'sphinx>=7.0.0',
            'sphinx-rtd-theme>=1.3.0',
        ],
    },
    entry_points={
        'console_scripts': [
            'Stracture-Master=cli.cli:main',
            'sm=cli.cli:main',
        ],
        'gui_scripts': [
            'Stracture-Master-gui=gui.main_window:main',
        ],
    },
    include_package_data=True,
    package_data={
        '': ['*.json', '*.yaml', '*.yml', '*.html', '*.css', '*.js'],
    },
    zip_safe=False,
    keywords=[
        'project-structure',
        'documentation',
        'code-analysis',
        'file-extraction',
        'structure-builder',
        'project-scanner',
    ],
    project_urls={
        'Bug Reports': 'https://github.com/Stracture-Master/Stracture-Master/issues',
        'Documentation': 'https://Stracture-Master.readthedocs.io/',
        'Source': 'https://github.com/Stracture-Master/Stracture-Master',
    },
)
