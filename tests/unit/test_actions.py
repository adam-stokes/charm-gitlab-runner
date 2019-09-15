import imp

import mock


class TestActions():
    def test_register_action(self, gitlabrunner, monkeypatch):
        mock_function = mock.Mock()
        monkeypatch.setattr(gitlabrunner, 'register', mock_function)
        assert mock_function.call_count == 0
        imp.load_source('register', './actions/register')
        assert mock_function.call_count == 1
