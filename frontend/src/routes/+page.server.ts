import { getDocuments } from '$lib/utils/api';
import type { PageServerLoad } from './$types';

export const load: PageServerLoad = async ({ params }) => {
	return {
		documents: await getDocuments()
	};
};
