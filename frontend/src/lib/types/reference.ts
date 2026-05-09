import type { Document } from './document';

export interface Reference {
	id: string;
	source_document_id: string;
	referenced_document_id: string;
	reference_text: string;
	reference_type: string;
	version_number: number;
	created_at: string;
}

export interface ExtractReferencesRequest {
	document_id: string;
	version_number?: number;
}

export interface ExtractReferencesResponse {
	document_id: string;
	version_number: number;
	extracted_references: string[];
	found_references: Reference[];
	unmatched_references: string[];
}

export interface LinkedDocumentsResponse {
	document: Document;
	referenced_documents: Document[];
	referencing_documents: Document[];
}
