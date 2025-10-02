# app.py
import io 
import zipfile
import os
import json
import hashlib
import cloudinary
import cloudinary.uploader


from datetime import datetime
from flask import Flask, request, jsonify, send_from_directory, render_template_string, redirect, url_for, session, send_file
from werkzeug.utils import secure_filename

cloudinary.config(
    cloud_name = os.environ.get("CLOUDINARY_CLOUD_NAME"),
    api_key = os.environ.get("CLOUDINARY_API_KEY"),
    api_secret = os.environ.get("CLOUDINARY_API_SECRET")
)
app.config['MAX_CONTENT_LENGTH'] = 20 * 1024 * 1024  # 20 MB max
app = Flask(__name__)
app.secret_key = "supersecret"

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

# File to store photo metadata (filename -> guest name)
PHOTO_META_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "photo_meta.json")

def load_photo_meta():
    if os.path.exists(PHOTO_META_FILE):
        with open(PHOTO_META_FILE, "r") as f:
            try:
                return json.load(f)
            except Exception:
                return {}
    return {}

def save_photo_meta(meta):
    with open(PHOTO_META_FILE, "w") as f:
        json.dump(meta, f)

HOST_PASSWORD = "password"  # password for host/admin


# ---------------- Home Page ----------------
@app.route("/", methods=["GET"])
def home():
    html = """
    <!doctype html>
    <html lang="en">
    <head>
      <meta charset="utf-8">
      <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
      <title>PartyPix Home</title>
      <style>
        body {
          font-family: system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif;
          margin:0;
          height:100vh;
          display:flex;
          justify-content:center;
          align-items:center;
          text-align:center;
          background: url('/static/istockphoto-853318464-612x612 (copy).png') no-repeat center center;
          background-size: cover;
        }
        h1 {
          font-size:2rem;
          margin-bottom:24px;
          color:#fff;
          text-shadow: 0 2px 6px rgba(0,0,0,0.7);
        }
        .btn {
          display:block;
          width:200px;
          padding:16px;
          margin:12px auto;
          font-size:18px;
          border-radius:12px;
          border:0;
          background:#1f7aec;
          color:#fff;
          cursor:pointer;
          text-align:center;
          box-shadow:0 3px 10px rgba(0,0,0,0.4);
        }
      </style>
    </head>
    <body>
      <div>
        <h1>Welcome to PartyPix!</h1>
        <button class="btn" onclick="location.href='/host_login'">Host</button>
        <button class="btn" onclick="location.href='/guest_login'">Guest</button>
      </div>
    </body>
    </html>
    """
    return render_template_string(html)


# ---------------- Host Login ----------------
@app.route("/host_login", methods=["GET", "POST"])
def host_login():
    if session.get("is_host"):
        return redirect(url_for("admin_panel"))
    error = ""
    if request.method == "POST":
        pw = request.form.get("password")
        if pw == HOST_PASSWORD:
            session["is_host"] = True
            return redirect(url_for("admin_panel"))
        else:
            error = "Wrong password. Please try again."
    html = f"""
    <!doctype html>
    <html lang="en">
    <head>
      <meta charset="utf-8">
      <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
      <title>Host Login</title>
      <style>
        body {{
          font-family: system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif;
          margin:0;
          height:100vh;
          display:flex;
          justify-content:center;
          align-items:center;
          text-align:center;
          background: url('/static/istockphoto-853318464-612x612 (copy).png') no-repeat center center;
          background-size: cover;
        }}
        .container {{
          background: rgba(0,0,0,0.6);
          padding: 40px 30px;
          border-radius: 18px;
          box-shadow: 0 4px 24px rgba(0,0,0,0.5);
          text-align: center;
        }}
        h2 {{
          color: #fff;
          font-size: 2.2rem;
          margin-bottom: 30px;
        }}
        input[type="password"] {{
          font-size: 1.5rem;
          padding: 18px;
          border-radius: 10px;
          border: none;
          margin-bottom: 24px;
          width: 90%;
        }}
        button {{
          font-size: 1.5rem;
          padding: 18px 40px;
          border-radius: 10px;
          border: none;
          background: #1f7aec;
          color: #fff;
          cursor: pointer;
          margin-top: 10px;
        }}
        .error {{
          color: #ffaaaa;
          font-size: 1.2rem;
          margin-bottom: 10px;
        }}
      </style>
    </head>
    <body>
      <div class="container">
        <h2>Host Login</h2>
        <form method="post">
          <input type="password" name="password" placeholder="Enter password" required><br>
          <button type="submit">Login</button>
        </form>
        <div class="error">{error}</div>
      </div>
    </body>
    </html>
    """
    return render_template_string(html)



# ---------------- Guest Login ----------------
# ---------------- Guest Login ----------------
@app.route("/guest_login", methods=["GET", "POST"])
def guest_login():
    error = ""
    if request.method == "POST":
        name = request.form.get("name")
        if name:
            session["guest_name"] = name
            return redirect(url_for("guest_page"))
        else:
            error = "Please enter your name."

    html = f"""
    <!doctype html>
    <html lang="en">
    <head>
      <meta charset="utf-8">
      <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
      <title>Guest Login</title>
      <style>
        body {{
          font-family: system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif;
          margin:0;
          height:100vh;
          display:flex;
          justify-content:center;
          align-items:center;
          text-align:center;
          background: url('/static/istockphoto-853318464-612x612 (copy).png') no-repeat center center;
          background-size: cover;
        }}
        .container {{
          background: rgba(0,0,0,0.6);
          padding: 40px 30px;
          border-radius: 18px;
          box-shadow: 0 4px 24px rgba(0,0,0,0.5);
          text-align: center;
        }}
        h2 {{
          color: #fff;
          font-size: 2.2rem;
          margin-bottom: 30px;
        }}
        input[type="text"] {{
          font-size: 1.5rem;
          padding: 18px;
          border-radius: 10px;
          border: none;
          margin-bottom: 24px;
          width: 90%;
        }}
        button {{
          font-size: 1.5rem;
          padding: 18px 40px;
          border-radius: 10px;
          border: none;
          background: #1f7aec;
          color: #fff;
          cursor: pointer;
          margin-top: 10px;
        }}
        .error {{
          color: #ffaaaa;
          font-size: 1.2rem;
          margin-bottom: 10px;
        }}
      </style>
    </head>
    <body>
      <div class="container">
        <h2>Guest Login</h2>
        <form method="post">
          <input type="text" name="name" placeholder="Enter your name" required><br>
          <button type="submit">Enter</button>
        </form>
        <div class="error">{error}</div>
      </div>
    </body>
    </html>
    """
    return render_template_string(html)

    
    



# ---------------- Guest Page ----------------
@app.route("/guest_page", methods=["GET"])
def guest_page():
    if not session.get("guest_name"):
        return redirect(url_for("guest_login"))

    html = f"""
    <!doctype html>
    <html lang="en">
    <head>
      <meta charset="utf-8">
      <meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover" />
      <title>PartyPix - Guest</title>
      <style>
        body {{
          font-family: system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif;
          margin:0;
          height:100vh;
          display:flex;
          justify-content:center;
          align-items:center;
          text-align:center;
          background: url('/static/istockphoto-853318464-612x612 (copy).png') no-repeat center center;
          background-size: cover;
        }}
        .container {{
          background: rgba(0,0,0,0.6);
          padding: 40px 30px;
          border-radius: 18px;
          box-shadow: 0 4px 24px rgba(0,0,0,0.5);
          text-align: center;
          max-width: 400px;
          width: 90%;
        }}
        h1 {{
          color: #fff;
          font-size: 1.8rem;
          margin-bottom: 20px;
        }}
        #camera {{ display: none; }}
        .btn {{
          display: block;
          width: 100%;
          padding: 16px;
          margin: 12px 0;
          font-size: 18px;
          border-radius: 12px;
          border: 0;
          background:#1f7aec;
          color:#fff;
          text-align:center;
          cursor:pointer;
          box-shadow:0 3px 10px rgba(0,0,0,0.4);
        }}
        .btn:disabled {{ opacity: .5; }}
        .btn.secondary {{ background:#0aa36f; }}
        #status {{
          margin: 8px 0 0;
          font-size: 1rem;
          color:#fff;
          min-height: 1.2em;
        }}
        #preview-wrap {{ margin-top: 16px; }}
        #preview {{
          width: 100%;
          max-height: 240px;
          object-fit: contain;
          border-radius: 12px;
          display: none;
          margin-top: 10px;
        }}
        small {{
          color:#ccc;
          display:block;
          margin-top: 6px;
        }}
      </style>
    </head>
    <body>
      <div class="container">
        <h1>Welcome, {session['guest_name']}!</h1>
        <input id="camera" type="file" accept="image/*" capture="environment" />
        <button id="take" class="btn">Take Photo</button>
        <button id="upload" class="btn secondary" disabled>Upload</button>
        <button class="btn" onclick="location.href='/gallery'">View Gallery</button>
        <div id="status">Ready</div>
        <small>Tip: Auto-upload starts when you choose a photo.</small>
        <div id="preview-wrap">
          <img id="preview" alt="Last uploaded preview" />
        </div>
      </div>
      <script>
        (function(){{
          const camera = document.getElementById('camera');
          const btnTake = document.getElementById('take');
          const btnUpload = document.getElementById('upload');
          const statusEl = document.getElementById('status');
          const preview = document.getElementById('preview');
          let selectedFile = null;
          let uploading = false;

          function setStatus(msg){{ statusEl.textContent = msg; }}
          function enableUpload(enabled){{ btnUpload.disabled = !enabled || uploading; }}

          async function doUpload(file){{
            if(!file || uploading) return;
            uploading = true;
            enableUpload(false);
            setStatus('Uploading…');
            try {{
              const fd = new FormData();
              fd.append('photo', file);
              const res = await fetch('/upload', {{ method: 'POST', body: fd }});
              const data = await res.json().catch(()=>({{ok:false,error:'Bad JSON'}}));
              if(!res.ok || !data.ok){{
                const err = (data && data.error)?data.error:'HTTP '+res.status;
                setStatus('Error: '+err);
                uploading = false;
                enableUpload(!!selectedFile);
                return;
              }}
              const url = '/uploads/' + encodeURIComponent(data.filename);
              preview.src = url;
              preview.style.display = 'block';
              setStatus('Saved as '+data.filename);
            }} catch(e){{ setStatus('Error: '+(e && e.message?e.message:'Upload failed')); }}
            finally{{ uploading = false; enableUpload(!!selectedFile); }}
          }}

          btnTake.addEventListener('click', ()=>{{ camera.click(); }});
          camera.addEventListener('change', ()=>{{
            const file = camera.files && camera.files[0];
            if(!file) return;
            selectedFile = file;
            enableUpload(true);
            doUpload(file);
          }});
          btnUpload.addEventListener('click', ()=>{{ if(selectedFile) doUpload(selectedFile); }});
        }})();
      </script>
    </body>
    </html>
    """
    return render_template_string(html)

# ---------------- Gallery Page ----------------
@app.route("/gallery", methods=["GET"])
def gallery():
    if not session.get("guest_name"):
        return redirect(url_for("guest_login"))

    meta = load_photo_meta()

    gallery_html = ""
    for public_id, guest in meta.items():
        # Build Cloudinary URL for this photo
        url = cloudinary.CloudinaryImage(public_id).build_url()
        gallery_html += f"""
        <div class="gallery-item">
          <img src="{url}" alt="Photo" class="gallery-img"/>
          <a href="{url}" download class="download-btn">Download</a>
          <p style="color:#fff;">Guest: {guest}</p>
        </div>
        """

    return render_template_string(f"""
    <!doctype html>
    <html lang="en">
    <head>
      <meta charset="utf-8">
      <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
      <title>PartyPix - Gallery</title>
      <style>
        body {{
          font-family: system-ui, sans-serif;
          margin:0;
          min-height:100vh;
          background: url('/static/istockphoto-853318464-612x612 (copy).png') no-repeat center center;
          background-size: cover;
          color:#fff;
        }}
        h1 {{
          text-align:center;
          margin: 20px 0;
        }}
        .top-btns {{
          text-align:center;
          margin-bottom:20px;
        }}
        .top-btns a {{
          background:#1f7aec;
          color:#fff;
          padding:10px 20px;
          border-radius:8px;
          text-decoration:none;
          margin: 0 10px;
        }}
        .gallery {{
          display: grid;
          grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
          gap: 12px;
          width: 95%;
          margin: 0 auto 40px;
        }}
        .gallery-item {{
          background: rgba(0,0,0,0.5);
          padding: 8px;
          border-radius: 12px;
          text-align: center;
        }}
        .gallery-img {{
          width: 100%;
          height: 150px;
          object-fit: cover;
          border-radius: 8px;
        }}
        .download-btn {{
          display: inline-block;
          margin-top: 6px;
          padding: 6px 12px;
          font-size: 0.9rem;
          border-radius: 6px;
          background:#1f7aec;
          color:#fff;
          text-decoration:none;
        }}
      </style>
    </head>
    <body>
      <h1>Gallery</h1>
      <div class="top-btns">
        <a href="/guest_page">← Back</a>
      </div>
      <div class="gallery">
        {gallery_html if gallery_html else "<p style='color:#fff;'>No photos yet.</p>"}
      </div>
    </body>
    </html>
    """)

# ---------------- Download All ----------------
@app.route("/download_all", methods=["GET"])
def download_all():
    if not session.get("guest_name"):
        return redirect(url_for("guest_login"))

    files = os.listdir(UPLOAD_DIR)
    if not files:
        return "No photos to download.", 404

    memory_file = io.BytesIO()
    with zipfile.ZipFile(memory_file, "w") as zf:
        for f in files:
            file_path = os.path.join(UPLOAD_DIR, f)
            zf.write(file_path, arcname=f)
    memory_file.seek(0)

    zip_filename = f"PartyPix_{datetime.now().strftime('%Y-%m-%d')}.zip"
    return send_file(memory_file, as_attachment=True, download_name=zip_filename, mimetype="application/zip")


# ---------------- Upload Endpoint ----------------
def compute_file_hash(file_obj):
    file_obj.seek(0)
    hasher = hashlib.sha256()
    while True:
        chunk = file_obj.read(8192)
        if not chunk:
            break
        hasher.update(chunk)
    file_obj.seek(0)
    return hasher.hexdigest()

@app.route("/upload", methods=["POST"])
def upload():
    if "photo" not in request.files:
        return jsonify(ok=False, error="Missing file field 'photo'"), 400

    file = request.files["photo"]
    if file.filename == "":
        return jsonify(ok=False, error="Empty filename"), 400
    if not (file.mimetype or "").startswith("image/"):
        return jsonify(ok=False, error="Only image/* allowed"), 400

    try:
        # Upload to Cloudinary
        result = cloudinary.uploader.upload(file, folder="partypix")

        # Secure URL to the image
        url = result["secure_url"]
        public_id = result["public_id"]

        # Save guest name if available
        guest_name = session.get("guest_name")
        meta = load_photo_meta()
        if guest_name:
            meta[public_id] = guest_name
            save_photo_meta(meta)

        return jsonify(ok=True, url=url, public_id=public_id)
    except Exception as e:
        return jsonify(ok=False, error=str(e)), 400

    if duplicate_found:
        return jsonify(ok=False, error="Duplicate image detected. Upload canceled."), 409

    try:
        file.save(save_path)
        print(f"Saved: {save_path}")
        # Save guest name if available
        guest_name = session.get("guest_name")
        meta = load_photo_meta()
        if guest_name:
            meta[final_name] = guest_name
            save_photo_meta(meta)
        return jsonify(ok=True, filename=final_name)
    except Exception as e:
        return jsonify(ok=False, error=str(e)), 400


@app.route("/uploads/<path:filename>", methods=["GET"])
def serve_uploads(filename):
    return send_from_directory(UPLOAD_DIR, filename)


# ---------------- Logout ----------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))


# ---------------- Admin Panel ----------------
@app.route("/admin/panel", methods=["GET", "POST"])
def admin_panel():
    if not session.get("is_host"):
        return redirect(url_for("host_login"))

    # Deletion
    if request.method == "POST":
        filename = request.form.get("delete")
        if filename:
            try:
                os.remove(os.path.join(UPLOAD_DIR, filename))
                meta = load_photo_meta()
                if filename in meta:
                    del meta[filename]
                    save_photo_meta(meta)
            except Exception as e:
                print(f"Error deleting {filename}: {e}")

    files = os.listdir(UPLOAD_DIR)
    files.sort(reverse=True)
    meta = load_photo_meta()

    html_files = ""
    for f in files:
        url = url_for("serve_uploads", filename=f)
        guest = meta.get(f, "<span style='color:#ccc'>(unknown guest)</span>")
        html_files += f"""
        <div class="file-card">
          <img src="{url}" class="thumb" />
          <span class="file-info">{f}<br><small>Guest: {guest}</small></span>
          <form method="post" class="delete-form">
            <input type="hidden" name="delete" value="{f}" />
            <button type="submit" class="delete-btn">X</button>
          </form>
        </div>
        """

    return render_template_string(f"""
    <!doctype html>
    <html lang="en">
    <head>
      <meta charset="utf-8">
      <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
      <title>Host Dashboard</title>
      <style>
        body {{
          font-family: system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif;
          margin:0;
          height:100vh;
          display:flex;
          justify-content:center;
          align-items:center;
          background: url('/static/istockphoto-853318464-612x612 (copy).png') no-repeat center center;
          background-size: cover;
        }}
        .container {{
          background: rgba(0,0,0,0.6);
          padding: 40px 30px;
          border-radius: 18px;
          box-shadow: 0 4px 24px rgba(0,0,0,0.5);
          text-align: center;
          width: 90%;
          max-width: 600px;
          max-height: 90vh;
          overflow-y: auto;
        }}
        h1 {{
          color: #fff;
          font-size: 2rem;
          margin-bottom: 20px;
        }}
        .top-links {{
          display: flex;
          justify-content: space-between;
          margin-bottom: 20px;
        }}
        a {{
          color: #1f7aec;
          text-decoration: none;
          font-weight: bold;
        }}
        .logout-btn {{
          background: #ff4d4d;
          border: none;
          color: white;
          padding: 6px 14px;
          border-radius: 8px;
          cursor: pointer;
          font-size: 1rem;
        }}
        .file-card {{
          display: flex;
          align-items: center;
          background: rgba(255,255,255,0.1);
          padding: 10px;
          border-radius: 12px;
          margin-bottom: 12px;
        }}
        .thumb {{
          width: 80px;
          height: 80px;
          object-fit: cover;
          border-radius: 8px;
          margin-right: 12px;
        }}
        .file-info {{
          flex: 1;
          color: #fff;
          text-align: left;
          font-size: 0.9rem;
        }}
        .delete-form {{
          margin: 0;
        }}
        .delete-btn {{
          background: #ff4d4d;
          border: none;
          color: white;
          padding: 6px 12px;
          border-radius: 8px;
          cursor: pointer;
          font-size: 1rem;
        }}
      </style>
    </head>
    <body>
      <div class="container">
        <h1>Host Dashboard</h1>
        <div class="top-links">
          <a href="/">← Back Home</a>
          <a href="/logout"><button class="logout-btn">Logout</button></a>
        </div>
        {html_files if html_files else "<p style='color:#fff;'>No uploaded images.</p>"}
      </div>
    </body>
    </html>
    """)




if __name__ == "__main__":
    print("Starting server on 0.0.0.0:5000")
    app.run(host="0.0.0.0", port=5000, debug=False)
