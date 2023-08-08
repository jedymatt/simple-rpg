import mongoose from 'mongoose';

const connect = async () => {
    try {
        await mongoose.connect(process.env.MONGODB_URI);
    } catch (error: any) {
        throw new Error(`Error connecting to database: ${error.message}`);
    }
};

export default connect;