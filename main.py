#!/usr/bin/env python3
import sys
import Enhancer
import argparse


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('input', help = "Name of input TCX/GPX file")
    parser.add_argument('output', help = "Name of output TCX/GPX file")
    parser.add_argument('api_key', help = "Mapzen API Key")
    parser.add_argument('-f', '--format', choices=['tcx','gpx','TCX','GPX'], default='tcx', help="Input and output file format")
    args = parser.parse_args()
    enh = Enhancer.Enhancer(args.input, args.output, args.api_key, format=args.format)
    enh.parse()
    enh.get_altitudes()
    enh.write()

if __name__ == '__main__':
    sys.exit(main())
