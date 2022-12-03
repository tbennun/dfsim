from setuptools import find_packages, setup

with open("README.md", "r") as fp:
    long_description = fp.read()

setup(name='dfsim',
      version='1.0',
      url='https://github.com/tbennun/dfsim',
      author='Tal Ben-Nun',
      author_email='tbennun@gmail.com',
      description='Dataflow architecture simulator in Python',
      long_description=long_description,
      long_description_content_type='text/markdown',
      classifiers=[
          "Programming Language :: Python :: 3",
          "License :: OSI Approved :: BSD License",
          "Operating System :: OS Independent",
      ],
      python_requires='>=3.6',
      packages=find_packages(exclude=["*.tests", "*.tests.*", "tests.*", "tests"]),
      install_requires=[
          'numpy'
      ],
)
