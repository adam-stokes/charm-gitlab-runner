[![pipeline status](https://git.ec0.io/pirate-charmers/charm-gitlab-runner/badges/master/pipeline.svg)](https://git.ec0.io/pirate-charmers/charm-gitlab-runner/commits/master)
[![coverage report](https://git.ec0.io/pirate-charmers/charm-gitlab-runner/badges/master/coverage.svg)](https://git.ec0.io/pirate-charmers/charm-gitlab-runner/commits/master)

GitLab CI Runner Charm
======================

This is a simple charm to install and configure the GitLab CI runner on a target system.
Presently, the registration token and GitLab URI need to be manually retrieved and configuring using the
`gitlab-uri` and `gitlab-token` configuration parameters on this charm.

The infrastructure is in place to handle this via a relation, but finishing this work is pending a method to
programatically obtain the token in the [GitLab charm](https://git.ec0.io/pirate-charmers/charm-gitlab).

TODO
====

- Pull required images
- Add relation-based registration
