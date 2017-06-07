import json
import time
import requests
import urllib
from collections import OrderedDict
from lxml import etree

class Enhancer(object):
    namespaces = {'tcx':'http://www.garmin.com/xmlschemas/TrainingCenterDatabase/v2',
                  'ae':'http://www.garmin.com/xmlschemas/ActivityExtension/v2'}
    API_KEY='XXXXXX'
    API_URL='http://elevation.mapzen.com/height'
    CHUNK_SIZE = 112
    warning_threshold = 0.25
    error_threshold = 0.75

    def __init__(self,  input, output, api_key=API_KEY, chunk_size = CHUNK_SIZE):
        self.input = input
        self.output = output
        self.coordinates = OrderedDict()
        self.api_key = api_key
        self.chunk_size = chunk_size

    def parse_xml(self):
        self.etree = etree.parse(self.input)
        self.laps = self.etree.findall('.//tcx:Lap', self.namespaces)
        self.track_points = self.etree.findall('.//tcx:Trackpoint', self.namespaces)

    def get_coordinates(self, max_points=0):
        for p in self.track_points:
            longitude = p.find('./tcx:Position/tcx:LongitudeDegrees', self.namespaces)
            latitude = p.find('./tcx:Position/tcx:LatitudeDegrees', self.namespaces)
            if longitude is not None and latitude is not None:
                try:
                    self.coordinates[(self._normalized_float(longitude.text), self._normalized_float(latitude.text))] = None
                except ValueError:
                    pass
            if max_points and max_points <= len(self.coordinates):
                self.coordinates = OrderedDict((k, self.coordinates[k]) for k in list(self.coordinates.keys())[0:max_points])

    def _chunks(self, _list, n):
        for i in range(0, len(_list), n):
            yield _list[i:i+n]

    def _normalized_float(self, value, round_digits=5):
        try:
            return round(float(value), round_digits)
        except ValueError:
            return None

    def _build_request_urls(self):
        shape_list = [OrderedDict([("lat", k[1]),("lon",k[0])]) for k in self.coordinates.keys()]
        for l in self._chunks(shape_list, self.chunk_size):
            dic = {'shape': l}
            params=urllib.parse.urlencode(OrderedDict([('json',json.dumps(dic)), ('api_key',self.api_key)]))
            yield '{}?{}'.format(self.API_URL,params)


    def _get_responses(self):
        self.responses = []
        for url in self._build_request_urls():
            try:
                resp = requests.get(url)
                self.responses.append(resp)
                if resp.status_code == 429:
                    time.sleep(2)
                    resp = requests.get(url)
                yield resp
            except Exception as e:
                print(str(e))
            time.sleep(0.5)

    def get_altitudes(self):
        for resp in self._get_responses():
            if resp.ok:
                jsn = resp.json()
                shape = jsn.get('shape')
                height = jsn.get('height')
                if shape and height:
                    shape_list =[(self._normalized_float(x.get('lon')), self._normalized_float(x.get('lat'))) for x in shape]
                    res = zip(shape_list, height)
                    for p,h in res:
                        self.coordinates[p] = h
        self._check_thresholds()

    def _check_thresholds(self):
        num_points = len(self.coordinates)
        empty_fraction = 0
        if num_points > 0:
            num_empty = len([x for x in self.coordinates.values() if x is None])
            empty_fraction = num_empty/num_points
            if self.warning_threshold and empty_fraction > self.warning_threshold:
                print('[WARNING]: {} out of {} track points is empty'.format(num_empty, num_points))
            if self.error_threshold and empty_fraction > self.error_threshold:
                print('[ERROR]: {} out of {} track points is empty'.format(num_empty, num_points))
                raise ValueError('{} out of {} track points is empty'.format(num_empty, num_points))
        return empty_fraction

    def append_altitudes(self):
        if len(self.coordinates):
            prev = 0
            for p in self.track_points:
                altitude = etree.Element('AltitudeMeters')
                longitude = p.find('./tcx:Position/tcx:LongitudeDegrees', self.namespaces)
                latitude = p.find('./tcx:Position/tcx:LatitudeDegrees', self.namespaces)
                if latitude is not None and longitude is not None:
                    prev = self.coordinates[(self._normalized_float(longitude.text), self._normalized_float(latitude.text))] or prev
                altitude.text = str(prev)
                p.append(altitude)

    def write(self):
        self.etree.write(self.output, encoding='utf-8', xml_declaration=True, method='xml')

