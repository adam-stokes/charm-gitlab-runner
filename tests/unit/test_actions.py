"""Unit test actions in the gitlab-runner charm."""
import imp

import mock


def test_register_action(gitlabrunner, monkeypatch, mock_action_set, mock_action_fail):
    """Unit test the register action."""
    mock_function = mock.Mock()
    monkeypatch.setattr(gitlabrunner, 'register', mock_function)
    assert mock_function.call_count == 0
    imp.load_source('register', './actions/register')
    assert mock_function.call_count == 1
