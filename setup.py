import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="padtexturetool",
    version="1.0.0",
    author="Cody Watts and Aradia",
    author_email="69992611+chasehult@users.noreply.github.com",
    license="MIT",
    description="A tool to extract textures from PAD",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/chasehult/padtexturetool",
    packages=setuptools.find_packages(),
    install_requires=[
        "pypng==0.0.20"
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.8',
)
