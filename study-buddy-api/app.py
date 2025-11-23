from flask import Flask, jsonify, request
import psycopg2
import os

app = Flask(__name__)

# Database connection function
def get_db_connection():
    conn = psycopg2.connect(
        host=os.getenv("DB_HOST", "db"),
        database=os.getenv("DB_NAME", "studybuddy"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", "postgres")
    )
    return conn


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "service": "study-buddy"}), 200


@app.route("/sessions", methods=["POST"])
def create_session():
    data = request.get_json() or {}
    topic = data.get("topic")
    minutes = data.get("minutes")

    if not topic or not isinstance(minutes, (int, float)):
        return jsonify({"error": "Invalid input"}), 400

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute(
        "INSERT INTO sessions (topic, minutes) VALUES (%s, %s) RETURNING id;",
        (topic, minutes)
    )
    session_id = cur.fetchone()[0]

    conn.commit()
    cur.close()
    conn.close()

    return jsonify({"message": "session logged", "id": session_id}), 201


@app.route("/sessions", methods=["GET"])
def list_sessions():
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("SELECT id, topic, minutes FROM sessions;")
    rows = cur.fetchall()

    cur.close()
    conn.close()

    sessions = [{"id": r[0], "topic": r[1], "minutes": r[2]} for r in rows]

    return jsonify({"count": len(sessions), "sessions": sessions}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
