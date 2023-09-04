import mongoose from 'mongoose';
import type { IMonster } from './monster';

interface ILocation {
	name: string;
	description: string;
	levelRequirement: number;
	monsters: mongoose.PopulatedDoc<mongoose.Document<mongoose.ObjectId[]> & IMonster[]>;
}

const locationSchema = new mongoose.Schema<ILocation>({
	name: { type: String, required: true, unique: true },
	description: { type: String, required: false },
	levelRequirement: { type: Number, required: true },
	monsters: { type: [mongoose.Schema.Types.ObjectId], ref: 'Monster', required: true }
});

const Location = mongoose.model<ILocation>('Location', locationSchema);

export { Location };
export type { ILocation };
