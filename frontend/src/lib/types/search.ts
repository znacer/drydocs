export interface SearchRequest {
	query: string;
	limit?: number;
	offset?: number;
}

export interface SearchResult {
	id: string;
	title: string;
	author: string;
	description?: string;
	current_version: number;
	status: string;
	created_at: string;
	updated_at: string;
	score: number;
	highlight?: string;
}

export interface SearchResponse {
	results: SearchResult[];
	count: number;
	total: number;
}
