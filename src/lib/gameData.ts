import { Location, Monster } from './types';

type LocationWithMonsters = Location & {
	monsters?: Monster[];
};

export const locations: LocationWithMonsters[] = [
	{
		name: 'Hometown',
		slug: 'hometown',
		description: 'A peaceful town where you live',
		minLevel: 1
	},
	{
		name: 'Forest',
		slug: 'forest',
		description: 'A dark and dangerous forest',
		minLevel: 1
	},
	{
		name: 'Cave',
		slug: 'cave',
		description: 'A dark and dangerous cave',
		minLevel: 3
	}
];
