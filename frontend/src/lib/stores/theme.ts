import { writable } from 'svelte/store';

// Create a writable store for theme
export const theme = writable<string | null>(null);

// Function to apply the theme
export const applyTheme = (themeName: string) => {
	document.documentElement.setAttribute('data-theme', themeName);
	localStorage.setItem('theme', themeName);
};

// Function to toggle theme
export const toggleTheme = () => {
	theme.update((current) => {
		const newTheme = current === 'dark' ? 'light' : 'dark';
		applyTheme(newTheme);
		return newTheme;
	});
};

// Initialize theme on module load (will be called by ThemeProvider)
export const initializeTheme = () => {
	const savedTheme = localStorage.getItem('theme');
	const systemPrefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;

	if (savedTheme) {
		applyTheme(savedTheme);
		theme.set(savedTheme);
	} else {
		const initialTheme = systemPrefersDark ? 'dark' : 'light';
		applyTheme(initialTheme);
		theme.set(initialTheme);
	}
};
