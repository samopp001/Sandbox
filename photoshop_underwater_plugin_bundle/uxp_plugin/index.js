const form = document.getElementById('correctionForm');
const resultDiv = document.getElementById('result');
const fileInput = document.getElementById('imageFile');
const beforeImage = document.getElementById('beforeImage');
const afterImage = document.getElementById('afterImage');
const preview = document.getElementById('preview');

let selectedFile = null;

function handleFile(file) {
  if (!file) return;
  selectedFile = file;
  beforeImage.src = URL.createObjectURL(file);
}

fileInput.addEventListener('change', () => handleFile(fileInput.files[0]));

preview.addEventListener('dragover', e => e.preventDefault());
preview.addEventListener('drop', e => {
  e.preventDefault();
  if (e.dataTransfer.files.length) {
    handleFile(e.dataTransfer.files[0]);
  }
});

form.addEventListener('submit', async (e) => {
  e.preventDefault();
  const imageUrl = document.getElementById('imageUrl').value;
  const outputUrl = document.getElementById('outputUrl').value;

  try {
    let response;
    if (selectedFile) {
      const formData = new FormData();
      formData.append('image', selectedFile);
      formData.append('output_url', outputUrl);
      response = await fetch('http://localhost:5000/process', {
        method: 'POST',
        body: formData
      });
    } else {
      response = await fetch('http://localhost:5000/process', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ image_url: imageUrl, output_url: outputUrl })
      });
    }
    const data = await response.json();
    resultDiv.textContent = `Submitted. Params: ${JSON.stringify(data.adjustments)}`;
    afterImage.src = outputUrl;
  } catch (err) {
    resultDiv.textContent = 'Error: ' + err;
  }
});
