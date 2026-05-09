<script lang="ts">
	import { m } from '$lib/paraglide/messages';
</script>

<div class="flex min-h-screen items-center justify-center bg-base-200 p-4">
	<div class="card w-full max-w-md bg-base-100 shadow-lg">
		<div class="card-body text-center">
			<div class="mb-6">
				<svg
					xmlns="http://www.w3.org/2000/svg"
					width="64"
					height="64"
					viewBox="0 0 24 24"
					fill="none"
					stroke="currentColor"
					stroke-width="2"
					class="mx-auto text-primary"
				>
					<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
					<polyline points="7 10 12 15 17 10" />
					<line x1="12" x2="12" y1="15" y2="3" />
				</svg>
			</div>

			<h1 class="mb-2 text-2xl font-bold">{m.check_your_email()}</h1>
			<p class="mb-6 text-base-content/70">
				A verification link has been sent to your email address. Click the link to verify your
				account.
			</p>

			<div class="space-y-3">
				<p class="text-sm text-base-content/70">
					Didn't receive the email?
					<a href="/auth/signup" class="link link-primary">{m.try_again()}</a>
				</p>
				<a href="/auth/signin" class="btn btn-ghost">{m.back_to_sign_in()}</a>
			</div>
		</div>
	</div>
</div>
