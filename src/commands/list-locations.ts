import { ApplyOptions } from '@sapphire/decorators';
import { Command } from '@sapphire/framework';
import { locations } from '../lib/gameData';
import { db } from '../lib/db';
import { Character, Optional, WithLocation } from '../lib/types';

@ApplyOptions<Command.Options>({
	description: 'The list of locations',
	preconditions: ['PlayerOnly']
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
		const character = await db
			.collection<Character & Optional<WithLocation, 'location'>>('characters')
			.findOne({ discordId: interaction.user.id });

		this.container.logger.debug(character);

		return interaction.reply({
			content: locations
				.map((location) => {
					return `Lvl. ${location.minLevel} ${location.name}` + (character?.location?.slug === location.slug ? ' (You are here)' : '');
				})
				.join('\n')
		});
	}
}
