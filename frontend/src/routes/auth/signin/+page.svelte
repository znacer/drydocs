<script lang="ts">
	import { enhance } from '$app/forms';
	import type { ActionData } from './$types';

	let { form }: { form: ActionData } = $props();
</script>

<div class="flex min-h-screen items-center justify-center bg-base-200 p-4">
	<div class="card w-full max-w-md bg-base-100 shadow-lg">
		<div class="card-body">
			<div class="mb-6 text-center">
				<h1 class="text-3xl font-bold">Sign In</h1>
				<p class="text-gray-500">Enter your credentials to access your account</p>
			</div>

			{#if form && form.message}
				<div class="mb-4 alert alert-error">
					<svg
						xmlns="http://www.w3.org/2000/svg"
						class="h-6 w-6 shrink-0 stroke-current"
						fill="none"
						viewBox="0 0 24 24"
					>
						<path
							stroke-linecap="round"
							stroke-linejoin="round"
							stroke-width="2"
							d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z"
						/>
					</svg>
					<span>{form.message}</span>
				</div>
			{/if}

			<form method="post" action="?/signInEmail" use:enhance class="space-y-4">
				<div class="form-control">
					<label class="label" for="email">
						<span class="label-text">Email</span>
					</label>
					<input
						id="email"
						type="email"
						name="email"
						placeholder="your@email.com"
						class="input-bordered input w-full"
						required
					/>
				</div>

				<div class="form-control">
					<label class="label" for="password">
						<span class="label-text">Password</span>
					</label>
					<input
						id="password"
						type="password"
						name="password"
						placeholder="••••••••"
						class="input-bordered input w-full"
						required
					/>
				</div>

				<div class="form-control mt-6">
					<button type="submit" class="btn w-full btn-primary"> Sign In </button>
				</div>
			</form>

			<div class="divider">OR</div>

			<div class="text-center">
				<p class="text-sm text-gray-500">
					Do not have an account?
					<a href="/auth/signup" class="link link-primary">Sign Up</a>
				</p>
			</div>
		</div>
	</div>
</div>
