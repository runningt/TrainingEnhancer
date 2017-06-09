from collections import OrderedDict
from lxml import etree
from utils import _normalized_float

class TrainingDocument(object):
    def __init__(self):
        self.coordinates = OrderedDict()

    def parse(self, input):
        raise NotImplementedError

    def write(self, output):
        raise NotImplementedError

    def get_coordinates(self, max_points=0):
        raise NotImplementedError

    def append_altitudes(self, coordinates):
        raise NotImplementedError


class XMLDocument(TrainingDocument):
    namespaces = {}

    def parse(self, input):
        self.etree = etree.parse(input)

    def write(self, output):
        self.etree.write(output, encoding='utf-8', xml_declaration=True, method='xml')

    def _get_longitude(self, point):
        raise NotImplementedError

    def _get_latitude(self, point):
        raise NotImplementedError

    def _create_altitude_elem(self):
        raise NotImplementedError

    def get_coordinates(self, max_points=0):
        for p in self.track_points:
            longitude = self._get_longitude(p)
            latitude = self._get_latitude(p)
            if longitude is not None and latitude is not None:
                try:
                    self.coordinates[(_normalized_float(longitude), _normalized_float(latitude))] = None
                except ValueError:
                    pass
            if max_points and max_points <= len(self.coordinates):
                self.coordinates = OrderedDict((k, self.coordinates[k]) for k in list(self.coordinates.keys())[0:max_points])
        return self.coordinates

    def append_altitudes(self, coordinates):
        if len(coordinates):
            prev = 0
            for p in self.track_points:
                altitude_elem = self._create_altitude_elem()
                longitude = self._get_longitude(p)
                latitude = self._get_latitude(p)
                if latitude is not None and longitude is not None:
                    prev = coordinates.get((_normalized_float(longitude), _normalized_float(latitude))) or prev
                altitude_elem.text = str(prev)
                p.append(altitude_elem)


class GPXDocument(XMLDocument):
    namespaces = {'gpx':'http://www.topografix.com/GPX/1/1',
                  'gpxx':'http://www.garmin.com/xmlschemas/GpxExtensions/v3',
                  'gpxtpx':'http://www.garmin.com/xmlschemas/TrackPointExtension/v1'}

    def parse(self, input):
        super().parse(input)
        self.track_points = self.etree.findall('.//gpx:trkpt', self.namespaces)

    def _get_longitude(self, point):
        return point.attrib.get('lon')

    def _get_latitude(self, point):
        return point.attrib.get('lat')

    def _create_altitude_elem(self):
        return etree.Element('ele')


class TCXDocument(XMLDocument):

    namespaces = {'tcx':'http://www.garmin.com/xmlschemas/TrainingCenterDatabase/v2',
                  'ae':'http://www.garmin.com/xmlschemas/ActivityExtension/v2'}

    def parse(self, input):
        super().parse(input)
        self.laps = self.etree.findall('.//tcx:Lap', self.namespaces)
        self.track_points = self.etree.findall('.//tcx:Trackpoint', self.namespaces)

    def _get_longitude(self, point):
        longitude = point.find('./tcx:Position/tcx:LongitudeDegrees', self.namespaces)
        if longitude is not None:
            return longitude.text
        else:
            return None

    def _get_latitude(self, point):
        latitude = point.find('./tcx:Position/tcx:LatitudeDegrees', self.namespaces)
        if latitude is not None:
            return latitude.text
        else:
            return None

    def _create_altitude_elem(self):
        return etree.Element('AltitudeMeters')
