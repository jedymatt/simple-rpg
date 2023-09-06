import { ApplyOptions } from '@sapphire/decorators';
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

	public async chatInputMove(interaction: Subcommand.ChatInputCommandInteraction) {
		const destinationInput = interaction.options.getString('location');

		const destinationLocation = await Location.findOne({
			name: { $regex: new RegExp(`^${destinationInput}$`, 'i') }
		});

		if (!destinationLocation) {
			return await interaction.reply(`Location ${destinationInput} not found`);
		}

		const character = await Character.findOne({ discordId: interaction.user.id });

		if (character!.location.equals(destinationLocation._id)) {
			return await interaction.reply(`You are already in ${destinationLocation.name}`);
		}


		if (destinationLocation.levelRequirement > character!.level) {
			return await interaction.reply(`You need to be level ${destinationLocation.levelRequirement} to go there`);
		}

		await character!.updateOne({ location: destinationLocation });

		return await interaction.reply(`You moved to ${destinationLocation.name}`);
	}

	public async chatInputCurrent(interaction: Subcommand.ChatInputCommandInteraction) {
		const character = await Character.findOne({ discordId: interaction.user.id });

		const currentLocation = await Location.findById(character!.location);

		await interaction.reply(`Your current location is ${currentLocation!.name}`);
	}
}
