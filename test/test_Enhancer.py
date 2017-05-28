import pytest
import mock
from Enhancer import Enhancer

class TestEnhancer(object):

    @pytest.fixture
    def test_input(self):
        return 'test_input.xml'

    @pytest.fixture
    def test_output(self):
        return 'test_output.xml'

    @pytest.fixture
    def test_key(self):
        return 'test_key'

    @pytest.fixture
    def enhancer(self, test_input, test_output, test_key):
        return Enhancer(test_input, test_output, test_key)

    def test_constructor(self, enhancer, test_input, test_output, test_key):
        assert enhancer.input == test_input
        assert enhancer.output == test_output
        assert enhancer.api_key == test_key
