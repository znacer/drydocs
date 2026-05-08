<script lang="ts">
	import { page } from '$app/stores';
	import { getDocument, downloadDocument, downloadMarkdown } from '$lib/utils/api';
	import StatusBadge from '$lib/components/StatusBadge.svelte';
	import type { DocumentWithVersion } from '$lib/utils/api';

	// Get document ID from route params
	let documentId = $derived($page.params.id);
	let documentPromise = $derived(documentId ? getDocument(documentId) : Promise.resolve(null));

	async function handleDownloadOriginal(doc: DocumentWithVersion) {
		if (!doc.latest_version || !documentId) return;
		try {
			const blob = await downloadDocument(documentId);
			const url = window.URL.createObjectURL(blob);
			const a = document.createElement('a');
			a.href = url;
			a.download = doc.latest_version.filename;
			document.body.appendChild(a);
			a.click();
			document.body.removeChild(a);
			window.URL.revokeObjectURL(url);
		} catch (err: unknown) {
			const errorObj = err as Error;
			throw errorObj;
		}
	}

	async function handleDownloadMarkdown(doc: DocumentWithVersion) {
		if (!doc.latest_version || !documentId) return;
		try {
			const blob = await downloadMarkdown(documentId);
			const url = window.URL.createObjectURL(blob);
			const a = document.createElement('a');
			a.href = url;
			a.download = `document_${documentId}.md`;
			document.body.appendChild(a);
			a.click();
			document.body.removeChild(a);
			window.URL.revokeObjectURL(url);
		} catch (err: unknown) {
			const errorObj = err as Error;
			throw errorObj;
		}
	}

	const formatDate = (dateString: string) => {
		return new Date(dateString).toLocaleDateString('en-US', {
			year: 'numeric',
			month: 'short',
			day: 'numeric',
			hour: '2-digit',
			minute: '2-digit'
		});
	};

	const formatFileSize = (bytes: number) => {
		if (bytes < 1024) return `${bytes} bytes`;
		if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
		return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
	};
</script>

<div class="container mx-auto px-4 py-8">
	{#await documentPromise}
		<div class="py-8 text-center">
			<p>Loading document...</p>
		</div>
	{:then docWithVersion}
		{#if !docWithVersion}
			<div class="py-8 text-center text-base-content/70">
				<p>Document not found</p>
			</div>
		{:else}
			<div class="mx-auto max-w-4xl">
				<!-- Back link -->
				<div class="mb-6">
					<a href="/" class="btn btn-ghost btn-sm">
						<svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
							<path fill-rule="evenodd" d="M12.707 5.293a1 1 0 010 1.414L9.414 10l3.293 3.293a1 1 0 01-1.414 1.414l-4-4a1 1 0 010-1.414l4-4a1 1 0 011.414 0z" clip-rule="evenodd" />
						</svg>
						Back to Documents
					</a>
				</div>

				<!-- Document header -->
				<div class="mb-6 card border border-base-200 bg-base-100 shadow-md">
					<div class="card-body">
						<div class="flex items-start justify-between">
							<div>
								<h1 class="mb-2 text-3xl font-bold">{docWithVersion.document.title}</h1>
								<div class="mb-4 flex items-center gap-4">
									<p class="text-base-content/70">By {docWithVersion.document.author}</p>
									<StatusBadge status={docWithVersion.document.status} />
								</div>
							</div>
						</div>

						{#if docWithVersion.document.description}
							<p class="mt-4 text-base-content/90">{docWithVersion.document.description}</p>
						{/if}

						<div class="divider my-4"></div>

						<!-- Version info -->
						<div class="grid grid-cols-1 gap-4 text-sm text-base-content/60 md:grid-cols-3">
							<div>
								<p><strong>Version:</strong> {docWithVersion.document.current_version}</p>
							</div>
							<div>
								<p><strong>Created:</strong> {formatDate(docWithVersion.document.created_at)}</p>
							</div>
							<div>
								<p><strong>Updated:</strong> {formatDate(docWithVersion.document.updated_at)}</p>
							</div>
						</div>
					</div>
				</div>

				<!-- Document file info -->
				{#if docWithVersion.latest_version}
					<div class="mb-6 card border border-base-200 bg-base-100 shadow-md">
						<div class="card-body">
							<h2 class="mb-4 card-title text-xl">File Information</h2>

							<div class="space-y-3">
								<div class="flex justify-between">
									<span class="text-base-content/70">Filename:</span>
									<span class="font-medium">{docWithVersion.latest_version.filename}</span>
								</div>
								<div class="flex justify-between">
									<span class="text-base-content/70">File Type:</span>
									<span class="font-medium">{docWithVersion.latest_version.file_type}</span>
								</div>
								<div class="flex justify-between">
									<span class="text-base-content/70">File Size:</span>
									<span class="font-medium">{formatFileSize(docWithVersion.latest_version.file_size)}</span>
								</div>
								<div class="flex justify-between">
									<span class="text-base-content/70">Validation Status:</span>
									<span class="font-medium">
										{#if docWithVersion.latest_version.is_valid}
											<span class="badge badge-success">Validated</span>
										{:else}
											<span class="badge badge-warning">Not Validated</span>
										{/if}
									</span>
								</div>
								{#if docWithVersion.latest_version.validation_notes}
									<div class="flex justify-between">
										<span class="text-base-content/70">Validation Notes:</span>
										<span class="font-medium">{docWithVersion.latest_version.validation_notes}</span>
									</div>
								{/if}
							</div>
						</div>
					</div>

					<!-- Download buttons -->
					<div class="mb-6 card border border-base-200 bg-base-100 shadow-md">
						<div class="card-body">
							<h2 class="mb-4 card-title text-xl">Downloads</h2>

							<div class="flex flex-col gap-4 sm:flex-row">
								<button onclick={() => handleDownloadOriginal(docWithVersion)} class="btn btn-primary btn-lg flex-1">
									<svg xmlns="http://www.w3.org/2000/svg" class="mr-2 h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
										<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
									</svg>
									Download Original ({docWithVersion.latest_version.file_type})
								</button>

								<button onclick={() => handleDownloadMarkdown(docWithVersion)} class="btn btn-secondary btn-lg flex-1">
									<svg xmlns="http://www.w3.org/2000/svg" class="mr-2 h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
										<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
									</svg>
									Download Markdown
								</button>
							</div>
						</div>
					</div>
				{/if}
			</div>
		{/if}
	{:catch error}
		<div class="alert alert-error">
			<svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 shrink-0 stroke-current" fill="none" viewBox="0 0 24 24">
				<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" />
			</svg>
			<span>{error.message || 'Failed to fetch document'}</span>
		</div>
	{/await}
</div>
