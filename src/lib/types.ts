export type Attribute = {
	hp: number;
	strength: number;
	defense: number;
};

export type Character = {
	discordId: string;
	exp: number;
	level: number;
	money: number;
};

export type Location = {
	name: string;
	slug: string;
	description: string;
	minLevel: number;
};

export type Monster = {
	name: string;
	slug: string;
	description: string;
};

export type CharacterWithAttribute = Character & {
	attribute: Attribute;
};

export type WithAttribute = {
	attribute: Attribute;
};

export type WithLocation = {
	location: Location;
};

export type Optional<T, K extends keyof T> = Omit<T, K> & Partial<T>;