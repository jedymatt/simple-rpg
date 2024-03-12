import { Precondition } from '@sapphire/framework';
import type { ChatInputCommandInteraction, ContextMenuCommandInteraction, Message, Snowflake } from 'discord.js';
import { db } from '../lib/db';

export class UserPrecondition extends Precondition {
	#message = 'Restricted to guests only';

	public override messageRun(message: Message) {
		return this.doGuestCheck(message.author.id);
	}

	public override chatInputRun(interaction: ChatInputCommandInteraction) {
		return this.doGuestCheck(interaction.user.id);
	}

	public override contextMenuRun(interaction: ContextMenuCommandInteraction) {
		return this.doGuestCheck(interaction.user.id);
	}

	private async doGuestCheck(userId: Snowflake) {
		const character = await db.collection('characters').findOne({ discordId: userId });

		return character ? this.error({ message: this.#message }) : this.ok();
	}
}

declare module '@sapphire/framework' {
	interface Preconditions {
		GuestOnly: never;
	}
}
