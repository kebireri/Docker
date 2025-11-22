from flask import Flask, jsonify

app = Flask(__name__)

@app.route("/ping")

def ping():
    data = {
        "status": "ok", 
        "service": "pinger"
        }

    return jsonify(data)
    
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)