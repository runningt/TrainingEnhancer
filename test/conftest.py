import pytest
from unittest.mock import Mock
from lxml import etree

@pytest.fixture
def track_points():
    points = []
    for x in range(5):
        point = Mock(spec=etree.Element)
        text = Mock()
        text.text = str(x)
        point.find = Mock(return_value=text)
        point.val = x
        point.attrib = Mock()
        point.attrib.get=Mock(return_value=text)
        point.append = Mock()
        points.append(point)
    return points

@pytest.fixture
def mock_etree(track_points):
    etr = Mock(spec=etree)
    etr.findall = Mock(return_value=track_points)
    return etr

@pytest.fixture
def test_input():
    return 'test_input.xml'


