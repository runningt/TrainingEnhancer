import pytest
from collections import OrderedDict
from lxml import etree
from unittest.mock import patch, call, Mock


from TrainingDocument import TCXDocument, GPXDocument

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
        point.attrib.get=Mock(return_value=str(x))
        point.append = Mock()
        points.append(point)
    return points


@pytest.fixture
def mock_etree(track_points):
    etr = Mock(spec=etree)
    etr.findall = Mock(return_value=track_points)
    return etr


class TestTCXDocument(object):
    @pytest.fixture
    def document(self):
        return TCXDocument()

    def test_parse(self, document, test_input, track_points, mock_etree):
        with patch.object(etree, 'parse', return_value = mock_etree) as parse_mock:
            document.parse(test_input)
            assert document.track_points == track_points
            parse_mock.assert_called_once_with(test_input)
            assert mock_etree.findall.call_count == 2
            assert mock_etree.findall.call_args_list[1][0] == ('.//tcx:Trackpoint', document.namespaces)
            assert mock_etree.findall.call_args_list[0][0] == ('.//tcx:Lap', document.namespaces)

    @pytest.mark.parametrize('limit', (0, None))
    def test_get_coordinates(self, limit, document, track_points):
        document.track_points = track_points
        if limit is None:
            document.get_coordinates()
        else:
            document.get_coordinates(limit)
        assert document.coordinates =={(x,x):None  for x in range(5)}
        for p in track_points:
            assert p.find.call_count == 2
            assert p.find.call_args_list == \
                [call('./tcx:Position/tcx:LongitudeDegrees', document.namespaces),
                 call('./tcx:Position/tcx:LatitudeDegrees', document.namespaces)]

    @pytest.mark.parametrize('limit', (1,4,5,6))
    def test_get_coordinates_limited(self, limit, document, track_points):
        document.track_points = track_points
        document.get_coordinates(limit)
        assert document.coordinates =={(x, x):None  for x in range(min(5,limit))}
        for p in track_points[0:min(5,limit)]:
            assert p.find.call_count == 2
            assert p.find.call_args_list == \
                [call('./tcx:Position/tcx:LongitudeDegrees', document.namespaces),
                    call('./tcx:Position/tcx:LatitudeDegrees', document.namespaces)]

    def test_append_altitudes(self, document, track_points):
        coordinates = OrderedDict((((p.val, p.val), p.val) for p in track_points))
        document.track_points = track_points
        document.append_altitudes(coordinates)
        for p in document.track_points:
            assert p.append.call_count == 1
            (altitude,) = p.append.call_args[0]
            assert altitude.text == str(p.val)


class TestGPXDocument(object):

    @pytest.fixture
    def document(self):
        return GPXDocument()

    def test_parse(self, document, test_input, track_points, mock_etree):
        with patch.object(etree, 'parse', return_value = mock_etree) as parse_mock:
            document.parse(test_input)
            assert document.track_points == track_points
            parse_mock.assert_called_once_with(test_input)
            mock_etree.findall.assert_called_once_with('.//gpx:trkpt', document.namespaces)

    @pytest.mark.parametrize('limit', (0, None))
    def test_get_coordinates(self, limit, document, track_points):
        document.track_points = track_points
        if limit is None:
            document.get_coordinates()
        else:
            document.get_coordinates(limit)
        assert document.coordinates =={(x,x):None  for x in range(5)}
        for p in track_points:
            assert p.attrib.get.call_count == 2

    @pytest.mark.parametrize('limit', (1,4,5,6))
    def test_get_coordinates_limited(self, limit, document, track_points):
        document.track_points = track_points
        document.get_coordinates(limit)
        assert document.coordinates =={(x, x):None  for x in range(min(5,limit))}
        for p in track_points[0:min(5,limit)]:
            assert p.attrib.get.call_count == 2

    def test_append_altitudes(self, document, track_points):
        coordinates = OrderedDict((((p.val, p.val), p.val) for p in track_points))
        document.track_points = track_points
        document.append_altitudes(coordinates)
        for p in document.track_points:
            assert p.append.call_count == 1
            (altitude,) = p.append.call_args[0]
            assert altitude.text ==  str(p.val)
