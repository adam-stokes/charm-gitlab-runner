"""Reactive charm layer for installing and configuring GitLab Runner."""
from charms.reactive import set_flag, when, when_not

from libgitlabrunner import GitLabRunner

glr = GitLabRunner()


@when_not('layer-gitlab-runner.installed')
def install_gitlab_runner():
    """Run upgrade helper function when GitLab Runner has not been installed previously to perform initial install."""
    glr.upgrade()
    set_flag('layer-gitlab-runner.installed')


@when_not('layer-gitlab-runner.docker_installed')
def install_docker():
    """Install docker during initial charm install as required by the GitLab Runner Docker executor."""
    glr.install_docker()
    set_flag('layer-gitlab-runner.docker_installed')


@when('layer-gitlab-runner.installed')
@when('config.changed')
def configure_gitlab_runner():
    """Upgrade and register the GitLab Runner in response to configuration changes and charm upgrades."""
    glr.configure()
