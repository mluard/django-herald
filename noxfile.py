import pathlib

import nox

nox.options.sessions = ["test", "coverage"]
nox.options.default_venv_backend = "uv"

# Define version matrices
# This matrix isn't exhaustive.  It hits the min and max python versions
# for each django version.  For the twilio and html2text versions, it
# runs against a versions that are several years old and the latest
# versions.  This should catch any breaking changes in the libraries
# that we depend on.
PYTHON_VERSIONS = ["3.8", "3.10", "3.12", "3.13", "3.14"]
DJANGO_VERSIONS = ["4.2", "5.0", "5.1", "5.2-rc"]
DEPENDECY_VERSIONS = [
    # There's no interdependency between these versions, so only
    # test and old and latest version of each, not every combination.
    {"twilio": "6.0.0", "html2text": "2019.8.11"},
    {"twilio": "9.5.1", "html2text": "2024.2.26"},
]

# Python/Django test combinations
DJANGO_PYTHON_MATRIX = {
    "4.2": ["3.8", "3.12"],
    "5.0": ["3.10", "3.13"],
    "5.1": ["3.10", "3.13"],
    "5.2-rc": ["3.10", "3.11", "3.12", "3.13", "3.14"],
}


def _coverage_path():
    path = pathlib.Path(".coverage-data")
    path.mkdir(exist_ok=True)
    return path


@nox.session(python=PYTHON_VERSIONS)
@nox.parametrize("django", DJANGO_VERSIONS)
@nox.parametrize("dependency_versions", DEPENDECY_VERSIONS)
def test(session, django, dependency_versions):
    """Run tests with all dependencies installed."""

    # Skip incompatible Python/Django combinations
    if session.python not in DJANGO_PYTHON_MATRIX.get(django, []):
        session.skip(f"Django {django} and Python {session.python} is not in the text matrix")

    # Create a unique coverage data file each parametrized run
    twilio = dependency_versions["twilio"]
    html2text = dependency_versions["html2text"]
    session_id = f"py{session.python}-django{django}-twilio{twilio}-html2text{html2text}".replace(
        ".", "_"
    )
    coverage_file = _coverage_path() / f".coverage.{session_id}"
    session.log(f"Coverage file: {coverage_file}")

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
    session.env["DJANGO_SETTINGS_MODULE"] = "tests.settings"

    # Install herald in development mode
    session.install("-e", ".")

    # Run the tests with unique coverage file
    session.run(
        "coverage",
        "run",
        f"--data-file={coverage_file}",
        "--source=herald",
        "runtests.py",
        "test",
    )


@nox.session
def lint(session):
    """Run the linter."""
    session.install("ruff")
    session.run("ruff", "check", ".")


@nox.session
def format(session):
    """Run the formatter, checking for changes without making them."""
    session.install("ruff")
    session.run("ruff", "format", "--check", ".")


@nox.session
def coverage(session):
    """Report test coverage by combining data from parallel runs."""
    # Install coverage with TOML support
    session.install("coverage[toml]")

    # Check if there are any coverage files
    if not list(_coverage_path().glob(".coverage.*")):
        session.log(f"No coverage data files found in {_coverage_path()}")
        return

    # Combine all coverage data files
    session.run("coverage", "combine", "--keep", _coverage_path())

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
@nox.session(python="3.14", tags=["manual"])
def django52(session):
    """Run a quick test with default versions for development against Django 5.2"""
    # Once Django 5.2 is released, use the following line:q
    # session.install("django~=5.2.0")
    session.install("django>=5.2.0rc,<5.2.1")
    _quick_test(session)


def _quick_test(session):
    session.install("coverage", "pytest", "jsonpickle")
    session.install("twilio==9.5.1")
    session.install("html2text==2024.2.26")
    session.env["HERALD_HTML2TEXT_ENABLED"] = "1"
    session.env["DJANGO_SETTINGS_MODULE"] = "tests.settings"
    session.install("-e", ".")
    session.run("python", "-Wd", "runtests.py", "test")
