from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)


@app.route("/api/health")
def health():
    return jsonify({"success": True, "message": "Parse Tree Generator backend is running"})


@app.route("/api/parse", methods=["POST"])
def parse():
    data = request.get_json(silent=True) or {}
    grammar = data.get("grammar", "").strip()
    string = data.get("string", "")
    if not grammar:
        return jsonify({"success": False, "error": "Grammar is empty"}), 400
    # TODO: validate grammar, convert to CNF, run CYK, build the tree
    return jsonify({"message": "Parsing not implemented yet", "grammar": grammar, "string": string})


if __name__ == "__main__":
    app.run(port=5000, debug=True)