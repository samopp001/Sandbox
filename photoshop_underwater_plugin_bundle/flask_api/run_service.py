from flask import Flask, request, jsonify
from main import process_image

app = Flask(__name__)

@app.route('/process', methods=['POST'])
def process():
    data = request.json
    image_url = data.get('image_url')
    output_url = data.get('output_url')
    result = process_image(image_url, output_url)
    return jsonify(result)

if __name__ == '__main__':
    app.run(port=5000)
