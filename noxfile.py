from nox import parametrize, session


@session
@parametrize(
    "python,pydantic",
    [
        (python, pydantic)
        for python in ("3.10", "3.11", "3.7", "3.8", "3.9")
        for pydantic in ("1.9", "1.10", "1.7", "1.8")
        if (python, pydantic) not in (("3.10", "1.7"), ("3.10", "1.8"))
    ],
)
def tests(session, python, pydantic):
    session.install(f"pydantic=={pydantic}")
    session.install("pytest", "pytest-cov", ".")
    session.run(
        "pytest", "-v", "tests/", "--cov-report=term-missing", "--cov=graphene_pydantic"
    )
