import os
import json
import numpy as np
from numpy.linalg import norm
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS
import datetime
from app.models import ChatHistory
from app import db, create_app
from flask_socketio import SocketIO, emit
from app.utils import parse_file

app = create_app()
socketio = SocketIO(app, cors_allowed_origins="*")

CORS(app)

OLLAMA_API_URL = "http://localhost:11434/api/"
DATA_FOLDER = "data"
EMBEDDINGS_FOLDER = "embeddings"

# Ensure necessary directories exist
os.makedirs(DATA_FOLDER, exist_ok=True)
os.makedirs(EMBEDDINGS_FOLDER, exist_ok=True)

@socketio.on('connect')
def handle_connect():
    print("Client connected")

@socketio.on('disconnect')
def handle_disconnect():
    print("Client disconnected")

@socketio.on('get_chats')
def handle_get_chats():
    try:
        # Ambil semua chat dari database
        chats = ChatHistory.query.order_by(ChatHistory.timestamp).all()

        # Format data untuk dikirim ke klien
        chat_list = [
            {'role': chat.role, 'message': chat.message, 'timestamp': chat.timestamp.isoformat()}
            for chat in chats
        ]

        # Kirim data ke klien
        emit('chat_history', chat_list)
    except Exception as e:
        emit('error', {'error': f"Gagal mengambil data chat: {str(e)}"})

    
# Function to request embeddings
def get_embeddings_from_ollama(modelname, chunk):
    try:
        response = requests.post(
            OLLAMA_API_URL + "embeddings",
            json={"model": modelname, "prompt": chunk},
        )
        response.raise_for_status()
        return response.json().get("embedding", [])
    except requests.exceptions.RequestException as e:
        print(f"Error connecting to Ollama API for embeddings: {e}")
        return []

# Function to request chat response
def chat_with_ollama(model, messages):
    try:
        response = requests.post(
            OLLAMA_API_URL + "chat",
            json={"model": model, "messages": messages},
        )
        
        if response.headers.get("Content-Type") == "application/x-ndjson":
            full_response = ""
            for line in response.text.splitlines():
                try:
                    json_data = json.loads(line)
                    if "message" in json_data and "content" in json_data["message"]:
                        full_response += json_data["message"]["content"]
                        if json_data.get("done"):
                            break
                except json.JSONDecodeError as e:
                    print(f"Error parsing line: {line}")
                    print(f"JSONDecodeError: {e}")
            return full_response
    except requests.exceptions.RequestException as e:
        print(f"Error during request: {e}")
        return "Maaf, saya tidak bisa terhubung ke API."


# Get or generate embeddings
def get_embeddings(filename, modelname, chunks):
    embedding_file_path = os.path.join(EMBEDDINGS_FOLDER, f"{filename}.json")
    
    if os.path.exists(embedding_file_path):
        print(f"Embedding file {filename}.json already exists. Loading embeddings...")
        with open(embedding_file_path, "r") as f:
            embeddings = json.load(f)
    else:
        print(f"Embedding file {filename}.json not found. Generating new embeddings...")
        embeddings = [
            get_embeddings_from_ollama(modelname, chunk) for chunk in chunks
        ]
        save_embeddings(filename, embeddings)
    
    return embeddings

# Save embeddings
def save_embeddings(filename, embeddings):
    with open(os.path.join(EMBEDDINGS_FOLDER, f"{filename}.json"), "w") as f:
        json.dump(embeddings, f)

# Cosine similarity
def find_most_similar(needle, haystack):
    needle_norm = norm(needle)
    similarity_scores = [
        np.dot(needle, item) / (needle_norm * norm(item)) for item in haystack
    ]
    return sorted(zip(similarity_scores, range(len(haystack))), reverse=True)

# Load data and embeddings on startup
# Load data and embeddings on startup
all_paragraphs = []
filenames = []

# Clear existing embeddings
embeddings = []  # Initialize embeddings as an empty list

# Load paragraphs from files in the DATA_FOLDER
for file in os.listdir(DATA_FOLDER):
    file_path = os.path.join(DATA_FOLDER, file)
    if file.lower().endswith((".txt", ".pdf", ".docx")):
        paragraphs = parse_file(file_path)
        if paragraphs:
            all_paragraphs.extend(paragraphs)
            filenames.append(file)

# Generate embeddings for the newly loaded paragraphs
embeddings = get_embeddings("data_api", "nomic-embed-text", all_paragraphs)


def save_chat_to_db(role, message):
    try:
        new_chat = ChatHistory(role=role, message=message, timestamp=datetime.datetime.now())
        db.session.add(new_chat)
        db.session.commit()
    except Exception as e:
        print(f"Error saving chat to database: {e}")


@app.route('/chat-history', methods=['GET'])
def get_chat_history():
    try:
        chats = ChatHistory.query.order_by(ChatHistory.timestamp.asc()).all()
        chat_history = [{"role": chat.role, "message": chat.message, "timestamp": chat.timestamp} for chat in chats]
        return jsonify({"chat_history": chat_history})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    
# Flask route
@app.route('/ask', methods=['POST'])
def ask():
    user_input = request.json.get('question')
    if not user_input:
        return jsonify({"error": "Pertanyaan wajib diisi."}), 400

    SYSTEM_PROMPT = (
        "You are an assistant that answers questions only in Bahasa Indonesia. "
        "Your answers must be based solely on the provided context from the database. "
        "If the answer cannot be determined, respond with 'Maaf, saya tidak tahu.' "
    )

    from app.models import Document

    # Simpan pertanyaan ke database
    save_chat_to_db('user', user_input)

    # Buat embedding untuk pertanyaan
    prompt_embedding = get_embeddings_from_ollama("nomic-embed-text", user_input)
    if not prompt_embedding:
        return jsonify({"error": "Gagal menghasilkan embedding untuk pertanyaan."}), 500

    # Ambil semua dokumen dari database
    documents = Document.query.all()
    contexts = [doc.content for doc in documents]

    # Cari dokumen paling relevan
    embeddings = [get_embeddings_from_ollama("nomic-embed-text", content) for content in contexts]
    most_similar = find_most_similar(prompt_embedding, embeddings)
    relevant_contexts = "\n".join(contexts[idx] for _, idx in most_similar[:5])

    # Gabungkan sistem prompt dan konteks
    full_prompt = SYSTEM_PROMPT + relevant_contexts

    # Panggil API LLM untuk mendapatkan jawaban
    response = chat_with_ollama(
        model="llama3",
        messages=[
            {"role": "system", "content": full_prompt},
            {"role": "user", "content": user_input},
        ]
    )

    save_chat_to_db('bot', response)

    return jsonify({"response": response})



if __name__ == "__main__":
    app.run(debug=True)
