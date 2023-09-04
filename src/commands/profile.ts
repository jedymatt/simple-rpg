import { ApplyOptions } from '@sapphire/decorators';
import { Command } from '@sapphire/framework';
import { Character, Location } from '../models';

@ApplyOptions<Command.Options>({
	description: 'Show your profile',
	preconditions: ['registeredOnly']
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
		const character = await Character.findOne({ discordId: interaction.user.id });

		// return a embed with the character's information
		return interaction.reply({
			embeds: [
				{
					title: interaction.user.username,
					thumbnail: { url: interaction.user.displayAvatarURL() },
					fields: [
						{
							name: 'Level',
							value: character!.level.toString()
						},
						{
							name: 'Exp',
							value: `${character!.exp}/${character!.level * 100}`
						},
						{
							name: 'Current Location',
							value: (await Location.findById(character!.location))!.name
						}
					]
				}
			]
		});
	}
}
