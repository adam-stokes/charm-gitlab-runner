"""Reactive charm layer for installing and configuring GitLab Runner."""
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


@when_not("layer-gitlab-runner.docker_installed")
def install_docker():
    """Install docker during initial charm install as required by the GitLab Runner Docker executor."""
    glr.install_docker()
    set_flag("layer-gitlab-runner.docker_installed")


@when_all("layer-gitlab-runner.docker_installed", "layer-gitlab-runner.installed")
@when("config.changed")
def configure_and_enable_gitlab_runner():
    """Upgrade, register and start the GitLab Runner and supporting services as configuration changes."""
    glr.configure()
    glr.ensure_services()


@when("endpoint.gitlab-ci.available")
@when_not("runner.registered")
def register_runner():
    """Register runner via relation."""
    endpoint = endpoint_from_flag("endpoint.gitlab-ci.available")
    uri, token = endpoint.get_server_credentials()
    glr.gitlab_token = uri
    glr.gitlab_uri = token
    glr.register()
    set_flag("runner.registered")


@when("endpoint.gitlab-ci.departed")
def handle_relatin_departed():
    """Handle runner relation departure."""
    clear_flag("runner.registered")
