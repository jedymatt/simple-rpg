import { ApplyOptions } from '@sapphire/decorators';
import { Command } from '@sapphire/framework';
import { Monster, Location } from '../../models';

@ApplyOptions<Command.Options>({
	description: 'Seed the database with default data',
	preconditions: ['ownerOnly'],
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
		const spiderMonster = await Monster.create({
			name: 'Spider',
			description: 'A small spider.',
			attributes: {
				hp: 30,
				strength: 10,
				defense: 5
			}
		});

		const slimeMonster = await Monster.create({
			name: 'Slime',
			description: 'A small slime.',
			attributes: {
				hp: 20,
				strength: 5,
				defense: 10
			}
		});

		await Location.create({
			name: 'Hometown',
			description: 'A place where you grew up.',
			levelRequirement: 1,
			monsters: [spiderMonster, slimeMonster]
		});

		await Location.create({
			name: 'Northern Plain',
			description: 'A place filled with grass and trees',
			levelRequirement: 5,
			monsters: [spiderMonster, slimeMonster]
		});

		await Location.create({
			name: 'Dry Lake',
			description: 'A place where a lake used to be.',
			levelRequirement: 12,
			monsters: []
		});

		return interaction.reply({ content: 'Done!' });
	}
}
