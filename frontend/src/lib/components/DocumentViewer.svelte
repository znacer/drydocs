<script lang="ts">
	import { getDocument, downloadMarkdown } from '$lib/utils/api';
	import type { DocumentWithVersion } from '$lib/utils/api';
	import { m } from '$lib/paraglide/messages';

	let { documentId }: { documentId: string } = $props();

	let markdownContent = $state<string | null>(null);
	let isLoading = $state<boolean>(true);
	let error = $state<string | null>(null);

	// Fetch markdown content when documentId changes
	$effect(() => {
		if (!documentId) return;

		async function fetchMarkdown() {
			isLoading = true;
			error = null;

			try {
				const doc = await getDocument(documentId);
				if (doc.latest_version?.markdown_path) {
					// The markdown is stored, but we need to fetch it
					// For now, download and read the blob
					const blob = await downloadMarkdown(documentId);
					markdownContent = await blob.text();
				} else {
					markdownContent = null;
				}
			} catch (err: unknown) {
				const errorObj = err as Error;
				error = errorObj.message || m.loading_document_content();
			} finally {
				isLoading = false;
			}
		}

		fetchMarkdown();
	});
</script>

{#if isLoading}
	<div class="p-8 text-center">
		<span class="loading loading-spinner loading-lg"></span>
		<p class="mt-4 text-base-content/70">{m.loading_document_content()}</p>
	</div>
{:else if error}
	<div class="alert alert-error">
		<svg
			xmlns="http://www.w3.org/2000/svg"
			class="h-6 w-6 shrink-0 stroke-current"
			fill="none"
			viewBox="0 0 24 24"
		>
			<path
				stroke-linecap="round"
				stroke-linejoin="round"
				stroke-width="2"
				d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z"
			/>
		</svg>
		<span>{error}</span>
	</div>
{:else if !markdownContent}
	<div class="p-8 text-center text-base-content/70">
		<p>{m.no_markdown_content()}</p>
	</div>
{:else}
	<!-- Markdown content display with basic styling -->
	<div class="prose max-w-none">
		{@html markdownContent}
	</div>
{/if}
