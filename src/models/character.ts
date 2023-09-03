import mongoose from 'mongoose';

interface ICharacter {
	discordId: string;
	level: number;
	exp: number;
	attributes: {
		hp: number;
		strength: number;
		defense: number;
	};
	location: String;
}

const characterSchema = new mongoose.Schema<ICharacter>({
	discordId: { type: String, required: true },
	level: { type: Number, required: true },
	exp: { type: Number, required: true},
	attributes: {
		hp: {type: Number, required: true},
		strength: {type: Number, required: true},
		defense: {type: Number, required: true},
	},
	location: { type: String, required: true }
});

const Character = mongoose.model<ICharacter>('Character', characterSchema);

export { Character };
