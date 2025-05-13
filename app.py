from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import firebase_admin
from firebase_admin import credentials, auth
from PIL import Image
import io
import pdf2image
from docx import Document
from fpdf import FPDF
import rembg

app = Flask(__name__)
CORS(app)

# Firebase initialization
cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred)

# Firebase Token Verification Decorator
def verify_token(f):
    from functools import wraps
    @wraps(f)
    def wrapper(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token or not token.startswith("Bearer "):
            return jsonify({"error": "Unauthorized"}), 401
        try:
            decoded = auth.verify_id_token(token.split("Bearer ")[1])
            request.user = decoded
            return f(*args, **kwargs)
        except Exception as e:
            return jsonify({"error": str(e)}), 401
    return wrapper

# Route to generate text based on the prompt
@app.route("/generate", methods=["POST"])
@verify_token
def generate():
    prompt = request.json.get("prompt")
    if not prompt:
        return jsonify({"error": "No prompt provided"}), 400
    # Replace below with actual generation logic
    return jsonify({"generated_text": f"You entered: {prompt}"})

# Route to convert image (JPEG, PNG, BMP, etc.) to another format
@app.route('/convert-image', methods=['POST'])
@verify_token
def convert_image():
    file = request.files['image']
    target_format = request.form.get('format')  # e.g., 'PNG', 'JPEG'
    
    # Open the image
    img = Image.open(file)
    
    # Convert the image to the desired format
    img_io = io.BytesIO()
    img.save(img_io, target_format)
    img_io.seek(0)
    
    return send_file(img_io, mimetype=f'image/{target_format.lower()}', as_attachment=True, download_name=f'converted_image.{target_format.lower()}')

# Route to convert PDF to image (using pdf2image)
@app.route('/convert-pdf-to-image', methods=['POST'])
@verify_token
def convert_pdf_to_image():
    file = request.files['pdf']
    
    # Convert the first page of the PDF to an image
    pdf = pdf2image.convert_from_bytes(file.read(), first_page=1, last_page=1)
    
    # Convert the image to a byte stream
    img_io = io.BytesIO()
    pdf[0].save(img_io, 'PNG')  # Save as PNG, but you can change the format
    img_io.seek(0)
    
    return send_file(img_io, mimetype='image/png', as_attachment=True, download_name='converted_image.png')

# Route to convert Word document to PDF
@app.route('/convert-word-to-pdf', methods=['POST'])
@verify_token
def convert_word_to_pdf():
    file = request.files['word']
    
    # Load the Word document
    doc = Document(file)
    
    # Create a PDF
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font('Arial', size=12)
    
    # Add the text content of the Word file to the PDF
    for para in doc.paragraphs:
        pdf.multi_cell(0, 10, para.text)
    
    # Save the PDF to a byte stream
    pdf_io = io.BytesIO()
    pdf.output(pdf_io)
    pdf_io.seek(0)
    
    return send_file(pdf_io, mimetype='application/pdf', as_attachment=True, download_name='converted_document.pdf')

# Route for Background Removal Tool (using rembg)
@app.route('/remove-background', methods=['POST'])
@verify_token
def remove_background():
    file = request.files['image']
    
    # Remove the background
    input_image = Image.open(file)
    output_image = rembg.remove(input_image)
    
    # Save to a byte stream
    img_io = io.BytesIO()
    output_image.save(img_io, 'PNG')
    img_io.seek(0)
    
    return send_file(img_io, mimetype='image/png', as_attachment=True, download_name='image_without_background.png')

# Route for Image Resizing Tool
@app.route('/resize-image', methods=['POST'])
@verify_token
def resize_image():
    file = request.files['image']
    width = int(request.form.get('width'))
    height = int(request.form.get('height'))
    
    # Open the image
    img = Image.open(file)
    
    # Resize the image
    resized_img = img.resize((width, height))
    
    # Save the resized image to a byte stream
    img_io = io.BytesIO()
    resized_img.save(img_io, 'PNG')
    img_io.seek(0)
    
    return send_file(img_io, mimetype='image/png', as_attachment=True, download_name=f'resized_image_{width}x{height}.png')

if __name__ == "__main__":
    app.run(debug=True)
