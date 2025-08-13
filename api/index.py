from flask import Flask, request, jsonify
# from flask_cors import CORS
from chatbot_backend import get_answer

import logging

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

app = Flask(__name__)
# CORS(app)


@app.route("/healthz", methods=["GET"])
def healthz():
    return "ok", 200


@app.route("/api/healthchecker", methods=["GET"])
def healthchecker():
    return {"status": "success", "message": "Integrate Flask Framework with Next.js"}


@app.route("/api/chat", methods=["POST"])
def chat():
    try:
        data = request.get_json(force=True)
        logging.debug("📩 Received:", data)
        print("📩 Received:", data)

        # ✅ Extract last message's content
        messages = data.get("messages", [])
        if not messages or "content" not in messages[-1]:
            print("❌ No valid message found")
            return jsonify({"error": "No valid message found"}), 400

        query = messages[-1]["content"]
        print("💬 Extracted query:", query)

        result = get_answer(query)
        return jsonify(result)

    except Exception as e:
        print("🔥 Error in chat route:", str(e))
        return jsonify({"error": "Server error"}), 500


if __name__ == '__main__':
    app.run(debug=True)
