from charmhelpers.core import hookenv, unitdata
from charmhelpers.core.host import get_distrib_codename
from charmhelpers.fetch import add_source, apt_install, apt_update
from socket import gethostname
import subprocess


class GitLabRunner:
    def __init__(self):
        self.charm_config = hookenv.config()
        self.kv = unitdata.kv()
        self.gitlab_token = False
        self.gitlab_uri = False
        self.gethostname = gethostname()
        if self.charm_config["gitlab-token"]:
            self.gitlab_token = self.charm_config["gitlab-token"]
        if self.charm_config["gitlab-uri"]:
            self.gitlab_uri = self.charm_config["gitlab-uri"]

    def register(self):
        """Register this GitLab runner with the GitLab CI server."""
        if (
            self.gitlab_token
            and self.gitlab_uri
            and not self.kv.get("registered", False)
        ):
            hookenv.log("Registering GitLab runner with {}".format(self.gitlab_uri))
            hookenv.status_set("maintenance", "Registering with GitLab")
            command = (
                "sudo gitlab-runner register "
                "--non-interactive "
                "--url {} "
                "--registration-token {} "
                "--name {} "
                "--tag-list juju,docker "
                "--executor docker"
            ).format(self.gitlab_uri,
                     self.gitlab_token,
                     self.hostname)
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

    def upgrade(self):
        self.add_sources()
        apt_update()
        apt_install("gitlab-runner")
        return True

    def configure(self):
        self.upgrade()
        self.register()
        return True
