<script lang="ts">
	import StatusBadge from './StatusBadge.svelte';
	import type { Document } from '$lib/types/document';

	let { document }: { document: Document } = $props();

	const formatDate = (dateString: string) => {
		return new Date(dateString).toLocaleDateString('en-US', {
			year: 'numeric',
			month: 'short',
			day: 'numeric'
		});
	};
</script>

<div
	class="card border border-base-200 bg-base-100 shadow-md transition-shadow duration-200 hover:shadow-xl"
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
		<div class="mt-4 flex gap-4 text-xs text-base-content/50">
			<span class="badge badge-ghost">v{document.current_version}</span>
			<span>Created: {formatDate(document.created_at)}</span>
			<span>Updated: {formatDate(document.updated_at)}</span>
		</div>
		<div class="mt-4 card-actions">
			<a href="/documents/{document.id}" class="btn btn-sm btn-primary"> View Document </a>
		</div>
	</div>
</div>
