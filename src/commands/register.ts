import { ApplyOptions } from '@sapphire/decorators';
import { Command } from '@sapphire/framework';
import { Attribute, Character } from '../lib/types';
import { db } from '../lib/db';

type CharacterWithAttribute = Character & {
	attribute: Attribute;
};

@ApplyOptions<Command.Options>({
	description: 'Register a new user',
	preconditions: ['GuestOnly']
})
export class UserCommand extends Command {
	public override registerApplicationCommands(registry: Command.Registry) {
		registry.registerChatInputCommand((builder) =>
			builder //
				.setName(this.name)
				.setDescription(this.description)
		);
	}

	public override async chatInputRun(interaction: Command.ChatInputCommandInteraction) {
		const character: CharacterWithAttribute = {
			discordId: interaction.user.id,
			exp: 0,
			level: 1,
			money: 0,
			attribute: {
				hp: 50,
				strength: 15,
				defense: 5
			}
		};

		await db.collection<CharacterWithAttribute>('characters').insertOne(character);

		return interaction.reply({ content: 'Succesfully registered!' });
	}
}
