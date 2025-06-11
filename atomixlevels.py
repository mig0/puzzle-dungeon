from random import randint

atomix_molecule_names = [
	"Water",
	"Methane",
	"Methanol",
	"Ethylene",
	"Propylene",
	"Ethanal",
	"Ethanol",
	"Acetic Acid",
	"Dimethyl Ether",
	"Methanal",
	"Acetone",
	"Trans Butylen",
	"Butanol",
	"Propanal",
	"Pyran",
	"Cyclobutane",
	"Ethane",
	"Lactic Acid",
	"Glycerin",
]

atomix_levels = []
for i, molecule_name in enumerate(atomix_molecule_names):
	atomix_levels.append({
		"n": 20 + (i + 1) / 100,
		"name": "Atomix: %s" % molecule_name,
		"bg_image": "bg/chemistry-%d.webp" % randint(1, 2),
		"theme": ("stoneage1", "stoneage2", "default", "modern1", "moss")[randint(0, 4)],
		"music": ("playful_sparrow", "film", "forest_walk", "epic_cinematic_trailer", "adventures")[randint(0, 4)] + ".mp3",
		"map_file": "atomix/" + molecule_name.replace(" ", "-").lower() + ".map",
		"goal": "{compose-molecule-label} %s" % molecule_name,
		"num_enemies": 0,
		"char_health": None,
		"atomix_puzzle": { "molecule_name": molecule_name },
	})
