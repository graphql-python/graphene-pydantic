from setuptools import find_packages, setup

requirements = [
    # To keep things simple, we only support newer versions of Graphene
    "graphene>=2.1.3,<3",
    # Same for Pydantic
    "pydantic>=0.25,<0.30",
]

dev_requirements = [
    "tox==3.7.0",  # Should be kept in sync with tox.ini
    "mypy==0.720",
    "black==19.3b0",
    "pre-commit==1.14.4",
]
test_requirements = ["pytest==4.6.3", "pytest-cov==2.7.1"]

setup(
    name="graphene-pydantic",
    version="0.1",
    description="Graphene Pydantic integration",
    long_description=open("README.md").read(),
    url="https://github.com/upsidetravel/graphene-pydantic",
    author="Upside Travel",
    author_email="rami@upside.com",
    license="Apache",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: Implementation :: PyPy",
    ],
    keywords="api graphql protocol rest relay graphene pydantic model",
    packages=find_packages(exclude=["tests"]),
    install_requires=requirements,
    extras_require={"dev": dev_requirements, "test": test_requirements},
    tests_require=test_requirements,
)
