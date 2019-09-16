"""GitLab Runner helper library for charm operations."""
import subprocess
from socket import gethostname

from charmhelpers.core import hookenv, unitdata
from charmhelpers.core.host import get_distrib_codename, service
from charmhelpers.fetch import add_source, apt_install, apt_update


class GitLabRunner:
    """Provide various charm helper methods to installing and configuring GitLab Runner."""

    def __init__(self):
        """Bootstrap the class."""
        self.charm_config = hookenv.config()
        self.kv = unitdata.kv()
        self.gitlab_token = False
        self.gitlab_uri = False
        self.hostname = gethostname()
        if self.charm_config["gitlab-token"]:
            self.gitlab_token = self.charm_config["gitlab-token"]
        if self.charm_config["gitlab-uri"]:
            self.gitlab_uri = self.charm_config["gitlab-uri"]

    def ensure_services(self):
        """Ensure services (docker, gitlab-runner) are enabled and running when installed and registered."""
        if self.kv.get("registered", False):
            service("enable", "docker")
            service("start", "docker")
            service("enable", "gitlab-runner")
            service("start", "gitlab-runner")

    def register(self):
        """Register this GitLab runner with the GitLab CI server."""
        if (
            self.gitlab_token
            and self.gitlab_uri
            and not self.kv.get("registered", False)
        ):
            hookenv.log("Registering GitLab runner with {}".format(self.gitlab_uri))
            hookenv.status_set("maintenance", "Registering with GitLab")
            command = [
                "/usr/bin/gitlab-runner",
                "register",
                "--non-interactive",
                "--url '{}'".format(self.gitlab_uri),
                "--registration-token '{}'".format(self.gitlab_token),
                "--name '{}'".format(self.hostname),
                "--tag-list juju,docker",
                "--executor docker",
                "--docker-image ubuntu:latest",
            ]
            subprocess.check_call(command, stderr=subprocess.STDOUT)
        elif self.kv.get("registered", False):
            hookenv.log("Already registered, ignoring request to register")
        else:
            hookenv.log("Could not register gitlab runner due to missing token or uri")
            hookenv.status_set("blocked", "Unregistered due to missing token or URI")
            return False
        hookenv.status_set("active", "Registered with {}")
        return True

    def add_sources(self):
        """Add APT sources to allow installation of GitLab Runner from GitLab's packages."""
        # https://packages.gitlab.com/runner/gitlab-runner/gpgkey
        # https://packages.gitlab.com/runner/gitlab-runner/ubuntu/ bionic main
        distro = get_distrib_codename()
        apt_key = "14219A96E15E78F4"
        apt_line = "deb https://packages.gitlab.com/runner/gitlab-runner/ubuntu/ {} main".format(
            distro
        )
        hookenv.log(
            "Installing and updating apt source for gitlab-runner: {} key {})".format(
                apt_line, apt_key
            )
        )
        add_source(apt_line, apt_key)
        return True

    def install_docker(self):
        """Install Docker which is required for running jobs."""
        apt_install("docker.io")

    def upgrade(self):
        """Install or upgrade the GitLab runner packages, adding APT sources as needed."""
        self.add_sources()
        apt_update()
        apt_install("gitlab-runner")
        return True

    def configure(self):
        """Upgrade and register GitLab Runner, perform configuration changes when charm configuration is modified."""
        self.upgrade()
        self.register()
        return True
