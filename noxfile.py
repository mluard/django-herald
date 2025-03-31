import nox

nox.options.sessions = ["format", "lint", "test", "coverage"]
nox.options.default_venv_backend = "uv"

# Define version matrices
PYTHON_VERSIONS = ["3.8", "3.10", "3.12", "3.13", "3.14"]
DJANGO_VERSIONS = ["4.2", "5.0", "5.1", "5.2-rc"]
TWILIO_VERSIONS = ["6.0.0", "9.5.1"]
HTML2TEXT_VERSIONS = ["2019.8.11", "2024.2.26"]

# Python/Django compatibility constraints
DJANGO_PYTHON_COMPATIBILITY = {
    "4.2": ["3.8", "3.12"],
    "5.0": ["3.10", "3.13"],
    "5.1": ["3.10", "3.13"],
    "5.2-rc": ["3.10", "3.11", "3.12", "3.13", "3.14"],
}


@nox.session(python=PYTHON_VERSIONS)
@nox.parametrize("django", DJANGO_VERSIONS)
@nox.parametrize("twilio", TWILIO_VERSIONS)
@nox.parametrize("html2text", HTML2TEXT_VERSIONS)
def test(session, django, twilio, html2text):
    """Run tests with all dependencies installed."""

    # Skip incompatible Python/Django combinations
    if session.python not in DJANGO_PYTHON_COMPATIBILITY.get(django, []):
        session.skip(f"Django {django} not compatible with Python {session.python}")

    # Create a unique coverage data file for parallel runs
    session_id = f"py{session.python}-django{django}-twilio{twilio}-html2text{html2text}".replace(
        ".", "_"
    )
    coverage_file = f".coverage.{session_id}"

    # Install base dependencies
    session.install("coverage", "pytest", "jsonpickle")

    # Install Django with appropriate version
    try:
        if django.endswith("-rc"):
            base_version = django.replace("-rc", "")
            session.install(f"django>={base_version}rc,<{float(base_version) + 0.1}")
        else:
            session.install(f"django~={django}.0")
    except Exception as e:
        session.error(f"Failed to install Django {django}: {e}")

    # Install Twilio with appropriate version
    try:
        session.install(f"twilio=={twilio}")
    except Exception as e:
        session.error(f"Failed to install Twilio {twilio}: {e}")

    # Install html2text with appropriate version
    try:
        session.install(f"html2text=={html2text}")
    except Exception as e:
        session.error(f"Failed to install html2text {html2text}: {e}")

    # Enable html2text for tests
    session.env["HERALD_HTML2TEXT_ENABLED"] = "1"

    # Install herald in development mode
    session.install("-e", ".")

    # Run the tests with unique coverage file
    session.run(
        "coverage", "run", f"--data-file=.coverage-data/{coverage_file}", "--source=herald", "runtests.py"
    )


@nox.session
def lint(session):
    """Run the linter."""
    session.install("ruff")
    session.run("ruff", "check", ".")


@nox.session
def format(session):
    """Run the formatter."""
    session.install("ruff")
    session.run("ruff", "format", "--check", ".")


@nox.session
def coverage(session):
    """Report test coverage by combining data from parallel runs."""
    session.install("coverage")
    
    # Combine all coverage data files
    session.run("coverage", "combine", "--keep", ".coverage-data/.coverage.*", silent=True)
    
    # Generate reports
    session.run("coverage", "report", "--show-missing")
    session.run("coverage", "html")


# Session for running tests against Django 4.2
@nox.session(python="3.8", tags=["manual"])
def django42(session):
    """Run a quick test with default versions for development against Django 4.2"""
    session.install("django~=4.2.0")
    _quick_test(session)


# Session for running tests against Django 5.2
@nox.session(python="3.10", tags=["manual"])
def django52(session):
    """Run a quick test with default versions for development against Django 5.2"""
    # session.install("django~=5.2.0")
    session.install(f"django>=5.2.0rc,<5.2.1")
    _quick_test(session)


def _quick_test(session):
    """Run quick tests with python and django versions already installed in the session"""
    session.install("coverage", "pytest", "jsonpickle")
    session.install("twilio==9.5.1")
    session.install("html2text==2024.2.26")
    session.env["HERALD_HTML2TEXT_ENABLED"] = "1"
    session.install("-e", ".")
    session.run("coverage", "run", "--source=herald", "runtests.py")
