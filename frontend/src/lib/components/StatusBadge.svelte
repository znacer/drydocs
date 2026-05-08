<script>
	import { Check, Pen, X } from '@lucide/svelte';

	let { status = $bindable() } = $props();
</script>

{#if status === 'valid'}
	<span class="badge badge-primary"><Check size={16} class="text-primary-content" /> Valid</span>
{:else if status === 'repealed'}
	<span class="badge badge-error"><X size={16} class="text-error-content" /> Repealed</span>
{:else}
	<span class="badge badge-secondary"><Pen size={16} class="text-secondary-content" /> Draft</span>
{/if}
