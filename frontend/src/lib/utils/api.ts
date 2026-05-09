import type { Document, Version } from '$lib/types/document';
import type {
	ExtractReferencesResponse,
	LinkedDocumentsResponse,
	Reference
} from '$lib/types/reference';
import type { SearchRequest, SearchResponse } from '$lib/types/search';

export interface UploadResponse {
	document: Document;
	latest_version: Version | null;
}

export interface DocumentListResponse {
	documents: Document[];
	count: number;
}

export interface DocumentWithVersion {
	document: Document;
	latest_version: Version | null;
}

interface ValidationResult {
	valid: boolean;
	errors?: string[];
	message?: string;
}

const BASE_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';

// Helper to handle responses
async function handleResponse<T>(response: Response): Promise<T> {
	if (!response.ok) {
		const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
		throw new Error(error.detail || 'Request failed');
	}
	return response.json();
}

// Upload a document
export async function uploadDocument(
	file: File,
	title: string,
	author: string,
	description: string = ''
): Promise<UploadResponse> {
	const formData = new FormData();
	formData.append('file', file);
	formData.append('title', title);
	formData.append('author', author);
	if (description) {
		formData.append('description', description);
	}

	const response = await fetch(`${BASE_URL}/documents/upload`, {
		method: 'POST',
		body: formData
	});
	return handleResponse<UploadResponse>(response);
}

// Fetch all documents
export async function getDocuments(): Promise<DocumentListResponse> {
	const response = await fetch(`${BASE_URL}/documents`);
	return handleResponse<DocumentListResponse>(response);
}

// Fetch a single document
export async function getDocument(id: string): Promise<DocumentWithVersion> {
	const response = await fetch(`${BASE_URL}/documents/${id}`);
	return handleResponse<DocumentWithVersion>(response);
}

// Validate a document version
export async function validateDocument(id: string): Promise<ValidationResult> {
	const response = await fetch(`${BASE_URL}/documents/${id}/validate`, {
		method: 'POST'
	});
	return handleResponse<ValidationResult>(response);
}

// Download Markdown
export async function downloadMarkdown(id: string): Promise<Blob> {
	const response = await fetch(`${BASE_URL}/documents/${id}/markdown`);
	if (!response.ok) throw new Error('Failed to download');
	return response.blob();
}

// Download original document file
export async function downloadDocument(id: string): Promise<Blob> {
	const response = await fetch(`${BASE_URL}/documents/${id}/download`);
	if (!response.ok) throw new Error('Failed to download');
	return response.blob();
}

// Search documents
export async function searchDocuments(request: SearchRequest): Promise<SearchResponse> {
	const response = await fetch(`${BASE_URL}/search`, {
		method: 'POST',
		headers: {
			'Content-Type': 'application/json'
		},
		body: JSON.stringify(request)
	});
	return handleResponse<SearchResponse>(response);
}

// Get linked documents for a document
export async function getLinkedDocuments(id: string): Promise<LinkedDocumentsResponse> {
	const response = await fetch(`${BASE_URL}/documents/${id}/references`);
	return handleResponse<LinkedDocumentsResponse>(response);
}

// Get outgoing references (documents this document references)
export async function getOutgoingReferences(id: string): Promise<Reference[]> {
	const response = await fetch(`${BASE_URL}/documents/${id}/references/outgoing`);
	return handleResponse<Reference[]>(response);
}

// Get incoming references (documents that reference this document)
export async function getIncomingReferences(id: string): Promise<Reference[]> {
	const response = await fetch(`${BASE_URL}/documents/${id}/references/incoming`);
	return handleResponse<Reference[]>(response);
}

// Extract references from a document
export async function extractReferences(
	id: string,
	versionNumber?: number
): Promise<ExtractReferencesResponse> {
	const url = versionNumber
		? `${BASE_URL}/documents/${id}/extract-references?version_number=${versionNumber}`
		: `${BASE_URL}/documents/${id}/extract-references`;
	const response = await fetch(url, {
		method: 'POST'
	});
	return handleResponse<ExtractReferencesResponse>(response);
}

// Search related documents
export async function searchRelatedDocuments(
	id: string,
	query?: string,
	limit?: number
): Promise<SearchResponse> {
	const params = new URLSearchParams();
	if (query) params.append('query', query);
	if (limit) params.append('limit', limit.toString());
	const url = `${BASE_URL}/documents/${id}/search?${params.toString()}`;
	const response = await fetch(url);
	return handleResponse<SearchResponse>(response);
}

// Delete a document
export async function deleteDocument(id: string): Promise<{ message: string; success: boolean }> {
	const response = await fetch(`${BASE_URL}/documents/${id}`, {
		method: 'DELETE'
	});
	return handleResponse<{ message: string; success: boolean }>(response);
}
