<script>
	let { status = $bindable() } = $props();
</script>

{#if status === 'valid'}
	<span class="badge badge-primary">✅ Valid</span>
{:else if status === 'repealed'}
	<span class="badge badge-error">❌ Repealed</span>
{:else}
	<span class="badge badge-secondary">📝 Draft</span>
{/if}
