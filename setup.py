import setuptools
import os
import io

with io.open("README.md", encoding="utf-8") as f:
    long_description = f.read().strip()

version = None
with io.open(os.path.join("itunessmart", "__init__.py"), encoding="utf-8") as f:
    for line in f:
        if line.strip().startswith("__version__"):
            version = line.split("=")[1].strip().replace('"', "").replace("'", "")
            break

setuptools.setup(
    name="itunessmart",
    version=version,
    license="MIT",
    author="cuzi",
    author_email="cuzi@openmail.cc",
    description="Decode iTunes Smart playlist rules. Convert iTunes smart playlists to Kodi xsp smart playlists.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/cvzi/itunes_smartplaylist",
    packages=["itunessmart"],
    package_dir={"itunessmart": "itunessmart"},
    zip_safe=True,
    test_suite="nose.collector",
    tests_require=["nose"],
    classifiers=(
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "License :: OSI Approved :: MIT License",
        "Operating System :: MacOS :: MacOS X",
        "Operating System :: Microsoft :: Windows",
        "Topic :: Multimedia :: Sound/Audio",
        "Topic :: Multimedia :: Sound/Audio :: Players"
    )
)
