import cmd
import argparse
import shlex
import sys
import re

from lib.wpapi import WPApi, WordPressApiNotV2
from lib.requestsession import RequestSession
from lib.console import Console
from lib.infodisplayer import InfoDisplayer

class ArgumentParser(argparse.ArgumentParser):
    """
    Wrapper for argparse.ArgumentParser (especially the help function that quits the application after display)
    """
    def __init__(self, prog="", description=""):
        argparse.ArgumentParser.__init__(self, prog=prog, add_help=False, description=description)
        self.add_argument("--help", "-h", help="print this help", action="store_true")
        self.should_help = True

    def custom_parse_args(self, args):
        args = self.parse_args(shlex.split(args))
        if args.help:
            if self.should_help:
                self.print_help(sys.stdout)
                print()
            self.should_help = False
            return None
        if self.should_help:
            return args
        else:
            return None

    def error(self, message):
        if self.should_help:
            self.print_help(sys.stdout)
            print()
            self.should_help = False

class InteractiveShell(cmd.Cmd):
    """
    The interactive shell for the application
    """
    intro = """
    Entering interactive session
    Use the 'help' command to get a list of available commands and parameters, 'exit' to quit
    `command -h` gives more details about a command
    """
    prompt = "> "

    def __init__(self, target, session, version):
        cmd.Cmd.__init__(self)
        self.target = target
        InteractiveShell.prompt = Console.red + target + Console.normal + " > "
        self.session = session
        self.version = version
        self.scanner = WPApi(self.target, session=session)

    def do_exit(self, arg):
        'Exit wp-json-scraper'
        return True
    
    def do_show(self, arg):
        'Shows information about parameters in memory'
        parser = ArgumentParser(prog='show', description='show information about global parameters')
        parser.add_argument("what", choices=['all', 'target', 'proxy', 'cookies', 'credentials', 'version'],
        help='choose the information to be displayed', default='all')
        args = parser.custom_parse_args(arg)
        if args is None:
            return
        if args.what == 'all' or args.what == 'target':
            print("Target: %s" % self.target)
        if args.what == 'all' or args.what == 'proxy':
            proxies = self.session.get_proxies()
            if proxies is not None and len(proxies) > 0:
                print ("Proxies:")
                for key, value in proxies.items():
                    print("\t%s: %s" % (key, value))
            else:
                print ("Proxy: none")
        if args.what == 'all' or args.what == 'cookies':
            cookies = self.session.get_cookies()
            if len(cookies) > 0:
                print("Cookies:")
                for key, value in cookies.items():
                    print("\t%s: %s" % (key, value))
            else:
                print("Cookies: none")
        if args.what == 'all' or args.what == 'credentials':
            credentials = self.session.get_creds()
            if credentials is not None:
                creds_str = "Credentials: "
                for el in credentials:
                    creds_str += el + ":"
                print(creds_str[:-1])
            else:
                print("Credentials: none")
        if args.what == 'all' or args.what == 'version':
            print("WPJsonScraper version: %s" % self.version)
        print()
    
    def do_set(self, arg):
        'Sets a global parameter of WPJsonScanner'
        parser = ArgumentParser(prog='set', description='sets global parameters for WPJsonScanner')
        parser.add_argument("what", choices=['target', 'proxy', 'cookies', 'credentials'],
        help='the parameter to set')
        parser.add_argument("value", type=str, help='the new value of the parameter (for cookies, set as cookie string: "n1=v1; n2=v2")')
        args = parser.custom_parse_args(arg)
        if args is None:
            return
        if args.what == 'target':
            self.target = args.value
            if re.match(r'^https?://.*$', self.target) is None:
                self.target = "http://" + self.target
            if re.match(r'^.+/$', self.target) is None:
                self.target += "/"
            InteractiveShell.prompt = Console.red + self.target + Console.normal + " > "
            print("target = %s" % args.value)
            self.scanner = WPApi(self.target, session=self.session)
            Console.log_info("Cache is erased but session stays the same (with cookies and authorization)")
        elif args.what == 'proxy':
            self.session.set_proxy(args.value)
            print("proxy = %s" % args.value)
        elif args.what == 'cookies':
            self.session.set_cookies(args.value)
            print("Cookies set!")
        elif args.what == "credentials":
            authorization_list = args.value.split(':')
            if len(authorization_list) == 1:
                authorization = (authorization_list[0], '')
            elif len(authorization_list) >= 2:
                authorization = (authorization_list[0],
                ':'.join(authorization_list[1:]))
            self.session.set_creds(authorization)
            print("Credentials set!")
        print()

    def do_list(self, arg):
        'Gets the list of something from the server'
        parser = ArgumentParser(prog='list', description='gets a list of something from the server')
        parser.add_argument("what", choices=[
            'posts', 
            #'post-revisions', 
            #'wp-blocks', 
            'categories',
            'tags',
            'pages',
            'comments',
            'media',
            'users',
            #'themes',
            #'search-results',
            'all',
            ],
            help='what to list')
        parser.add_argument("--json", "-j", help="list and store as json to the specified file")
        parser.add_argument("--csv", "-c", help="list and store as csv to the specified file")
        parser.add_argument("--limit", "-l", type=int, help="limit the number of results")
        parser.add_argument("--start", "-s", type=int, help="start at the given index")
        parser.add_argument("--no-cache", dest="cache", action="store_false", help="don't lookup in cache and ask the server")
        args = parser.custom_parse_args(arg)
        if args is None:
            return
        if args.what == "all" or args.what == "posts":
            print("Posts list")
            try:
                posts = self.scanner.get_posts(comments=False, start=args.start, num=args.limit, force=not args.cache)
                InfoDisplayer.display_posts(posts)
            except WordPressApiNotV2:
                Console.log_error("The API does not support WP V2")
            print()
        if args.what == "all" or args.what == "categories":
            print("Categories list") # TODO
            print()
        if args.what == "all" or args.what == "tags":
            print("Tags list") # TODO
            print()
        if args.what == "all" or args.what == "pages":
            print("Pages list") # TODO
            print()
        if args.what == "all" or args.what == "comments":
            print("Comments list") # TODO
            print()
        if args.what == "all" or args.what == "media":
            print("Media list") # TODO
            print()
        if args.what == "all" or args.what == "users":
            print("Users list") # TODO
            print()


def start_interactive(target, session, version):
    """
    Starts a new interactive session
    """
    InteractiveShell(target, session, version).cmdloop()