import sys
from nox import parametrize, session


@session
@parametrize(
    "pydantic",
    (
        (2, 0),
        (2, 1),
        (2, 2),
        (2, 3),
        (2, 4),
        (2, 5),
        (2, 6),
        (2, 7),
        (2, 8),
        (2, 9),
        (2, 10),
    ),
)
@parametrize("graphene", ("2.1.8", "2.1.9", "3.0", "3.1", "3.2", "3.3", "3.4"))
def tests(session, pydantic, graphene):
    if sys.version_info > (3, 10) and pydantic in ((1, 7), (1, 8)):
        return session.skip()
    if sys.version_info > (3, 10) and graphene <= "3":
        return session.skip()
    if sys.version_info > (3, 11) and pydantic < (2, 9):
        return session.skip()
    pydantic_version_string = ".".join([str(n) for n in pydantic])
    session.install(f"pydantic=={pydantic_version_string}")
    session.install(f"graphene=={graphene}")
    session.install("pytest", "pytest-cov", ".")
    session.run(
        "pytest", "-v", "tests/", "--cov-report=term-missing", "--cov=graphene_pydantic"
    )
