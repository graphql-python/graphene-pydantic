import sys
from nox import parametrize, session


@session
@parametrize(
    "pydantic",
    ("1.9", "1.10", "1.7", "1.8"),
)
@parametrize("graphene", ("2.1.9", "3"))
def tests(session, pydantic, graphene):
    if sys.version_info > (3, 10) and pydantic in ("1.7", "1.8"):
        return session.skip()
    if sys.version_info > (3, 10) and graphene != "3":
        # Graphene 2.x doesn't support Python 3.11
        return session.skip()
    session.install(f"pydantic=={pydantic}")
    session.install(f"graphene=={graphene}")
    session.install("pytest", "pytest-cov", ".")
    session.run(
        "pytest", "-v", "tests/", "--cov-report=term-missing", "--cov=graphene_pydantic"
    )
