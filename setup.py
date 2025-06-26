from setuptools import setup, find_packages


def get_readme():
    with open("./readme.md", 'r') as file:
        return file.read()


setup(
    name="AVPlay",
    version="1.1.1",
    description="Audio and video playback library",
    long_description=get_readme(),
    long_description_content_type='text/markdown',
    url='https://github.com/still-standing88/av-play/',
    license='MIT',
    author="still-standing88",
    packages=find_packages(),
    entry_points={
    },
    install_requires=["python-mpv", "python-vlc", "pyfmodex", "validators", "music-tag"],
    python_requires=">=3.6",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Topic :: Software Development :: Documentation",
        "Topic :: Utilities",
    ],
    keywords="av-play AVPlay audio video media playback",
)
