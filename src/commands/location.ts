import { ApplyOptions } from '@sapphire/decorators';
import { Args } from '@sapphire/framework';
import { Subcommand } from '@sapphire/plugin-subcommands';
import { Character, Location } from '../models';

@ApplyOptions<Subcommand.Options>({
	description: 'A basic slash command',
	preconditions: ['registeredOnly'],
	subcommands: [
		{
			name: 'move',
			chatInputRun: 'chatInputMove'
		},
		{
			name: 'current',
			chatInputRun: 'chatInputCurrent'
		}
	]
})
export class UserCommand extends Subcommand {
	public override registerApplicationCommands(registry: Subcommand.Registry) {
		registry.registerChatInputCommand((builder) =>
			builder //
				.setName(this.name)
				.setDescription(this.description)
				.addSubcommand((command) =>
					command
						.setName('move')
						.setDescription('Move to a location')
						.addStringOption((option) => option.setName('location').setDescription('The location to move to').setRequired(true))
				)
				.addSubcommand((command) => command.setName('current').setDescription('Get your current location'))
		);
	}

	public async chatInputMove(interaction: Subcommand.ChatInputCommandInteraction, _: Args) {
		await interaction.reply('Hello');
	}

	public async chatInputCurrent(interaction: Subcommand.ChatInputCommandInteraction) {
		const character = await Character.findOne({ discordId: interaction.user.id });

		const currentLocation = await Location.findById(character!.location);

		await interaction.reply(`Your current location is ${currentLocation!.name}`);
	}
}
