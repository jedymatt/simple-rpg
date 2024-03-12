import { envParseString } from '@skyra/env-utilities';
import * as mongodb from 'mongodb';

const MONGODB_URI = envParseString('MONGODB_URI');

const client = new mongodb.MongoClient(MONGODB_URI);

export const connect = async () => {
	await client.connect();
};

export const db = client.db('simple_rpg');

type COLLECTION_NAMES = 'characters' | 'locations' | 'monsters';
declare module 'mongodb' {
	export interface Db {
		collection<TSchema extends mongodb.Document = mongodb.Document>(name: COLLECTION_NAMES, options?: CollectionOptions): Collection<TSchema>;
	}
}
