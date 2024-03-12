import { Precondition } from '@sapphire/framework';
import type { ChatInputCommandInteraction, ContextMenuCommandInteraction, Message, Snowflake } from 'discord.js';
import { db } from '../lib/db';

export class UserPrecondition extends Precondition {
	#message = 'You need to register first!';

	public override messageRun(message: Message) {
		return this.doPlayerCheck(message.author.id);
	}

	public override chatInputRun(interaction: ChatInputCommandInteraction) {
		return this.doPlayerCheck(interaction.user.id);
	}

	public override contextMenuRun(interaction: ContextMenuCommandInteraction) {
		return this.doPlayerCheck(interaction.user.id);
	}

	private async doPlayerCheck(userId: Snowflake) {
		const character = await db.collection('characters').findOne({ discordId: userId });

		return character ? this.ok() : this.error({ message: this.#message });
	}
}

declare module '@sapphire/framework' {
	interface Preconditions {
		PlayerOnly: never;
	}
}
