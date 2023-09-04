import mongoose from 'mongoose';

interface IMonster {
	name: string;
	slug: string;
	description: string;
	attributes: {
		hp: number;
		strength: number;
		defense: number;
	};
}

const monsterSchema = new mongoose.Schema<IMonster>({
	name: { type: String, required: true, unique: true },
	description: { type: String, required: true },
	attributes: {
		hp: { type: Number, required: true },
		strength: { type: Number, required: true },
		defense: { type: Number, required: true }
	}
});

const Monster = mongoose.model<IMonster>('Monster', monsterSchema);

export { Monster };
export type { IMonster };
