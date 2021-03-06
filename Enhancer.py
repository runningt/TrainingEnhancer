import json
import time
import requests
import urllib
from collections import OrderedDict

from TrainingDocument import GPXDocument, TCXDocument
from utils import _normalized_float


class Enhancer(object):
    API_URL='http://elevation.mapzen.com/height'
    CHUNK_SIZE = 112
    warning_threshold = 0.25
    error_threshold = 0.75

    def __init__(self,  input, output, api_key, format='guess', chunk_size = CHUNK_SIZE):
        self.input = input
        self.output = output
        self.api_key = api_key
        self.chunk_size = chunk_size
        if format == 'guess':
            format = self.input.split('.')[-1]
        self.document = self._document_factory(format)
        self.coordinates = OrderedDict()

    def _document_factory(self, format):
        '''Yes, I do use design patterns :P '''
        if format.upper() == 'GPX':
            return GPXDocument()
        else:
            return TCXDocument()

    def parse(self):
        self.document.parse(self.input)
        self.coordinates = self.document.get_coordinates()


    def _chunks(self, _list, n):
        for i in range(0, len(_list), n):
            yield _list[i:i+n]


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
                    shape_list =[(_normalized_float(x.get('lon')), _normalized_float(x.get('lat'))) for x in shape]
                    res = zip(shape_list, height)
                    for p,h in res:
                        self.coordinates[p] = h
        if self._check_thresholds() < self.error_threshold:
            self.document.append_altitudes(self.coordinates)

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


    def write(self):
        self.document.write(self.output)
