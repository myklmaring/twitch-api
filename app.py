from flask import Flask, request
import requests
app = Flask(__name__)


@app.route("/", methods=['POST'])
def hello_world():
    return "<p>Hello, World!</p>"


if __name__ == "__main__":
    app.run()
