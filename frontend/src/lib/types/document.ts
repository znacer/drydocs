export interface Document {
	id: string;
	title: string;
	author: string;
	description?: string;
	current_version: number;
	status: string;
	created_at: string;
	updated_at: string;
}

export interface Version {
	id: string;
	document_id: string;
	version_number: number;
	filename: string;
	file_type: string;
	file_size: number;
	storage_path: string;
	markdown_path: string | null;
	is_valid: boolean;
	validated_by: string | null;
	validation_notes: string | null;
	validated_at: string | null;
	created_at: string;
}
