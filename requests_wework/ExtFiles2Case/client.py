import argparse

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from requests_wework.ExtFiles2Case import main_ext_file2case, init_ext_file2case_parser


def main():
    """ API test: parse command line options and run commands.
    """
    # 实例化解析器
    parser = argparse.ArgumentParser()
    # 添加解析器参数
    init_ext_file2case_parser(parser)
    # sys.argv长度=1 表示只有当前文件这个参数，所以打印帮助文档
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(0)
    args = parser.parse_args()

    # sys.stdout.write(str(args))
    # 调用生成用例的方法
    main_ext_file2case(args)


if __name__ == "__main__":
    main()
