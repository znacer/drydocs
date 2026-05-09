<script lang="ts">
	import StatusBadge from './StatusBadge.svelte';
	import type { Document } from '$lib/types/document';
	import { deleteDocument } from '$lib/utils/api';

	let {
		document,
		showActions = true,
		score,
		highlight,
		onclick
	}: {
		document: Document;
		showActions?: boolean;
		score?: number;
		highlight?: string;
		onclick?: (event: MouseEvent) => void;
	} = $props();

	const formatDate = (dateString: string) => {
		return new Date(dateString).toLocaleDateString('en-US', {
			year: 'numeric',
			month: 'short',
			day: 'numeric'
		});
	};

	let isDeleting = $state(false);

	async function handleDelete(event: MouseEvent) {
		event.preventDefault();
		event.stopPropagation();

		if (!confirm('Are you sure you want to delete this document? This action cannot be undone.')) {
			return;
		}

		try {
			isDeleting = true;
			await deleteDocument(document.id);
			// Refresh the page to update the document list
			window.location.reload();
		} catch (err: unknown) {
			const errorObj = err as Error;
			alert(errorObj.message || 'Failed to delete document');
		} finally {
			isDeleting = false;
		}
	}
</script>

<div
	class="card border border-base-200 bg-base-100 shadow-md transition-shadow duration-200 hover:shadow-xl {onclick
		? 'cursor-pointer'
		: ''}"
>
	<div class="card-body">
		<div class="flex items-start justify-between">
			<h3 class="card-title text-lg">{document.title}</h3>
			<StatusBadge status={document.status} />
		</div>
		<p class="text-sm text-base-content/70">By {document.author}</p>
		{#if document.description}
			<p class="my-2 text-base-content/90">{document.description}</p>
		{/if}
		{#if highlight}
			<div class="mt-2 text-sm text-base-content/80">
				<span class="font-medium">Preview:</span>
				{highlight}
			</div>
		{/if}
		<div class="mt-4 flex gap-4 text-xs text-base-content/50">
			<span class="badge badge-ghost">v{document.current_version}</span>
			<span>Created: {formatDate(document.created_at)}</span>
			<span>Updated: {formatDate(document.updated_at)}</span>
			{#if score !== undefined}
				<span class="flex-1"></span>
				<span class="font-medium text-primary">{score.toFixed(2)}</span>
			{/if}
		</div>
		{#if showActions}
			<div class="mt-4 card-actions">
				<a href="/documents/{document.id}" class="btn btn-sm btn-primary"> View Document </a>
				<button onclick={handleDelete} class="btn btn-sm btn-error" disabled={isDeleting}>
					{isDeleting ? 'Deleting...' : 'Delete'}
				</button>
			</div>
		{/if}
	</div>
</div>
