import { writable } from 'svelte/store';
import { getDocuments } from '$lib/utils/api';
import type { Document } from '$lib/types';

export const documents = writable<Document[]>([]);
export const isLoading = writable<boolean>(false);
export const error = writable<string | null>(null);

export async function loadDocuments() {
	isLoading.set(true);
	error.set(null);
	try {
		const data = await getDocuments();
		documents.set(data.documents);
	} catch (err: unknown) {
		const errorObj = err as Error;
		error.set(errorObj.message || 'Unknown error');
	} finally {
		isLoading.set(false);
	}
}
