from flask import Flask
from flask_autoindex import AutoIndex
import configparser


def main():
    config = configparser.ConfigParser()

    # INI file validation.
    try:
        with open('log_access.ini') as f:
            config.read('log_access.ini')
    except IOError:
        print("log_access.ini doesn't exist. Hence taking a default dict."
              f" with path : /tmp/redant and port : 5000")
        config = {"serverdata" : {"path" : "/tmp/redant", "port": 5000}}

    # Path extraction and validation.
    try:
        ppath = config['serverdata']['path']
    except Exception as KeyError:
        print("Key error in path. Defaulting to /tmp/redant as log path.")
        ppath = "/tmp/redant"

    # Port extraction and validation.
    try:
        fport = int(config['serverdata']['port'])
    except Exception as KeyError:
        print("Key error in port. Defaulting to 5000.")
        fport = 5000
    except Exception as ValueError:
        print("Value error in port. Defaulting to 5000.")
        fport = 5000

    app = Flask(__name__)
    AutoIndex(app, browse_root=ppath)
    app.run(host='0.0.0.0', port=fport)

if __name__ == "__main__":
    main()
