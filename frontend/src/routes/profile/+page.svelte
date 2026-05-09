<script lang="ts">
	import type { PageData } from './$types';
	import { m } from '$lib/paraglide/messages';

	let { data }: { data: PageData } = $props();
</script>

<div class="min-h-screen bg-base-200 p-4">
	<div class="mx-auto max-w-4xl">
		<div class="card bg-base-100 shadow-lg">
			<div class="card-body">
				<div class="flex flex-col items-center gap-6">
					<div class="online placeholder avatar">
						<div class="w-24 rounded-full bg-primary text-primary-content">
							<span class="text-3xl">{data.user.name.charAt(0).toUpperCase()}</span>
						</div>
					</div>

					<div class="text-center">
						<h1 class="text-3xl font-bold">{data.user.name}</h1>
						<p class="mt-2 text-base-content/70">{data.user.email}</p>
						{#if data.user.emailVerified}
							<span class="mt-2 badge badge-success">{m.email_verified()}</span>
						{:else}
							<span class="mt-2 badge badge-warning">{m.email_not_verified()}</span>
						{/if}
					</div>

					<div class="divider w-full"></div>

					<div class="w-full space-y-4">
						<div class="stats shadow">
							<div class="stat">
								<div class="stat-title">{m.account_created()}</div>
								<div class="stat-value">
									{new Date(data.user.createdAt).toLocaleDateString()}
								</div>
							</div>
						</div>

						<div class="card-actions justify-end">
							<a href="/settings" class="btn btn-ghost">{m.settings()}</a>
							<form method="post" action="/api/signout">
								<button type="submit" class="btn btn-error">{m.sign_out()}</button>
							</form>
						</div>
					</div>
				</div>
			</div>
		</div>
	</div>
</div>
