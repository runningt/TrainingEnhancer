# TrainingEnhancer
Enhance training tracks with data from external sources 

## Motivation
When using [Linux TomTom GPS Watch Utilities](https://github.com/ryanbinns/ttwatch) I noticed that elevation data for TomTom Runner 3 is not stored in exported TCX, CSV nor GPX files.  It looks like there is an [open deffect](https://github.com/ryanbinns/ttwatch/issues/100) for this issue. While waiting for a fix I decided to create simple project to fetch altitude/elevation from external source end enhance XML (TCX and GPX in some future) files with this data. In future I would like to add other data sources and other supported formats to enhance training tracks with more interesting data.

## External data sources
### Altitude Sources 
#### [Mapzen Elevation Service](https://mapzen.com/documentation/elevation/elevation-service/)
Please not that in order to use Mapzen API you have to register there and provide your own
[API Key](https://mapzen.com/documentation/overview/api-keys/) in TrainingEnhancer configuration.

Prior to use this API, please make sure you have read Mapzen [Terms of Service](https://mapzen.com/terms/)

In future:
#### [Google Elevation API](https://developers.google.com/maps/documentation/elevation/intro)

### Other Sources
None currently.

## Supported formats

#### [Training Center XML](https://en.wikipedia.org/wiki/Training_Center_XML)

In future:
#### [GPS Exchange Format](https://en.wikipedia.org/wiki/GPS_Exchange_Format)


## Usage:

`python3 main.py <INPUT_TCX> <OUTPUT_TCX> <MAPZEN_API_KEY>`

`postprocess.sh` is a simple bash script that can be specified as a `PostProcessor` in `ttwatch.conf` 
See [TTWatch config files](https://github.com/ryanbinns/ttwatch#config-files) for more details.

