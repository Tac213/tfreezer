import requests


def main():
    r = requests.get("https://api.github.com/user", auth=("user", "pass"), timeout=10)
    print(r.status_code)
    print(r.headers["content-type"])
    print(r.encoding)
    print(r.text)
    r.json()


if __name__ == "__main__":
    main()
