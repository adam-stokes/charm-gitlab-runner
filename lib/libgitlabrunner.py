"""GitLab Runner helper library for charm operations."""
import subprocess
from socket import gethostname

from charmhelpers.core import hookenv, templating, unitdata
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
        self.executor_dir = "/opt/lxd-executor"
        if self.charm_config["gitlab-token"]:
            self.gitlab_token = self.charm_config["gitlab-token"]
        else:
            self.gitlab_token = self.kv.get("gitlab_token", None)
        if self.charm_config["gitlab-uri"]:
            self.gitlab_uri = self.charm_config["gitlab-uri"]
        else:
            self.gitlab_uri = self.kv.get("gitlab_uri", None)

    def ensure_services(self):
        """Ensure services (docker, gitlab-runner) are enabled and running when installed and registered."""
        if self.kv.get("registered", False):
            service("enable", "docker")
            service("start", "docker")
            service("enable", "gitlab-runner")
            service("start", "gitlab-runner")

    def register(self):
        """Register this GitLab runner with the GitLab CI server."""
        if self.gitlab_token and self.gitlab_uri:
            hookenv.log("Registering GitLab runner with {}".format(self.gitlab_uri))
            hookenv.status_set("maintenance", "Registering with GitLab")
            # Docker executor
            command = [
                "/usr/bin/gitlab-runner",
                "register",
                "--non-interactive",
                "--url",
                "{}".format(self.gitlab_uri),
                "--registration-token",
                "{}".format(self.gitlab_token),
                "--name",
                "{}-docker".format(self.hostname),
                "--tag-list",
                "docker",
                "--executor",
                "docker",
                "--docker-image",
                "ubuntu:latest",
            ]
            subprocess.check_call(command, stderr=subprocess.STDOUT)
            # LXD executor
            command = [
                "/usr/bin/gitlab-runner",
                "register",
                "--non-interactive",
                "--url",
                "{}".format(self.gitlab_uri),
                "--registration-token",
                "{}".format(self.gitlab_token),
                "--name",
                "{}-lxd".format(self.hostname),
                "--tag-list",
                "juju",
                "--executor",
                "custom",
                "--builds-dir",
                "/builds",
                "--cache-dir",
                "/cache",
                "--custom-run-exec",
                "/opt/lxd-executor/run.sh",
                "--custom-prepare-exec",
                "/opt/lxd-executor/prepare.sh",
                "--custom-cleanup-exec",
                "/opt/lxd-executor/cleanup.sh",
            ]
            subprocess.check_call(command, stderr=subprocess.STDOUT)
        else:
            hookenv.log("Could not register gitlab runner due to missing token or uri")
            hookenv.status_set("blocked", "Unregistered due to missing token or URI")
            return False
        hookenv.status_set(
            "active", "Registered with {}".format(self.gitlab_uri.lstrip("http://"))
        )
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

    def setup_lxd(self):
        """Set up custom LXD executor scripts."""
        templating.render("base.j2", self.executor_dir + "/base.sh", context="")
        templating.render("prepare.j2", self.executor_dir + "/prepare.sh", context="")
        templating.render("run.j2", self.executor_dir + "/run.sh", context="")
        templating.render("cleanup.j2", self.executor_dir + "/cleanup.sh", context="")

    def unregister(self):
        """Unregister all runners."""
        command = [
            "/usr/bin/gitlab-runner",
            "unregister",
            "--all-runners",
        ]
        subprocess.check_call(command, stderr=subprocess.STDOUT)
