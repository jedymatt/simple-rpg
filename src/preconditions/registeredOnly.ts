import { Precondition } from '@sapphire/framework';
import type { ChatInputCommandInteraction, ContextMenuCommandInteraction, Message } from 'discord.js';
import { Character } from '../models';

export class UserPrecondition extends Precondition {
	public override async messageRun(message: Message) {
		return await this.registered(message.author.id);
	}

	public override async chatInputRun(interaction: ChatInputCommandInteraction) {
		return await this.registered(interaction.user.id);
	}

	public override async contextMenuRun(interaction: ContextMenuCommandInteraction) {
		return await this.registered(interaction.user.id);
	}

	public async registered(discordId: string): Promise<Precondition.Result> {
		const registeredCharacter = await Character.findOne({ discordId: discordId });

		if (registeredCharacter) return this.ok();

		return this.error({ message: 'You must register a character before you can use this command.' });
	}
}

declare module '@sapphire/framework' {
	interface Preconditions {
		registeredOnly: never;
	}
}
