<script lang="ts">
	import { resolve } from '$app/paths';
	import { page } from '$app/stores';
	import { locales, localizeHref } from '$lib/paraglide/runtime';
	import './layout.css';
	import favicon from '$lib/assets/favicon.svg';
	import ThemeProvider from '$lib/components/ThemeProvider.svelte';
	import DrawerLayout from '$lib/components/DrawerLayout.svelte';

	let { children } = $props();
</script>

<ThemeProvider>
	<DrawerLayout>
		{@render children()}
	</DrawerLayout>
</ThemeProvider>

<svelte:head>
	<link rel="icon" href={favicon} />
</svelte:head>

<div style="display:none">
	{#each locales as locale (locale)}
		<a href={resolve(localizeHref($page.url.pathname, { locale }) as any)}>{locale}</a>
	{/each}
</div>
