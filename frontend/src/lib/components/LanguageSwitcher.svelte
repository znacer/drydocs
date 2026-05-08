<script lang="ts">
	import type { Pathname } from '$app/types';
	import { resolve } from '$app/paths';
	import { page } from '$app/state';
	import { locales, localizeHref } from '$lib/paraglide/runtime';
	let language = $derived.by(() => {
		const locale = page.url.pathname;
		if (locale === '/') {
			return 'en';
		}
		if (locale.startsWith('/')) {
			return locale.slice(1);
		}
		return locale;
	});
</script>

<div class="dropdown dropdown-start">
	<div tabindex="0" role="button" class="btn m-1 btn-ghost">
		<!-- display the current language -->
		{language}
	</div>
	<ul tabindex="-1" class="dropdown-content menu w-52 rounded-box bg-base-100 p-2 shadow">
		{#each locales as locale (locale)}
			<li>
				<a href={resolve(localizeHref(page.url.pathname, { locale }) as Pathname)}>{locale}</a>
			</li>
		{/each}
	</ul>
</div>
