"""Functional test of GitLab Runner installation and configuration."""
import os
import stat
import subprocess
import time

import pytest

# Treat all tests as coroutines
pytestmark = pytest.mark.asyncio

juju_repository = os.getenv("JUJU_REPOSITORY", ".").rstrip("/")
series = ["bionic"]
sources = [
    ("local", "{}/builds/gitlab-runner".format(juju_repository)),
    # ('jujucharms', 'cs:...'),
]


# Custom fixtures
@pytest.fixture(params=series)
def series(request):
    """Provide access to the series test parameter."""
    return request.param


@pytest.fixture(params=sources, ids=[s[0] for s in sources])
def source(request):
    """Provide access to the charm install source test parameter."""
    return request.param


@pytest.fixture
async def app(model, series, source):
    """Provide access to the current app test parameter."""
    app_name = "gitlab-runner-{}-{}".format(series, source[0])
    return await model._wait_for_new("application", app_name)


@pytest.mark.timeout(30)
@pytest.mark.deploy
async def test_gitlabrunner_deploy(model, series, source, request):
    """Deploy gitlab-runner."""
    # Starts a deploy for each series
    # Using subprocess b/c libjuju fails with JAAS
    # https://github.com/juju/python-libjuju/issues/221
    application_name = "gitlab-runner-{}-{}".format(series, source[0])
    cmd = [
        "juju",
        "deploy",
        source[1],
        "-m",
        model.info.name,
        "--series",
        series,
        application_name,
    ]
    if request.node.get_closest_marker("xfail"):
        cmd.append("--force")
    subprocess.check_call(cmd)


@pytest.mark.timeout(90)
@pytest.mark.deploy
async def test_gitlab_deploy(model):
    """Deploy gitlab bundle."""
    # Starts a deploy for each series
    # Using subprocess b/c libjuju fails with JAAS
    # https://github.com/juju/python-libjuju/issues/221
    cmd = [
        "juju",
        "deploy",
        "./tests/functional/gitlab.bundle",
        "-m",
        model.info.name,
    ]
    subprocess.check_call(cmd)


@pytest.mark.timeout(420)
@pytest.mark.deploy
async def test_charm_upgrade(model, app):
    """Upgrade the charmstore version of the charm to the locally installed one."""
    if app.name.endswith("local"):
        pytest.skip()  # No need to upgrade the local deploy
    unit = app.units[0]
    await model.block_until(lambda: unit.agent_status == "idle")
    subprocess.check_call(
        [
            "juju",
            "upgrade-charm",
            "--switch={}".format(sources[0][1]),
            "-m",
            model.info.name,
            app.name,
        ]
    )
    await model.block_until(lambda: unit.agent_status == "executing")


# Tests
@pytest.mark.timeout(900)
async def test_gitlabrunner_status(model, app):
    """Verify status of deployed unit."""
    # Verifies status for all deployed series of the charm
    await model.block_until(lambda: app.status == "blocked")
    unit = app.units[0]
    await model.block_until(lambda: unit.agent_status == "idle")


@pytest.mark.timeout(30)
async def test_register_action(app):
    """Test action for registering a runner."""
    unit = app.units[0]
    action = await unit.run_action("register")
    action = await action.wait()
    assert action.status == "failed"


@pytest.mark.timeout(30)
async def test_run_command(app, jujutools):
    """Test the running of a command on the unit with expected output."""
    unit = app.units[0]
    cmd = "hostname -i"
    results = await jujutools.run_command(cmd, unit)
    assert results["Code"] == "0"
    assert unit.public_address in results["Stdout"]


@pytest.mark.timeout(30)
async def test_file_stat(app, jujutools):
    """Test the contents of a file on the unit with expected contents."""
    unit = app.units[0]
    path = "/var/lib/juju/agents/unit-{}/charm/metadata.yaml".format(
        unit.entity_id.replace("/", "-")
    )
    fstat = await jujutools.file_stat(path, unit)
    assert stat.filemode(fstat.st_mode) == "-rw-r--r--"
    assert fstat.st_uid == 0
    assert fstat.st_gid == 0


@pytest.mark.timeout(900)
async def test_gitlab_status(model):
    """Verify status of supporting deploy."""
    # Verifies status of the gitlab deploy to test against
    redis = model.applications["redis"]
    postgresql = model.applications["postgresql"]
    gitlab = model.applications["gitlab"]
    count = 10
    while count > 0:
        await model.block_until(lambda: redis.status == "active")
        await model.block_until(lambda: postgresql.status == "active")
        await model.block_until(lambda: gitlab.status == "active")
        await model.block_until(lambda: gitlab.units[0].agent_status == "idle")
        count = count - 1
        time.sleep(1)


@pytest.mark.relate
@pytest.mark.timeout(120)
async def test_add_relation(model, app):
    """Verify the runner relation completes."""
    gitlab = model.applications["gitlab"]
    await model.block_until(lambda: gitlab.status == "active")
    await app.add_relation("runner", "gitlab:runner")
    await model.block_until(lambda: app.status == "active")
