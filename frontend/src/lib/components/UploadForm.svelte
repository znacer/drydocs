<script lang="ts">
	import { uploadDocument } from '$lib/utils/api';
	import { goto } from '$app/navigation';
	import { m } from '$lib/paraglide/messages';

	let title = $state('');
	let author = $state('');
	let description = $state('');
	let file = $state<File | null>(null);
	let loading = $state(false);
	let error = $state<string | null>(null);
	let success = $state<string | null>(null);

	function handleFileChange(event: Event) {
		const input = event.target as HTMLInputElement;
		if (input.files && input.files[0]) {
			file = input.files[0];
		}
	}

	async function handleSubmit(event: Event) {
		event.preventDefault();

		if (!file) {
			error = m.upload_failed();
			return;
		}

		if (!title.trim()) {
			error = m.title();
			return;
		}

		if (!author.trim()) {
			error = m.author();
			return;
		}

		loading = true;
		error = null;
		success = null;

		try {
			const result = await uploadDocument(file, title, author, description);
			loading = false;
			success = m.upload_success();

			// Reset form
			title = '';
			author = '';
			description = '';
			file = null;

			// Navigate to the document page
			const docId = result.document.id;
			goto(`/documents/${docId}`);
		} catch (err: unknown) {
			loading = false;
			const errorObj = err as Error;
			error = errorObj.message || m.upload_failed();
		}
	}
</script>

<div class="card border border-base-200 bg-base-100 shadow-md">
	<div class="card-body">
		<h2 class="mb-6 card-title text-xl">{m.upload_document()}</h2>

		<form onsubmit={handleSubmit} class="space-y-4">
			<div class="form-control">
				<label class="label" for="title">
					<span class="label-text">{m.title()} <span class="text-error">*{m.required()}</span></span
					>
				</label>
				<input
					type="text"
					id="title"
					bind:value={title}
					placeholder={m.title()}
					class="input-bordered input w-full"
					required
				/>
			</div>

			<div class="form-control">
				<label class="label" for="author">
					<span class="label-text"
						>{m.author()} <span class="text-error">*{m.required()}</span></span
					>
				</label>
				<input
					type="text"
					id="author"
					bind:value={author}
					placeholder={m.author()}
					class="input-bordered input w-full"
					required
				/>
			</div>

			<div class="form-control">
				<label class="label" for="description">
					<span class="label-text"
						>{m.description()} <span class="text-base-content/50">({m.optional()})</span></span
					>
				</label>
				<textarea
					bind:value={description}
					id="description"
					placeholder={m.description()}
					class="textarea-bordered textarea w-full"
					rows="3"
				></textarea>
			</div>

			<div class="form-control">
				<label class="label" for="file">
					<span class="label-text"
						>{m.document_file()} <span class="text-error">*{m.required()}</span></span
					>
				</label>
				<input
					type="file"
					id="file"
					accept=".pdf,.docx,.doc"
					onchange={handleFileChange}
					class="file-input-bordered file-input w-full"
					required
				/>
				{#if file}
					<p class="mt-2 text-sm text-base-content/70">
						{m.selected_file({ name: file.name, size: Math.round(file.size / 1024) })}
					</p>
				{/if}
			</div>

			{#if error}
				<div class="alert text-sm alert-error">
					<svg
						xmlns="http://www.w3.org/2000/svg"
						class="h-4 w-4 shrink-0 stroke-current"
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
			{/if}

			<button type="submit" class="btn btn-primary" disabled={loading}>
				{#if loading}
					<span class="loading loading-spinner"></span>
					{m.uploading()}
				{:else}
					{m.upload()}
				{/if}
			</button>
		</form>
	</div>
</div>
