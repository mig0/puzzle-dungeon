NUM_MAPS = 10

stoneage_infos = [
	# theme, code, time, number
	(1,     None,  87),  # 001
	(1, 'BOVIDO', 118),  # 002
	(2, 'SIDULA',  87),  # 003
	(3, 'BIFISI',  50),  # 004
	(2, 'LOVUHO', 125),  # 005
	(1, 'BADEBA', 125),  # 006
	(3, 'LUFIDO', 100),  # 007
	(4, 'HAVULU',  81),  # 008
	(3, 'LODISE', 131),  # 009
	(4, 'HIFUHI', 100),  # 010
	(1, 'DIVOBI', 600),  # 011
	(1, 'HEDIDA', 600),  # 012
	(1, 'DAFALI', 600),  # 013
	(1, 'HUVESU', 600),  # 014
	(1, 'DADOHA', 600),  # 015
	(1, 'SOFOBO', 600),  # 016
	(1, 'DIVIDE', 600),  # 017
	(1, 'SIDABI', 600),  # 018
	(1, 'BEFEDO', 600),  # 019
	(1, 'SAVOLI', 600),  # 020
	(1, 'BUDUSU', 600),  # 021
	(1, 'LIFOHU', 600),  # 022
	(1, 'BOVIBE', 600),  # 023
	(1, 'LIDADA', 600),  # 024
	(1, 'BIFALO', 600),  # 025
	(1, 'LEVUSA', 600),  # 026
	(1, 'HADOHI', 600),  # 027
	(1, 'LUFIBO', 600),  # 028
	(1, 'HIVADA', 600),  # 029
	(1, 'DODALO', 600),  # 030
	(1, 'HIFUSE', 600),  # 031
	(1, 'DIVEHE', 600),  # 032
	(1, 'SEDIBI', 600),  # 033
	(1, 'DUFUDI', 600),  # 034
	(1, 'SUVIBU', 600),  # 035
	(1, 'DIDUDI', 600),  # 036
	(1, 'SOFELU', 600),  # 037
	(1, 'BIVISA', 600),  # 038
	(1, 'SEDUHO', 600),  # 039
	(1, 'BEFIBE', 600),  # 040
	(1, 'LUVUDI', 600),  # 041
	(1, 'BUDOLO', 600),  # 042
	(1, 'LIFISA', 600),  # 043
	(1, 'HAVAHU', 600),  # 044
	(1, 'LIDEBU', 600),  # 045
	(1, 'HEFODE', 600),  # 046
	(1, 'DEVOLI', 600),  # 047
	(1, 'HUDISO', 600),  # 048
	(1, 'DUFAHA', 600),  # 049
	(1, 'HIVEBI', 600),  # 050
	(1, 'DADODU', 600),  # 051
	(1, 'SIFUBA', 600),  # 052
	(1, 'DEVODO', 600),  # 053
	(1, 'SEDILE', 600),  # 054
	(1, 'BUFASE', 600),  # 055
	(1, 'SUVAHI', 600),  # 056
	(1, 'BIDUBI', 600),  # 057
	(1, 'LAFODU', 600),  # 058
	(1, 'BIVILI', 600),  # 059
	(1, 'LEDASU', 600),  # 060
	(1, 'BOFAHA', 600),  # 061
	(1, 'LUVUBO', 600),  # 062
	(1, 'HUDEDE', 600),  # 063
	(1, 'LIFILI', 600),  # 064
	(1, 'HAVUSO', 600),  # 065
	(1, 'DODIHA', 600),  # 066
	(1, 'HETUBU', 600),  # 067
	(1, 'DOREDU', 600),  # 068
	(1, 'SUHIBE', 600),  # 069
	(1, 'DUTUDI', 600),  # 070
	(1, 'SIRILO', 600),  # 071
	(1, 'DAHUSA', 600),  # 072
	(1, 'SOTOHI', 600),  # 073
	(1, 'BERIBU', 600),  # 074
	(1, 'SOHADA', 600),  # 075
	(1, 'BUTELO', 600),  # 076
	(1, 'LUROSE', 600),  # 077
	(1, 'BIHOHI', 600),  # 078
	(1, 'LATIBI', 600),  # 079
	(1, 'HORADI', 600),  # 080
	(1, 'LEHELU', 600),  # 081
	(1, 'HOTOSU', 600),  # 082
	(1, 'DARUNU', 600),  # 083
	(1, 'HUHOBA', 600),  # 084
	(1, 'DITIDO', 600),  # 085
	(1, 'HARABA', 600),  # 086
	(1, 'DOHADI', 600),  # 087
	(1, 'SATULO', 600),  # 088
	(1, 'DOROSA', 600),  # 089
	(1, 'SAHIHO', 600),  # 090
	(1, 'BUTABU', 600),  # 091
	(1, 'SIRADE', 600),  # 092
	(1, 'BIHULI', 600),  # 093
	(1, 'LOTESI', 600),  # 094
	(1, 'BARIHA', 600),  # 095
	(1, 'LOHUBI', 600),  # 096
	(1, 'BATIDU', 600),  # 097
	(1, 'LURULA', 600),  # 098
	(1, 'HIHESO', 600),  # 099
	(1, 'LITIHE', 600),  # 100
]

music_files = [
	"01_stardust_falling",
	"02_bone_and_stone",
	"03_plastic_age",
	"04_autumn_storm",
	"05_the_dragon's_tale",
	"06_no_choice_left",
	"07_wildlife",
	"08_the_golden_valley",
]

stoneage_levels = []

for i in range(NUM_MAPS):
	n = i + 1
	stoneage_levels.append({
		"n": 15 + n / 1000,
		"title": "Original Stone Age",
		"name": "{level-label} %d" % n,
		"goal": "finish-stoneage-puzzle",
		"map_size": (20, 11),
		"map_file": "stoneage/%03d.map" % n,
		"theme": "stoneage%d" % stoneage_infos[i][0],
		"music": "stoneage/%s" % music_files[i % len(music_files)],  # random.choise(music_files)
		"bg_image": "images/stoneage%d/bg.webp" % stoneage_infos[i][0],
		"time_limit": stoneage_infos[i][2],
		"char_health": None,
		"num_enemies": 0,
		"stoneage_puzzle": {
			"code": stoneage_infos[i][1],
		},
	})
