""" Convert HAR (HTTP Archive) to YAML/JSON testcase for HttpRunner.

Usage:
    # convert to JSON format testcase
    $ hrun har2ncase demo.har

    # convert to YAML format testcase
    $ hrun har2ncase demo.har -2y

"""
import sys
from argparse import ArgumentParser

from loguru import logger
from sentry_sdk import capture_message
from pathlib import Path

from requests_wework.har2ncase.core import HarParser
from requests_wework.har2ncase.make import call_gen_py_testcase


def init_har2ncase_parser(parser:ArgumentParser):
    """ HAR converter: parse command line options and run commands.
    """

    group=parser.add_mutually_exclusive_group()
    group.add_argument("--har_source_file", nargs="?",  dest="har_source_file",help="Specify HAR source file")
    group.add_argument("--har_source_dir", dest="har_source_dir", nargs="?", help="Specify HAR source directory,The suffix of all files in the HAR source must be. Har")
    parser.add_argument(
        "-2y",
        "--to-yml",
        "--to-yaml",
        dest="to_yaml",
        action="store_true",
        help="Convert to YAML format, if not specified, convert to pytest format by default.",
    )
    parser.add_argument(
        "-2j",
        "--to-json",
        dest="to_json",
        action="store_true",
        help="Convert to JSON format, if not specified, convert to pytest format by default.",
    )
    parser.add_argument(
        "--filter",
        help="Specify filter keyword, only url include filter string will be converted.",
    )
    parser.add_argument(
        "--exclude",
        help="Specify exclude keyword, url that includes exclude string will be ignored, "
             "multiple keywords can be joined with '|'",
    )


    return parser


def main_har2ncase(args):
    if args.to_yaml:
        output_file_type = "YAML"
    elif args.to_json:
        output_file_type = "JSON"
    else:
        output_file_type = "pytest"

    capture_message(f"har2ncase {output_file_type}")
    # 以下代码是lnz添加
    # 判断传递了har文件名，就去循环转换文件
    # todo 实现转换未json.yaml 格式
    if args.har_source_dir:
        p = Path(args.har_source_dir)
        # 循环迭代转换har目录下的文件（lnz添加）
        for sub_file_name in p.iterdir():
            # 检查是文件后缀名是否包含.har
            if sub_file_name.suffix.find('.har') != -1:
                har_source_file=str(sub_file_name)
                output_testcase_file=HarParser(har_source_file).gen_testcase(output_file_type)
                call_gen_py_testcase(output_testcase_file)

            else:
                logger.error("HAR file not found,The suffix of all files in the folder must be. Har")
                sys.exit(1)

    else:
        output_testcase_file=HarParser(args.har_source_file).gen_testcase(output_file_type)
        call_gen_py_testcase(output_testcase_file)

    return 0
