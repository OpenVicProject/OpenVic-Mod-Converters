#%%
# YOU NEED TO RUN THE MOD CHECKER FIRST AND FIX ALL THE MISTAKES THAT CAN NOT BE DISABLED IN THE DONT_IGNORE_ISSUE PART OR THIS PROGRAM WILL LIKELY CRASH AS NEARLY ALL CHECKS ARE REMOVED! AND OF COURSE AFTER FIXING THE MISTAKES YOU NEED TO RUN THE MOD CHECKER AGAIN TO MAKE SURE YOU ACTUALLY FIXED ALL! THE "V2 mod standard" FOLDER FROM GITHUB MUST ALSO BE IN THE MOD FOLDER!

from PIL import Image
import math
import os
import random
import re
import shutil
# These mod specific values are the only parts of the script you might need to change, just follow the instructions.

START_DATE = "1444.11.11" # Replace 1444.11.11 with the intended start date in the form years.months.days, unless it would be a date outside the range 1.1.1 to 65535.12.31. Any input that is not valid will be replaced with 1444.11.11. The history will be applied until the start date, including identical dates like 01444.11.11. However the mod itself will start in 1836.1.1 because currently the automatic conversion does not replace the tech, so a 1444.11.11 start would mean a few centuries without any available techs to research.
ENCODING = "windows-1252" # Change this to whatever the encoding of the mod is, most likely it is either "utf-8" or "windows-1252". If it is mixed and you want to be able to automatically convert the mod to an OpenVic mod, you currently would have to pick one and change the files with the other encoding.
OUTPUT_ENCODING = "windows-1252" # Change this to whatever the encoding of the created mod should be, so for Victoria 2 it should be "windows-1252", while for OpenVic it can also be "utf-8" and if the converted mod is only supposed to be played with OpenVic it is definitely recommended to use "utf-8".
LANGUAGES = ["english"]
# While localisation used from the base game would not have to be part of an EU4 mod to function when EU4 runs the mod, like government or continent names, the mod converter will NOT grab it from EU4. For modder convenience i listed some here, but this is not complete. SO DO NOT IGNORE THE MISSING LOCALISATION WARNINGS, THE SCRIPT DOES NOT CHECK THE BASE GAME FILES, IF THE MOD MISSES SOMETHING THE OUTPUT WILL ALSO MISS THIS, IF THE SCRIPT DOES NOT SIMPLY CRASH BEFORE CREATING THE OUTPUT!
EU4_LOCALISATION_DICTIONARY = {
	"republic_name":{"english":"Republic","french":"République","german":"Republik","polish":"Republika","spanish":"República"},
	"monarchy_name":{"english":"Monarchy","french":"Monarchie","german":"Monarchie","polish":"Monarchia","spanish":"Monarquía"},
	"theocracy_name":{"english":"Theocracy","french":"Théocratie","german":"Theokratie","polish":"Teokracja","spanish":"Teocracia"},
	"tribal_name":{"english":"Tribe","french":"Tribus","german":"Stamm","polish":"Plemię","spanish":"Tribal"},
	"native_name":{"english":"Native","french":"Indigènes","german":"Ureinwohner","polish":"Rdzenny","spanish":"Nativo"},
	"europe":{"english":"Europe","french":"Europe","german":"Europa","polish":"Europa","spanish":"Europa"},
	"asia":{"english":"Asia","french":"Asie","german":"Asien","polish":"Azja","spanish":"Asia"},
	"africa":{"english":"Africa","french":"Afrique","german":"Afrika","polish":"Afryka","spanish":"África"},
	"north_america":{"english":"North America","french":"Amérique du Nord","german":"Nordamerika","polish":"Ameryka Północna","spanish":"Norteamérica"},
	"south_america":{"english":"South America","french":"Amérique du Sud","german":"Südamerika","polish":"Ameryka Południowa","spanish":"Sudamérica"},
	"oceania":{"english":"Oceania","french":"Océanie","german":"Ozeanien","polish":"Oceania","spanish":"Oceanía"},
	"new_world":{"english":"The New World","french":"Nouveau Monde","german":"Die Neue Welt","polish":"Nowy Świat","spanish":"El Nuevo Mundo"}
}
#POPS_AND_RATIOS = { # For Elder Scrolls Universalis
#	"artisans":{"standard":500},
#	"clergy":{"standard":50,"theocracy":200},
#	"commoners":{"standard":8600,"native":5000,"tribal":500},
#	"criminals":{"standard":10,},
#	"guild_artisans":{"standard":500},
#	"mages":{"standard":100},
#	"merchants":{"standard":50,"republic":200},
#	"nobles":{"standard":50,"monarchy":200},
#	"slaves":{"standard":0},
#	"tribals":{"standard":0,"native":3000,"tribal":8000},
#	"warriors":{"standard":300}
#} # The size of the pops will be sum of development multiplied with the number behind the pop type. You can change the names and numbers however you want, as well as add or remove pops. The above is currently intended to be used to create Elder Scrolls Universalis pops, once i actually create the pops folders for them and generally changed the game to fit the new pops, while the below creates standard Victoria 2 pops:
POPS_AND_RATIOS = {
	"aristocrats":{"standard":100,"monarchy":150},
	"artisans":{"standard":500},
	"bureaucrats":{"standard":80,"native":30,"tribal":10},
	"capitalists":{"standard":0,"republic":10},
	"clergymen":{"standard":110,"republic":150,"theocracy":160,"native":50,"tribal":50},
	"clerks":{"standard":0},
	"craftsmen":{"standard":0},
	"farmers":{"standard":9000},
	"officers":{"standard":10},
	"slaves":{"standard":0},
	"soldiers":{"standard":200,"native":310,"tribal":330}
}
RIVER_DICTIONARY = {0:0, 1:1, 2:2, 3:6, 4:8, 5:10, 6:12, 7:14, 8:16, 9:18, 10:20, 11:22, 12:22, 13:22, 14:22, 254:254, 255:255} # If the mod checker did not mention anything about river colors not being in the dictionary you don't need to change this, otherwise assign the additional index to 22, which is the thickest possible river in Victoria 2 and still considerably thinner than EU4 rivers at index 11 would be.
ATLAS_PATH = "map\\terrain\\atlas0.dds" # The texture to color the terrain map seems to be always here, but just to be sure i may as well make it easy to change the path.
ATLAS_SIZE = (4,4) # Change this to the number of different squares in the map\terrain\atlas0 file, however (8,8) is the maximum. First number is from left to right, second is up down, although they are most likely the same.
ATLAS_DICTIONARY = {35:{"atlas_index":3,"bmp_index":52}} # The first number is the EU4 terrain index. For example EU4 uses 35 for the coastline, but has only 16 squares, so only "atlas_index" 0 to 15 could have a terrain, which means you either have to reuse another "atlas_index" like the desert which is 3 or add some coastline terrain to "bmp_index" 52 in the texturesheet after creating the output, as Victoria 2 uses this square for the coastline. Mods can use a different "atlas_index" for the coastline like Elder Scrolls Universalis uses 39 instead, so make sure you pick the right one. Similarly EU4 has grassland at index 5, but that square is simply gray, so you either need to add the terrain yourself after creating the output or set this to another value like 5:{"atlas_index":0} as "atlas_index" 0 is also grassland and has the texture. If you know you want to add or change some terrain manually afterwards you can just set the "atlas_index" to 64 and the square will be black (0,0,0), if you add a completely incorrect value the program may crash. Do not add a value for oceans though, they have their default Victoria 2 texture. Only the coastline needs a "bmp_index" and it must be 52, but you can add it for any other terrain as well, if you want them in a particular order, however the number for each MUST BE UNIQUE and from 0 to 63, but again not 52 as that is for the coastline. If you want to see how the atlas squares will look in V2 before deciding, you can simply run these 2 lines in the mod folder:
# from PIL import Image
# Image.open("map\\terrain\\atlas0.dds").convert(mode="RGB").save("texturesheet.tga")
#FORCE_OCEAN = ["impassable_rivers"] # For Elder Scrolls Universalis
FORCE_OCEAN = [] # You can simply leave the brackets empty [], if there are no provinces which are continental in EU4, but you want them to be ocean in Victoria 2. Otherwise just like with the mod checker you have to insert the terrain that is used to identify them. For example Elder Scrolls Universalis has impassable river provinces, which use "impassable_rivers" terrain as identifier and are turned into ocean provinces in Victoria 2/OpenVic. Keep in mind that the terrain already has to be ocean for these provinces and you can use the mod checker to automatically generate both the terrain.bmp and rivers.bmp with correct terrain, although the generated output will be called terrain2.bmp and rivers2.bmp, so you have to at least temporarily rename the terrain file. The river file will actually be generated like this here as well though, so there is no need to rename it.
RGO_DICTIONARY = {"precious_metal":50,"iron":112,"coal":200,"sulphur":35,"timber":281,"tropical_wood":63,"dye":200,"wool":176,"cotton":200,"silk":30,"grain":1000,"fruit":262,"fish":239,"cattle":267,"coffee":63,"tea":400,"tobacco":200,"opium":21} # Don't change these values unless you also change the V2 economy or realised that some values are too high or low and the problem is not just due to randomness.
THE_MOD_CHECKER_DID_MENTION_NOTHING = False # Switch this to True to get the output once running the modchecker shows no more issues. The "V2 mod standard" folder from Github must be in the same folder as well. If you do not want to fix issues that can be disabled by setting the DONT_IGNORE_ISSUE values to False, then do set it to False and make sure you actually fixed all the ones that can not be disabled. Just here to prevent the people who don't follow the instructions to get broken output or see this script crash and then complain about it as all checks for mistakes are removed, except checks for mistakes that can cause an infinite loop. If you have a sufficiently new Python version installed, probably anything after 3.7 will work as well as a recent PILLOW version, you can run this script. That's it.

# formats a text file when given the path.
def format_text_in_path(path):
	with open(path,'r',encoding=ENCODING,errors='replace') as file:
		text = []
		for line in file:
			text.append(line.split('#',maxsplit=1)[0])
		text = " ".join(text)
		text = text.replace("{"," { ").replace("}"," } ").replace("="," = ")
		text = " " + " ".join(text.split()) + " "
	return text

# Makes sure that the start date is valid and removes any unnecessary zeros in front of the numbers.
def verify_date(date):
	if 2 != date.count("."):
		print(f"{date} Try again...")
		return "1444.11.11"
	[years,months,days] = date.split(".")
	years = int(years)
	months = int(months)
	days = int(days)
	if years < 1 or years > 65535:
		print(f"{date} is not a valid date as OpenVic does not support years beyond 1 to 65535 or 1 to 2^16 - 1.")
		return "1444.11.11"
	if months < 1 or months > 12 or days < 1 or days > 31:
		print(f"{date} is not a valid date")
		return "1444.11.11"
	if days == 31:
		if months == 4 or months == 6 or months == 9 or months == 11:
			print(f"{date} is not a valid date")
			return "1444.11.11"
	if months == 2:
		if days == 29:
			print(f"29th February is not a valid date in OpenVic, so {date} will be changed to {years}.{months}.28 instead.")
			return f"{years}.{months}.28"
		elif days == 30 or days == 31:
			print(f"{days}th February? Really?")
			return "1444.11.11"
	return f"{years}.{months}.{days}"

# replace everything with " " between all occurances of a given string ending with a {, including that string, until the brackets close again and return the new string.
def remove_text_between_brackets(text,sub_string):
	while text.__contains__(sub_string):
		[prior_text,leftover] = text.split(sub_string,maxsplit=1)
		counter = 1
		for index in range(len(leftover)):
			if leftover[index] == "{":
				counter += 1
			elif leftover[index] == "}":
				counter -= 1
				if counter == 0:
					leftover = leftover[index + 1:]
					break
		text = prior_text + leftover
	text = " " + text.strip() + " "
	return text

# Will return the string between the first occurance starting substring and the closing bracket. Any additional occurances of the same subtring will be ignored.
def get_text_between_brackets(text,sub_string):
	text = text.split(sub_string,maxsplit=1)[1]
	counter = 1
	for index in range(len(text)):
		if text[index] == "{":
			counter += 1
		elif text[index] == "}":
			counter -= 1
			if counter == 0:
				text = text[:index]
				break
	return text

# creates a set of all cultures and a dictionary {culture_group:{culture:{male_names:"names",female_names:"names",dynasty_names:"names"}}}
def get_cultures():
	culture_dictionary = dict()
	for root, dirs, files in os.walk("common/cultures"):
		for file in files:
			text = format_text_in_path(os.path.join(root, file))
			if text == "  ":
				continue
			text = remove_text_between_brackets(text," country = {")
			text = remove_text_between_brackets(text," province = {")
			counter = 0
			culture_group = ""
			culture = ""
			while text.__contains__(" = {"):
				[prior_text,leftover] = text.split(" = {",maxsplit=1)
				counter = 1 + counter + prior_text.count("{") - prior_text.count("}")
				new_entry = prior_text.rsplit(" ",maxsplit=1)[1]
				if counter == 1:
					culture_group = new_entry
					culture_dictionary[culture_group] = dict()
					culture_dictionary[culture_group]["standard_names"] = dict()
				elif counter == 2:
					if new_entry == "male_names" or new_entry == "female_names" or new_entry == "dynasty_names":
						[name_string,leftover] = leftover.split("}",maxsplit=1)
						counter -= 1
						name_list = []
						name_tuple = ()
						if name_string == " ":
							name_string = ""
						elif name_string.count('"') == 0:
							name_tuple = sorted(tuple(set(name_string.split())),key=str.lower)
						else:
							while name_string.count('"') > 1:
								[first_part,name,second_part] = name_string.split('"',maxsplit=2)
								name_list.append('"' + name.strip() + '"')
								name_string = first_part + " " + second_part
							name_tuple = sorted(tuple(set(name_list + name_string.split())),key=str.lower)
						if name_tuple:
							name_string = ""
							for name in name_tuple:
								name_string += name + " "
						if name_string != "":
							culture_dictionary[culture_group]["standard_names"][new_entry] = name_string.strip()
					else:
						culture = new_entry
						culture_dictionary[culture_group][culture] = dict()
				elif counter == 3:
					[name_string,leftover] = leftover.split("}",maxsplit=1)
					counter -= 1
					name_list = []
					name_tuple = ()
					if name_string == " ":
						name_string = ""
					elif name_string.count('"') == 0:
						name_tuple = sorted(tuple(set(name_string.split())),key=str.lower)
					else:
						while name_string.count('"') > 1:
							[first_part,name,second_part] = name_string.split('"',maxsplit=2)
							name_list.append('"' + name.strip() + '"')
							name_string = first_part + " " + second_part
						name_tuple = sorted(tuple(set(name_list + name_string.split())),key=str.lower)
					if name_tuple:
						name_string = ""
						for name in name_tuple:
							name_string += name + " "
					if name_string != "":
						culture_dictionary[culture_group][culture][new_entry] = name_string.strip()
				text = leftover
	culture_set = set()
	for culture_group in culture_dictionary:
		for culture in culture_dictionary[culture_group]:
			if culture != "standard_names":
				culture_set.add(culture)
	return [culture_dictionary, culture_set]

# Creates a set and a dictionary of the religions from all files in the common/religions folder.
def get_religions():
	religion_dictionary = dict()
	religion_set = set()
	COLOR_STRUCTURE = re.compile(r' color = \{ [0-1][.][0-9]{1,3} [0-1][.][0-9]{1,3} [0-1][.][0-9]{1,3} \}')
	OPTIONAL_COLOR_STRUCTURE = re.compile(r' color = \{ [0-9]{1,3} [0-9]{1,3} [0-9]{1,3} \}')
	ICON_STRUCTURE = re.compile(r' icon = [0-9]{1,3} ')
	for root, dirs, files in os.walk("common/religions"):
		for file in files:
			text = format_text_in_path(os.path.join(root, file))
			if text == "  ":
				continue
			colors = re.findall(COLOR_STRUCTURE,text)
			optional_colors = re.findall(OPTIONAL_COLOR_STRUCTURE,text)
			if optional_colors:
				colors = optional_colors
			icons = re.findall(ICON_STRUCTURE,text)
			counter = 0
			religion_group = religion = ""
			for i in range(len(icons)):
				icon_index = text.find(icons[i])
				color_index = text.find(colors[i])
				mindex = min(icon_index,color_index)
				maxdex = max(icon_index + len(icons[i]), color_index + len(colors[i]))
				for k in range(mindex):
					if text[k] == "{":
						if counter == 0:
							if text[k-3:k] == " = ":
								religion_group = text[:k-3].rsplit(" ",maxsplit=1)[1]
								religion_dictionary[religion_group] = dict()
						elif counter == 1:
							if text[k-3:k] == " = ":
								religion = text[:k-3].rsplit(" ",maxsplit=1)[1]
						counter += 1
					elif text[k] == "}":
						counter -= 1
						if counter == 0:
							religion_group = ""
						elif counter == 1:
							religion = ""
				for k in range(mindex + 7,maxdex):
					if text[k] == "{":
						counter += 1
					elif text[k] == "}":
						counter -= 1
				icon = icons[i].split(" ")[3]
				color = colors[i].split(" ")[4:7]
				if optional_colors:
					for index in range(3):
						color[index] = str(round(int(color[index])/255,3))
				color = "{ " + color[0] + " " + color[1] + " " + color[2] + " }"
				religion_dictionary[religion_group][religion] = dict()
				religion_dictionary[religion_group][religion]["icon"] = icon
				religion_dictionary[religion_group][religion]["color"] = color
				religion_set.add(religion)
				text = text[maxdex:]
	return [religion_dictionary,religion_set]

def get_governments():
	government_set = set()
	for root, dirs, files in os.walk("common/governments"):
		for file in files:
			text = format_text_in_path(os.path.join(root, file))
			if text == "  ":
				continue
			while text.__contains__(" = {"):
				next_government = text.split(" = {",maxsplit=1)[0].rsplit(" ",maxsplit=1)[1]
				text = remove_text_between_brackets(text," " + next_government + " = {")
				if next_government != "pre_dharma_mapping":
					government_set.add(next_government)
	return government_set

def get_tech_groups():
	tech_group_set = set()
	text = format_text_in_path("common/technology.txt")
	counter = 1
	text = text.split(" groups = {",maxsplit=1)[1]
	for i in range(len(text)):
		if text[i] == "{":
			counter += 1
			if counter == 2:
				tech_group_set.add(text[:i].rsplit(" =",maxsplit=1)[0].rsplit(" ",maxsplit=1)[1])
		elif text[i] == "}":
			counter -= 1
			if counter == 0:
				break
	return tech_group_set

def create_definition_csv():
	definition_csv = []
	definitions_dictionary = dict()
	RGB_dictionary = dict()
	with open("map/definition.csv",'r',encoding=ENCODING,errors='replace') as file:
		for line in file:
			if re.fullmatch("[1-9]",line[0]):
				[provinceID,red,green,blue] = line.split(";",maxsplit=4)[0:4]
				definition_csv.append([provinceID,red,green,blue])
				RGB = tuple((int(red),int(green),int(blue)))
				definitions_dictionary[provinceID] = RGB
				RGB_dictionary[RGB] = provinceID
	return [definition_csv,definitions_dictionary,RGB_dictionary]

# gets all the text from ?.?.? = { text } for a specified date, including further occurances of it and returns them, but adds " # " between them or returns "#" if either the date entry is empty or none is found or an error occurs.
def get_date_text(text,date):
	date_text = " "
	next_date = re.search(r'[^-0-9]' + date + " = {",text)
	while "None" != str(next_date):
		counter = 1
		text = text[next_date.end():]
		for i in range(len(text)):
			if text[i] == "{":
				counter += 1
			elif text[i] == "}":
				counter -= 1
				if counter == 0:
					date_text += text[:i] + " # "
					text = text[i + 1:]
					break
		next_date = re.search(r'[^-0-9]' + date + " = {",text)
	date_text = " " + " ".join(date_text.split()) + " "
	if date_text == "  ":
		return "#"
	return date_text

# Removes all valid date entries from a file and replaces dates with " ## " so for example "text ?.?.? = { .{}{.}. } more text" will be turned into "text ## more text" or if an error is found into "#". This should work with any number of valid dates, including duplicates, as long as the brackets are correct, but this also means invalid date entries are added to the base date.
def get_base_date_text(text,sorted_list):
	if not text.__contains__("{"):
		return text
	for date in sorted_list:
		if date == "BASE_DATE" or date == "START_DATE":
			continue
		next_date = re.search(r'[^-0-9]' + date + " = {",text)
		while str(next_date) != "None":
			prior_text = text[:next_date.start() + 1]
			leftover = text[next_date.end():]
			counter = 1
			for i in range(len(leftover)):
				if leftover[i] == "{":
					counter += 1
				elif leftover[i] == "}":
					counter -= 1
					if counter == 0:
						leftover = leftover[i + 1:]
						break
			text = prior_text + " ## " + leftover
			next_date = re.search(r'[^-0-9]' + date + " = {",text)
	text = " " + " ".join(text.split()) + " "
	if text == "  ":
		return "#"
	return text

# Adds all valid dates of the form "years.months.days = {" from the text to the date_list, if they are not yet in it, which includes multiple functionally identical dates like 1.1.1 and 01.01.01 to use them for searching. While the 29th February does not exist in OpenVic, it will still be added to the list. Then the dates get sorted, with the exception of functionally identical dates like 1.1.1 and 01.01.01 which stay in whatever order they happen to be found first.
def get_sorted_dates(text):
	date_list = []
	next_date = DATE_STRUCTURE.search(text)
	while "None" != str(next_date):
		date = next_date.group()[1:].split(" ")[0]
		[years,months,days] = date.split(".")
		text = text[next_date.end():]
		next_date = DATE_STRUCTURE.search(text)
		if int(years) < 1 or int(years) > 65535:
			continue
		if int(months) < 1 or int(months) > 12 or int(days) < 1 or int(days) > 31:
			continue
		if int(days) == 31:
			if int(months) == 4 or int(months) == 6 or int(months) == 9 or int(months) == 11:
				continue
		if int(months) == 2:
			if int(days) == 30 or int(days) == 31:
				continue
		if date not in date_list:
			date_list.append(date)
	date_list.append(START_DATE)
	sorted_list = []
	while len(date_list) > 0:
		prior_date = date_list[0]
		[y,m,d] = prior_date.split(".")
		for entry in date_list:
			[Y,M,D] = entry.split(".")
			if int(y) > int(Y):
				prior_date = entry
				[y,m,d] = prior_date.split(".")
			elif int(y) == int(Y) and int(m) > int(M):
				prior_date = entry
				[y,m,d] = prior_date.split(".")
			elif int(y) == int(Y) and int(m) == int(M) and int(d) > int(D):
				prior_date = entry
				[y,m,d] = prior_date.split(".")
		date_list.remove(prior_date)
		sorted_list.append(prior_date)
	sorted_list.reverse()
	sorted_list[sorted_list.index(START_DATE)] = "START_DATE"
	sorted_list.reverse()
	sorted_list.insert(0,"BASE_DATE")
	return sorted_list

# Checks country files in history/countries, their paths in common/country_tags and the files in common/countries.
def create_country_dictionary():
	tag_dictionary = dict()
	path_dictionary = dict()
	country_dictionary = dict()
	technology_set = set()
	for root, dirs, files in os.walk("history/countries"):
		for file in files:
			tag = file[:3]
			tag_dictionary[tag] = "No path"
			country_dictionary[tag] = dict()
			if tag == "REB" or tag == "NAT" or tag == "PIR":
				continue
			path = os.path.join(root, file)
			text = format_text_in_path(path)
			for character in [" monarch = {"," monarch_consort = {"," monarch_heir = {"," monarch_foreign_heir = {"," queen = {"," heir = {"," define_advisor = {"," leader = {"]:
				text = remove_text_between_brackets(text,character)
			sorted_list = get_sorted_dates(text)
			uniques = ["government","primary_culture","religion","capital","technology_group"]
			accepted_culture_list = []
			for date in sorted_list:
				if date == "BASE_DATE":
					date_text = get_base_date_text(text,sorted_list)
				elif date == "START_DATE":
					if country_dictionary[tag]["primary_culture"] in accepted_culture_list:
						accepted_culture_list.remove(country_dictionary[tag]["primary_culture"])
					if accepted_culture_list:
						country_dictionary[tag]["accepted_cultures"] = accepted_culture_list
					technology_set.add(country_dictionary[tag]["technology_group"])
					break
				else:
					date_text = get_date_text(text,date)
				if date_text == "#":
					continue
				for index in range(len(uniques)):
					if date_text.count(" " + uniques[index] + " = ") == 1:
						country_dictionary[tag][uniques[index]] = date_text.split(" " + uniques[index] + " = ",maxsplit=1)[1].split(" ",maxsplit=1)[0]
				add_culture_text = date_text
				while add_culture_text.__contains__(" add_accepted_culture = "): # TODO make it an if then split the text without the maxsplit = 1
					add_culture_text = add_culture_text.split(" add_accepted_culture = ",maxsplit=1)[1]
					[culture,add_culture_text] = add_culture_text.split(" ",maxsplit=1)
					add_culture_text = " " + add_culture_text
					if culture not in accepted_culture_list:
						accepted_culture_list.append(culture)
				remove_culture_text = date_text
				while remove_culture_text.__contains__(" remove_accepted_culture = "):
					remove_culture_text = remove_culture_text.split(" remove_accepted_culture = ",maxsplit=1)[1]
					[culture,remove_culture_text] = remove_culture_text.split(" ",maxsplit=1)
					remove_culture_text = " " + remove_culture_text
					if culture in accepted_culture_list:
						accepted_culture_list.remove(culture)
	for root, dirs, files in os.walk("common/country_tags"):
		for file in files:
			text = format_text_in_path(os.path.join(root, file))
			if text == "  ":
				continue
			for tag in tag_dictionary.keys():
				if text.__contains__(tag + ' = "countries/'):
					[first,second] = text.split(tag + ' = "countries/',maxsplit=1)
					[country_path,second] = second.split('"',maxsplit=1)
					tag_dictionary[tag] = country_path
					path_dictionary[country_path] = tag
				text = first + second
	COLOR_STRUCTURE = re.compile(r' color = \{ [0-9]{1,3} [0-9]{1,3} [0-9]{1,3} \} ')
	for root, dirs, files in os.walk("common/countries"):
		for file in files:
			text = format_text_in_path(os.path.join(root, file))
			colors = COLOR_STRUCTURE.search(text)
			country_dictionary[path_dictionary[file]]["color"] = colors.group()[8:].strip()
			country_dictionary[path_dictionary[file]]["graphical_culture"] = text.split(" graphical_culture = ",maxsplit=1)[1].split(" ",maxsplit=1)[0]
	tag_set = set(tag_dictionary.keys())
	return [tag_set,tag_dictionary,country_dictionary,technology_set]

def create_terrain_list():
	text = format_text_in_path("map\\terrain.txt")
	terrain = get_text_between_brackets(text,"categories = {")
	terrain_index = get_text_between_brackets(text," terrain = {")
	terrain_index_list = terrain_index.split()
	terrain = " ".join(terrain.split(" pti = { type = pti } ",maxsplit=1))
	terrain_list = terrain.split(" = {")
	province_terrain_dictionary = dict()
	terrain_bmp_index_dictionary = dict()
	terrain_modifier_set = {"supply_limit","movement_cost","combat_width","defence"}
	while len(terrain_list) > 1:
		last_word = terrain_list[0].rsplit(" ",maxsplit=1)[1]
		if last_word == "color":
			province_terrain_dictionary[current_terrain]["color"] = terrain_list[1].split("}",maxsplit=1)[0]
		elif last_word == "terrain_override":
			province_terrain_dictionary[current_terrain]["terrain_override"] = set(terrain_list[1].split("}",maxsplit=1)[0].split())
		else:
			current_terrain = last_word
			province_terrain_dictionary[current_terrain] = dict()
			province_terrain_dictionary[current_terrain]["movement_cost"] = 1
		terrain_list.remove(terrain_list[0])
		terrain_text_list = terrain_list[0].split()
		for i in range(0, len(terrain_text_list) - 3):
			if terrain_text_list[i] in terrain_modifier_set and terrain_text_list[i+1] == "=":
				if terrain_text_list[i] == "movement_cost":
					modifier_value = max(1,float(terrain_text_list[i+2]))
				elif terrain_text_list[i] == "combat_width":
					modifier_value = max(-0.8,float(terrain_text_list[i+2]))
				else:
					modifier_value = float(terrain_text_list[i+2])
				if modifier_value != 0:
					province_terrain_dictionary[current_terrain][terrain_text_list[i]] = str(int(modifier_value)) if modifier_value.is_integer() else str(modifier_value)
	for i in range(0,len(terrain_index_list),12):
		terrain_bmp_index_dictionary[int(terrain_index_list[i + 9])] = terrain_index_list[i + 5]
	return [province_terrain_dictionary,terrain_bmp_index_dictionary]

def create_province_dictionary():
	full_province_dictionary = dict()
	for root, dirs, files in os.walk("history/provinces"):
		for file in files:
			text = format_text_in_path(os.path.join(root, file))
			province_ID = ""
			while re.fullmatch("[0-9]",file[0]):
				province_ID += file[0]
				file = file[1:]
			full_province_dictionary[province_ID] = dict()
			sorted_list = get_sorted_dates(text)
			province_dictionary = get_province_data(text,sorted_list)
			full_province_dictionary[province_ID] = province_dictionary
	force_ocean_set = set()
	for terrain in PROVINCE_TERRAIN_DICTIONARY:
		if "terrain_override" in PROVINCE_TERRAIN_DICTIONARY[terrain]:
			if terrain in FORCE_OCEAN:
				force_ocean_set = force_ocean_set.union(PROVINCE_TERRAIN_DICTIONARY[terrain]["terrain_override"])
			elif terrain not in {"ocean","inland_ocean"}:
				for province in PROVINCE_TERRAIN_DICTIONARY[terrain]["terrain_override"]:
					full_province_dictionary[province]["terrain"] = terrain
	# TODO add terrain specific life rating
	return [full_province_dictionary,force_ocean_set]

# Checks if dates contain obvious mistakes like cultures that don't exist in the culture files.
def get_province_data(text,sorted_list):
	uniques = ["culture","religion","owner","controller","trade_goods"]
	development =[["base_tax",0],["base_production",0],["base_manpower",0]]
	current_cores = []
	province_dictionary = dict()
	province_dictionary["owner"] = "---"
	for date in sorted_list:
		if date == "BASE_DATE":
			date_text = get_base_date_text(text,sorted_list)
		elif date == "START_DATE":
			province_dictionary["add_core"] = current_cores
			population = development[0][1] + development[1][1] + development[2][1]
			if population > 0:
				province_dictionary["population"] = population
			return province_dictionary
		else:
			date_text = get_date_text(text,date)
		if date_text == "#":
			continue
		for index in range(len(uniques)):
			if date_text.count(" " + uniques[index] + " = ") == 1:
				province_dictionary[uniques[index]] = date_text.split(" " + uniques[index] + " = ",maxsplit=1)[1].split(" ",maxsplit=1)[0]
		for index in range(3):
			if date_text.count(" " + development[index][0] + " = ") == 1:
				development[index][1] = int(date_text.split(" " + development[index][0] + " = ",maxsplit=1)[1].split(" ",maxsplit=1)[0])
		core_text = date_text
		while core_text.__contains__(" add_core = "):
			core_text = core_text.split(" add_core = ",maxsplit=1)[1]
			tag = str(core_text)[:3]
			if tag not in current_cores:
				current_cores.append(tag)
		remove_core_text = date_text
		while remove_core_text.__contains__(" remove_core = "):
			remove_core_text = remove_core_text.split(" remove_core = ",maxsplit=1)[1]
			tag = str(remove_core_text)[:3]
			if tag in current_cores:
				current_cores.remove(tag)
	return dict() # This case should never happen, but just to be sure.

def create_continent_list():
	text = format_text_in_path("map/continent.txt")
	continent_list = []
	while text.__contains__("= {"):
		[continent_name,text] = text.split("= {",maxsplit=1)
		[provinces,text] = text.split("}",maxsplit=1)
		if provinces == " ":
			continue
		if continent_name.strip() == "island_check_provinces":
			continue
		provinces = set(provinces.split()).difference(FORCE_OCEAN_SET) # TODO sort them
		continent_list.append([continent_name.strip(),provinces])
	if len(continent_list) > 6:
		print("OpenVic only supports 6 continents in the UI, so while it will work when there are more, there wont be any functional buttons for them in some windows. Until support for this gets added, you will have to combine continents. Of course you can just generate the output and merge the continents there instead or ignore this problem.")
	text = format_text_in_path("map/default.map")
	max_provinces = text.split(" max_provinces = ",maxsplit=1)[1].split(" ",maxsplit=1)[0] # It seems any large enough number works
	ocean_set = set(text.split("sea_starts = {",maxsplit=1)[1].split("}",maxsplit=1)[0].split())
	continent_list.append(["ocean",ocean_set])
	lake_set = set(text.split("lakes = {",maxsplit=1)[1].split("}",maxsplit=1)[0].split())
	water_province_set = ocean_set.union(lake_set,FORCE_OCEAN_SET)
	continent_list.append(["lakes",lake_set.union(FORCE_OCEAN_SET - ocean_set)])
	return [continent_list,ocean_set,lake_set,water_province_set,max_provinces]

def create_climate_list():
	text = format_text_in_path("map/climate.txt")
	climate_list = []
	impassable_set = set()
	while text.__contains__(" = {"):
		[climate_name,text] = text.split(" = {",maxsplit=1)
		[provinces,text] = text.split("}",maxsplit=1)
		if provinces == " ":
			continue
		climate_name = climate_name.rsplit(" ",maxsplit=1)[1]
		provinces = set(provinces.split())
		climate_list.append([climate_name,provinces])
		if climate_name == "impassable":
			impassable_set = provinces
	return [climate_list,impassable_set]

def create_state_list():
	state_list = []
	state_set = set()
	text = format_text_in_path("map/area.txt")
	text_list = text.split(" = {")
	area_name = text_list[0].strip()
	text_list.remove(text_list[0])
	for entry in text_list:
		state_provinces = []
		for province in set(entry.split("}",maxsplit=1)[0].split()):
			if province not in WATER_PROVINCE_SET:
				state_provinces.append(province)
		if state_provinces:
			state_list.append((area_name,state_provinces))
			state_set.add(area_name)
		area_name = entry.split("}",maxsplit=1)[1].strip()
	return [state_list,state_set]

def create_positions_list():
	OCEAN_RGB_SET = set()
	for provinceID in OCEAN_SET:
		OCEAN_RGB_SET.add(DEFINITIONS_DICTIONARY[provinceID])
	for color in OCEAN_RGB_SET:
		ocean = color
		break
	UNIMPORTANT_RGB_SET = set()
	for provinceID in WATER_PROVINCE_SET - OCEAN_SET:
		UNIMPORTANT_RGB_SET.add(DEFINITIONS_DICTIONARY[provinceID])
	for color in UNIMPORTANT_RGB_SET:
		unimportant = color
		break
	for provinceID in IMPASSABLE_SET:
		UNIMPORTANT_RGB_SET.add(DEFINITIONS_DICTIONARY[provinceID])
	positions = format_text_in_path("map/positions.txt")
	image = Image.open("map/provinces.bmp").copy()
	w,h = image.size
	image_load = image.load()
	for x in range(w):
		for y in range(h):
			if image_load[x,y] in OCEAN_RGB_SET:
				image_load[x,y] = ocean
			elif image_load[x,y] in UNIMPORTANT_RGB_SET:
				image_load[x,y] = unimportant
	OCEAN_OR_UNIMPORTANT = {ocean,unimportant}
	if image_load[0,0] in OCEAN_OR_UNIMPORTANT:
		last_was_continental_and_unimportant = False
	elif ocean not in {image_load[0,1],image_load[1,0],image_load[1,1]}:
		image_load[0,0] = unimportant
		last_was_continental_and_unimportant = True
	else:
		last_was_continental_and_unimportant = False
	for y in range(1,h-1):
		if image_load[0,y] in OCEAN_OR_UNIMPORTANT:
			last_was_continental_and_unimportant = False
		elif last_was_continental_and_unimportant:
			if ocean not in {image_load[0,y+1],image_load[1,y+1]}:
				image_load[0,y] = unimportant
			else:
				last_was_continental_and_unimportant = False
		elif ocean not in {image_load[0,y-1],image_load[0,y+1],image_load[1,y-1],image_load[1,y],image_load[1,y+1]}:
			image_load[0,y] = unimportant
			last_was_continental_and_unimportant = True
	if image_load[0,h-1] in OCEAN_OR_UNIMPORTANT:
		pass
	elif last_was_continental_and_unimportant:
		image_load[0,h-1] = unimportant
	elif ocean not in {image_load[0,h-2],image_load[1,h-2],image_load[1,h-1]}:
		image_load[0,h-1] = unimportant
	for x in range(1,w-1):
		if image_load[x,0] in OCEAN_OR_UNIMPORTANT:
			last_was_continental_and_unimportant = False
		elif ocean not in {image_load[x-1,0],image_load[x-1,1],image_load[x,1],image_load[x+1,0],image_load[x+1,1]}:
			image_load[x,0] = unimportant
			last_was_continental_and_unimportant = True
		else:
			last_was_continental_and_unimportant = False
		for y in range(1,h-1):
			if image_load[x,y] in OCEAN_OR_UNIMPORTANT:
				last_was_continental_and_unimportant = False
			elif last_was_continental_and_unimportant:
				if ocean not in {image_load[x-1,y+1],image_load[x,y+1],image_load[x+1,y+1]}:
					image_load[x,y] = unimportant
				else:
					last_was_continental_and_unimportant = False
			elif ocean not in {image_load[x-1,y-1],image_load[x-1,y],image_load[x-1,y+1],image_load[x,y-1],image_load[x,y+1],image_load[x+1,y-1],image_load[x+1,y],image_load[x+1,y+1]}:
				image_load[x,y] = unimportant
				last_was_continental_and_unimportant = True
		if image_load[x,h-1] in OCEAN_OR_UNIMPORTANT:
			pass
		elif last_was_continental_and_unimportant:
			image_load[x,h-1] = unimportant
		elif ocean not in {image_load[x-1,h-2],image_load[x-1,h-1],image_load[x,h-2],image_load[x+1,h-2],image_load[x+1,h-1]}:
			image_load[x,h-1] = unimportant
	if image_load[w-1,0] in OCEAN_OR_UNIMPORTANT:
		last_was_continental_and_unimportant = False
	elif ocean not in {image_load[w-2,0],image_load[w-2,1],image_load[w-1,1]}:
		image_load[w-1,0] = unimportant
		last_was_continental_and_unimportant = True
	else:
		last_was_continental_and_unimportant = False
	for y in range(1,h-1):
		if image_load[w-1,y] in OCEAN_OR_UNIMPORTANT:
			last_was_continental_and_unimportant = False
		elif last_was_continental_and_unimportant:
			if ocean not in {image_load[w-2,y+1],image_load[w-1,y+1]}:
				image_load[w-1,y] = unimportant
			else:
				last_was_continental_and_unimportant = False
		elif ocean not in {image_load[w-2,y-1],image_load[w-2,y],image_load[w-2,y+1],image_load[w-1,y-1],image_load[w-1,y+1]}:
			image_load[w-1,y] = unimportant
			last_was_continental_and_unimportant = True
	if image_load[w-1,h-1] in OCEAN_OR_UNIMPORTANT:
		pass
	elif last_was_continental_and_unimportant:
		image_load[w-1,h-1] = unimportant
	elif ocean not in {image_load[w-2,h-2],image_load[w-2,h-1],image_load[w-1,h-2]}:
		image_load[w-1,h-1] = unimportant
	coastal_pixel_set = set(color for count, color in image.getcolors(65536)) - {ocean} - {unimportant}
	coastal_province_set = set()
	for color in coastal_pixel_set:
		coastal_province_set.add(RGB_DICTIONARY[color])
	positions = format_text_in_path("map/positions.txt")
	port_positions = dict()
	search_coast = [(1,0),(-1,0),(0,1),(0,-1),(1,1),(-1,1),(1,-1),(-1,-1),(2,0),(-2,0),(0,2),(0,-2),(2,1),(-2,1),(2,-1),(-2,-1),(1,2),(-1,2),(1,-2),(-1,-2),(2,2),(-2,2),(2,-2),(-2,-2)]
	search_ocean = [(-1,0),(-1,1),(0,1),(1,1),(1,0),(1,-1),(0,-1),(-1,-1)]
	while positions.__contains__("position = { "):
		[provinceID,positions] = positions.split("position = { ",maxsplit=1)
		counter = 1
		for index in range(len(provinceID) - 1,4,-1):
			if provinceID[index] == "}":
				counter += 1
			elif provinceID[index] == "{":
				counter -= 1
				if counter == 0:
					provinceID = provinceID[:index-3].rsplit(" ",maxsplit=1)[1]
					break
		if provinceID not in coastal_province_set:
			continue
		[port_x,port_y,positions] = positions.split(" ",maxsplit=8)[6:]
		port_x = int(float(port_x))
		port_y = int(h-1 - float(port_y))
		port_positions[provinceID] = dict()
		if image_load[port_x,port_y] == ocean:
			for dx,dy in search_coast:
				if 0 <= port_x + dx < w and 0 <= port_y + dy < h:
					if image_load[port_x + dx,port_y + dy] == DEFINITIONS_DICTIONARY[provinceID]:
						port_x = port_x + dx
						port_y = port_y + dy
						break
		for dx,dy in search_ocean:
			if 0 <= port_x + dx < w and 0 <= port_y + dy < h:
				if image_load[port_x + dx,port_y + dy] != ocean:
					new_rotation = search_ocean[1 + search_ocean.index((dx,dy)):] + search_ocean[:1 + search_ocean.index((dx,dy))] # start with the first one after a not ocean pixel to end on a not ocean pixel
					break
			else:
				new_rotation = search_ocean[1 + search_ocean.index((dx,dy)):] + search_ocean[:1 + search_ocean.index((dx,dy))]
				break
		else:
			port_positions[provinceID]["position"] = [str(port_x - 1),str(h-1 - port_y)]
			continue
		coastline = []
		longest_coastline = []
		for dx,dy in new_rotation:
			if 0 <= port_x + dx < w and 0 <= port_y + dy < h and image_load[port_x + dx,port_y + dy] == ocean:
				coastline.append((dx,dy))
				continue
			elif len(coastline) > len(longest_coastline):
				longest_coastline = coastline
			coastline = []
		else:
			if len(longest_coastline) % 2 == 1:
				dx,dy = longest_coastline[len(longest_coastline) // 2]
			else:
				dx,dy = longest_coastline[len(longest_coastline) // 2]
				dx1,dy1 = longest_coastline[len(longest_coastline) // 2 - 1]
				if dx != dx1:
					dx = (dx + dx1) / 2
				else:
					dy = (dy + dy1) / 2
			port_positions[provinceID]["position"] = [str(port_x + dx),str(h-1 - (port_y + dy))]
			rotation = round(((math.atan2(dx,-dy) + 2.5 * math.pi) % (2 * math.pi)),6)
			if rotation != 0:
				port_positions[provinceID]["rotation"] = str(rotation)
	return port_positions

def create_localisation_text():
	TAG_ADJ_SET = set()
	PROV_SET = set()
	localisation_dictionary = dict()
	for tag in TAG_SET:
		if tag not in {"REB","NAT","PIR"}:
			localisation_dictionary[tag] = dict()
			TAG_ADJ_SET.add(tag + "_ADJ")
			localisation_dictionary[tag + "_ADJ"] = dict()
	for state in STATE_SET:
		localisation_dictionary[state] = dict()
	for prov in PROVINCE_SET:
		PROV_SET.add("PROV" + str(prov))
		localisation_dictionary["PROV" + str(prov)] = dict()
	for culture in CULTURE_SET:
		localisation_dictionary[culture] = dict()
	for religion in RELIGION_SET:
		localisation_dictionary[religion] = dict()
	for tech_group in TECH_GROUP_SET:
		localisation_dictionary[tech_group] = dict()
	for terrain in set(PROVINCE_TERRAIN_DICTIONARY.keys()) - {"ocean","inland_ocean"}:
		localisation_dictionary[terrain] = dict()
		localisation_dictionary[terrain + "_desc"] = dict()
	for government in GOVERNMENT_SET:
		if government + "_name" in EU4_LOCALISATION_DICTIONARY:
			localisation_dictionary[government + "_name"] = EU4_LOCALISATION_DICTIONARY[government + "_name"]
		else:
			localisation_dictionary[government + "_name"] = dict()
	for index in range(min(6,len(CONTINENT_LIST) - 2)):
		if CONTINENT_LIST[index][0] in EU4_LOCALISATION_DICTIONARY:
			localisation_dictionary[CONTINENT_LIST[index][0]] = EU4_LOCALISATION_DICTIONARY[CONTINENT_LIST[index][0]]
		else:
			localisation_dictionary[CONTINENT_LIST[index][0]] = dict()
	for language in LANGUAGES:
		l_language_yml = "_l_" + language + ".yml"
		for root, dirs, files in os.walk("localisation"):
			for file in files:
				if file.__contains__(l_language_yml):
					with open(os.path.join(root, file),'r',encoding="utf-8-sig",errors='replace') as loc:
						for line in loc:
							if line.__contains__(':'):
								[key,value] = line.split(':',maxsplit=1)
								key = key.strip()
								if key not in localisation_dictionary:
									continue
								value = value[value.find('"') + 1:value.rfind('"')].replace('\\"','"')
								localisation_dictionary[key][language] = value
	PROV_TUPLE = sorted(tuple(PROV_SET),key=str)
	return localisation_dictionary,PROV_TUPLE

def create_river_bmp():
	province_bmp = Image.open("map/provinces.bmp").transpose(Image.FLIP_TOP_BOTTOM)
	w,h = province_bmp.size
	province_bmp_load = province_bmp.load()
	EU4_river = Image.open("map/rivers.bmp").transpose(Image.FLIP_TOP_BOTTOM)
	load_EU4_river = EU4_river.load()
	V2_river = Image.new(mode="P", size=(w,h), color=(0,0,0))
	load_V2_river = V2_river.load()
	river_palette = [0, 255, 0, 255, 0, 0, 2,2,2, 3,3,3, 0, 250, 255, 5,5,5, 0, 200, 255, 7,7,7, 0, 150, 255, 9,9,9, 0, 100, 255, 11,11,11, 0, 50, 255, 13,13,13, 0, 0, 255, 15,15,15, 0, 0, 200, 17,17,17, 0, 0, 150, 19,19,19, 0, 0, 100, 21,21,21, 0, 0, 50]
	river_palette.extend(693 * [0])
	river_palette += [125,125,125,255,255,255]
	V2_river.putpalette(river_palette)
	for x in range(w):
		for y in range(h):
			if load_EU4_river[x,y] < 254:
				load_V2_river[x,y] = RIVER_DICTIONARY[load_EU4_river[x,y]]
			elif RGB_DICTIONARY[province_bmp_load[x,y]] in WATER_PROVINCE_SET:
				load_V2_river[x,y] = 254
			else:
				load_V2_river[x,y] = 255
	for x in range(w):
		for y in range(h):
			if load_EU4_river[x,y] == 0:
				current_river_pixel = (x,y)
				former_river_pixel = (x,y)
				check_for_more = True
				tributary_rivers = []
				while check_for_more:
					a,b = current_river_pixel
					for dx , dy in [(0,-1),(0,1),(-1,0),(1,0)]:
						nx , ny = a + dx , b + dy
						if 0 <= nx < w and 0 <= ny < h and former_river_pixel != (nx,ny):
							if 2 < load_V2_river[nx,ny] < 254:
								if RGB_DICTIONARY[province_bmp_load[a,b]] not in WATER_PROVINCE_SET: # land
									current_river_pixel = (nx,ny)
									if RGB_DICTIONARY[province_bmp_load[nx,ny]] in WATER_PROVINCE_SET:
										if load_V2_river[a,b] == 0:
											load_V2_river[a,b] = 255
											load_V2_river[nx,ny] = 254
									if RGB_DICTIONARY[province_bmp_load[former_river_pixel]] in WATER_PROVINCE_SET:
										if RGB_DICTIONARY[province_bmp_load[nx,ny]] in WATER_PROVINCE_SET:
											load_V2_river[former_river_pixel] = 254
											load_V2_river[a,b] = 255
											load_V2_river[nx,ny] = 254
								else: # water
									if load_V2_river[former_river_pixel] == 0:
										if RGB_DICTIONARY[province_bmp_load[former_river_pixel]] in WATER_PROVINCE_SET:
											load_V2_river[former_river_pixel] = 254
										else:
											load_V2_river[former_river_pixel] = 255
									else:
										load_V2_river[a,b] = 254
									if RGB_DICTIONARY[province_bmp_load[nx,ny]] in WATER_PROVINCE_SET: # both water
										if load_V2_river[a,b] == 0:
											load_V2_river[a,b] = 254
										current_river_pixel = (nx,ny)
									else:
										current_river_pixel = (nx,ny)
										if load_V2_river[former_river_pixel] < 254:
											load_V2_river[nx,ny] = 0
										else:
											load_V2_river[a,b] = 0 # In EU4 rivers can go through lakes/oceans, but in V2 they can not, so creating multiple rivers is necessary.
							elif 0 < load_V2_river[nx,ny] < 3:
								tributary_rivers.append([(nx,ny),(a,b)])
					former_river_pixel = (a,b)
					if former_river_pixel == current_river_pixel:
						if RGB_DICTIONARY[province_bmp_load[a,b]] in WATER_PROVINCE_SET:
							for dx , dy in [(0,-1),(0,1),(-1,0),(1,0)]:
								nx , ny = a + dx , b + dy
								if 0 <= nx < w and 0 <= ny < h:
									if load_V2_river[nx,ny] < 254:
										break
							else:
								load_V2_river[a,b] = 254
						if load_V2_river[a,b] == 0:
							if RGB_DICTIONARY[province_bmp_load[a,b]] in WATER_PROVINCE_SET:
								load_V2_river[a,b] = 254
							else:
								load_V2_river[a,b] = 255
					if former_river_pixel != current_river_pixel:
						pass
					elif tributary_rivers:
						current_river_pixel = tributary_rivers[0][0]
						former_river_pixel = tributary_rivers[0][1]
						started_from_index = load_V2_river[current_river_pixel]
						if RGB_DICTIONARY[province_bmp_load[current_river_pixel]] in WATER_PROVINCE_SET:
							load_V2_river[current_river_pixel] = 254
						else:
							load_V2_river[current_river_pixel] = 255
						tributary_rivers.remove(tributary_rivers[0])
						if 1 == started_from_index:
							search_for_valid_source = True
							while search_for_valid_source:
								a,b = current_river_pixel
								for dx , dy in [(0,-1),(0,1),(-1,0),(1,0)]:
									nx , ny = a + dx , b + dy
									if 0 <= nx < w and 0 <= ny < h and former_river_pixel != (nx,ny):
										if 2 < load_V2_river[nx,ny] < 254:
											current_river_pixel = (nx,ny)
											break
								if current_river_pixel == (a,b):
									load_V2_river[a,b] = 0
									search_for_valid_source = False
								former_river_pixel = (a,b)
						elif 2 == started_from_index:
							a,b = current_river_pixel
							for dx , dy in [(0,-1),(0,1),(-1,0),(1,0)]:
								nx , ny = a + dx , b + dy
								if 0 <= nx < w and 0 <= ny < h and former_river_pixel != (nx,ny):
									if 2 < load_V2_river[nx,ny] < 254:
										load_V2_river[nx,ny] = 0
										current_river_pixel = (nx,ny)
								if 0 <= nx < w and 0 <= ny < h:
									if 0 < load_V2_river[nx,ny] < 3:
										tributary_rivers.append([(nx,ny),(a,b)])
							former_river_pixel = current_river_pixel
					elif former_river_pixel == current_river_pixel:
						check_for_more = False
	for x in range(w):
		for y in range(h):
			if load_EU4_river[x,y] == 1:
				a,b = x,y
				river_counter = 0
				nearby_river_color = 0
				for dx , dy in [(0,-1),(0,1),(-1,0),(1,0)]:
					nx , ny = a + dx , b + dy
					if 0 <= nx < w and 0 <= ny < h:
						if load_V2_river[nx,ny] < 3:
							break
						if 2 < load_V2_river[nx,ny] < 254:
							river_counter += 1
							nearby_river_color = load_V2_river[nx,ny]
				else:
					if RGB_DICTIONARY[province_bmp_load[a,b]] not in WATER_PROVINCE_SET: # land
						if river_counter == 2:
							load_V2_river[a,b] = 1
						elif river_counter == 1:
							load_V2_river[a,b] = nearby_river_color
	return V2_river

	# The 0 in front of the normal localisation file name is to make sure that this localisation gets applied, rather than base V2 localisation.
def create_localisation_file(localisation_iterable,extension_list,file_name):
	output_path = os.getcwd() + "\\OpenVic\\localisation\\0 " + file_name + ".csv"
	os.makedirs(os.path.dirname(output_path), exist_ok = True)
	with open(output_path,"a",encoding=OUTPUT_ENCODING,newline='\n') as file:
		for localisation in localisation_iterable:
			for extension in extension_list:
				file.write(localisation + extension + ";")
				for language in ["english","french","german","polish","spanish"]:
					if language in LANGUAGES:
						file.write(LOCALISATION_DICTIONARY[localisation + extension][language] + ";")
					else:
						file.write(";")
				for language in set(LANGUAGES) - {"english","french","german","polish","spanish"}:
					file.write(LOCALISATION_DICTIONARY[localisation + extension][language] + ";")
				file.write("\n")
	return

if THE_MOD_CHECKER_DID_MENTION_NOTHING:
	START_DATE = verify_date(START_DATE)
	[CULTURE_DICTIONARY,CULTURE_SET] = get_cultures()
	[RELIGION_DICTIONARY,RELIGION_SET] = get_religions()
	GOVERNMENT_SET = get_governments()
	TECH_GROUP_SET = get_tech_groups()
	[DEFINITION_CSV,DEFINITIONS_DICTIONARY,RGB_DICTIONARY] = create_definition_csv()
	DATE_STRUCTURE = re.compile(r'[^-0-9]-?[0-9]{1,5}[.][0-9]{1,2}[.][0-9]{1,2} = {')
	[TAG_SET,TAG_DICTIONARY,COUNTRY_DICTIONARY,TECHNOLOGY_SET] = create_country_dictionary()
	[PROVINCE_TERRAIN_DICTIONARY,TERRAIN_BMP_INDEX_DICTIONARY] = create_terrain_list()
	[PROVINCE_DICTIONARY,FORCE_OCEAN_SET] = create_province_dictionary()
	[CONTINENT_LIST,OCEAN_SET,LAKE_SET,WATER_PROVINCE_SET,MAX_PROVINCES] = create_continent_list()
	for index in range(len(CONTINENT_LIST)):
		for province in CONTINENT_LIST[index][1]:
			if province not in PROVINCE_DICTIONARY:
				PROVINCE_DICTIONARY[province] = dict()
			PROVINCE_DICTIONARY[province]["continent"] = CONTINENT_LIST[index][0]
	[CLIMATE_LIST,IMPASSABLE_SET] = create_climate_list()
	PORT_POSITIONS = create_positions_list()
	[STATE_LIST,STATE_SET] = create_state_list()
	#V2_river_bmp = create_river_bmp()
	#V2_river_bmp.save("rivers.bmp")
	PROVINCE_SET = set(PROVINCE_DICTIONARY.keys())
	LOCALISATION_DICTIONARY,PROV_TUPLE = create_localisation_text()
	STATE_TUPLE = sorted(tuple(STATE_SET),key=str)
	# TODO create starting armies from soldier pops
	shutil.copytree("V2 mod standard","OpenVic")
	for tag in COUNTRY_DICTIONARY:
		if tag == "NAT" or tag == "PIR":
			continue
		output_path = os.getcwd() + "\\OpenVic\\common\\countries\\" + TAG_DICTIONARY[tag]
		os.makedirs(os.path.dirname(output_path), exist_ok = True)
		with open(output_path,"a",encoding=OUTPUT_ENCODING,newline='\n') as newfile:
			newfile.write("graphical_culture = EuropeanGC\ncolor = " + COUNTRY_DICTIONARY[tag]["color"] + "\n")
			if tag == "REB":
				continue
			newfile.write('party = {\n	name = "openvic_generic_fascist"\n	start_date = 1905.1.1\n	end_date = 9999.1.1\n\n	ideology = fascist\n\n	trade_policy = protectionism\n	economic_policy = state_capitalism\n	religious_policy = moralism\n	citizenship_policy = residency\n	war_policy = jingoism\n}\n')
			newfile.write('party = {\n	name = "openvic_generic_reactionary"\n	start_date = 1836.1.1\n	end_date = 9999.1.1\n\n	ideology = reactionary\n\n	trade_policy = protectionism\n	economic_policy = state_capitalism\n	religious_policy = moralism\n	citizenship_policy = residency\n	war_policy = jingoism\n}\n')
			newfile.write('party = {\n	name = "openvic_generic_conservative"\n	start_date = 1836.1.1\n	end_date = 9999.1.1\n\n	ideology = conservative\n\n	trade_policy = protectionism\n	economic_policy = interventionism\n	religious_policy = moralism\n	citizenship_policy = residency\n	war_policy = pro_military\n}\n')
			newfile.write('party = {\n	name = "openvic_generic_socialist"\n	start_date = 1848.1.1\n	end_date = 9999.1.1\n\n	ideology = socialist\n\n	trade_policy = free_trade\n	economic_policy = planned_economy\n	religious_policy = secularized\n	citizenship_policy = full_citizenship\n	war_policy = anti_military\n}\n')
			newfile.write('party = {\n	name = "openvic_generic_communist"\n	start_date = 1848.1.1\n	end_date = 9999.1.1\n\n	ideology = communist\n\n	trade_policy = protectionism\n	economic_policy = planned_economy\n	religious_policy = pro_atheism\n	citizenship_policy = full_citizenship\n	war_policy = pro_military\n}\n')
			newfile.write('party = {\n	name = "openvic_generic_liberal"\n	start_date = 1836.1.1\n	end_date = 9999.1.1\n\n	ideology = liberal\n\n	trade_policy = free_trade\n	economic_policy = laissez_faire\n	religious_policy = pluralism\n	citizenship_policy = full_citizenship\n	war_policy = pro_military\n}\n')
			newfile.write('party = {\n	name = "openvic_generic_anarcho_liberal"\n	start_date = 1836.1.1\n	end_date = 9999.1.1\n\n	ideology = anarcho_liberal\n\n	trade_policy = free_trade\n	economic_policy = laissez_faire\n	religious_policy = secularized\n	citizenship_policy = full_citizenship\n	war_policy = pro_military\n}\n')
			newfile.write("unit_names = { }\n")
	w,h = Image.open("map/terrain.bmp").size
	output_path = os.getcwd() + "\\OpenVic\\common\\bookmarks.txt"
	os.makedirs(os.path.dirname(output_path), exist_ok = True)
	with open(output_path,"a",encoding=OUTPUT_ENCODING,newline='\n') as newfile:
		newfile.write('bookmark = {\n	name = "GC_NAME"\n	desc = "GC_DESC"\n	date = 1836.1.1\n	cameraX = ' + str(w//2) + '\n	cameraY = ' + str(h//2) + '\n}\n') # TODO eventually add the intended start date
	output_path = os.getcwd() + "\\OpenVic\\common\\countries.txt"
	os.makedirs(os.path.dirname(output_path), exist_ok = True)
	with open(output_path,"a",encoding=OUTPUT_ENCODING,newline='\n') as newfile:
		newfile.write('REB = "countries/' + TAG_DICTIONARY["REB"] + '"\n')
		for tag in COUNTRY_DICTIONARY:
			if tag == "REB" or tag == "NAT" or tag == "PIR":
				continue
			newfile.write(tag + ' = "countries/' + TAG_DICTIONARY[tag] + '"\n')
	output_path = os.getcwd() + "\\OpenVic\\common\\country_colors.txt"
	os.makedirs(os.path.dirname(output_path), exist_ok = True)
	with open(output_path,"a",encoding=OUTPUT_ENCODING,newline='\n') as newfile:
		pass
	output_path = os.getcwd() + "\\OpenVic\\common\\cultures.txt"
	os.makedirs(os.path.dirname(output_path), exist_ok = True)
	with open(output_path,"a",encoding=OUTPUT_ENCODING,newline='\n') as newfile:
		for culture_group in CULTURE_DICTIONARY:
			newfile.write(culture_group + " = {\n	leader = european\n	unit = EuropeanGC\n")
			for culture in CULTURE_DICTIONARY[culture_group]:
				if culture == "standard_names":
					continue
				newfile.write("	" + culture + " = {\n		color = { " + str(random.randint(0,255)) + " " + str(random.randint(0,255)) + " " + str(random.randint(0,255)) + " }\n")
				if "male_names" in CULTURE_DICTIONARY[culture_group][culture]:
					name_string = CULTURE_DICTIONARY[culture_group][culture]["male_names"]
				else:
					name_string = CULTURE_DICTIONARY[culture_group]["standard_names"]["male_names"]
				newfile.write("		first_names = {\n			" + name_string + "\n		}\n")
				if "dynasty_names" in CULTURE_DICTIONARY[culture_group][culture]:
					name_string = CULTURE_DICTIONARY[culture_group][culture]["dynasty_names"]
				else:
					name_string = CULTURE_DICTIONARY[culture_group]["standard_names"]["dynasty_names"]
				newfile.write("		last_names = {\n			" + name_string + "\n		}\n")
				newfile.write("	}\n")
			newfile.write("}\n")
	text = []
	with open("OpenVic/common/defines.lua",'r') as file:
		for line in file:
			if line.startswith("#"):
				text.append("start_date = '1836.1.1',\n") # TODO eventually add the start date, but without tech changes this is a bad idea.
			else:
				text.append(line)
	with open("OpenVic/common/defines.lua",'w') as file:
		for line in text:
			file.writelines(line)
	output_path = os.getcwd() + "\\OpenVic\\common\\governments.txt"
	os.makedirs(os.path.dirname(output_path), exist_ok = True)
	with open(output_path,"a",encoding=OUTPUT_ENCODING,newline='\n') as newfile:
		for government in GOVERNMENT_SET:
			newfile.write(government + " = {\n	fascist = yes\n	reactionary = yes\n	conservative = yes\n	socialist = yes\n	communist = yes\n	liberal = yes\n	anarcho_liberal = yes\n\n	election = no\n	appoint_ruling_party = yes\n}\n")
		newfile.write("proletarian_dictatorship = {\n	communist = yes\n\n	election = no\n	appoint_ruling_party = yes\n}\n")
		newfile.write("presidential_dictatorship = {\n	reactionary = yes\n\n	election = no\n	appoint_ruling_party = yes\n}\n")
		newfile.write("bourgeois_dictatorship = {\n	anarcho_liberal = yes\n\n	election = no\n	appoint_ruling_party = yes\n}\n")
		newfile.write("fascist_dictatorship = {\n	fascist = yes\n\n	election = no\n	appoint_ruling_party = yes\n}\n")
		newfile.write("absolute_monarchy = {\n	reactionary = yes\n	conservative = yes\n	liberal = yes\n\n	election = no\n	appoint_ruling_party = yes\n}\n")
		newfile.write("prussian_constitutionalism = {\n	reactionary = yes\n	conservative = yes\n	socialist = yes\n	liberal = yes\n\n	election = yes\n	duration = 48\n	appoint_ruling_party = yes\n}\n")
		newfile.write("hms_government = {\n	fascist = yes\n	reactionary = yes\n	conservative = yes\n	socialist = yes\n	communist = yes\n	liberal = yes\n	anarcho_liberal = yes\n\n	election = yes\n	duration = 48\n	appoint_ruling_party = yes\n}\n")
		newfile.write("democracy = {\n	fascist = yes\n	reactionary = yes\n	conservative = yes\n	socialist = yes\n	communist = yes\n	liberal = yes\n	anarcho_liberal = yes\n\n	election = yes\n	duration = 48\n	appoint_ruling_party = no\n}\n")
	output_path = os.getcwd() + "\\OpenVic\\common\\nationalvalues.txt"
	os.makedirs(os.path.dirname(output_path), exist_ok = True)
	with open(output_path,"a",encoding=OUTPUT_ENCODING,newline='\n') as newfile:
		for technology in TECHNOLOGY_SET:
			newfile.write(technology + " = { }\n")
		if "nv_order" not in TECHNOLOGY_SET:
			newfile.write("nv_order = { }\n")
		if "nv_liberty" not in TECHNOLOGY_SET:
			newfile.write("nv_liberty = { }\n")
		if "nv_equality" not in TECHNOLOGY_SET:
			newfile.write("nv_equality = { }\n")
	output_path = os.getcwd() + "\\OpenVic\\common\\religion.txt"
	os.makedirs(os.path.dirname(output_path), exist_ok = True)
	with open(output_path,"a",encoding=OUTPUT_ENCODING,newline='\n') as newfile:
		for religion_group in RELIGION_DICTIONARY:
			newfile.write(religion_group + " = {\n")
			for religion in RELIGION_DICTIONARY[religion_group]:
				newfile.write("	" + religion + " = { color = " + RELIGION_DICTIONARY[religion_group][religion]["color"] + " icon = " + RELIGION_DICTIONARY[religion_group][religion]["icon"] + " }\n")
			newfile.write("}\n")
	os.makedirs("OpenVic/gfx/flags", exist_ok = True)
	for tag in TAG_SET:
		if os.path.exists("gfx/flags/" + tag + ".tga"):
			EU4_flag = Image.open("gfx/flags/" + tag + ".tga").resize((64,64),resample=Image.LANCZOS)
			loaded_EU4_flag = EU4_flag.load()
			V2_flag = Image.new(mode="RGB", size=(93,64), color=(0,0,0))
			loaded_flag = V2_flag.load()
			for i in range(93):
				for k in range(64):
					loaded_flag[i,k] = loaded_EU4_flag[min(63,max(0,i-15)),k]
			V2_flag.save("OpenVic/gfx/flags/" + tag + ".tga",compression="tga_rle")
		else:
			Image.new(mode="RGB", size=(93,64), color=(0,0,0)).save("OpenVic/gfx/flags/" + tag + ".tga",compression="tga_rle")
	os.makedirs("OpenVic\\gfx\\interface\\terrain", exist_ok = True)
	religion_dds = Image.open("gfx/interface/icon_religion_small.dds") # The small version in EU4 is the required size for V2 and the small version in V2 seems to be not used at all.
	w,h = religion_dds.size
	religion_dds.save("OpenVic/gfx/interface/icon_religion.dds")
	text = []
	with open("OpenVic/interface/general_gfx.gfx",'r') as file:
		for line in file:
			if line.startswith("#"):
				text.append(line.replace("#", "		noOfFrames = " + str(int(w/h))))
			else:
				text.append(line)
	with open("OpenVic/interface/general_gfx.gfx",'w') as file:
		for line in text:
			file.writelines(line)
	EU4_TERRAIN_PICTURES = set()
	for root, dirs, files in os.walk("gfx\\interface\\"):
		for file in files:
			if file.startswith("colony_terrain_"):
				terrain = file.split("colony_terrain_",maxsplit=1)[1].rsplit(".dds",maxsplit=1)[0]
				if terrain in PROVINCE_TERRAIN_DICTIONARY and terrain not in FORCE_OCEAN:
					Image.open(os.path.join(root, file)).resize((374,94),resample=Image.LANCZOS).save("OpenVic\\gfx\\interface\\terrain\\" + terrain + ".tga",compression="tga_rle")
					EU4_TERRAIN_PICTURES.add(terrain)
	text = []
	with open("OpenVic\\interface\\province_interface.gfx",'r') as file:
		for line in file:
			if line.startswith("	### Terrain ###"):
				text.append(line)
				text.append('\n')
				for terrain in EU4_TERRAIN_PICTURES:
					text.append('	spriteType = {\n')
					text.append('		name = "GFX_terrainimg_' + terrain + '"\n')
					text.append('		texturefile = "gfx\\interface\\terrain\\' + terrain + '.tga"\n')
					text.append('		norefcount = yes\n')
					text.append('	}\n')
				if "ocean" not in EU4_TERRAIN_PICTURES:
					text.append('	spriteType = {\n')
					text.append('		name = "GFX_terrainimg_ocean"\n')
					if "inland_ocean" in EU4_TERRAIN_PICTURES:
						text.append('		texturefile = "gfx\\interface\\terrain\\inland_ocean.tga"\n')
					else:
						text.append('		texturefile = "gfx\\interface\\terrain\\' + terrain + '.tga"\n')
					text.append('		norefcount = yes\n')
					text.append('	}\n')
			else:
				text.append(line)
	with open("OpenVic\\interface\\province_interface.gfx",'w') as file:
		for line in text:
			file.writelines(line)
	text = []
	with open("OpenVic\\map\\terrain.txt",'r') as file:
		for line in file:
			if line.startswith("# categories"):
				for terrain in PROVINCE_TERRAIN_DICTIONARY:
					if terrain in ["ocean","inland_ocean"] or terrain in FORCE_OCEAN:
						continue
					text.append('	' + terrain + ' = {\n')
					text.append('		color = {' + PROVINCE_TERRAIN_DICTIONARY[terrain]["color"] + '}\n')
					text.append('		movement_cost = ' + PROVINCE_TERRAIN_DICTIONARY[terrain]["movement_cost"] + '\n')
					if "combat_width" in PROVINCE_TERRAIN_DICTIONARY[terrain]:
						text.append('		combat_width = ' + PROVINCE_TERRAIN_DICTIONARY[terrain]["combat_width"] + '\n')
					if "defence" in PROVINCE_TERRAIN_DICTIONARY[terrain]:
						text.append('		defence = ' + PROVINCE_TERRAIN_DICTIONARY[terrain]["defence"] + '\n')
					if "supply_limit" in PROVINCE_TERRAIN_DICTIONARY[terrain]:
						text.append('		supply_limit = ' + PROVINCE_TERRAIN_DICTIONARY[terrain]["supply_limit"] + '\n')
					text.append('	}\n')
			elif line.startswith("# text"):
				terrain_order = dict()
				for key,value in ATLAS_DICTIONARY.items():
					if "bmp_index" in value:
						terrain_order[ATLAS_DICTIONARY[key]["bmp_index"]] = TERRAIN_BMP_INDEX_DICTIONARY[key]
				n = 0
				for i in range(0,64):
					if i in TERRAIN_BMP_INDEX_DICTIONARY:
						if TERRAIN_BMP_INDEX_DICTIONARY[i] not in ["ocean","inland_ocean"] and TERRAIN_BMP_INDEX_DICTIONARY[i] not in FORCE_OCEAN:
							if i in ATLAS_DICTIONARY:
								if "bmp_index" in ATLAS_DICTIONARY[i]:
									continue
							while n in terrain_order:
								n += 1
							if i not in ATLAS_DICTIONARY:
								ATLAS_DICTIONARY[i] = dict()
								ATLAS_DICTIONARY[i]["atlas_index"] = n
							if "bmp_index" not in ATLAS_DICTIONARY[i]:
								ATLAS_DICTIONARY[i]["bmp_index"] = n
							terrain_order[n] = TERRAIN_BMP_INDEX_DICTIONARY[i]
							n += 1
						else:
							ATLAS_DICTIONARY[i] = dict()
							ATLAS_DICTIONARY[i]["atlas_index"] = 254
							ATLAS_DICTIONARY[i]["bmp_index"] = 254
				for i in range(0,64):
					if i % 4 == 0 and i != 0:
						text.append('\n')
					if i in terrain_order:
						text.append('text_' + str(i) + ' = { type = ' + terrain_order[i] + ' color = { ' + str(i) + ' } priority = ' + str(i) + ' }\n')
					else:
						text.append('text_' + str(i) + ' = { type = unused color = { ' + str(i) + ' } priority = ' + str(i) + ' }\n')
			else:
				text.append(line)
	with open("OpenVic\\map\\terrain.txt",'w') as file:
		for line in text:
			file.writelines(line)
	atlas = Image.open(ATLAS_PATH).convert(mode="RGB")
	w,h = atlas.size
	w = w / ATLAS_SIZE[0]
	h = h / ATLAS_SIZE[1]
	texturesheet = Image.new(mode="RGB", size=(2048,2048), color=(0,0,0))
	for i in ATLAS_DICTIONARY:
		if ATLAS_DICTIONARY[i]["atlas_index"] < ATLAS_SIZE[0] * ATLAS_SIZE[1]:
			left = (ATLAS_DICTIONARY[i]["atlas_index"] % ATLAS_SIZE[0]) * w
			upper = (ATLAS_DICTIONARY[i]["atlas_index"] // ATLAS_SIZE[0]) * h
			right = left + w
			lower = upper + h
			texture = atlas.crop((left,upper,right,lower)).resize((256,256),resample=Image.LANCZOS)
			left = (ATLAS_DICTIONARY[i]["bmp_index"] % 8) * 256
			upper = (ATLAS_DICTIONARY[i]["bmp_index"] // 8) * 256
			texturesheet.paste(texture,(left,upper))
	os.makedirs("OpenVic\\map\\terrain", exist_ok = True)
	texturesheet.save("OpenVic\\map\\terrain\\texturesheet.tga",compression="tga_rle")
	texturesheet.save("OpenVic\\map\\terrain\\texturesheet2.tga",compression="tga_rle")
	for tag in COUNTRY_DICTIONARY:
		if tag == "NAT" or tag == "PIR":
			continue
		output_path = os.getcwd() + "\\OpenVic\\history\\countries\\" + tag + ".txt"
		os.makedirs(os.path.dirname(output_path), exist_ok = True)
		with open(output_path,"a",encoding=OUTPUT_ENCODING,newline='\n') as newfile:
			if tag == "REB":
				continue
			newfile.write("capital = " + COUNTRY_DICTIONARY[tag]["capital"] + "\ngovernment = " + COUNTRY_DICTIONARY[tag]["government"] + "\nreligion = " + COUNTRY_DICTIONARY[tag]["religion"] + "\nprimary_culture = " + COUNTRY_DICTIONARY[tag]["primary_culture"] + "\n")
			if "accepted_cultures" in COUNTRY_DICTIONARY[tag]:
				for culture in COUNTRY_DICTIONARY[tag]["accepted_cultures"]:
					newfile.write("culture = " + culture + "\n")
			newfile.write("nationalvalue = " + COUNTRY_DICTIONARY[tag]["technology_group"] + "\n")
			if COUNTRY_DICTIONARY[tag]["government"] != "native" and COUNTRY_DICTIONARY[tag]["government"] != "tribal":
				newfile.write("civilized = yes\nliteracy = 0.5\nnon_state_culture_literacy = 0.5\n")
			elif COUNTRY_DICTIONARY[tag]["government"] == "native":
				newfile.write("literacy = 0.2\nnon_state_culture_literacy = 0.2\n")
			else:
				newfile.write("literacy = 0\nnon_state_culture_literacy = 0\n")
			if COUNTRY_DICTIONARY[tag]["government"] == "monarchy" or COUNTRY_DICTIONARY[tag]["government"] == "theocracy":
				newfile.write("ruling_party = openvic_generic_conservative\n")
			elif COUNTRY_DICTIONARY[tag]["government"] == "native" or COUNTRY_DICTIONARY[tag]["government"] == "tribal":
				newfile.write("ruling_party = openvic_generic_reactionary\n")
			elif COUNTRY_DICTIONARY[tag]["government"] == "republic":
				newfile.write("ruling_party = openvic_generic_liberal\n")
			else:
				print(f"An unexpected government: {COUNTRY_DICTIONARY[tag]["government"]} has been found and assigned the ruling party reactionary, please mention this issue on github or discord, so i can fix this.")
				newfile.write("ruling_party = openvic_generic_reactionary\n")
			if COUNTRY_DICTIONARY[tag]["government"] != "native" and COUNTRY_DICTIONARY[tag]["government"] != "tribal":
				newfile.write("\npost_napoleonic_thought = 1\nflintlock_rifles = 1\nbronze_muzzle_loaded_artillery = 1\nmilitary_staff_system = 1\npost_nelsonian_thought = 1\nclipper_design = 1\nprivate_banks = 1\nno_standard = 1\nearly_classical_theory_and_critique = 1\nfreedom_of_trade = 1\nguild_based_production = 1\nlate_enlightenment_philosophy = 1\nmalthusian_thought = 1\nwater_wheel_power = 1\npublishing_industry = 1\nmechanical_production = 1\nmechanized_mining = 1\nexperimental_railroad = 1\nbasic_chemistry = 1\n")
			if COUNTRY_DICTIONARY[tag]["government"] == "monarchy":
				newfile.write("# for monarchies:\nmuzzle_loaded_rifles = 1\n")
			elif COUNTRY_DICTIONARY[tag]["government"] == "theocracy":
				newfile.write("# for theocracies\npositivism = 1\n")
			elif COUNTRY_DICTIONARY[tag]["government"] == "republic":
				newfile.write("# for republics\npractical_steam_engine = 1\n")
	RGO_LIST = list(RGO_DICTIONARY.keys())
	RGO_WEIGHT = list(RGO_DICTIONARY.values())
	for province in PROVINCE_DICTIONARY:
		output_path = os.getcwd() + "\\OpenVic\\history\\provinces\\OpenVic_" + PROVINCE_DICTIONARY[province]["continent"] + "\\" + province + ".txt"
		os.makedirs(os.path.dirname(output_path), exist_ok = True)
		with open(output_path,"a",encoding=OUTPUT_ENCODING,newline='\n') as newfile:
			if "terrain" in PROVINCE_DICTIONARY[province]:
				newfile.write("terrain = " + PROVINCE_DICTIONARY[province]["terrain"] + "\n")
			if "trade_goods" in PROVINCE_DICTIONARY[province]:
				newfile.write("life_rating = 30\ntrade_goods = " + random.choices(RGO_LIST,weights=RGO_WEIGHT,k=1)[0] + "\n")
				#newfile.write("trade_goods = " + PROVINCE_DICTIONARY[province]["trade_goods"] + "\n") # TODO change the dictionary to convert EU4 goods and only randomise the rest, but also with weighted odds so goods are added proportionally.
			if "owner" in PROVINCE_DICTIONARY[province]:
				if PROVINCE_DICTIONARY[province]["owner"] != "---":
					government = COUNTRY_DICTIONARY[PROVINCE_DICTIONARY[province]["owner"]]["government"]
					newfile.write("owner = " + PROVINCE_DICTIONARY[province]["owner"] + "\n")
					newfile.write("controller = " + PROVINCE_DICTIONARY[province]["controller"] + "\n")
					if PROVINCE_DICTIONARY[province]["owner"] in PROVINCE_DICTIONARY[province]["add_core"]:
						newfile.write("add_core = " + PROVINCE_DICTIONARY[province]["owner"] + "\n")
				else:
					government = "standard"
			else:
				government = "standard"
			for tag in PROVINCE_DICTIONARY[province]["add_core"]:
				if tag != PROVINCE_DICTIONARY[province]["owner"]:
					newfile.write("add_core = " + tag + "\n")
		if "population" in PROVINCE_DICTIONARY[province]:
			if PROVINCE_DICTIONARY[province]["culture"] == "no_culture" or PROVINCE_DICTIONARY[province]["religion"] == "no_religion":
				continue
			output_path = os.getcwd() + "\\OpenVic\\history\\pops\\1836.1.1\\" + PROVINCE_DICTIONARY[province]["continent"] + ".txt" # If this is changed to the actual start date, pops wont show up, so leave it. Once the mod start date is used the empty files for the second start date have to be added as well in the default folder.
			os.makedirs(os.path.dirname(output_path), exist_ok = True)
			with open(output_path,"a",encoding=OUTPUT_ENCODING,newline='\n') as newfile:
				newfile.write(province + " = {\n")
				for pop_type, ratios in POPS_AND_RATIOS.items():
					if government in ratios:
						if POPS_AND_RATIOS[pop_type][government] != 0:
							newfile.write("	" + pop_type +" = { culture = " + PROVINCE_DICTIONARY[province]["culture"] + " religion = " + PROVINCE_DICTIONARY[province]["religion"] + " size = " + str(ratios[government]*PROVINCE_DICTIONARY[province]["population"]) + " }\n")
					elif POPS_AND_RATIOS[pop_type]["standard"] != 0:
						newfile.write("	" + pop_type +" = { culture = " + PROVINCE_DICTIONARY[province]["culture"] + " religion = " + PROVINCE_DICTIONARY[province]["religion"] + " size = " + str(POPS_AND_RATIOS[pop_type]["standard"]*PROVINCE_DICTIONARY[province]["population"]) + " }\n")
				newfile.write("}" + "\n")
	create_localisation_file(TAG_SET - {"REB","NAT","PIR"},["","_ADJ"],"countries")
	create_localisation_file(STATE_TUPLE,[""],"states")
	create_localisation_file(PROV_TUPLE,[""],"provinces")
	create_localisation_file(CULTURE_SET,[""],"cultures")
	create_localisation_file(RELIGION_SET,[""],"religions")
	create_localisation_file(TECH_GROUP_SET,[""],"technology_groups")
	# The 0 in front of the normal localisation file name is to make sure that this localisation gets applied, rather than base V2 localisation.
	output_path = os.getcwd() + "\\OpenVic\\localisation\\0 terrain.csv"
	os.makedirs(os.path.dirname(output_path), exist_ok = True)
	with open(output_path,"a",encoding=OUTPUT_ENCODING,newline='\n') as file:
		for terrain in set(PROVINCE_TERRAIN_DICTIONARY.keys()) - {"ocean","inland_ocean"} - set(FORCE_OCEAN):
			file.write(terrain + ";")
			for language in ["english","french","german","polish","spanish"]:
				if language in LANGUAGES:
					file.write("§Y" + LOCALISATION_DICTIONARY[terrain][language] + "§!\\n" + LOCALISATION_DICTIONARY[terrain + "_desc"][language] + ";")
				else:
					file.write(";")
			for language in set(LANGUAGES) - {"english","french","german","polish","spanish"}:
				file.write("§Y" + LOCALISATION_DICTIONARY[terrain][language] + "§!\\n" + LOCALISATION_DICTIONARY[terrain + "_desc"][language] + ";")
			file.write("\n")
	output_path = os.getcwd() + "\\OpenVic\\localisation\\0 governments.csv"
	os.makedirs(os.path.dirname(output_path), exist_ok = True)
	with open(output_path,"a",encoding=OUTPUT_ENCODING,newline='\n') as file:
		for government in GOVERNMENT_SET:
			file.write(government + ";")
			for language in ["english","french","german","polish","spanish"]:
				if language in LANGUAGES:
					file.write(LOCALISATION_DICTIONARY[government + "_name"][language] + ";")
				else:
					file.write(";")
			for language in set(LANGUAGES) - {"english","french","german","polish","spanish"}:
				file.write(LOCALISATION_DICTIONARY[government + "_name"][language] + ";")
			file.write("\n")
	V2_CONTINENT_LIST = ["europe","asia","africa","north_america","south_america","oceania"]
	V2_DIPLOMACY_FILTER = ["DIPLOMACY_FILTER_EUROPE","DIPLOMACY_FILTER_ASIA","DIPLOMACY_FILTER_AFRICA","DIPLOMACY_FILTER_NORTH_AMERICA","DIPLOMACY_FILTER_SOUTH_AMERICA","DIPLOMACY_FILTER_OCEANIA"]
	V2_DIPLOMACY_FILTER_TOOLTIP = ["DIPLOMACY_FILTER_EUROPE_TOOLTIP","DIPLOMACY_FILTER_ASIA_TOOLTIP","DIPLOMACY_FILTER_AFRICA_TOOLTIP","DIPLOMACY_FILTER_NORTH_AMERICA_TOOLTIP","DIPLOMACY_FILTER_SOUTH_AMERICA_TOOLTIP","DIPLOMACY_FILTER_OCEANIA_TOOLTIP"]
	output_path = os.getcwd() + "\\OpenVic\\localisation\\0 continents.csv"
	os.makedirs(os.path.dirname(output_path), exist_ok = True)
	with open(output_path,"a",encoding=OUTPUT_ENCODING,newline='\n') as file:
		for index in range(min(6,len(CONTINENT_LIST) - 2)):
			file.write(V2_CONTINENT_LIST[index] + ";")
			for language in ["english","french","german","polish","spanish"]:
				if language in LANGUAGES:
					file.write(LOCALISATION_DICTIONARY[CONTINENT_LIST[index][0]][language] + ";")
				else:
					file.write(";")
			for language in set(LANGUAGES) - {"english","french","german","polish","spanish"}:
				file.write(LOCALISATION_DICTIONARY[CONTINENT_LIST[index][0]][language] + ";")
			file.write("\n")
			file.write(V2_DIPLOMACY_FILTER[index] + ";")
			for language in ["english","french","german","polish","spanish"]:
				if language in LANGUAGES:
					file.write(LOCALISATION_DICTIONARY[CONTINENT_LIST[index][0]][language] + ";")
				else:
					file.write(";")
			for language in set(LANGUAGES) - {"english","french","german","polish","spanish"}:
				file.write(LOCALISATION_DICTIONARY[CONTINENT_LIST[index][0]][language] + ";")
			file.write("\n")
			file.write(V2_DIPLOMACY_FILTER_TOOLTIP[index] + ";")
			for language in ["english","french","german","polish","spanish"]:
				if language in LANGUAGES:
					file.write(LOCALISATION_DICTIONARY[CONTINENT_LIST[index][0]][language] + ";")
				else:
					file.write(";")
			for language in set(LANGUAGES) - {"english","french","german","polish","spanish"}:
				file.write(LOCALISATION_DICTIONARY[CONTINENT_LIST[index][0]][language] + ";")
			file.write("\n")
		for index in range(max(0,len(CONTINENT_LIST) - 8)):
			file.write(CONTINENT_LIST[index + 6][0] + ";")
			for language in ["english","french","german","polish","spanish"]:
				if language in LANGUAGES:
					file.write(LOCALISATION_DICTIONARY[CONTINENT_LIST[index][0]][language] + ";")
				else:
					file.write(";")
			for language in set(LANGUAGES) - {"english","french","german","polish","spanish"}:
				file.write(LOCALISATION_DICTIONARY[CONTINENT_LIST[index][0]][language] + ";")
			file.write("\n")
	output_path = os.getcwd() + "\\OpenVic\\map\\adjacencies.csv"
	os.makedirs(os.path.dirname(output_path), exist_ok = True)
	with open(output_path,"a",encoding=OUTPUT_ENCODING,newline='\n') as newfile:
		pass
	output_path = os.getcwd() + "\\OpenVic\\map\\climate.txt"
	os.makedirs(os.path.dirname(output_path), exist_ok = True)
	with open(output_path,"a",encoding=OUTPUT_ENCODING,newline='\n') as newfile:
		for index in range(len(CLIMATE_LIST)):
			newfile.write(CLIMATE_LIST[index][0] + " = {\n")
			province_string = ""
			for province in CLIMATE_LIST[index][1]:
				province_string += province + " "
			newfile.write("	" + province_string.strip() + "\n}\n")
	output_path = os.getcwd() + "\\OpenVic\\map\\continent.txt"
	os.makedirs(os.path.dirname(output_path), exist_ok = True)
	with open(output_path,"a",encoding=OUTPUT_ENCODING,newline='\n') as newfile:
		for index in range(min(6,len(CONTINENT_LIST) - 2)):
			newfile.write(V2_CONTINENT_LIST[index] + " = { # " + CONTINENT_LIST[index][0] + "\n	provinces = {")
			province_string = ""
			for province in CONTINENT_LIST[index][1]:
				province_string += province + " "
			if index != 5:
				newfile.write("\n		" + province_string.strip() + "\n	}\n}\n")
			else:
				newfile.write("\n		" + province_string.strip() + "\n	")
		for index in range(max(0,len(CONTINENT_LIST) - 8)):
			newfile.write("	# " + CONTINENT_LIST[index + 6][0])
			province_string = ""
			for province in CONTINENT_LIST[index][1]:
				province_string += province + " "
			newfile.write("\n		" + province_string.strip() + "\n	")
		newfile.write("}\n}\n")
		#for index in range(len(CONTINENT_LIST) - 2):
		#	newfile.write(CONTINENT_LIST[index][0] + " = {\n	provinces = {")
		#	province_string = ""
		#	for province in CONTINENT_LIST[index][1]:
		#		province_string += province + " "
		#	newfile.write("\n		" + province_string.strip() + "\n	}\n}\n")
	output_path = os.getcwd() + "\\OpenVic\\map\\default.map"
	os.makedirs(os.path.dirname(output_path), exist_ok = True)
	with open(output_path,"a",encoding=OUTPUT_ENCODING,newline='\n') as newfile:
		newfile.write("max_provinces = " + MAX_PROVINCES + "\nsea_starts = {\n")
		if CONTINENT_LIST[len(CONTINENT_LIST)-2][1]:
			newfile.write("	# EU4 ocean provinces:\n")
			province_string = ""
			for province in CONTINENT_LIST[len(CONTINENT_LIST)-2][1]:
				province_string += province + " "
			newfile.write("	" + province_string.strip() + "\n")
		if CONTINENT_LIST[len(CONTINENT_LIST) - 1][1]:
			newfile.write("	# EU4 lake provinces:\n")
			province_string = ""
			for province in CONTINENT_LIST[len(CONTINENT_LIST) - 1][1]:
				province_string += province + " "
			newfile.write("	" + province_string.strip() + "\n")
		newfile.write('}\ndefinitions = "../mod/OpenVic/map/definition.csv"\nprovinces = "provinces.bmp"\npositions = "positions.txt"\nterrain = "terrain.bmp"\nrivers = "rivers.bmp"\nterrain_definition = "terrain.txt"\ntree_definition = "trees.txt"\ncontinent = "continent.txt"\nadjacencies = "adjacencies.csv"\nregion = "region.txt"\nregion_sea = "region_sea.txt"\nprovince_flag_sprite = "province_flag_sprites"\n\nborder_heights = {\n	500\n	800\n	1100\n}\nterrain_sheet_heights = {\n	500\n}\ntree = 350\nborder_cutoff = 1100.0\n')
	output_path = os.getcwd() + "\\OpenVic\\map\\definition.csv"
	os.makedirs(os.path.dirname(output_path), exist_ok = True)
	with open(output_path,"a",encoding=OUTPUT_ENCODING,newline='\n') as newfile:
		newfile.write("province;red;green;blue;name;\n")
		for line in DEFINITION_CSV:
			newfile.write(";".join(line) + ";x;\n")
	output_path = os.getcwd() + "\\OpenVic\\map\\positions.txt"
	os.makedirs(os.path.dirname(output_path), exist_ok = True)
	with open(output_path,"a",encoding=OUTPUT_ENCODING,newline='\n') as newfile:
		for province in PORT_POSITIONS:
			if "rotation" in PORT_POSITIONS[province]:
				newfile.write(province + " = {\n	building_position = {\n		naval_base = { x = " + PORT_POSITIONS[province]["position"][0] + " y = " + PORT_POSITIONS[province]["position"][1] + " }\n	}\n	building_rotation = { naval_base = " + PORT_POSITIONS[province]["rotation"] + " }\n}\n")
			else:
				newfile.write(province + " = {\n	building_position = {\n		naval_base = {\n			x = " + PORT_POSITIONS[province]["position"][0] + "\n			y = " + PORT_POSITIONS[province]["position"][1] + "\n		}\n	}\n}\n")
	Image.open("map/provinces.bmp").transpose(Image.FLIP_TOP_BOTTOM).save("OpenVic/map/provinces.bmp")
	V2_river_bmp = create_river_bmp()
	V2_river_bmp.save("OpenVic/map/rivers.bmp")
	EU4_terrain = Image.open("map/terrain.bmp").transpose(Image.FLIP_TOP_BOTTOM)
	terrain_palette = EU4_terrain.getpalette()
	terrain_palette += [0] * max(0,768 - len(terrain_palette))
	w,h = EU4_terrain.size
	load_EU4_terrain = EU4_terrain.load()
	for x in range(w):
		for y in range(h):
			load_EU4_terrain[x,y] = ATLAS_DICTIONARY[load_EU4_terrain[x,y]]["bmp_index"]
	terrain_palette[762:765] = [0, 0, 255] # TODO use correct terrain colors eventually
	EU4_terrain.putpalette(terrain_palette)
	EU4_terrain.save("OpenVic\\map\\terrain.bmp")
	terrain_palette = [140, 125, 90] * 256
	terrain_palette[762:765] = [200, 200, 175]
	EU4_terrain.putpalette(terrain_palette)
	EU4_terrain.convert(mode="RGBA").resize((266,102),resample=Image.LANCZOS).transpose(Image.FLIP_TOP_BOTTOM).save("OpenVic\\gfx\\interface\\minimap.dds")
	os.makedirs("OpenVic/map/terrain", exist_ok = True)
	Image.open("map/terrain/colormap_spring.dds").transpose(Image.FLIP_TOP_BOTTOM).save("OpenVic/map/terrain/colormap.dds") #, pixel_format="DXT1") others that should work with this version: DXT1, DXT3, DXT5, BC2, BC3 and BC5
	Image.new(mode="RGBA", size=(1,1), color=(128,128,128,255)).save("OpenVic/map/terrain/colormap_no_shadow.dds")
	Image.new(mode="RGBA", size=(1,1), color=(128,128,128,255)).save("OpenVic/map/terrain/colormap_political.dds")
	Image.open("map/terrain/colormap_water.dds").transpose(Image.FLIP_TOP_BOTTOM).save("OpenVic/map/terrain/colormap_water.dds")
	output_path = os.getcwd() + "\\OpenVic\\map\\region.txt"
	os.makedirs(os.path.dirname(output_path), exist_ok = True)
	with open(output_path,"a",encoding=OUTPUT_ENCODING,newline='\n') as newfile:
		for state in STATE_LIST:
			newfile.write(state[0] + " = { " + " ".join(state[1]) + " }\n")
		for index in range(len(CLIMATE_LIST)): # TODO remove this eventually, but right now it prevents crashes when clicking on impassable provinces as those would not be in a state otherwise.
			if CLIMATE_LIST[index][0] != "impassable":
				continue
			newfile.write("\nimpassable = { ")
			province_string = ""
			for province in CLIMATE_LIST[index][1]:
				province_string += province + " "
			newfile.write(province_string + "}\n")

	print("Done")
else:
	print("READ AND FOLLOW THE INSTRUCTIONS!")
#%%
