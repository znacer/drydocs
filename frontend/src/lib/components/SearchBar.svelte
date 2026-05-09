<script lang="ts">
	import { Search, X } from '@lucide/svelte';
	import type { SearchRequest, SearchResponse } from '$lib/types/search';
	import { searchDocuments } from '$lib/utils/api';
	import { m } from '$lib/paraglide/messages';

	let { onSearch }: { onSearch: (results: SearchResponse, query: string) => void } = $props();
	let searchQuery = $state('');
	let isSearching = $state(false);
	let debounceTimer: ReturnType<typeof setTimeout> | null = $state(null);

	// Debounce search input
	function handleInput() {
		if (debounceTimer) {
			clearTimeout(debounceTimer);
		}

		if (searchQuery.trim() === '') {
			// Clear results if query is empty
			onSearch({ results: [], count: 0, total: 0 }, '');
			return;
		}

		isSearching = true;
		debounceTimer = setTimeout(async () => {
			try {
				const request: SearchRequest = {
					query: searchQuery.trim(),
					limit: 20,
					offset: 0
				};
				const response = await searchDocuments(request);
				onSearch(response, searchQuery.trim());
			} catch (err) {
				console.error('Search error:', err);
				onSearch({ results: [], count: 0, total: 0 }, searchQuery.trim());
			} finally {
				isSearching = false;
			}
		}, 300); // 300ms debounce delay
	}

	// Handle form submission (enter key)
	async function handleSubmit(event: Event) {
		event.preventDefault();
		if (searchQuery.trim() === '') return;

		if (debounceTimer) {
			clearTimeout(debounceTimer);
		}

		isSearching = true;
		try {
			const request: SearchRequest = {
				query: searchQuery.trim(),
				limit: 20,
				offset: 0
			};
			const response = await searchDocuments(request);
			onSearch(response, searchQuery.trim());
		} catch (err) {
			console.error('Search error:', err);
			onSearch({ results: [], count: 0, total: 0 }, searchQuery.trim());
		} finally {
			isSearching = false;
		}
	}

	// Clear search
	function clearSearch() {
		searchQuery = '';
		onSearch({ results: [], count: 0, total: 0 }, '');
		if (debounceTimer) {
			clearTimeout(debounceTimer);
		}
	}
</script>

<div class="relative w-full">
	<form onsubmit={handleSubmit} class="relative">
		<div class="relative">
			<Search class="absolute top-1/2 left-3 h-5 w-5 -translate-y-1/2 text-base-content/50" />
			<input
				type="search"
				bind:value={searchQuery}
				oninput={handleInput}
				placeholder="{m.search()}..."
				class="input w-full border border-base-200 bg-base-200 pr-10 pl-10 focus:border-primary focus:ring-1 focus:ring-primary focus:outline-none"
			/>
			{#if searchQuery}
				<button
					type="button"
					onclick={clearSearch}
					class="btn absolute top-1/2 right-3 btn-circle -translate-y-1/2 btn-ghost btn-sm"
				>
					<X />
				</button>
			{/if}
		</div>
	</form>
	{#if isSearching}
		<div class="absolute top-1/2 right-3 -translate-y-1/2">
			<span class="loading loading-xs loading-spinner"></span>
		</div>
	{/if}
</div>
