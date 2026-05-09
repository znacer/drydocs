<script lang="ts">
	import UploadForm from '$lib/components/UploadForm.svelte';
	import { m } from '$lib/paraglide/messages';
</script>

<div class="container mx-auto px-4 py-8">
	<h1 class="text-3xl font-bold mb-8">{m.upload_a_new_document()}</h1>
	
	<div class="max-w-2xl mx-auto">
		<UploadForm />
	</div>
</div>
