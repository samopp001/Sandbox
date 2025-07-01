const form = document.getElementById('correctionForm');
const resultDiv = document.getElementById('result');

form.addEventListener('submit', async (e) => {
  e.preventDefault();
  const imageUrl = document.getElementById('imageUrl').value;
  const outputUrl = document.getElementById('outputUrl').value;

  try {
    const response = await fetch('http://localhost:5000/process', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ image_url: imageUrl, output_url: outputUrl })
    });
    const data = await response.json();
    resultDiv.textContent = `Submitted. Params: ${JSON.stringify(data.adjustments)}`;
  } catch (err) {
    resultDiv.textContent = 'Error: ' + err;
  }
});
