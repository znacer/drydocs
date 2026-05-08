<script>
	let { status = $bindable() } = $props();
</script>

{#if status === 'valid'}
	<div class="badge badge-primary">✅ Valid</div>
{:else if status === 'repealed'}
	<div class="badge badge-error">❌ Repealed</div>
{:else}
	<div class="badge badge-secondary">📝 Draft</div>
{/if}
