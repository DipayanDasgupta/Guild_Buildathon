document.addEventListener('DOMContentLoaded', () => {
    const uploadForm = document.getElementById('upload-form');
    const fileInput = document.getElementById('document-upload');
    const fileNameSpan = document.getElementById('file-name');
    const resultContainer = document.getElementById('result-container');
    const resultOutput = document.getElementById('result-output');
    const spinner = document.getElementById('spinner');

    fileInput.addEventListener('change', () => {
        if (fileInput.files.length > 0) {
            fileNameSpan.textContent = fileInput.files[0].name;
        } else {
            fileNameSpan.textContent = 'No file chosen';
        }
    });

    uploadForm.addEventListener('submit', async (event) => {
        event.preventDefault();

        if (fileInput.files.length === 0) {
            alert('Please select a file to process.');
            return;
        }

        const file = fileInput.files[0];
        const formData = new FormData();
        formData.append('document', file);

        // Show spinner and result container
        resultContainer.classList.remove('hidden');
        spinner.classList.remove('hidden');
        resultOutput.textContent = '';
        resultOutput.style.color = 'var(--text-color)';

        try {
            const response = await fetch('/api/documents/process', {
                method: 'POST',
                body: formData,
            });

            const result = await response.json();

            if (!response.ok) {
                throw new Error(result.message || 'An error occurred during processing.');
            }
            
            // Format the JSON for beautiful display
            const formattedResult = JSON.stringify(result.data, null, 2);
            resultOutput.textContent = formattedResult;
            resultOutput.style.color = 'var(--success-color)';

        } catch (error) {
            resultOutput.textContent = `Error: ${error.message}`;
            resultOutput.style.color = 'var(--error-color)';
        } finally {
            // Hide spinner
            spinner.classList.add('hidden');
        }
    });
});
