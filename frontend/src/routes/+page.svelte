<script lang="ts">
	import { Plus } from '@lucide/svelte';
	import DocumentCard from '$lib/components/DocumentCard.svelte';
	import SearchBar from '$lib/components/SearchBar.svelte';
	import SearchResults from '$lib/components/SearchResults.svelte';
	import type { SearchResponse } from '$lib/types/search';

	let { data } = $props();
	let searchResults = $state<SearchResponse | null>(null);
	let searchQuery = $state('');

	function handleSearch(results: SearchResponse, query: string = '') {
		searchResults = results;
		searchQuery = query;
	}

	function clearSearch() {
		searchResults = null;
		searchQuery = '';
	}

	let showSearchResults = $derived(
		searchResults !== null && (searchResults.results.length > 0 || searchQuery !== '')
	);
</script>

<div class="container mx-auto px-4 py-8">
	<div class="mb-8 flex items-center justify-between">
		<h1 class="text-3xl font-bold">Documents</h1>
		<a href="/upload" class="btn btn-primary">
			<Plus />
			Upload Document
		</a>
	</div>

	<!-- Search Bar -->
	<div class="mb-8">
		<SearchBar onSearch={handleSearch} />
	</div>

	<!-- Search Results -->
	{#if showSearchResults && searchResults}
		<SearchResults results={searchResults} />
	{:else}
		<!-- Document Grid -->
		{#if data.documents.documents.length === 0}
			<p class="py-8 text-center text-base-content/70">No documents found.</p>
		{:else}
			<div class="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-3">
				{#each data.documents.documents as document}
					<DocumentCard {document} />
				{/each}
			</div>
		{/if}
	{/if}
</div>
