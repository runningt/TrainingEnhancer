import itertools
import json
import pytest
import requests
import urllib
from collections import OrderedDict
from lxml import etree
from unittest.mock import Mock, patch, call
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
        assert enhancer.chunk_size == Enhancer.CHUNK_SIZE

    @pytest.fixture
    def track_points(self):
        points = []
        for x in range(5):
            point = Mock(spec=etree.Element)
            text = Mock()
            text.text = str(x)
            point.find = Mock(return_value=text)
            point.val = x
            point.append = Mock()
            points.append(point)
        return points

    @pytest.fixture
    def mock_etree(self, track_points):
        etr = Mock(spec=etree)
        etr.findall = Mock(return_value=track_points)
        return etr

    def test_parse_xml(self, enhancer, track_points, mock_etree):
        with patch.object(etree, 'parse', return_value = mock_etree) as parse_mock:
            enhancer.parse_xml()
            assert enhancer.track_points == track_points
            parse_mock.assert_called_once_with(enhancer.input)
            assert mock_etree.findall.call_count == 2
            assert mock_etree.findall.call_args_list[1][0] == ('.//tcx:Trackpoint', enhancer.namespaces)
            assert mock_etree.findall.call_args_list[0][0] == ('.//tcx:Lap', enhancer.namespaces)

    @pytest.mark.parametrize('limit', (0, None))
    def test_get_coordinates(self, limit, enhancer, track_points):
        enhancer.track_points = track_points
        if limit is None:
            enhancer.get_coordinates()
        else:
            enhancer.get_coordinates(limit)
        assert enhancer.coordinates =={(x,x):None  for x in range(5)}
        for p in track_points:
            assert p.find.call_count == 2
            assert p.find.call_args_list == \
                [call('./tcx:Position/tcx:LongitudeDegrees', enhancer.namespaces),
                 call('./tcx:Position/tcx:LatitudeDegrees', enhancer.namespaces)]

    @pytest.mark.parametrize('limit', (1,4,5,6))
    def test_get_coordinates_limited(self, limit, enhancer, track_points):
        enhancer.track_points = track_points
        enhancer.get_coordinates(limit)
        print(enhancer.coordinates)
        assert enhancer.coordinates =={(x, x):None  for x in range(min(5,limit))}
        for p in track_points[0:min(5,limit)]:
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
        enhancer.coordinates = points
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
        enhancer.coordinates = points
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

    @pytest.mark.parametrize('_list, len, expected',
        (([1,2,3], 3, [[1,2,3]]),
         ([1,2,3], 4, [[1,2,3]]),
         ([1,2,3], 2, [[1,2], [3]]),
         ([1,2,3], 1, [[1], [2], [3]]),
         ([1,2,3,4], 2, [[1, 2], [3, 4]])))
    def test_chunks(self, enhancer, _list, len, expected):
        assert list(enhancer._chunks(_list, len)) == expected

    @pytest.fixture(params=[
        {(1,1):None, (1,2):None, (1,3):None},
        {(1.2222,1.2222):None, (1.3333,1.33333):None, (1.9999,1.9999):None},
        {(1.222222,1.2222222):None, (99999.99999999,99999.999999999):None, (7.7777777,2.2222222):None},
    ])
    def points(self, request):
        return request.param

    @pytest.fixture
    def shape_json(self, points):
        return "{{\"shape\": [{{\"lat\": {}, \"lon\": {}}}, {{\"lat\": {}, \"lon\": {}}}, {{\"lat\": {}, \"lon\": {}}}]}}".\
        format(*itertools.chain(*((y,x) for (x,y) in points.keys())))

    def test_build_request_urls(self, enhancer, points, shape_json, test_key):
        enhancer.coordinates = points
        assert list(enhancer._build_request_urls()) == \
        ['http://elevation.mapzen.com/height?json={}&api_key={}'.\
        format(urllib.parse.quote_plus(shape_json), test_key)]

    @pytest.fixture
    def points_with_heights(self, points):
        return OrderedDict(((round(x,5),round(y,5)),round(x,5)) for (x,y) in points.keys())


    @pytest.fixture
    def jsn(self, points_with_heights):
        jsn = {'shape':[{'lat':y, 'lon':x} for x,y in points_with_heights.keys()],
               'height':[x for x,y in points_with_heights.keys()]}
        return jsn

    @pytest.fixture
    def response(self, jsn):
        response = Mock(spec=requests.Response)
        response.json = Mock(return_value=jsn)
        response.ok = True
        return response

    @pytest.fixture
    def err_response(self, response):
        response.ok = False
        return response

    @pytest.fixture
    def wrong_jsn_response(self, points_with_heights):
        return self.response({'shape':'Wrong Shape', 'height':None})

    @patch.object(Enhancer, '_check_thresholds')
    def test_get_altitudes(self, check_mock, enhancer, points_with_heights, response):
        with patch.object(Enhancer, '_get_responses', return_value=[response, response]) as get_resp_mock:
            enhancer.get_altitudes()
            assert check_mock.call_count == 1
            assert get_resp_mock.call_count == 1
            assert enhancer.coordinates == points_with_heights

    @patch.object(Enhancer, '_check_thresholds')
    def test_get_altitudes_err_response(self, check_mock, enhancer, err_response):
        with patch.object(Enhancer, '_get_responses', return_value=[err_response]) as get_resp_mock:
            enhancer.get_altitudes()
            assert check_mock.call_count == 1
            assert get_resp_mock.call_count == 1
            assert enhancer.coordinates == OrderedDict()

    @patch.object(Enhancer, '_check_thresholds')
    def test_get_altitudes_wrong_response(self, check_mock, enhancer, wrong_jsn_response):
        with patch.object(Enhancer, '_get_responses', return_value=[wrong_jsn_response]) as get_resp_mock:
            enhancer.get_altitudes()
            assert check_mock.call_count == 1
            assert get_resp_mock.call_count == 1
            assert enhancer.coordinates == OrderedDict()

    @patch.object(Enhancer, '_check_thresholds')
    def test_get_altitudes_no_responses(self, check_mock, enhancer):
        with patch.object(Enhancer, '_get_responses', return_value=[]) as get_resp_mock:
            enhancer.get_altitudes()
            assert check_mock.call_count == 1
            assert get_resp_mock.call_count == 1
            assert enhancer.coordinates == OrderedDict()

    def test_append_altitudes(self, enhancer, track_points):
        enhancer.coordinates = OrderedDict((((p.val, p.val), p.val) for p in track_points))
        enhancer.track_points = track_points
        enhancer.append_altitudes()
        for p in enhancer.track_points:
            assert p.append.call_count == 1
            (altitude,) = p.append.call_args[0]
            assert altitude.text ==  str(p.val)
