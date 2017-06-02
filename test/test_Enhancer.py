import pytest
from unittest.mock import Mock, patch, call
from Enhancer import Enhancer
from lxml import etree

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
    def xml_points(self):
        points = []
        for x in range(5):
            point = Mock(spec=etree.Element)
            text = Mock()
            text.text = str(x)
            point.find = Mock(return_value=text)
            points.append(point)
        return points

    @pytest.fixture
    def mock_etree(self, xml_points):
        etr = Mock(spec=etree)
        etr.findall = Mock(return_value=xml_points)
        return etr

    def test_parse_xml(self, enhancer, xml_points, mock_etree):
        with patch.object(etree, 'parse', return_value = mock_etree) as parse_mock:
            enhancer.parse_xml()
            assert enhancer.xml_points == xml_points
            parse_mock.assert_called_once_with(enhancer.input)
            mock_etree.findall.assert_called_once_with('.//tcx:Trackpoint', enhancer.namespaces)

    @pytest.mark.parametrize('limit', (0, None))
    def test_get_all_points(self, limit, enhancer, xml_points):
        enhancer.xml_points = xml_points
        if limit is None:
            enhancer.get_all_points()
        else:
            enhancer.get_all_points(limit)
        assert enhancer.points =={(x,x):None  for x in range(5)}
        for p in xml_points:
            assert p.find.call_count == 2
            assert p.find.call_args_list == \
                [call('./tcx:Position/tcx:LongitudeDegrees', enhancer.namespaces),
                 call('./tcx:Position/tcx:LatitudeDegrees', enhancer.namespaces)]

    @pytest.mark.parametrize('limit', (1,4,5,6))
    def test_get_all_points_limited(self, limit, enhancer, xml_points):
        enhancer.xml_points = xml_points
        enhancer.get_all_points(limit)
        print(enhancer.points)
        assert enhancer.points =={(x, x):None  for x in range(min(5,limit))}
        for p in xml_points[0:min(5,limit)]:
            assert p.find.call_count == 2
            assert p.find.call_args_list == \
                [call('./tcx:Position/tcx:LongitudeDegrees', enhancer.namespaces),
                    call('./tcx:Position/tcx:LatitudeDegrees', enhancer.namespaces)]

    @pytest.mark.parametrize('points, expected, warning',
    (({(1,1):1},0,0),
     ({},0,0),
     ({(1,1):1, (1,2):None}, 0.5, 0.6),
     ({(1,1):1, (1,2):None}, 0.5, 0.4),
     ({(1,1):1, (1,2):1, (1,3):None}, 0.33333333333, 0.5),
     ({(1,1):1, (1,2):1, (1,3):None, (10,10):1}, 0.25, 0.2)
    ))
    def test_check_threshold(self, enhancer, points, expected, warning):
        enhancer.points = points
        enhancer.warning_threshold = warning
        enhancer.error_threshold = 0
        with patch('builtins.print', autospec=True, side_effect=print) as print_mock:
            res = enhancer._check_thresholds()
            assert abs(res -  expected) < 1e-05
            if warning and res > warning:
                assert print_mock.call_count == 1
                assert 'WARNING' in print_mock.call_args[0][0]
            else:
                assert print_mock.call_count == 0

    @pytest.mark.parametrize('points',
    ({(1,1):1, (1,2):None},
     {(1,1):1, (1,2):1, (1,3):None},
     {(1,1):1, (1,2):1, (1,3):None, (10,10):1}
    ))
    def test_check_threshold_exception_raised(self, enhancer, points):
        enhancer.points = points
        enhancer.warning_threshold = 0
        enhancer.error_threshold = 0.1
        with patch('builtins.print', autospec=True, side_effect=print) as print_mock:
            with pytest.raises(ValueError):
                enhancer._check_thresholds()
            assert print_mock.call_count == 1
            assert 'ERROR' in print_mock.call_args[0][0]


    @pytest.mark.parametrize('value, expected',
        ((1, 1), ('1', 1), (-1, -1),
         (1100.23456, 1100.23456),
         (-1000.123456,-1000.12346),
         (0.123454,0.12345),
         ('10.12345', 10.12345),
         ('100000.123456', 100000.12346)))
    def test_normalized_float(self, enhancer, value, expected):
        assert enhancer._normalized_float(value) == expected
