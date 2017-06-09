import pytest

@pytest.fixture
def test_output():
    return 'test_output.xml'


@pytest.fixture
def test_key():
    return 'test_key'


@pytest.fixture
def test_input():
    return 'test_input.xml'
