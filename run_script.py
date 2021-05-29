#!/usr/bin/python

import argparse as argparse

from src.race.data_processing import process_screenshots
from src.race.data_gathering import gather_screenshots
from src.race.data_visualization import visualize_data


video_path = ""

parser = argparse.ArgumentParser(
    description='Collect and visualize F1 Race sector data from F1TV Data Channel Feed.\n'
                'All optional arguments are on by default if none are provided.')

parser.add_argument('path', metavar='p', type=str, nargs='+', help='gather data from supplied video path')
parser.add_argument('-g', '--gather', help='gather screenshots from race', action='store_true')
parser.add_argument('-p', '--process', help='process screenshot data', action='store_true')
parser.add_argument('-v', '--visualize', help='visualize sector data', action='store_true')
parser.add_argument('compare', metavar='c', type=str, nargs='+', help='drivers to compare')

args = parser.parse_args()

# If no arguments are given, execute everything.
if not args.gather and not args.process and not args.visualize:
    args.gather = args.process = args.visualize = True

if args.gather:
    print("Gathering screenshots...")
    gather_screenshots(args.path[0])
if args.process:
    print("Processing screenshots...")
    process_screenshots()
if args.visualize:
    print("Visualizing gathered data...")
    visualize_data(args.compare if args.compare else None)
