from xml.etree import ElementTree
import requests
import urllib
import json
import time
from collections import OrderedDict

class Enhancer(object):
    namespaces = {'tcx':'http://www.garmin.com/xmlschemas/TrainingCenterDatabase/v2',
                  'ae':'http://www.garmin.com/xmlschemas/ActivityExtension/v2',
                  '':'http://www.garmin.com/xmlschemas/TrainingCenterDatabase/v2'}
    API_KEY='XXXXXX'
    API_URL='http://elevation.mapzen.com/height'
    CHUNK_SIZE = 112
    warning_threshold = 0.25
    error_threshold = 0.75

    def __init__(self,  input, output, api_key=API_KEY, chunk_size = CHUNK_SIZE):
        self.input = input
        self.output = output
        self.points = OrderedDict()
        self.api_key = api_key
        self.chunk_size = chunk_size
        for (k,v) in self.namespaces.items():
            if k != 'tcx':
                ElementTree.register_namespace(k,v)

    def parse_xml(self):
        self.etree = ElementTree.parse(self.input)
        self.xml_points = self.etree.findall('.//tcx:Trackpoint', self.namespaces)

    def get_all_points(self, max_points=0):
        for p in self.xml_points:
            longitude = p.find('./tcx:Position/tcx:LongitudeDegrees', self.namespaces)
            latitude = p.find('./tcx:Position/tcx:LatitudeDegrees', self.namespaces)
            if longitude is not None and latitude is not None:
                try:
                    self.points[(self._normalized_float(longitude.text), self._normalized_float(latitude.text))] = None
                except ValueError:
                    pass
            if max_points and max_points <= len(self.points):
                self.points = OrderedDict((k, self.points[k]) for k in list(self.points.keys())[0:max_points])

    def _chunks(self, _list, n):
        for i in range(0, len(_list), n):
            yield _list[i:i+n]

    def _normalized_float(self, value, round_digits=5):
        try:
            return round(float(value), round_digits)
        except ValueError:
            return None

    def _build_request_urls(self):
        shape_list = [{"lat": k[1], "lon": k[0]} for k in self.points.keys()]
        for l in self._chunks(shape_list, self.chunk_size):
            dic = {'shape': l}
            params=urllib.parse.urlencode({'json':json.dumps(dic), 'api_key':self.api_key})
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
                        self.points[p] = h
        self._check_thresholds()

    def _check_thresholds(self):
        num_points = len(self.points)
        empty_fraction = 0
        if num_points > 0:
            num_empty = len([x for x in self.points.values() if x is None])
            empty_fraction = num_empty/num_points
            if self.warning_threshold and empty_fraction > self.warning_threshold:
                print('[WARNING]: {} out of {} track points is empty'.format(num_empty, num_points))
            if self.error_threshold and empty_fraction > self.error_threshold:
                print('[ERROR]: {} out of {} track points is empty'.format(num_empty, num_points))
                raise ValueError('{} out of {} track points is empty'.format(num_empty, num_points))
        return empty_fraction

    def append_altitudes(self):
        if len(self.points):
            prev = 0
            for p in self.xml_points:
                altitude = ElementTree.Element('AltitudeMeters')
                longitude = p.find('./tcx:Position/tcx:LongitudeDegrees', self.namespaces)
                latitude = p.find('./tcx:Position/tcx:LatitudeDegrees', self.namespaces)
                if latitude and longitude:
                    prev = self.points[(self._normalized_float(longitude.text), self._normalized_float(latitude.text))] or prev
                altitude.text = str(prev)
                p.append(altitude)

    def write(self):
        #TODO: tags with namespace 'ae' are written as e.g. <ae:TPX>.
        #Endomondo would prefer <TPX xmlns=...>
        self.etree.write(self.output, encoding='utf-8', xml_declaration=True, method='xml')

