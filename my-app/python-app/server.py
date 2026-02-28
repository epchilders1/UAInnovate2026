from flask import Flask, request, jsonify
from flask_cors import CORS
import json
from jarvis import Jarvis


app = Flask(__name__)
CORS(app)
jarvis = Jarvis()

@app.route("/ask_jarvis", methods=['POST'])
async def ask_jarvis():
    data = request.get_json()
    text = data.get("question")
    response = await jarvis.ask_jarvis(text=text)
    return json.dumps(response)

if __name__ == "__main__":
    app.run(port=5001)