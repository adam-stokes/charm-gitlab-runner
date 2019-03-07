#!/usr/bin/python3


class TestLib():
    def test_pytest(self):
        assert True

    def test_gitlabrunner(self, gitlabrunner):
        ''' See if the helper fixture works to load charm configs '''
        assert isinstance(gitlabrunner.charm_config, dict)

    # Include tests for functions in lib_gitlab_runner
