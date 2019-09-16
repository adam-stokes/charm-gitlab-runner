#!/usr/bin/python3
"""Provide test fixtures for unit tests."""
import mock

import pytest


# If layer options are used, add this to layergitlabrunner
# and import layer in libgitlabrunner
@pytest.fixture
def mock_layers(monkeypatch):
    """Mock charm layer configuration."""
    import sys

    sys.modules["charms.layer"] = mock.Mock()
    sys.modules["reactive"] = mock.Mock()
    # Mock any functions in layers that need to be mocked here

    def options(layer):
        # mock options for layers here
        if layer == "example-layer":
            options = {"port": 9999}
            return options
        else:
            return None

    monkeypatch.setattr("libgitlabrunner.layer.options", options)


@pytest.fixture
def mock_hookenv_config(monkeypatch):
    """Mock the charm configuration with default values."""
    import yaml

    def mock_config():
        cfg = {}
        yml = yaml.safe_load(open("./config.yaml"))

        # Load all defaults
        for key, value in yml["options"].items():
            cfg[key] = value["default"]

        # Manually add cfg from other layers
        # cfg['my-other-layer'] = 'mock'
        return cfg

    monkeypatch.setattr("libgitlabrunner.hookenv.config", mock_config)


@pytest.fixture
def mock_remote_unit(monkeypatch):
    """Mock the remote unit data."""
    monkeypatch.setattr("libgitlabrunner.hookenv.remote_unit", lambda: "unit-mock/0")


@pytest.fixture
def mock_charm_dir(monkeypatch):
    """Mock the charm directory location."""
    monkeypatch.setattr("libgitlabrunner.hookenv.charm_dir", lambda: "/mock/charm/dir")


@pytest.fixture
def mock_service(monkeypatch):
    """Mock the service function in the charmhelpers host library."""
    mocked_service = mock.Mock(returnvalue=True)
    monkeypatch.setattr("libgitlabrunner.service", mocked_service)
    return mocked_service


@pytest.fixture
def mock_apt_install(monkeypatch):
    """Mock the charmhelper fetch apt_install method."""
    mocked_apt_install = mock.Mock(returnvalue=True)
    monkeypatch.setattr("libgitlabrunner.apt_install", mocked_apt_install)
    return mocked_apt_install


@pytest.fixture
def mock_apt_update(monkeypatch):
    """Mock the charmhelpers fetch apt_update method."""
    mocked_apt_update = mock.Mock(returnvalue=True)
    monkeypatch.setattr("libgitlabrunner.apt_update", mocked_apt_update)
    return mocked_apt_update


@pytest.fixture
def mock_add_source(monkeypatch):
    """Mock the charmhelpers fetch add_source method."""
    def print_add_source(line, key):
        print("Mocked add source: {} ({})".format(line, key))
        return True

    mocked_add_source = mock.Mock()
    mocked_add_source.get.side_effect = print_add_source
    monkeypatch.setattr("libgitlabrunner.add_source", mocked_add_source)
    return mocked_add_source


@pytest.fixture
def mock_get_distrib_codename(monkeypatch):
    """Mock the distribution codename as returned by get_destrib_codename."""
    mocked_get_distrib_codename = mock.Mock(returnvalue="bionic")
    monkeypatch.setattr("libgitlabrunner.get_distrib_codename", mocked_get_distrib_codename)
    return mocked_get_distrib_codename


@pytest.fixture
def mock_check_call(monkeypatch):
    """Mock check_call to mock process executions."""
    def print_check_call(args, *, kwargs={}):
        print(args)
        return True

    mocked_check_call = mock.Mock()
    mocked_check_call.get.side_effect = print_check_call
    monkeypatch.setattr("libgitlabrunner.subprocess.check_call", mocked_check_call)
    return mocked_check_call


@pytest.fixture
def mock_log(monkeypatch):
    """Mock charm log functionality."""
    mocked_log = mock.Mock()
    monkeypatch.setattr("libgitlabrunner.hookenv.log", mocked_log)
    return mocked_log


@pytest.fixture
def mock_gethostname(monkeypatch):
    """Mock gethostname to return consistent hostnames during testing."""
    mocked_gethostname = mock.Mock(returnvalue='mocked-hostname')
    monkeypatch.setattr("libgitlabrunner.gethostname",
                        mocked_gethostname)
    return mocked_gethostname


@pytest.fixture
def mock_action_set(monkeypatch):
    """Mock action_set to facilitate testing of action results."""
    mocked_action_set = mock.Mock(returnvalue=True)
    monkeypatch.setattr("charmhelpers.core.hookenv.action_set", mocked_action_set)
    return mocked_action_set


@pytest.fixture
def mock_action_fail(monkeypatch):
    """Mock action_fail to facilitate testing of action failure."""
    mocked_action_fail = mock.Mock()
    monkeypatch.setattr("charmhelpers.core.hookenv.action_fail", mocked_action_fail)
    return mocked_action_fail


@pytest.fixture
def gitlabrunner(tmpdir, mock_hookenv_config, mock_charm_dir, monkeypatch):
    """Mock the GitLab runner helper module used throughout the charm."""
    from libgitlabrunner import GitLabRunner

    glr = GitLabRunner()

    # Example config file patching
    cfg_file = tmpdir.join("example.cfg")
    with open("./tests/unit/example.cfg", "r") as src_file:
        cfg_file.write(src_file.read())
    glr.example_config_file = cfg_file.strpath

    # Any other functions that load helper will get this version
    monkeypatch.setattr("libgitlabrunner.GitLabRunner", lambda: glr)

    return glr
