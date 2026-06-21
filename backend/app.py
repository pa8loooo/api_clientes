from flask import Flask, request, jsonify
from flask_cors import CORS
import mysql.connector
import os
import time

app = Flask(__name__)
CORS(app)

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "mysql"),
    "port": int(os.getenv("DB_PORT", 3306)),
    "user": os.getenv("DB_USER", "appuser"),
    "password": os.getenv("DB_PASSWORD", "apppassword"),
    "database": os.getenv("DB_NAME", "clientesdb"),
}

def get_connection(retries=10, delay=3):
    """Tenta conectar ao MySQL com retentativas (útil no startup)."""
    for attempt in range(retries):
        try:
            conn = mysql.connector.connect(**DB_CONFIG)
            return conn
        except mysql.connector.Error as e:
            print(f"[{attempt+1}/{retries}] Aguardando MySQL... ({e})")
            time.sleep(delay)
    raise Exception("Não foi possível conectar ao MySQL após várias tentativas.")


def init_db():
    """Cria a tabela de clientes se não existir."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS clientes (
            id          INT AUTO_INCREMENT PRIMARY KEY,
            nome        VARCHAR(120) NOT NULL,
            email       VARCHAR(120) NOT NULL UNIQUE,
            telefone    VARCHAR(30),
            criado_em   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    cursor.close()
    conn.close()
    print("Banco de dados inicializado.")


# ──────────────────────────────────────────────
# ROTAS
# ──────────────────────────────────────────────

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"}), 200


# ── CREATE ──
@app.route("/users", methods=["POST"])
def create_user():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Body JSON ausente"}), 400

    nome     = data.get("nome", "").strip()
    email    = data.get("email", "").strip()
    telefone = data.get("telefone", "").strip()

    if not nome or not email:
        return jsonify({"error": "Campos 'nome' e 'email' são obrigatórios"}), 400

    try:
        conn   = get_connection(retries=1)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO clientes (nome, email, telefone) VALUES (%s, %s, %s)",
            (nome, email, telefone or None),
        )
        conn.commit()
        new_id = cursor.lastrowid
        cursor.close()
        conn.close()
        return jsonify({"message": "Cliente criado com sucesso", "id": new_id}), 201
    except mysql.connector.IntegrityError:
        return jsonify({"error": "E-mail já cadastrado"}), 409
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ── READ ALL ──
@app.route("/users", methods=["GET"])
def list_users():
    try:
        conn   = get_connection(retries=1)
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id, nome, email, telefone, criado_em FROM clientes ORDER BY id DESC")
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        # Serializa datetime para string
        for row in rows:
            if row.get("criado_em"):
                row["criado_em"] = str(row["criado_em"])
        return jsonify(rows), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ── READ ONE ──
@app.route("/users/<int:user_id>", methods=["GET"])
def get_user(user_id):
    try:
        conn   = get_connection(retries=1)
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id, nome, email, telefone, criado_em FROM clientes WHERE id = %s", (user_id,))
        row = cursor.fetchone()
        cursor.close()
        conn.close()
        if not row:
            return jsonify({"error": "Cliente não encontrado"}), 404
        if row.get("criado_em"):
            row["criado_em"] = str(row["criado_em"])
        return jsonify(row), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ── UPDATE ──
@app.route("/users/<int:user_id>", methods=["PUT"])
def update_user(user_id):
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Body JSON ausente"}), 400

    nome     = data.get("nome", "").strip()
    email    = data.get("email", "").strip()
    telefone = data.get("telefone", "").strip()

    if not nome or not email:
        return jsonify({"error": "Campos 'nome' e 'email' são obrigatórios"}), 400

    try:
        conn   = get_connection(retries=1)
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE clientes SET nome=%s, email=%s, telefone=%s WHERE id=%s",
            (nome, email, telefone or None, user_id),
        )
        conn.commit()
        affected = cursor.rowcount
        cursor.close()
        conn.close()
        if affected == 0:
            return jsonify({"error": "Cliente não encontrado"}), 404
        return jsonify({"message": "Cliente atualizado com sucesso"}), 200
    except mysql.connector.IntegrityError:
        return jsonify({"error": "E-mail já em uso por outro cliente"}), 409
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ── DELETE ──
@app.route("/users/<int:user_id>", methods=["DELETE"])
def delete_user(user_id):
    try:
        conn   = get_connection(retries=1)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM clientes WHERE id = %s", (user_id,))
        conn.commit()
        affected = cursor.rowcount
        cursor.close()
        conn.close()
        if affected == 0:
            return jsonify({"error": "Cliente não encontrado"}), 404
        return jsonify({"message": "Cliente removido com sucesso"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ──────────────────────────────────────────────

if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000, debug=False)
