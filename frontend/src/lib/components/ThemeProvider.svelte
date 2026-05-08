<script lang="ts">
	import { onMount } from 'svelte';
	import { initializeTheme } from '$lib/stores/theme';

	let { children } = $props();

	onMount(() => {
		initializeTheme();
	});
</script>

{@render children()}
