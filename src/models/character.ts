import mongoose from 'mongoose';

const Character = mongoose.model(
    'Character',
    new mongoose.Schema({
        discordId: String,
        level: Number,
        exp: Number
    })
);

export { Character };
