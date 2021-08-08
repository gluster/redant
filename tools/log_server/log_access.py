from flask import Flask
from flask_autoindex import AutoIndex
import configparser

app = Flask(__name__)

if __name__ == "__main__":
    config = configparser.ConfigParser()
    config.read('log_access.ini')
    ppath = config['logpath']['path']
    fport = int(config['logpath']['port'])
    AutoIndex(app, browse_root=ppath)
    app.run(host='0.0.0.0', port=fport)
