#!/usr/bin/python3

import os
import os.path
import threading
import argparse

from distutils.dir_util import copy_tree

from build import build_website, autobuild_website

SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))

cwd = os.getcwd()


def build_arg_parser():
    parser = argparse.ArgumentParser(description='Build static websites.')
    parser.add_argument('-v', '--version', action='version', version='statwebgen 0.4')

    subparsers = parser.add_subparsers(dest='command', help='All available subcommands')

    parent_parser = argparse.ArgumentParser(add_help=False)
    parent_parser.add_argument('-i', '--in', default=os.getcwd(), dest='input_dir', help='Input directory')
    parent_parser.add_argument('-o', '--out', dest='output_dir', help='Output directory')

    build_parser = subparsers.add_parser('build', parents=[parent_parser], help='Build a static website')
    build_parser.add_argument('-t', '--testrun', dest='testrun', action='store_true', help='Build without writing to disk (for testing)')
    build_parser.add_argument('-d', '--draft', dest='draft', action='store_true', help='Build with drafts included')
    build_parser.add_argument('-w', '--watch', dest='watch', action='store_true', help='Rebuild on changes')

    return parser

def watch_project(args):
    print(f"Started statwebgen\n\tWatching '{args.input_dir}' for changes\n\tOutput in '{args.output_dir}'")

    # Set up kill flag
    kill_switch = threading.Event()
    kill_switch.clear()

    try: 
        autobuild_website(args, kill_switch)
    except KeyboardInterrupt:
        kill_switch.set()


def main(args):
    if not args.command:
        return

    if not args.output_dir:
        args.output_dir = os.path.join(args.input_dir, ".build")

    args.input_dir = os.path.abspath(args.input_dir)

    if args.command == 'build' and not args.watch:
        build_website(args)
        print("Website build complete.")
    elif args.command == 'build' and args.watch:
        watch_project(args)


if __name__ == "__main__":
    parser = build_arg_parser()
    arguments = parser.parse_args()
    main(arguments)