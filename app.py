from flask import Flask, render_template, request, redirect, url_for
import os
from werkzeug.utils import secure_filename
from utils.file_processing import process_file
from utils.summarization import summarize_text
from utils.conversion import convert_file
from config import Config

app = Flask(__name__)
app.config.from_object(Config)

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        if 'file' not in request.files:
            return redirect(request.url)
        
        file = request.files['file']
        if file.filename == '':
            return redirect(request.url)
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            
            # Process based on selected operation
            operation = request.form.get('operation')
            if operation == 'summarize':
                result = summarize_text(filepath)
            elif operation == 'convert':
                target_format = request.form.get('target_format')
                result = convert_file(filepath, target_format)
            else:
                result = process_file(filepath)
            
            return render_template('results.html', result=result)
    
    return render_template('upload.html')

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS

if __name__ == '__main__':
    app.run(debug=True)
