import sys
import time
import json
from pathlib import Path
from functools import wraps

from flask import Flask, jsonify, request, Response, stream_with_context
from flask_cors import CORS

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from config import FLASK_SECRET_KEY, FLASK_DEBUG, FLASK_PORT
from src.rag_chain import build_rag_chain, build_streaming_chain, PROMPT
from src.vectorstore import load_vectorstore, get_retriever
from src.auth import register_user, login_user, verify_token
from src.logger import get_logger
from src.chat_store import (
    create_session, get_sessions, update_session_title, 
    delete_session, save_message, get_messages
)

log = get_logger(__name__)

def require_auth(f):
    @wraps(f)
    def decorated(*args,**kwargs):
        auth_header = request.headers.get("Authorization","")
        if not auth_header.startswith("Bearer"):
            return jsonify("error","Missing or invalid token"),401
        token = auth_header.split(" ")[1]
        result = verify_token(token)
        if not result["valid"]:
            return jsonify({"error":result["error"]}),401
        # pyrefly: ignore [missing-attribute]
        request.user_id = result["user_id"]
        # pyrefly: ignore [missing-attribute]
        request.user_email = result["email"]
        return f(*args,**kwargs)
        
    return decorated

def create_app():
    app = Flask(__name__)
    app.secret_key = FLASK_SECRET_KEY
    app.url_map.strict_slashes = False
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    log.info("Initializing RAG pipeline...")
    try:
        vs = load_vectorstore()
        retriever = get_retriever(vs)
        chain = build_rag_chain(retriever)
        app.config["CHAIN"] = chain
        app.config["RETRIEVER"] = retriever
        log.info("RAG Pipeline ready")
    except Exception as e:
        log.error(f"Failed to init RAG PIPELINE: {e}")
        app.config["CHAIN"] = None
        app.config["RETRIEVER"] = None

    @app.route("/api/health")
    def health():
        ready = app.config.get("CHAIN") is not None
        return jsonify({
            "status":"ok" if ready else "degraded",
            "model": "gpt-4o",
            "vectors":20475,
            "ready": ready,
        }), 200 if ready else 503

    
    @app.route("/api/auth/register", methods=["POST"])
    def register():
        data = request.get_json(silent=True) or {}
        email = (data.get("email") or "").strip().lower()
        password = (data.get("password") or "").strip()
        full_name = (data.get("full_name") or "").strip()

        if not email or not password or not full_name:
            return jsonify({"error": "Email, password and full name are required"}), 400
        
        result = register_user(email, password, full_name)
        if not result["success"]:
            return jsonify({"error": result["error"]}), 409
        
        log.info(f"New user registered: {email}")
        return jsonify(result), 201 
    
    @app.route("/api/auth/login", methods=["POST"])
    def login():
        data = request.get_json(silent=True) or {}
        email = (data.get("email") or "").strip().lower()
        password = (data.get("password") or "").strip()

        if not email or not password:
            return jsonify({"error": "Email and password are required"}), 400
        
        result = login_user(email, password)
        if not result["success"]:
            return jsonify({"error": result["error"]}), 401
        
        return jsonify(result), 200
    
    @app.route("/api/auth/me")
    @require_auth
    def me():
        return jsonify({
            # pyrefly: ignore [missing-attribute]
            "user_id": request.user_id,
            # pyrefly: ignore [missing-attribute]
            "email": request.user_email
        })
    
    @app.route("/api/sessions", methods=["GET"])
    @require_auth
    def list_sessions():
        # pyrefly: ignore [missing-attribute]
        sessions = get_sessions(request.user_id)
        return jsonify({"sessions": sessions})

    @app.route("/api/sessions", methods=["POST"])
    @require_auth
    def new_session():
        data = request.get_json(silent=True) or {}
        title = data.get("title", "New Chat")
        # pyrefly: ignore [missing-attribute]
        session = create_session(request.user_id, title)
        return jsonify(session), 201
    
    @app.route("/api/sessions/<session_id>", methods=["DELETE"])
    @require_auth
    def remove_session(session_id):
        # pyrefly: ignore [missing-attribute]
        delete_session(session_id, request.user_id)
        return jsonify({"success": True})
    
    @app.route("/api/sessions/<session_id>/messages", methods=["GET"])
    @app.route("/api/sessions/<session_id>", methods=["GET"])
    @require_auth
    def list_messages(session_id):
        messages = get_messages(session_id)
        return jsonify({"messages": messages})
    
    @app.route("/api/chat/stream",methods=["POST"])
    @require_auth
    def chat_stream():
        retriever = app.config.get("RETRIEVER")
        if retriever is None:
            return jsonify({"error":"RAG pipeline not ready"}), 503
        data = request.get_json(silent=True) or {}
        question = (data.get("question") or "").strip()
        session_id = (data.get("session_id") or "").strip()

        if not question:
            return jsonify({"error":"No question provided"}), 400
        if not session_id:
            return jsonify({"error":"No Session_id provided"})
        if len(question) > 2000:
            return jsonify({"error":"Question too long"})
        
        save_message(session_id,"user",question)

        # pyrefly: ignore [missing-attribute]
        sessions = get_sessions(request.user_id)
        current = next((s for s in sessions if s["id"] == session_id),None)
        if current and current["title"] == "New Chat":
            # pyrefly: ignore [bad-argument-type, unsupported-operation]
            title = question[:50] + ("..." if len(question) > 50 else "")
            update_session_title(session_id,title)

        from openai import OpenAI
        from config import OPENAI_API_KEY, OPENAI_LLM_MODEL, LLM_TEMPERATURE

        def generate():
            try:
                docs = retriever.invoke(question)
                seen = set()
                sources = []
                for doc in docs:
                    page = doc.metadata.get("page","?")
                    if page not in seen:
                        seen.add(page)
                        sources.append({
                            "page": page,
                            "preview": doc.page_content[:150].replace("\n"," ") + "..."
                        })
                context = "\n\n".join([doc.page_content for doc in docs])
                prompt_text = PROMPT.format(context=context, question=question)

                client = OpenAI(api_key=OPENAI_API_KEY)
                stream = client.chat.completions.create(
                    model=OPENAI_LLM_MODEL,
                    temperature=LLM_TEMPERATURE,
                    max_tokens=1024,
                    stream=True,
                    messages=[{"role":"user","content": prompt_text}]
                )

                full_answer = ""
                start = time.time()

                for chunk in stream:
                    delta = chunk.choices[0].delta.content
                    if delta:
                        full_answer += delta
                        yield f"data: {json.dumps({'type': 'token', 'content': delta})}\n\n"
                
                duration_ms = round((time.time() - start) * 1000)

                save_message(session_id,"bot",full_answer, sources=sources, duration_ms=duration_ms)

                yield f"data: {json.dumps({'type':'sources', 'sources': sources })}\n\n"
                yield f"data: {json.dumps({'type':'done'})}\n\n"
            
            except Exception as e:
                log.error(f"Streaming error: {e}")
                yield f"data: {json.dumps({'type':'error','content':str(e)})}\n\n"
        
        return Response(
            stream_with_context(generate()),
            mimetype="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "X-Accel-Buffering": "no",
            }
        )





    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"error": "Route not found"}), 404
    
    @app.errorhandler(500)
    def server_error(e):
        return jsonify({"error": "Internal server error"}), 500
    
    return app


if __name__ == "__main__":
    app = create_app()
    log.info(f"MedBot starting on port {FLASK_PORT}")
    app.run(host="0.0.0.0",port=FLASK_PORT, debug=FLASK_DEBUG)