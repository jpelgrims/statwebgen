#!/usr/bin/python3

import os
import sys
import threading
import argparse
import configparser
import webbrowser
import signal

from distutils.dir_util import copy_tree

from website import Website

SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))

cwd = os.getcwd()

parser = argparse.ArgumentParser(description='Build static websites.')
parser.add_argument('-v', '--version', action='version', version='statwebgen 0.4')

subparsers = parser.add_subparsers(dest='command', help='All available subcommands')

parent_parser = argparse.ArgumentParser(add_help=False)
parent_parser.add_argument('-i', '--in', default=os.getcwd(), dest='input_dir', help='Input directory')
parent_parser.add_argument('-o', '--out', dest='output_dir', help='Output directory')

build_parser = subparsers.add_parser('build', parents=[parent_parser], help='Build a static website')
build_parser.add_argument('-t', '--testrun', dest='testrun', action='store_true', help='Build the static website without writing to disk (for testing)')

watch_parser = subparsers.add_parser('watch', parents=[parent_parser], help='Rebuild a static website on changes')


def build_project(args):
    website = Website(args.input_dir)
    website.build()
    print("Website build complete.")

def watch_project(args):
    website = Website(args.input_dir)

    # Set up kill flag
    kill_switch = threading.Event()
    kill_switch.clear()

    try: 
        website.autobuild(kill_switch)
    except KeyboardInterrupt:
        kill_switch.set()


def main(args):
    
    if not args.command:
        return

    if not args.output_dir:
        args.output_dir = os.path.join(args.input_dir, ".build")

    if args.command == 'build':
        build_project(args)
    elif args.command == 'watch':
        watch_project(args)


if __name__ == "__main__":
    arguments = parser.parse_args()
    print(arguments)
    main(arguments)