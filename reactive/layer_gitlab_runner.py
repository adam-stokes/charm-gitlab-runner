"""Reactive charm layer for installing and configuring GitLab Runner."""
from charmhelpers.core import hookenv

from charms.reactive import (
    clear_flag,
    endpoint_from_flag,
    set_flag,
    when,
    when_all,
    when_not,
)

from libgitlabrunner import GitLabRunner

glr = GitLabRunner()


@when_not("layer-gitlab-runner.installed")
def install_gitlab_runner():
    """Run upgrade helper function when GitLab Runner has not been installed previously to perform initial install."""
    glr.upgrade()
    set_flag("layer-gitlab-runner.installed")


@when_not("layer-gitlab-runner.lxd_setup")
def setup_lxd_executor():
    """Set up custom executor scripts for lxd executor."""
    glr.setup_lxd()
    set_flag("layer-gitlab-runner.lxd_setup")


@when_not("layer-gitlab-runner.docker_installed")
def install_docker():
    """Install docker during initial charm install as required by the GitLab Runner Docker executor."""
    glr.install_docker()
    set_flag("layer-gitlab-runner.docker_installed")


@when_all(
    "layer-gitlab-runner.docker_installed",
    "layer-gitlab-runner.installed",
    "layer-gitlab-runner.lxd_setup",
)
@when("config.changed")
def configure_and_enable_gitlab_runner():
    """Upgrade, register and start the GitLab Runner and supporting services as configuration changes."""
    glr.configure()
    glr.ensure_services()


@when("endpoint.runner.available")
@when_not("runner.registered")
def register_runner():
    """Register runner via relation."""
    endpoint = endpoint_from_flag("endpoint.runner.available")
    uri, token = endpoint.get_server_credentials()
    glr.gitlab_token = token
    glr.gitlab_uri = uri
    glr.kv.set("gitlab_token", token)
    glr.kv.set("gitlab_uri", uri)
    hookenv.log("Registering runner url/token: {}/{}".format(uri, token))
    glr.unregister()
    glr.register()
    set_flag("runner.registered")


@when("endpoint.runner.departed")
def handle_relatin_departed():
    """Handle runner relation departure."""
    clear_flag("runner.registered")
    glr.kv.set("gitlab_token", None)
    glr.kv.set("gitlab_uri", None)
    glr.unregister()
