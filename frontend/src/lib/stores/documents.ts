import { writable } from 'svelte/store';
import { getDocuments } from '../utils/api';

export const documents = writable([]);
export const isLoading = writable(false);
export const error = writable(null);

// Fetch and update documents
export async function loadDocuments() {
	isLoading.set(true);
	error.set(null);
	try {
		const data = await getDocuments();
		documents.set(data);
	} catch (err) {
		error.set(err.message);
	} finally {
		isLoading.set(false);
	}
}
