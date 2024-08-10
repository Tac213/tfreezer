# -*- coding: utf-8 -*-
# author: Tac
# contact: cookiezhx@163.com

import requests


def main():
    r = requests.get("https://api.github.com/user", auth=("user", "pass"))
    print(r.status_code)
    print(r.headers["content-type"])
    print(r.encoding)
    print(r.text)
    r.json()


if __name__ == "__main__":
    main()
