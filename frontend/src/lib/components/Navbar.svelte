<script lang="ts">
	import { page } from '$app/state';
	import LanguageSwitcher from './LanguageSwitcher.svelte';
	import ThemeToggle from './ThemeToggle.svelte';
	import UserMenu from './UserMenu.svelte';
</script>

<div class="navbar bg-base-200">
	<div class="flex-none">
		<label for="my-drawer" class="drawer-button btn btn-square btn-ghost lg:hidden">
			<svg
				xmlns="http://www.w3.org/2000/svg"
				fill="none"
				viewBox="0 0 24 24"
				class="inline-block h-5 w-5 stroke-current"
			>
				<path
					stroke-linecap="round"
					stroke-linejoin="round"
					stroke-width="2"
					d="M4 6h16M4 12h16M4 18h16"
				></path>
			</svg>
		</label>
	</div>
	<div class="flex-1">
		<a href="/" class="btn text-xl normal-case btn-ghost">drydocs</a>
	</div>
	<div class="flex flex-none items-center gap-2">
		<LanguageSwitcher />
		<ThemeToggle />
		<UserMenu user={page.data.user} />
	</div>
</div>
