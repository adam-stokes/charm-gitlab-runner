from libgitlabrunner import GitLabRunner
from charms.reactive import set_flag, when_not, when

glr = GitLabRunner()


@when_not('layer-gitlab-runner.installed')
def install_gitlab_runner():
    glr.upgrade()
    set_flag('layer-gitlab-runner.installed')


@when('layer-gitlab-runner.installed')
@when('config.changed')
def configure_gitlab_runner():
    glr.configure()
