<script lang="ts">
	import StatusBadge from './StatusBadge.svelte';
	import type { Document } from '$lib/types/document';
	import { deleteDocument } from '$lib/utils/api';
	import { m } from '$lib/paraglide/messages';

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
		return new Date(dateString).toLocaleDateString(undefined, {
			year: 'numeric',
			month: 'short',
			day: 'numeric'
		});
	};

	let isDeleting = $state(false);

	async function handleDelete(event: MouseEvent) {
		event.preventDefault();
		event.stopPropagation();

		if (!confirm(m.are_you_sure_delete())) {
			return;
		}

		try {
			isDeleting = true;
			await deleteDocument(document.id);
			// Refresh the page to update the document list
			window.location.reload();
		} catch (err: unknown) {
			const errorObj = err as Error;
			alert(errorObj.message || m.delete_failed());
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
		<p class="text-sm text-base-content/70">{m.by_author({ author: document.author })}</p>
		{#if document.description}
			<p class="my-2 text-base-content/90">{document.description}</p>
		{/if}
		{#if highlight}
			<div class="mt-2 text-sm text-base-content/80">
				<span class="font-medium">{m.preview()}:</span>
				{highlight}
			</div>
		{/if}
		<div class="mt-4 flex gap-4 text-xs text-base-content/50">
			<span class="badge badge-ghost">v{document.current_version}</span>
			<span>{m.created()}: {formatDate(document.created_at)}</span>
			<span>{m.updated()}: {formatDate(document.updated_at)}</span>
			{#if score !== undefined}
				<span class="flex-1"></span>
				<span class="font-medium text-primary">{score.toFixed(2)}</span>
			{/if}
		</div>
		{#if showActions}
			<div class="mt-4 card-actions">
				<a href="/documents/{document.id}" class="btn btn-sm btn-primary">{m.view_document()}</a>
				<button onclick={handleDelete} class="btn btn-sm btn-error" disabled={isDeleting}>
					{isDeleting ? m.deleting() : m.delete()}
				</button>
			</div>
		{/if}
	</div>
</div>
