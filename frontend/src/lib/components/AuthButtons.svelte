<script lang="ts">
	import type { User } from 'better-auth';

	let { user }: { user?: User | null } = $props();
</script>

<div class="flex gap-2">
	{#if user}
		<a href="/profile" class="btn btn-ghost btn-sm">{user.name}</a>
		<form method="post" action="/api/signout">
			<button type="submit" class="btn text-red-500 btn-ghost btn-sm">Sign out</button>
		</form>
	{:else}
		<a href="/auth/signin" class="btn btn-ghost btn-sm">Sign in</a>
		<a href="/auth/signup" class="btn btn-sm btn-primary">Sign up</a>
	{/if}
</div>
