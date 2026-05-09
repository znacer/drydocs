<script lang="ts">
	import SearchBar from '$lib/components/SearchBar.svelte';
	import SearchResults from '$lib/components/SearchResults.svelte';
	import type { SearchResponse, SearchResult } from '$lib/types/search';

	let searchResults = $state<SearchResponse>({ results: [], count: 0, total: 0 });

	function handleSearch(results: SearchResponse, query: string) {
		searchResults = results;
	}

	function handleSelect(doc: SearchResult) {
		// Navigate to document detail page
		window.location.href = `/documents/${doc.id}`;
	}
</script>

<div class="container mx-auto px-4 py-8">
	<div class="mx-auto max-w-4xl">
		<!-- Header -->
		<div class="mb-8">
			<h1 class="text-3xl font-bold">Search Documents</h1>
			<p class="mt-2 text-base-content/70">
				Find documents by keywords in title, author, description, or content.
			</p>
		</div>

		<!-- Search Bar -->
		<div class="mb-8">
			<SearchBar onSearch={handleSearch} />
		</div>

		<!-- Search Results -->
		<SearchResults results={searchResults} onSelect={handleSelect} />
	</div>
</div>
