#!/usr/bin/env python3
import sys
import Enhancer
import argparse


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('input', help = "Name of input TCX file")
    parser.add_argument('output', help = "Name of output TCX file")
    parser.add_argument('api_key', help = "Mapzen API Key")
    args = parser.parse_args()
    enh = Enhancer.Enhancer(args.input, args.output, args.api_key)
    enh.parse_xml()
    enh.get_coordinates()
    enh.get_altitudes()
    enh.append_altitudes()
    enh.write()

if __name__ == '__main__':
    sys.exit(main())
