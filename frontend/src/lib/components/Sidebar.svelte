<script lang="ts">
	import { m } from '$lib/paraglide/messages';
</script>

<div class="drawer-side">
	<label for="my-drawer" aria-label="close sidebar" class="drawer-overlay"></label>
	<ul class="menu min-h-full w-80 bg-base-200 p-4 text-base-content">
		<li><a href="/" class="active">{m.nav_home()}</a></li>
		<li><a href="/about">{m.nav_about()}</a></li>
		<li><a href="/docs">{m.nav_docs()}</a></li>
		<li><a href="/contact">{m.nav_contact()}</a></li>
	</ul>
</div>
