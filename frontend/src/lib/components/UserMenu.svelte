<script lang="ts">
	import type { User } from 'better-auth';

	let { user }: { user?: User | null } = $props();
</script>

{#if user}
	<div class="dropdown dropdown-end">
		<div role="button" class="btn avatar btn-circle btn-ghost">
			<div class="w-10 rounded-full">
				{#if user.image}
					<img src={user.image} alt={user.name} />
				{:else}
					<div
						class="flex h-full w-full items-center justify-center bg-primary text-xl text-primary-content"
					>
						{user.name.charAt(0).toUpperCase()}
					</div>
				{/if}
			</div>
		</div>
		<ul class="dropdown-content menu w-52 rounded-box bg-base-100 p-2 shadow">
			<li>
				<a href="/profile" class="justify-between">
					Profile
					<span class="badge badge-primary">{user.name}</span>
				</a>
			</li>
			<li>
				<a href="/settings">Settings</a>
			</li>
			<li>
				<form method="post" action="/api/signout">
					<button type="submit" class="text-red-500">Sign out</button>
				</form>
			</li>
		</ul>
	</div>
{:else}
	<a href="/auth/signin" class="btn btn-ghost">Sign in</a>
{/if}
