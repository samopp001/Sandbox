from flask import Flask, request, jsonify
from main import process_image

app = Flask(__name__)

@app.route('/process', methods=['POST'])
def process():
    if request.content_type and request.content_type.startswith('multipart/form-data'):
        image_file = request.files.get('image')
        output_url = request.form.get('output_url')
        if not image_file:
            return jsonify({'error': 'No image uploaded'}), 400
        result = process_image(output_url=output_url, image_file=image_file)
    else:
        data = request.json or {}
        image_url = data.get('image_url')
        output_url = data.get('output_url')
        result = process_image(image_url=image_url, output_url=output_url)
    return jsonify(result)

if __name__ == '__main__':
    app.run(port=5000)
