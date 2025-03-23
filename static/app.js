// UI State
let currentModel = null;

// DOM Elements
const modelSource = document.getElementById('modelSource');
const modelType = document.getElementById('modelType');
const searchQuery = document.getElementById('searchQuery');
const modelList = document.getElementById('modelList');
const generateBtn = document.getElementById('generate');
const resultsContainer = document.getElementById('results');

// Event Listeners
modelSource.addEventListener('change', searchModels);
modelType.addEventListener('change', searchModels);
searchQuery.addEventListener('input', debounce(searchModels, 500));
generateBtn.addEventListener('click', generateImage);

// Debounce function for search
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Search Models
async function searchModels() {
    const source = modelSource.value;
    const type = modelType.value;
    const query = searchQuery.value;

    try {
        const response = await fetch('/api/models/search', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                source,
                model_type: type,
                query,
                flux_only: source === 'huggingface',
                limit: 20
            })
        });

        if (!response.ok) throw new Error('Search failed');
        
        const data = await response.json();
        displayModels(data.models);
    } catch (error) {
        console.error('Search failed:', error);
        showError('Failed to search models');
    }
}

// Display Models
function displayModels(models) {
    modelList.innerHTML = '';
    
    models.forEach(model => {
        const card = document.createElement('div');
        card.className = 'bg-white border rounded-lg overflow-hidden shadow-sm hover:shadow-md transition-shadow';
        
        let imageUrl = model.image_url;
        if (!imageUrl) {
            imageUrl = 'https://placehold.co/300x300?text=No+Preview';
        }
        
        card.innerHTML = `
            <div class="aspect-w-16 aspect-h-9">
                <img src="${imageUrl}" alt="${model.name}" class="object-cover w-full h-48">
            </div>
            <div class="p-4">
                <h3 class="font-semibold text-gray-900 mb-1">${model.name}</h3>
                <p class="text-sm text-gray-600 mb-2">${model.type}</p>
                <button class="download-btn px-3 py-1 bg-indigo-600 text-white rounded hover:bg-indigo-700 text-sm"
                        data-model='${JSON.stringify(model)}'>
                    Download Model
                </button>
            </div>
        `;
        
        const downloadBtn = card.querySelector('.download-btn');
        downloadBtn.addEventListener('click', () => downloadModel(model));
        
        modelList.appendChild(card);
    });
}

// Download Model
async function downloadModel(model) {
    try {
        const response = await fetch('/api/models/download', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                ...model,
                source: modelSource.value
            })
        });

        if (!response.ok) throw new Error('Download failed');
        
        const data = await response.json();
        currentModel = data.model_name;
        showSuccess(`Successfully downloaded ${data.model_name}`);
    } catch (error) {
        console.error('Download failed:', error);
        showError('Failed to download model');
    }
}

// Generate Image
async function generateImage() {
    if (!currentModel) {
        showError('Please select a model first');
        return;
    }

    const request = {
        prompt: document.getElementById('prompt').value,
        negative_prompt: document.getElementById('negativePrompt').value,
        model_name: currentModel,
        steps: parseInt(document.getElementById('steps').value),
        cfg_scale: parseFloat(document.getElementById('cfgScale').value),
        width: parseInt(document.getElementById('width').value),
        height: parseInt(document.getElementById('height').value),
        seed: document.getElementById('seed').value ? parseInt(document.getElementById('seed').value) : null
    };

    try {
        generateBtn.disabled = true;
        generateBtn.textContent = 'Generating...';

        const response = await fetch('/api/generate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(request)
        });

        if (!response.ok) throw new Error('Generation failed');
        
        const data = await response.json();
        displayResult(data);
    } catch (error) {
        console.error('Generation failed:', error);
        showError('Failed to generate image');
    } finally {
        generateBtn.disabled = false;
        generateBtn.textContent = 'Generate Image';
    }
}

// Display Generated Image
function displayResult(data) {
    const resultCard = document.createElement('div');
    resultCard.className = 'bg-white border rounded-lg overflow-hidden shadow-sm';
    
    resultCard.innerHTML = `
        <img src="${data.image}" alt="Generated image" class="w-full h-auto">
        <div class="p-4">
            <p class="text-sm text-gray-600">Seed: ${data.seed}</p>
        </div>
    `;
    
    resultsContainer.insertBefore(resultCard, resultsContainer.firstChild);
}

// Notifications
function showError(message) {
    // You can implement a proper notification system here
    alert(message);
}

function showSuccess(message) {
    // You can implement a proper notification system here
    alert(message);
}

// Initial load
searchModels();
