import { ApplyOptions } from '@sapphire/decorators';
import { Command } from '@sapphire/framework';
import { Character } from '../models/character';

@ApplyOptions<Command.Options>({
	description: 'Register a character',
})
export class UserCommand extends Command {
	public override registerApplicationCommands(registry: Command.Registry) {
		registry.registerChatInputCommand((builder) =>
			builder
				.setName(this.name)
				.setDescription(this.description)
		);
	}

	public override async chatInputRun(interaction: Command.ChatInputCommandInteraction) {
		if (await Character.exists({ discordId: interaction.user.id })) {
			return await interaction.reply({ content: 'You already have a character registered!', ephemeral: true });
		}

		await Character.create({
			discordId: interaction.user.id,
			level: 1,
			exp: 0,
			attributes: {
				hp: 50,
				strength: 15,
				defense: 5,
			},
			location: 'hometown',
		});


		return interaction.reply({ content: 'Character successfully registered.' });
	}
}
