import { Precondition } from '@sapphire/framework';
import type { ChatInputCommandInteraction, ContextMenuCommandInteraction, Message, User } from 'discord.js';

export class UserPrecondition extends Precondition {
	public override messageRun(message: Message) {
		return this.owner(message.author);
	}

	public override chatInputRun(interaction: ChatInputCommandInteraction) {
		return this.owner(interaction.user);
	}

	public override contextMenuRun(interaction: ContextMenuCommandInteraction) {
		return this.owner(interaction.user);
	}

	public owner(user: User): Precondition.Result {
		if (user.id === process.env.OWNER_ID) return this.ok();

		return this.error({ message: 'Only the bot owner(s) may run this command.' });
	}
}

declare module '@sapphire/framework' {
	interface Preconditions {
		ownerOnly: never;
	}
}
