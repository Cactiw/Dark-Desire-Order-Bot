# @oldf4g property - do NOT copy, do NOT distribute

from collections import defaultdict

alch_recipes = defaultdict(dict)
# 509 - Poison pack - Alchemy lvl 1 - 10💧
# 1 Maccunut + 1 Ephijora
alch_recipes['poison pack'] = defaultdict(dict)
alch_recipes['poison pack']['mana'] = '10'
alch_recipes['poison pack']['code'] = '509'
alch_recipes['poison pack']['recipe']['maccunut'] = '1'
alch_recipes['poison pack']['recipe']["ephijora"] = '1'

# Зелья на слот щита-кинжала для алхимиков - описание читать в разделе Алхимик
# 507 - Remedy pack - Alchemy lvl 1 - 10💧
# 1 Cliff Rue + 1 Tecceagrass
alch_recipes['remedy pack'] = defaultdict(dict)
alch_recipes['remedy pack']['mana'] = '10'
alch_recipes['remedy pack']['code'] = '507'
alch_recipes['remedy pack']['recipe']['cliff rue'] = '1'
alch_recipes['remedy pack']['recipe']["tecceagrass"] = '1'


# 506 - Bottle of Remedy💧
# 1 Cliff Rue + 1 Tecceagrass
alch_recipes['bottle of remedy'] = defaultdict(dict)
alch_recipes['bottle of remedy']['code'] = '506'


# 63 - Assassin Vine: - 15💧
# 1 White Blossom + 1 Sanguine Parsley
alch_recipes['assassin vine'] = defaultdict(dict)
alch_recipes['assassin vine']['mana'] = '15'
alch_recipes['assassin vine']['code'] = '63'
alch_recipes['assassin vine']['recipe']['white blossom'] = '1'
alch_recipes['assassin vine']['recipe']['sanguine parsley'] = '1'

# 61 - Ethereal Bone: - 10💧
# 1 Yellow Seed + 1 Ephijora + 1 Ilaves + 1 Maccunut
alch_recipes['ethereal bone'] = defaultdict(dict)
alch_recipes['ethereal bone']['mana'] = '10'
alch_recipes['ethereal bone']['code'] = '61'
alch_recipes['ethereal bone']['recipe']['yellow seed'] = '1'
alch_recipes['ethereal bone']['recipe']['ephijora'] = '1'
alch_recipes['ethereal bone']['recipe']['ilaves'] = '1'
alch_recipes['ethereal bone']['recipe']['maccunut'] = '1'

# 62 - Itacory: - 15💧
# 1 Swamp Lavender + 1 Ash Rosemary
alch_recipes['itacory'] = defaultdict(dict)
alch_recipes['itacory']['mana'] = '15'
alch_recipes['itacory']['code'] = '62'
alch_recipes['itacory']['recipe']['swamp lavender'] = '1'
alch_recipes['itacory']['recipe']['ash rosemary'] = '1'

# 64 - Kloliarway:  - 15💧
# 1 Mercy Sassafras + Queen's Pepper
alch_recipes['kloliarway'] = defaultdict(dict)
alch_recipes['kloliarway']['mana'] = '15'
alch_recipes['kloliarway']['code'] = '64'
alch_recipes['kloliarway']['recipe']['mercy sassafras'] = '1'
alch_recipes['kloliarway']['recipe']["queen's pepper"] = '1'

alch_recipes['plasma of abyss'] = defaultdict(dict)
alch_recipes['plasma of abyss']['mana'] = '10'
alch_recipes['plasma of abyss']['code'] = '59'
alch_recipes['plasma of abyss']['recipe']['cliff rue'] = '1'
alch_recipes['plasma of abyss']['recipe']['sun tarragon'] = '1'
alch_recipes['plasma of abyss']['recipe']['cave garlic'] = '1'

alch_recipes['silver dust'] = defaultdict(dict)
alch_recipes['silver dust']['mana'] = '30'
alch_recipes['silver dust']['code'] = '69'
alch_recipes['silver dust']['recipe']['powder'] = '2'
alch_recipes['silver dust']['recipe']['silver ore'] = '5'
alch_recipes['silver dust']['recipe']['tecceagrass'] = '1'

# 60 - Ultramarine Dust: - 10💧
# 1 Stinky Sumac + 1 Tecceagrass + 1 Storm Hyssop
alch_recipes['ultramarine dust'] = defaultdict(dict)
alch_recipes['ultramarine dust']['mana'] = '10'
alch_recipes['ultramarine dust']['code'] = '60'
alch_recipes['ultramarine dust']['recipe']['stinky sumac'] = '1'
alch_recipes['ultramarine dust']['recipe']['tecceagrass'] = '1'
alch_recipes['ultramarine dust']['recipe']['storm hyssop'] = '1'

# Зелья ярости (Rage) + к атаке, родной без учета шмота
# p01 - Vial of Rage - Alchemy lvl 1 - 10💧 - +5%⚔️
# 1 Sun Tarragon + 1 Storm Hyssop
alch_recipes['vial of rage'] = defaultdict(dict)
alch_recipes['vial of rage']['mana'] = '10'
alch_recipes['vial of rage']['code'] = 'p01'
alch_recipes['vial of rage']['recipe']['sun tarragon'] = '1'
alch_recipes['vial of rage']['recipe']["storm hyssop"] = '1'

# p02 - Potion of Rage - Alchemy lvl 2 - 15💧 - +10%⚔️
# 1 Assassin Vine + 2 Storm Hyssop + 1 Plasma of Abyss
alch_recipes['potion of rage'] = defaultdict(dict)
alch_recipes['potion of rage']['mana'] = '10'
alch_recipes['potion of rage']['code'] = 'p02'
alch_recipes['potion of rage']['recipe']['assassin vine'] = '1'
alch_recipes['potion of rage']['recipe']["storm hyssop"] = '2'
alch_recipes['potion of rage']['recipe']["plasma of abyss"] = '1'

# p03 - Bottle of Rage - Alchemy lvl 3 - 30💧 - +15%⚔️
# 2 Assassin Vine + 1 Wolf Root + 1 Plasma of Abyss + 1 Spring Bay Leaf
alch_recipes['bottle of rage'] = defaultdict(dict)
alch_recipes['bottle of rage']['mana'] = '30'
alch_recipes['bottle of rage']['code'] = 'p03'
alch_recipes['bottle of rage']['recipe']['assassin vine'] = '2'
alch_recipes['bottle of rage']['recipe']["wolf root"] = '1'
alch_recipes['bottle of rage']['recipe']["plasma of abyss"] = '1'
alch_recipes['bottle of rage']['recipe']["spring bay leaf"] = '1'

# Зелья покоя (Peace) + к дефу, родному, без учета шмота
# 04 - Vial of Peace - Alchemy lvl 1 - 10💧 - +5%🛡
# 1 Stinky Sumac + 1 Cave Garlic
alch_recipes['vial of peace'] = defaultdict(dict)
alch_recipes['vial of peace']['mana'] = '10'
alch_recipes['vial of peace']['code'] = 'p04'
alch_recipes['vial of peace']['recipe']['stinky sumac'] = '1'
alch_recipes['vial of peace']['recipe']["cave garlic"] = '1'

# p05 - Potion of Peace - Alchemy lvl 2 - 15💧 - +10%🛡
# 1 Ultramarine Dust + 2 Cave Garlic + 1 Itacory
alch_recipes['potion of peace'] = defaultdict(dict)
alch_recipes['potion of peace']['mana'] = '15'
alch_recipes['potion of peace']['code'] = 'p05'
alch_recipes['potion of peace']['recipe']['ultramarine dust'] = '1'
alch_recipes['potion of peace']['recipe']["cave garlic"] = '2'
alch_recipes['potion of peace']['recipe']["itacory"] = '1'

# p06 - Bottle of Peace - Alchemy lvl 3 - 30💧 - +15%🛡
# 2 Itacory + 1 Spring Bay Leaf + 1 Dragon Seed + 1 Ultramarine Dust
alch_recipes['bottle of peace'] = defaultdict(dict)
alch_recipes['bottle of peace']['mana'] = '30'
alch_recipes['bottle of peace']['code'] = 'p06'
alch_recipes['bottle of peace']['recipe']['itacory'] = '2'
alch_recipes['bottle of peace']['recipe']["spring bay leaf"] = '1'
alch_recipes['bottle of peace']['recipe']["dragon seed"] = '1'
alch_recipes['bottle of peace']['recipe']["ultramarine dust"] = '1'

# Зелья жадности (Greed) - что дает, до сих пор точно неизвестно
# p07 - Vial of Greed - Alchemy lvl 1 - 10💧
# 1 Yellow Seed + 1 Ilaves
alch_recipes['vial of greed'] = defaultdict(dict)
alch_recipes['vial of greed']['mana'] = '10'
alch_recipes['vial of greed']['code'] = 'p07'
alch_recipes['vial of greed']['recipe']['yellow seed'] = '1'
alch_recipes['vial of greed']['recipe']["ilaves"] = '1'

# p08 - Potion of Greed - Alchemy lvl 2 - 15💧
# 1 Ethereal Bone + 1 Kloliarway
alch_recipes['potion of greed'] = defaultdict(dict)
alch_recipes['potion of greed']['mana'] = '15'
alch_recipes['potion of greed']['code'] = 'p08'
alch_recipes['potion of greed']['recipe']['ethereal bone'] = '1'
alch_recipes['potion of greed']['recipe']["kloliarway"] = '1'

# p09 - Bottle of Greed - Alchemy lvl 3 - 30💧
# 1 Love Creeper + 1 Spring Bay Leaf + 1 Ethereal Bone + 2 Kloliarway
alch_recipes['bottle of greed'] = defaultdict(dict)
alch_recipes['bottle of greed']['mana'] = '30'
alch_recipes['bottle of greed']['code'] = 'p09'
alch_recipes['bottle of greed']['recipe']['love creeper'] = '1'
alch_recipes['bottle of greed']['recipe']["spring bay leaf"] = '1'
alch_recipes['bottle of greed']['recipe']["ethereal bone"] = '1'
alch_recipes['bottle of greed']['recipe']["kloliarway"] = '2'

# Зелья природы (Nature) - увеличивает уровень скила Harvest для всех классов
# p10 - Vial of Nature - Alchemy lvl 1 - 10💧 - Harvest + 1 уровень
# 4 Powder + 1 Cliff Rue + 1 Ephijora
alch_recipes['vial of nature'] = defaultdict(dict)
alch_recipes['vial of nature']['mana'] = '10'
alch_recipes['vial of nature']['code'] = 'p10'
alch_recipes['vial of nature']['recipe']['powder'] = '4'
alch_recipes['vial of nature']['recipe']["cliff rue"] = '1'
alch_recipes['vial of nature']['recipe']["ephijora"] = '1'

# p11 - Potion of Nature - Alchemy lvl 2 - 15💧- Harvest + 3 уровня
# 7 Powder + 1 Plasma of Abyss + 3 Ephijora +3 Bone Powder
alch_recipes['potion of nature'] = defaultdict(dict)
alch_recipes['potion of nature']['mana'] = '15'
alch_recipes['potion of nature']['code'] = 'p11'
alch_recipes['potion of nature']['recipe']['powder'] = '7'
alch_recipes['potion of nature']['recipe']["plasma of abyss"] = '1'
alch_recipes['potion of nature']['recipe']["ephijora"] = '3'
alch_recipes['potion of nature']['recipe']["bone powder"] = '3'

# p12 - Bottle of Nature
alch_recipes['bottle of nature'] = defaultdict(dict)
alch_recipes['bottle of nature']['mana'] = '30'
alch_recipes['bottle of nature']['code'] = 'p12'
alch_recipes['bottle of nature']['recipe']['purified powder'] = '1'
alch_recipes['bottle of nature']['recipe']['kloliarway'] = '1'
alch_recipes['bottle of nature']['recipe']['plasma of abyss'] = '3'

alch_recipes['vial of mana'] = defaultdict(dict)
alch_recipes['vial of mana']['mana'] = '15'
alch_recipes['vial of mana']['code'] = 'p13'
alch_recipes['vial of mana']['recipe']['powder'] = '3'
alch_recipes['vial of mana']['recipe']['cliff rue'] = '1'
alch_recipes['vial of mana']['recipe']['tecceagrass'] = '2'
alch_recipes['vial of mana']['recipe']['ethereal bone'] = '1'

alch_recipes['potion of mana'] = defaultdict(dict)
alch_recipes['potion of mana']['mana'] = '30'
alch_recipes['potion of mana']['code'] = 'p14'
alch_recipes['potion of mana']['recipe']['powder'] = '3'
alch_recipes['potion of mana']['recipe']['cliff rue'] = '3'
alch_recipes['potion of mana']['recipe']['maccunut'] = '2'
alch_recipes['potion of mana']['recipe']['astrulic'] = '1'
alch_recipes['potion of mana']['recipe']['itacory'] = '2'

alch_recipes['bottle of mana'] = defaultdict(dict)
alch_recipes['bottle of mana']['mana'] = '50'
alch_recipes['bottle of mana']['code'] = 'p15'
alch_recipes['bottle of mana']['recipe']['ephijora'] = '2'
alch_recipes['bottle of mana']['recipe']['tecceagrass'] = '4'
alch_recipes['bottle of mana']['recipe']['plexisop'] = '1'
alch_recipes['bottle of mana']['recipe']['ethereal bone'] = '2'
alch_recipes['bottle of mana']['recipe']['kloliarway'] = '1'

alch_recipes['vial of twilight'] = defaultdict(dict)
alch_recipes['vial of twilight']['mana'] = '15'
alch_recipes['vial of twilight']['code'] = 'p16'
alch_recipes['vial of twilight']['recipe']['silver ore'] = '3'
alch_recipes['vial of twilight']['recipe']['stinky sumac'] = '1'
alch_recipes['vial of twilight']['recipe']['tecceagrass'] = '2'
alch_recipes['vial of twilight']['recipe']['love creeper'] = '1'

alch_recipes['potion of twilight'] = defaultdict(dict)
alch_recipes['potion of twilight']['mana'] = '30'
alch_recipes['potion of twilight']['code'] = 'p17'
alch_recipes['potion of twilight']['recipe']['ilaves'] = '3'
alch_recipes['potion of twilight']['recipe']['yellow seed'] = '2'
alch_recipes['potion of twilight']['recipe']['astrulic'] = '1'
alch_recipes['potion of twilight']['recipe']['kloliarway'] = '1'
alch_recipes['potion of twilight']['recipe']['silver dust'] = '1'

alch_recipes['bottle of twilight'] = defaultdict(dict)
alch_recipes['bottle of twilight']['mana'] = '50'
alch_recipes['bottle of twilight']['code'] = 'p18'
alch_recipes['bottle of twilight']['recipe']['maccunut'] = '3'
alch_recipes['bottle of twilight']['recipe']['stinky sumac'] = '3'
alch_recipes['bottle of twilight']['recipe']['wolf root'] = '1'
alch_recipes['bottle of twilight']['recipe']['mammoth dill'] = '1'
alch_recipes['bottle of twilight']['recipe']['kloliarway'] = '1'
alch_recipes['bottle of twilight']['recipe']['silver dust'] = '3'

alch_recipes['vial of morph'] = defaultdict(dict)
alch_recipes['vial of morph']['mana'] = '15'
alch_recipes['vial of morph']['code'] = 'p19'
alch_recipes['vial of morph']['recipe']['powder'] = '5'
alch_recipes['vial of morph']['recipe']['storm hyssop'] = '1'
alch_recipes['vial of morph']['recipe']['flammia nut'] = '1'
alch_recipes['vial of morph']['recipe']['assassin vine'] = '1'
alch_recipes['vial of morph']['recipe']['itacory'] = '1'

alch_recipes['potion of morph'] = defaultdict(dict)
alch_recipes['potion of morph']['mana'] = '30'
alch_recipes['potion of morph']['code'] = 'p20'
alch_recipes['potion of morph']['recipe']['maccunut'] = '3'
alch_recipes['potion of morph']['recipe']["queen's pepper"] = '1'
alch_recipes['potion of morph']['recipe']['mammoth dill'] = '1'
alch_recipes['potion of morph']['recipe']['itacory'] = '1'
alch_recipes['potion of morph']['recipe']['plasma of abyss'] = '1'
alch_recipes['potion of morph']['recipe']['silver dust'] = '2'

alch_recipes['bottle of morph'] = defaultdict(dict)
alch_recipes['bottle of morph']['mana'] = '50'
alch_recipes['bottle of morph']['code'] = 'p21'
alch_recipes['bottle of morph']['recipe']['ephijora'] = '3'
alch_recipes['bottle of morph']['recipe']["mercy sassafras"] = '2'
alch_recipes['bottle of morph']['recipe']['plexisop'] = '1'
alch_recipes['bottle of morph']['recipe']['flammia nut'] = '1'
alch_recipes['bottle of morph']['recipe']['assassin vine'] = '1'
alch_recipes['bottle of morph']['recipe']['plasma of abyss'] = '1'
alch_recipes['bottle of morph']['recipe']['silver dust'] = '6'
alch_recipes['bottle of morph']['recipe']['ultramarine dust'] = '1'

# print(alch_recipes)
print(alch_recipes.keys())
