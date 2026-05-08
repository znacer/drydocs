const BASE_URL = 'http://127.0.0.1:8000';

// Helper to handle responses
async function handleResponse(response) {
	if (!response.ok) {
		const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
		throw new Error(error.detail || 'Request failed');
	}
	return response.json();
}

// Upload a document
export async function uploadDocument(file, title, author) {
	const formData = new FormData();
	formData.append('file', file);
	formData.append('title', title);
	formData.append('author', author);

	const response = await fetch(`${BASE_URL}/upload`, {
		method: 'POST',
		body: formData
	});
	return handleResponse(response);
}

// Fetch all documents
export async function getDocuments() {
	const response = await fetch(`${BASE_URL}/documents`);
	return handleResponse(response);
}

// Fetch a single document
export async function getDocument(id) {
	const response = await fetch(`${BASE_URL}/documents/${id}`);
	return handleResponse(response);
}

// Validate a document version
export async function validateDocument(id) {
	const response = await fetch(`${BASE_URL}/documents/${id}/validate`, {
		method: 'POST'
	});
	return handleResponse(response);
}

// Download Markdown
export async function downloadMarkdown(id) {
	const response = await fetch(`${BASE_URL}/documents/${id}/markdown`);
	if (!response.ok) throw new Error('Failed to download');
	return response.blob(); // For <a download> or object URL
}
