<script lang="ts">
	import Navbar from './Navbar.svelte';
	import Sidebar from './Sidebar.svelte';
	import Footer from './Footer.svelte';

	let { children } = $props();
</script>

<div class="drawer">
	<input id="my-drawer" type="checkbox" class="drawer-toggle" />
	<div class="drawer-content flex flex-col">
		<Navbar />
		<div class="grow p-4">
			{@render children()}
		</div>
		<Footer />
	</div>
	<Sidebar />
</div>
