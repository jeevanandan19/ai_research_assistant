"""
AI Research Assistant Agent — Flask Application
Compatible with LangChain 1.x, langchain-google-genai 4.x
"""
import os
import sys
import uuid
import json
import logging
import traceback
from datetime import datetime
from pathlib import Path

from flask import (
    Flask, request, jsonify, render_template,
    session, send_file, redirect, url_for,
)
from werkzeug.utils import secure_filename

# ── Path setup ────────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent
sys.path.insert(0, str(BASE_DIR))

# ── Load .env ─────────────────────────────────────────────────────
try:
    from dotenv import load_dotenv
    load_dotenv(BASE_DIR / ".env")
except ImportError:
    pass

# ── Config ────────────────────────────────────────────────────────
UPLOAD_FOLDER = BASE_DIR / "uploads"
DATABASE_DIR  = BASE_DIR / "database"
UPLOAD_FOLDER.mkdir(exist_ok=True)
DATABASE_DIR.mkdir(exist_ok=True)

CHUNK_SIZE      = int(os.environ.get("CHUNK_SIZE", 1000))
CHUNK_OVERLAP   = int(os.environ.get("CHUNK_OVERLAP", 200))
RETRIEVAL_K     = int(os.environ.get("RETRIEVAL_K", 5))
EMBEDDING_MODEL = os.environ.get("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
MAX_FILE_MB     = 50

# ── Logging ───────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)

# ── Flask ─────────────────────────────────────────────────────────
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "ai-research-assistant-secret-2024")
app.config["MAX_CONTENT_LENGTH"] = MAX_FILE_MB * 1024 * 1024

# ── In-memory document sessions ───────────────────────────────────
document_sessions: dict = {}


# ─────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────

def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() == "pdf"


def reconstruct_chunks(doc_data: dict):
    """Rebuild Document objects from stored session data."""
    from langchain_core.documents import Document
    return [
        Document(page_content=text, metadata=meta)
        for text, meta in zip(doc_data["chunks"], doc_data["chunk_metadata"])
    ]


def get_session_id() -> str:
    return request.get_json(silent=True, force=True).get("session_id", "") \
        if request.is_json else request.form.get("session_id", "")


# ─────────────────────────────────────────────────────────────────
# Page Routes
# ─────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/upload")
def upload_page():
    return render_template("upload.html")


@app.route("/dashboard")
def dashboard():
    sid = session.get("session_id", "")
    if not sid or sid not in document_sessions:
        return redirect(url_for("upload_page"))
    doc = document_sessions[sid]
    return render_template("dashboard.html",
                           session_id=sid,
                           metadata=doc.get("metadata", {}))


# ─────────────────────────────────────────────────────────────────
# API: Upload & Process PDF
# ─────────────────────────────────────────────────────────────────

@app.route("/api/upload", methods=["POST"])
def upload_pdf():
    if "file" not in request.files:
        return jsonify({"success": False, "error": "No file provided"}), 400

    file = request.files["file"]
    if not file.filename:
        return jsonify({"success": False, "error": "No file selected"}), 400
    if not allowed_file(file.filename):
        return jsonify({"success": False, "error": "Only PDF files are supported"}), 400

    try:
        # ── Save file ─────────────────────────────────────────────
        filename   = secure_filename(file.filename)
        saved_name = f"{uuid.uuid4().hex}_{filename}"
        file_path  = str(UPLOAD_FOLDER / saved_name)
        file.save(file_path)
        logger.info(f"Saved: {file_path}")

        # ── Load PDF ──────────────────────────────────────────────
        from modules.pdf_loader import PDFLoaderModule
        from modules.text_splitter import TextSplitterModule
        from modules.embeddings import EmbeddingsModule
        from modules.vector_store import VectorStoreModule

        loader   = PDFLoaderModule()
        metadata = loader.get_pdf_metadata(file_path)
        docs     = loader.load_pdf(file_path)

        # ── Split ─────────────────────────────────────────────────
        splitter = TextSplitterModule(chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP)
        chunks   = splitter.split_documents(docs)
        stats    = splitter.get_stats(chunks)

        # ── Embed + FAISS ─────────────────────────────────────────
        sid = uuid.uuid4().hex
        faiss_path = str(DATABASE_DIR / f"faiss_{sid}")

        emb_module = EmbeddingsModule(model_name=EMBEDDING_MODEL)
        vs_module  = VectorStoreModule(emb_module, index_path=faiss_path)
        vs_module.create_vector_store(chunks)
        vs_module.save_vector_store(faiss_path)

        # ── Store session ─────────────────────────────────────────
        document_sessions[sid] = {
            "session_id":        sid,
            "file_path":         file_path,
            "original_filename": filename,
            "metadata":          {**metadata, **stats},
            "faiss_path":        faiss_path,
            "chunks":            [c.page_content for c in chunks],
            "chunk_metadata":    [c.metadata     for c in chunks],
            "summary":           None,
            "keywords":          None,
            "insights":          None,
            "chat_history":      [],
            "created_at":        datetime.now().isoformat(),
        }
        session["session_id"] = sid
        logger.info(f"Session {sid}: {len(chunks)} chunks indexed.")

        return jsonify({
            "success":    True,
            "session_id": sid,
            "metadata":   {**metadata, **stats},
            "message":    f"Processed {len(chunks)} chunks from {metadata['total_pages']} pages.",
        })

    except Exception as e:
        logger.error(traceback.format_exc())
        return jsonify({"success": False, "error": str(e)}), 500


# ─────────────────────────────────────────────────────────────────
# API: Summarize
# ─────────────────────────────────────────────────────────────────

@app.route("/api/summarize", methods=["POST"])
def summarize():
    data = request.get_json(silent=True) or {}
    sid  = data.get("session_id") or session.get("session_id", "")

    if not sid or sid not in document_sessions:
        return jsonify({"success": False, "error": "No document loaded. Please upload a PDF first."}), 400

    doc = document_sessions[sid]
    if doc.get("summary"):
        return jsonify({"success": True, "summary": doc["summary"], "cached": True})

    try:
        from modules.summarizer import SummarizerModule
        chunks = reconstruct_chunks(doc)
        result = SummarizerModule().generate_summary(chunks)
        doc["summary"] = result["summary"]
        return jsonify({"success": True, "summary": doc["summary"], "cached": False})
    except Exception as e:
        logger.error(traceback.format_exc())
        return jsonify({"success": False, "error": str(e)}), 500


# ─────────────────────────────────────────────────────────────────
# API: Keywords
# ─────────────────────────────────────────────────────────────────

@app.route("/api/keywords", methods=["POST"])
def extract_keywords():
    data = request.get_json(silent=True) or {}
    sid  = data.get("session_id") or session.get("session_id", "")

    if not sid or sid not in document_sessions:
        return jsonify({"success": False, "error": "No document loaded."}), 400

    doc = document_sessions[sid]
    if doc.get("keywords"):
        return jsonify({"success": True, "keywords": doc["keywords"], "cached": True})

    try:
        from modules.keyword_extractor import KeywordExtractorModule
        chunks = reconstruct_chunks(doc)
        result = KeywordExtractorModule().extract_keywords(chunks)
        doc["keywords"] = result
        return jsonify({"success": True, "keywords": result, "cached": False})
    except Exception as e:
        logger.error(traceback.format_exc())
        return jsonify({"success": False, "error": str(e)}), 500


# ─────────────────────────────────────────────────────────────────
# API: Insights
# ─────────────────────────────────────────────────────────────────

@app.route("/api/insights", methods=["POST"])
def extract_insights():
    data = request.get_json(silent=True) or {}
    sid  = data.get("session_id") or session.get("session_id", "")

    if not sid or sid not in document_sessions:
        return jsonify({"success": False, "error": "No document loaded."}), 400

    doc = document_sessions[sid]
    if doc.get("insights"):
        return jsonify({"success": True, "insights": doc["insights"], "cached": True})

    try:
        from modules.summarizer import SummarizerModule
        chunks = reconstruct_chunks(doc)
        sm = SummarizerModule()
        insights_data = {
            "insights": sm.generate_insights(chunks)["insights"],
            "novelty":  sm.detect_novelty(chunks)["novelty"],
        }
        doc["insights"] = insights_data
        return jsonify({"success": True, "insights": insights_data, "cached": False})
    except Exception as e:
        logger.error(traceback.format_exc())
        return jsonify({"success": False, "error": str(e)}), 500


# ─────────────────────────────────────────────────────────────────
# API: Q&A (RAG)
# ─────────────────────────────────────────────────────────────────

@app.route("/api/ask", methods=["POST"])
def ask_question():
    data     = request.get_json(silent=True) or {}
    sid      = data.get("session_id") or session.get("session_id", "")
    question = data.get("question", "").strip()

    if not sid or sid not in document_sessions:
        return jsonify({"success": False, "error": "No document loaded."}), 400
    if not question:
        return jsonify({"success": False, "error": "Question cannot be empty."}), 400

    doc = document_sessions[sid]

    try:
        from modules.embeddings import EmbeddingsModule
        from modules.vector_store import VectorStoreModule
        from modules.rag_chain import RAGChainModule

        emb = EmbeddingsModule(model_name=EMBEDDING_MODEL)
        vs  = VectorStoreModule(emb, index_path=doc["faiss_path"])
        vs.load_vector_store(doc["faiss_path"])

        rag    = RAGChainModule(vs, retrieval_k=RETRIEVAL_K)
        result = rag.answer_question(question)

        entry = {
            "id":               uuid.uuid4().hex[:8],
            "question":         question,
            "answer":           result["answer"],
            "retrieved_context":result.get("retrieved_context", []),
            "timestamp":        datetime.now().isoformat(),
            "num_sources":      result.get("num_sources", 0),
        }
        doc.setdefault("chat_history", []).append(entry)

        return jsonify({
            "success":          True,
            "answer":           result["answer"],
            "retrieved_context":result.get("retrieved_context", []),
            "num_sources":      result.get("num_sources", 0),
        })

    except Exception as e:
        logger.error(traceback.format_exc())
        return jsonify({"success": False, "error": str(e)}), 500


# ─────────────────────────────────────────────────────────────────
# API: Chat History
# ─────────────────────────────────────────────────────────────────

@app.route("/api/chat-history", methods=["GET"])
def get_chat_history():
    sid = request.args.get("session_id") or session.get("session_id", "")
    if not sid or sid not in document_sessions:
        return jsonify({"success": True, "history": [], "count": 0})
    h = document_sessions[sid].get("chat_history", [])
    return jsonify({"success": True, "history": h, "count": len(h)})


@app.route("/api/chat-history/clear", methods=["POST"])
def clear_chat_history():
    data = request.get_json(silent=True) or {}
    sid  = data.get("session_id") or session.get("session_id", "")
    if sid in document_sessions:
        document_sessions[sid]["chat_history"] = []
    return jsonify({"success": True})


# ─────────────────────────────────────────────────────────────────
# API: Session Info
# ─────────────────────────────────────────────────────────────────

@app.route("/api/session-info", methods=["GET"])
def session_info():
    sid = request.args.get("session_id") or session.get("session_id", "")
    if not sid or sid not in document_sessions:
        return jsonify({"success": False, "has_session": False})
    doc = document_sessions[sid]
    return jsonify({
        "success":      True,
        "has_session":  True,
        "session_id":   sid,
        "filename":     doc.get("original_filename", ""),
        "metadata":     doc.get("metadata", {}),
        "has_summary":  bool(doc.get("summary")),
        "has_keywords": bool(doc.get("keywords")),
        "has_insights": bool(doc.get("insights")),
        "chat_count":   len(doc.get("chat_history", [])),
        "created_at":   doc.get("created_at", ""),
    })


# ─────────────────────────────────────────────────────────────────
# API: Download Summary as PDF
# ─────────────────────────────────────────────────────────────────

@app.route("/api/download-summary", methods=["POST"])
def download_summary():
    data = request.get_json(silent=True) or {}
    sid  = data.get("session_id") or session.get("session_id", "")

    if not sid or sid not in document_sessions:
        return jsonify({"success": False, "error": "No document loaded."}), 400

    doc     = document_sessions[sid]
    summary = doc.get("summary")
    if not summary:
        return jsonify({"success": False, "error": "Generate a summary first."}), 400

    filename = doc.get("original_filename", "document.pdf")

    try:
        import io
        from reportlab.lib.pagesizes import letter
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
        from reportlab.lib import colors

        buf = io.BytesIO()
        pdf = SimpleDocTemplate(buf, pagesize=letter,
                                rightMargin=72, leftMargin=72,
                                topMargin=72, bottomMargin=72)
        styles = getSampleStyleSheet()

        title_style = ParagraphStyle("T", parent=styles["Heading1"],
                                     fontSize=18, textColor=colors.HexColor("#2c3e50"))
        head_style  = ParagraphStyle("H", parent=styles["Heading2"],
                                     fontSize=13, textColor=colors.HexColor("#2980b9"))
        body_style  = ParagraphStyle("B", parent=styles["Normal"],
                                     fontSize=11, leading=16)

        story = [
            Paragraph("AI Research Assistant — Paper Analysis", title_style),
            Paragraph(f"Document: {filename}", body_style),
            Paragraph(f"Generated: {datetime.now().strftime('%B %d, %Y %I:%M %p')}", body_style),
            Spacer(1, 20),
        ]

        for line in summary.split("\n"):
            line = line.strip()
            if not line:
                story.append(Spacer(1, 6))
            elif line.startswith("##"):
                story.append(Paragraph(line.lstrip("# ").strip(), head_style))
            elif line.startswith("#"):
                story.append(Paragraph(line.lstrip("# ").strip(), title_style))
            else:
                story.append(Paragraph(line, body_style))

        kw = doc.get("keywords", {})
        if kw and kw.get("all_keywords"):
            story.append(Spacer(1, 16))
            story.append(Paragraph("Keywords", head_style))
            story.append(Paragraph(" • ".join(kw["all_keywords"]), body_style))

        pdf.build(story)
        buf.seek(0)

        out_name = filename.replace(".pdf", "") + "_analysis.pdf"
        return send_file(buf, as_attachment=True,
                         download_name=out_name, mimetype="application/pdf")

    except Exception as e:
        # Fallback to plain text
        import io
        buf = io.BytesIO(f"Research Paper Analysis\n\n{summary}".encode())
        buf.seek(0)
        return send_file(buf, as_attachment=True,
                         download_name=filename.replace(".pdf","") + "_analysis.txt",
                         mimetype="text/plain")


# ─────────────────────────────────────────────────────────────────
# API: Export Keywords
# ─────────────────────────────────────────────────────────────────

@app.route("/api/export-keywords", methods=["POST"])
def export_keywords():
    data = request.get_json(silent=True) or {}
    sid  = data.get("session_id") or session.get("session_id", "")

    if not sid or sid not in document_sessions:
        return jsonify({"success": False, "error": "No document loaded."}), 400

    doc  = document_sessions[sid]
    kw   = doc.get("keywords")
    if not kw:
        return jsonify({"success": False, "error": "Extract keywords first."}), 400

    import io
    payload = json.dumps({
        "document": doc.get("original_filename", ""),
        "generated_at": datetime.now().isoformat(),
        **kw,
    }, indent=2)
    buf = io.BytesIO(payload.encode())
    buf.seek(0)
    return send_file(buf, as_attachment=True,
                     download_name="keywords_export.json",
                     mimetype="application/json")


# ─────────────────────────────────────────────────────────────────
# Error handlers
# ─────────────────────────────────────────────────────────────────

@app.errorhandler(413)
def too_large(e):
    return jsonify({"success": False, "error": f"File too large. Max {MAX_FILE_MB} MB."}), 413

@app.errorhandler(404)
def not_found(e):
    return redirect(url_for("index"))

@app.errorhandler(500)
def server_error(e):
    return jsonify({"success": False, "error": "Internal server error."}), 500


# ─────────────────────────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    port  = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_ENV", "development") == "development"

    # Warn if API key not set
    provider = os.environ.get("LLM_PROVIDER", "gemini")
    if provider == "gemini" and not os.environ.get("GOOGLE_API_KEY", "").strip():
        logger.warning("⚠  GOOGLE_API_KEY not set — add it to .env before using AI features.")
    elif provider == "openai" and not os.environ.get("OPENAI_API_KEY", "").strip():
        logger.warning("⚠  OPENAI_API_KEY not set — add it to .env before using AI features.")

    logger.info(f"Starting AI Research Assistant → http://localhost:{port}")
    app.run(host="0.0.0.0", port=port, debug=debug)
