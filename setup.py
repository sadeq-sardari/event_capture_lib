from setuptools import setup, find_packages


def get_requirements():
    with open("requirements.txt") as fp:
        return [x.strip() for x in fp.read().split("\n") if not x.startswith("#")]


install_requires = get_requirements()

setup(
    name="event_capture_lib",
    version="0.6.0",
    python_requires=">=3.9",
    packages=find_packages(),
    install_requires=install_requires,
)
