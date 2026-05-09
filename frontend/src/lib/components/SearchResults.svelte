<script lang="ts">
	import type { SearchResponse, SearchResult } from '$lib/types/search';
	import DocumentCard from './DocumentCard.svelte';

	let { results, onSelect }: { results: SearchResponse; onSelect?: (doc: SearchResult) => void } =
		$props();

	function handleSelect(doc: SearchResult) {
		if (onSelect) {
			onSelect(doc);
		}
	}
</script>

{#if results.total === 0}
	<div class="py-8 text-center text-base-content/50">
		<p>No documents found matching your search.</p>
	</div>
{:else}
	<div class="space-y-4">
		<div class="text-sm text-base-content/60">
			Found {results.total} result{results.total !== 1 ? 's' : ''}
			{#if results.total > results.count}
				(showing {results.count})
			{/if}
		</div>

		<div class="space-y-3">
			{#each results.results as doc}
				<DocumentCard
					document={doc}
					showActions={false}
					score={doc.score}
					highlight={doc.highlight}
					onclick={() => handleSelect(doc)}
				/>
			{/each}
		</div>
	</div>
{/if}
