import { ApplyOptions } from '@sapphire/decorators';
import { Command } from '@sapphire/framework';
import { Character } from '../models/character';
import { Location } from '../models/location';
import { Monster } from '../models/monster';

@ApplyOptions<Command.Options>({
	description: 'Fight a monster in your current location',
	preconditions: ['registeredOnly']
})
export class UserCommand extends Command {
	public override registerApplicationCommands(registry: Command.Registry) {
		registry.registerChatInputCommand((builder) => builder.setName(this.name).setDescription(this.description));
	}

	public override async chatInputRun(interaction: Command.ChatInputCommandInteraction) {
		const character = await Character.findOne({ discordId: interaction.user.id });
		const currentLocation = await Location.findById(character!.location);

		// find monsters in current location
		const monstersInLocation = await Monster.find({ _id: { $in: currentLocation!.monsters } });

		// pick a random monster
		const monsterToFight = monstersInLocation[Math.floor(Math.random() * monstersInLocation.length)];

		// fight the monster until either the player or the monster dies
		let characterHp = character!.attributes.hp;
		let monsterHp = monsterToFight.attributes.hp;
		while (characterHp > 0 && monsterHp > 0) {
			// player attacks monster
			const playerDamage = character!.attributes.strength - monsterToFight.attributes.defense;
			monsterHp -= playerDamage;

			// monster attacks player
			const monsterDamage = monsterToFight.attributes.strength - character!.attributes.defense;
			characterHp -= monsterDamage;
		}

		// if the player died, return a message saying so
		if (characterHp <= 0) {
			// include the remaining hp of the monster in the message
			return interaction.reply({ content: `You died! Remaining hp of ${monsterToFight.name} is ${monsterHp}/${monsterToFight.attributes.hp}.` });
		}

		// if the monster died, return a message saying so
		if (monsterHp <= 0) {
			// give experience to the player
			await character!.updateOne({ exp: character!.exp + 20 });

			return interaction.reply({
				content: `You killed the ${monsterToFight.name}! Your remaining hp is ${characterHp}/${character!.attributes.hp}. Gain 20 exp.`
			});
		}

		// if neither died, return a message saying so
		return interaction.reply({ content: 'Something went wrong!' });
	}
}
