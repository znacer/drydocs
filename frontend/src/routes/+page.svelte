<script lang="ts">
	import { getDocuments } from '$lib/utils/api';
	import DocumentCard from '$lib/components/DocumentCard.svelte';
	
	interface Document {
		id: string;
		title: string;
		author: string;
		description?: string;
		current_version: number;
		status: string;
		created_at: string;
		updated_at: string;
	}
	
	let documents = $state<Document[]>([]);
	let loading = $state(true);
	let error = $state<string | null>(null);
	
	async function fetchDocuments() {
		loading = true;
		error = null;
		try {
			const data = await getDocuments();
			documents = data.documents || [];
		} catch (err) {
			error = err.message || 'Failed to fetch documents';
		} finally {
			loading = false;
		}
	}
	
	fetchDocuments();
</script>

<div class="container mx-auto px-4 py-8">
	<h1 class="text-3xl font-bold mb-8">Documents</h1>

	{#if loading}
		<p class="text-center py-8">Loading documents...</p>
	{:else if error}
		<div class="alert alert-error">
			<svg xmlns="http://www.w3.org/2000/svg" class="stroke-current shrink-0 h-6 w-6" fill="none" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
			<span>{error}</span>
		</div>
	{:else if documents.length === 0}
		<p class="text-center py-8 text-base-content/70">No documents found.</p>
	{:else}
		<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
			{#each documents as document}
				<DocumentCard {document} />
			{/each}
		</div>
	{/if}
</div>
