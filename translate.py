from flask import Flask, render_template, request
import requests

app = Flask(__name__)
app.secret_key = 'your_secret_key'

def translate_text(text, target_lang):
    url = "https://libretranslate.com/translate"
    payload = {
        'q': text,
        'source': 'auto',
        'target': target_lang,
        'format': 'text'
    }
    response = requests.post(url, data=payload)
    if response.status_code == 200:
        return response.json().get('translatedText')
    return None

@app.route('/translate', methods=['GET', 'POST'])
def translate():
    extracted_text = request.args.get('text', '')  # text can be passed as query param
    translated_text = ''
    target_lang = ''

    if request.method == 'POST':
        extracted_text = request.form.get('extracted_text', '')
        target_lang = request.form.get('target_lang', '')

        if extracted_text and target_lang:
            translated_text = translate_text(extracted_text, target_lang)
            if translated_text is None:
                translated_text = "Translation service error."

    return render_template('translate.html',
                           extracted_text=extracted_text,
                           translated_text=translated_text,
                           target_lang=target_lang)
