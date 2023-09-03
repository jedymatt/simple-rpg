import mongoose from "mongoose";

interface ILocation {
    name: string;
    slug: string;
    description: string;
    monsters: string[];
}

const locationSchema = new mongoose.Schema<ILocation>({
    name: { type: String, required: true },
    slug: { type: String, required: true },
    description: { type: String, required: true },
    monsters: { type: [String], required: true }
});

const Location = mongoose.model<ILocation>("Location", locationSchema);

export { Location };
