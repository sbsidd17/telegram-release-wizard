from flask import Flask
app = Flask(__name__)

@app.route('/')
def hello_world():
    app.logger.debug("Root endpoint called")
    return 'Free Storage Server Working'

@app.route('/health')
def health():
    app.logger.debug("Health check endpoint called")
    return 'OK', 200

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
