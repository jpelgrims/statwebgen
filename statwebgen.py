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
from server import *

SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))

# get current working directory
cwd = os.getcwd()

parser = argparse.ArgumentParser(description='Build static websites.')
parser.add_argument('-v', '--version', action='version', version='statwebgen 0.3')

subparsers = parser.add_subparsers(dest='command', help='All available subcommands')

parent_parser = argparse.ArgumentParser(add_help=False)
parent_parser.add_argument('-i', '--in', default=os.getcwd(), dest='input_folder', help='Input folder')
parent_parser.add_argument('-o', '--out', default=os.path.join(os.getcwd(), ".build"), dest='output_folder', help='Output folder')
parent_parser.add_argument('-p', '--project', default=None, dest='project', help='Project to work with')

create_parser = subparsers.add_parser('create', help='Create a new static website')
create_parser.add_argument('-n', '--name', default=None, dest='name', help='Project name')
create_parser.add_argument('-p', '---path', default=os.getcwd(), dest='path', help='Project path')
create_parser.add_argument('-s', '--skeleton', default="default", dest='skeleton', help='Project skeleton to start with')

build_parser = subparsers.add_parser('build', parents=[parent_parser], help='Build a static website')
build_parser.add_argument('-t', '--testrun', dest='testrun', action='store_true', help='Build the static website without writing to disk (for testing)')

watch_parser = subparsers.add_parser('watch', parents=[parent_parser], help='Rebuild a static website on changes')

serve_parser = subparsers.add_parser('serve', parents=[parent_parser], help='Serve a static website locally and rebuild on changes')
serve_parser.add_argument('-t', '--port', type=int, default=8000, dest='port', help='Port to serve on, defaults to 8000')
serve_parser.add_argument('-r', '--autoreload', dest='autoreload', action='store_true', help='Automatically refresh browser pages on changes')
serve_parser.add_argument('-b', '--browse', dest='browse', action='store_true', help='Open the website in the default browser')


clean_parser = subparsers.add_parser('clean', help='Empty the build folder of a project')
clean_parser.add_argument('-f', '---path', default=os.getcwd(), dest='path', help='Project path')
clean_parser.add_argument('-p', '--project', default=None, dest='project', help='Project to work with')


def get_project_config(arguments, config):
    input_folder = None
    output_folder = None

    if arguments.project:
        try:
            index = config["projects"].index(next(filter(lambda x: x.get("name") == arguments.project, config["projects"])))
            input_folder = config["projects"][index].get("input_folder", arguments.input_folder)
            output_folder = config["projects"][index].get("output_folder", arguments.output_folder)
        except ValueError:
            print(f"Project '{arguments.project}' doesn't exist.")
            exit(0)
    else:
        input_folder = arguments.input_folder
        output_folder = arguments.output_folder
    
    return input_folder, output_folder
    

def create_project(config, config_file, arguments):
    if arguments.name:
        project = {"name": arguments.name, "input_folder": arguments.path}
        config["projects"].append(project)
        with open(config_file, "w") as f:
            json.dump(config, f, indent=4, sort_keys=True)

    if arguments.skeleton:
        try:
            print("test")
            copy_tree(os.path.join(SCRIPT_DIR, "skeletons", arguments.skeleton), arguments.path)
            print(os.path.join(SCRIPT_DIR, "skeletons", arguments.skeleton))
        except Exception as e:
            print("Something went wrong while creating a new project.")
            print(e)
    
    
    print(f"Project was successfully created in {arguments.path}.")


def build_project(arguments, config):
    input_dir, output_dir = get_project_config(arguments, config)
    website = Website(input_dir)
    website.build()
    print("Website build complete.")

def watch_project(arguments, config):
    input_dir, output_dir = get_project_config(arguments, config)
    website = Website(input_dir)

    # Set up kill flag
    kill_switch = threading.Event()
    kill_switch.clear()

    try: 
        website.autobuild(kill_switch)
    except KeyboardInterrupt:
        kill_switch.set()

def serve_project(arguments, config):
    # Initial project build, so the server has something to serve
    input_dir, output_dir = get_project_config(arguments, config)
    print(input_dir)
    print(output_dir)
    website = Website(input_dir, output_dir=output_dir)
    website.build()

    # Set up kill flag
    kill_switch = threading.Event()
    kill_switch.clear()

    # Set up live refresh server
    live_refresh_server = LiveRefreshServer(("", 8001))
    live_refresh_thread = threading.Thread(target=live_refresh_server.serve_forever)
    live_refresh_thread.daemon = True
    live_refresh_thread.start()

    # Set up project autobuilding
    autobuild_thread = threading.Thread(target=website.autobuild, args=(kill_switch, live_refresh_server,))
    autobuild_thread.start()

    try:
        port = 8002

        # Open webbrowser
        if arguments.browse:
            # Note to self: this won't be able to open a browser if testing on WSL
            webbrowser.open("http://localhost:{}/".format(port), new=2)

        # Serve project build
        website_server = StaticWebsiteServer(("", port), output_dir)
        website_server.serve_forever()
        print("Serving at port", port)
    except KeyboardInterrupt:
        website_server.server_close()
        kill_switch.set()
        live_refresh_server.shutdown()
        website_server.shutdown()

def main(args):
    config_file = os.path.join(SCRIPT_DIR, 'config.json')
    with open(config_file, 'r') as f:
        config = json.load(f)

    if args.command == 'create':
        create_project(config, config_file, args)
    elif args.command == 'build':
        build_project(arguments, config)
    elif args.command == 'watch':
        watch_project(arguments, config)
    elif args.command == 'serve':
        serve_project(arguments, config)


if __name__ == "__main__":
    arguments = parser.parse_args()
    main(arguments)