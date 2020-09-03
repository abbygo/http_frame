## http_frame是一套接口测试框架，可轻松生成测试用例，

## 主要特点

- 集成了request库

- 自定义yaml或json格式的用例

- 支持postman中的json格式、Har格式数据自动生成用例，

- 支持批量生成测试用例

- 集成了pytest测试框架

- 集成了allure测试框架

## 用法

```shell
#安装pyinstaller
pip install pyinstaller
#进入到requests_wework\ExtFiles2Case\client.py目录下，执行生成exe单文件的命名，-n 是指定exe应用的名称
pyinstaller -F client.py -n ext2case
#在client.py文件的目录下，产生dist文件夹，文件夹里有一个ext2case.exe;复制ext2case.exe到虚拟环境下;eg：D:\tutorial-env\Scripts；
#删除刚才产生的多余文件后，执行如下命令


ext2case -h
usage: ext2case [-h] (-F [HAR_SOURCE_FILE] | -D [HAR_SOURCE_DIR] | -P [POSTMAN_JSON_FILE]) [-2y] [-2j] [--filter FILTER]
                [--exclude EXCLUDE]

optional arguments:
  -h, --help            show this help message and exit
  -F [HAR_SOURCE_FILE], --har_source_file [HAR_SOURCE_FILE]
                        Specify HAR source file
  -D [HAR_SOURCE_DIR], --har_source_dir [HAR_SOURCE_DIR]
                        Specify HAR source directory,The suffix of all files in the HAR source must be. Har
  -P [POSTMAN_JSON_FILE], --postman_json_file [POSTMAN_JSON_FILE]
                        Specify postman json source file
  -2y, --to-yml, --to-yaml
                        Convert to YAML format, if not specified, convert to pytest format by default.
  -2j, --to-json        Convert to JSON format, if not specified, convert to pytest format by default.
  --filter FILTER       Specify filter keyword, only url include filter string will be converted.
  --exclude EXCLUDE     Specify exclude keyword, url that includes exclude string will be ignored, multiple keywords can
                        be joined with '|'


```



- postman导出的json文件转case命令

ext2case  -P  json文件全路径

eg:

```shell
(tutorial-env) C:\Users\lnz\PycharmProjects\http_homework>ext2case -P C:\Users\lnz\PycharmProjects\http_homework\requests_we
work\data\Json\postman_collection.json
2020-09-03 20:28:18.828 | INFO     | requests_wework.ExtFiles2Case.core:make_output_dir:629 - Create a new directory : C:\Us
ers\lnz\PycharmProjects\http_homework\requests_wework\data\output_dir
2020-09-03 20:28:18.830 | INFO     | requests_wework.ExtFiles2Case.core:call_gen_python_testcase_by_postman:284 - Start to g
enerate testcase from C:\Users\lnz\PycharmProjects\http_homework\requests_wework\data\Json\postman_collection.json
2020-09-03 20:28:18.837 | INFO     | requests_wework.ExtFiles2Case.make:gen_py_testcase_no_yaml:222 - testcase to py format.

2020-09-03 20:28:18.850 | INFO     | requests_wework.ExtFiles2Case.make:format_pytest_with_black:15 - format pytest cases wi
th black ...
reformatted C:\Users\lnz\PycharmProjects\http_homework\requests_wework\data\output_dir\test_postman_collection.py
All done! ✨ � ✨
1 file reformatted.
2020-09-03 20:28:19.388 | INFO     | requests_wework.ExtFiles2Case.make:gen_py_testcase_no_yaml:260 - Generate py testcase s
uccessfully: C:\Users\lnz\PycharmProjects\http_homework\requests_wework\data\output_dir\test_postman_collection.py

(tutorial-env) C:\Users\lnz\PycharmProjects\http_homework>

```

查看用例文件

```python
class Testpostman_collection(PareStep):
    config = Config("request methods testcase: reference testcase").verify(False)

    def test_get(self):
        self.start(
            Step(
                RunRequest()
                .get("https://postman-echo.com/get")
                .with_params(**{"foo1": "bar1", "foo2": "bar2"})
                .validate()
                .assert_equal("status_code", 200)
            )
        )

    def test_post(self):
        self.start(
            Step(
                RunRequest()
                .post("https://postman-echo.com/post")
                .with_data({"foo1": "bar1", "foo2": "bar2"})
                .validate()
                .assert_equal("status_code", 200)
            )
        )

    def test_put(self):
        self.start(
            Step(
                RunRequest()
                .put("https://postman-echo.com/put")
                .with_data("This is expected to be sent back as part of response body.")
                .validate()
                .assert_equal("status_code", 200)
            )
        )

```


