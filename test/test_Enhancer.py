import pytest
from unittest.mock import Mock, patch, call
from Enhancer import Enhancer
from xml.etree import ElementTree

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
        assert enhancer.chunk_size == Enhancer.CHUNK_SIZE

    @pytest.fixture
    def points(self):
        points = []
        for x in range(5):
            point = Mock(spec=ElementTree.Element)
            text = Mock()
            text.text = str(x)
            point.find = Mock(return_value=text)
            points.append(point)
        return points

    @pytest.fixture
    def mock_etree(self, points):
        etree = Mock()
        etree.findall = Mock(return_value=points)
        return etree

    def test_parse_xml(self, enhancer, points, mock_etree):
        with patch.object(ElementTree, 'parse', return_value = mock_etree) as parse_mock:
            enhancer.parse_xml()
            assert enhancer.xml_points == points
            parse_mock.assert_called_once_with(enhancer.input)
            mock_etree.findall.assert_called_once_with('.//tcx:Trackpoint', enhancer.namespaces)

    @pytest.mark.parametrize('limit', (0, None))
    def test_get_all_points(self, limit, enhancer, points):
        enhancer.xml_points = points
        if limit is None:
            enhancer.get_all_points()
        else:
            enhancer.get_all_points(limit)
        assert enhancer.points =={(str(x),str(x)):None  for x in range(5)}
        for p in points:
            assert p.find.call_count == 2
            assert p.find.call_args_list == \
                [call('./tcx:Position/tcx:LongitudeDegrees', enhancer.namespaces),
                 call('./tcx:Position/tcx:LatitudeDegrees', enhancer.namespaces)]

    @pytest.mark.parametrize('limit', (1,4,5,6))
    def test_get_all_points_limited(self, limit, enhancer, points):
        enhancer.xml_points = points
        enhancer.get_all_points(limit)
        print(enhancer.points)
        assert enhancer.points =={(str(x),str(x)):None  for x in range(min(5,limit))}
        for p in points[0:min(5,limit)]:
            assert p.find.call_count == 2
            assert p.find.call_args_list == \
                [call('./tcx:Position/tcx:LongitudeDegrees', enhancer.namespaces),
                    call('./tcx:Position/tcx:LatitudeDegrees', enhancer.namespaces)]

