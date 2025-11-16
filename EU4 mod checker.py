#%%
# Place this Python script into whatever mod folder you want to check. The mod needs to have the common\countries, common\country_tags, common\cultures, common\religions, common\governments, history\countries and history\provinces folders and map\area.txt, map\climate.txt, map\continent.txt, map\definition.csv and map\default.map files as well as the provinces.bmp, rivers.bmp and terrain.bmp. If those are not present, either because the mod uses the base game files or relies on another mod you have to copy them or can't use this script. If there are any DS_Store files they need to be removed.
from collections import defaultdict
from PIL import Image
import re
import os
# These global values are the only parts of the script you might need to change, just follow the instructions.
START_DATE = "1444.11.11" # Replace 1444.11.11 with the intended start date in the form years.months.days, unless it would either be a 29th February as those do neither exist in OpenVic nor Victoria 2 and will be replaced with 28th February and for OpenVic it must be a date within the range 1.1.1 to 65535.12.31 or if the output is intended for Victoria 2, i assume dates must be after 1.1.1 or even later, but i am not sure about the exact details. Any input that is not valid will be replaced with 1444.11.11. The history will be applied until the start date, including identical dates like 01444.11.11 and error messages will be shown, for example if the province has only a religion or culture, but not both at the start date.
ENCODING = "windows-1252" # Change this to whatever the encoding of the mod is, most likely it is either "utf-8" or "windows-1252". If it is mixed and you want to be able to automatically convert the mod to an OpenVic mod, you currently would have to pick one and convert the files with the other encoding.
LANGUAGES = ["english"] # Add or remove whatever language, where you want to check the Victoria 2/OpenVic related localisation. You can also leave the brackets empty [] if you want to search for specific files instead, to ensure that the localisation is only present in those.
TERRAIN_DICTIONARY = {
	"OCEAN_INDEX": 15, # Replace this number, if the mod changes the default EU4 index values for the ocean and inland ocean, which can be found in the map/terrain.txt by looking at the type = ocean/inland_ocean { color = { ?? } } at the end of the file or map/terrain.bmp for example by using GIMP and selecting an ocean/inland_ocean pixel with the color picker which will show the index.
	"INLAND_OCEAN_INDEX": 17, # Same as with OCEAN_INDEX.
	"CONTINENTAL_INDEX": 0, # This and COASTAL_INDEX will only be used to automatically create a new terrain.bmp, if you enable the option below. Specifically any pixel belonging to a continental province that is currently an ocean pixel will be changed to CONTINENTAL_INDEX.
	"COASTAL_INDEX": 35, # Any coastal pixel that is not actually coastal will be replaced by CONTINENTAL_INDEX.
	"FORCE_INLAND_OCEAN": ["inland_ocean"] # You can simply make the brackets empty [] if you don't want the following to happen: Any province in the terrain_override part for the terrains in this list will be turned into inland ocean terrain in the terrain.bmp and rivers.bmp, just like any current inland ocean province not in this list will have it's terrain turned into regular ocean terrain, if you set "INCORRECT_TERRAIN" = True. For example Elder Scrolls Universalis has impassable river provinces, which use "impassable_rivers" terrain as identifier, as i currently intend to turn these rivers into impassable ocean provinces in Victoria 2/OpenVic.
}
ATLAS_PATH = "map\\terrain\\atlas0.dds" # The textures for the terrain map seem to be always here, but just to be sure i may as well make it easy to change the path.
ATLAS_SIZE = (4,4) # Change this to the number of different squares in the map\terrain\atlas0 file, however (8,8) is the maximum and (2,2) the minimum. First number is from left to right, second is up down, although they are most likely the same.
MIN_PROVINCE_SIZE = 10 # You will get a warning for every province that has less pixels than the number you enter, as it may not be an intended province, but rather some leftover pixels.
MAX_PROVINCE_SIZE = 16363 # When provinces are too big Victoria 2 can bug out, like a large land province can be shown as partially ocean. Simply splitting up the provinces will solve that issue, though it may not be necessary to do that, so just increase the size if there are no issues with this and you don't want to see the warnings.
DONT_IGNORE_ISSUE = { # Not all issues cause trouble when generating output files, so you can choose to ignore them, though in some cases you really should check them.
	"INDIVIDUAL_PIXELS":False, # Some provinces will be assigned to a continent, while some of their pixels in the terrain.bmp are for oceans/in the TERRAIN_DICTIONARY, while other provinces are assigned as ocean or lake in the default.map file, but have pixels that are not according to the TERRAIN_DICTIONARY. The province IDs with such wrong pixels will be shown regardless of whether this option is False or True, but setting this option to True will also show all individual wrong pixels, which can easily cause tens of thousands of lines mentioning wrong pixels.
	"DATES_AFTER_START_DATE":True, # If you only care about mistakes that happen until the START_DATE, set this to False.
	"MISSING_EMPTY_SPACE":True, # For example "add_core =" is searched as " add_core =" instead, as if it always had an empty space in front of it, which the formatting also inserts before and after "=", "{", "}" and the at the start and end of the text itself, as well as any time some parts get removed like date entries or put together like duplicate date entries. However there could be situations where EU4 does not actually require an empty space in front of it, for example 'capital = "?"add_core', which this script would not recognise as a core being added, so you should check all these warnings.
	"IDENTICAL_DATES":True, # This mentions if one date appears multiple times in the same file, but their entries get combined anyway, so you can ignore this, if you don't want to combine the entries.
	"DUPLICATE_DATES":True, # 1.1.1 and 01.01.01 entries do not get combined and are applied in whatever order they are found first, so you have to check those.
	"DUPLICATE_NAMES":True, # Sometimes the male, female or dynasty names lists can contain duplicates, which does nothing, so you can ignore this, if you don't want to remove them.
	"LONG_NAMES":True, # Sometimes names can be quite long, so maybe the quotation marks where done wrong.
	"DUPLICATE_CORES":True, # Sometimes cores that already exist are added again, which does nothing, so you can ignore this, if you don't want to remove such duplicates.
	"DUPLICATE_REMOVAL_CORE":True, # Cores may be removed twice for the same date, which does nothing, so you can ignore this.
	"REMOVE_NON_EXISTANT_CORE":True, # Sometimes cores are removed even though they were not present at this date. So maybe some other core was actually supposed to be removed.
	"DUPLICATE_CULTURES":True, # Sometimes accepted cultures are added again, which does nothing, so you can ignore this.
	"DUPLICATE_REMOVAL_CULTURE":True, # Cultures may be removed twice for the same date, which does nothing, so you can ignore this.
	"REMOVE_NON_EXISTANT_CULTURE":True, # Sometimes cultures are removed as accepted cultures, even though they were not accepted at this date. So maybe some other culture was actually supposed to be removed.
	"MISSING_PROVINCE_FILE":True, # Some provinces may be placed on a continent or such, but lack a province file, can be ignored as an empty "provinceID.txt" file will simply be generated anyway for the output.
	"MISSING_PROVINCE_ID":True, # While it is not necessary to use all numbers between 1 and the number of provinces as IDs, maybe you still want to add empty files for such cases, if not you can set it to False.
	"OCEAN_AND_LAKE_CLIMATE":False, # In EU4 oceans and lakes can use climates to let them freeze during winter, but you may want to remove some not not needed ones.
	"THROUGH_NOT_IN_OCEAN":False, # While not necessary you may want to set the adjacency type sea in map\adjacencies.csv to land, river or lake, if the Through province is not an ocean.
	"CANAL_NOT_MUTUAL_NEIGHBOUR":False, # It is not necessary for a canal to be next to the From and To province, the Through province can even be the same as From or To, but maybe you want to know about such cases.
	"CITY_POSITION_OUTSIDE_BMP":False, # The position of the city could be outside the bmp, though this currently does not matter for conversion to a Victoria 2 mod.
	"UNIT_POSITION_OUTSIDE_BMP":False, # The position of the unit could be outside the bmp, though this currently does not matter for conversion to a Victoria 2 mod.
	"NAME_POSITION_OUTSIDE_BMP":False, # The position of the name could be outside the bmp, though this currently does not matter for conversion to a Victoria 2 mod.
	"CITY_POSITION":False, # The position of the city could be outside of the province, though this currently does not matter for conversion to a Victoria 2 mod.
	"UNIT_POSITION":False, # The position of units could be outside of the province, though this currently does not matter for conversion to a Victoria 2 mod.
	"NAME_POSITION":False, # The position of the name could be outside of the province, though this currently does not matter for conversion to a Victoria 2 mod.
	"MISSING_TERRAIN_MODIFIER": True, # If True you will get a message for every terrain that has no supply_limit, movement_cost, combat_width or defence in map\terrain.txt, the default for the mod converter will be 1 for movement_cost and the movement_cost will also have a minimal value of 1 and 0 for supply_limit, combat_width and defence and combat_width will have a minimum of -0.8 as well.
	"NO_TERRAIN_OVERRIDE": False, # If set to True you get a list of all continental provinces that are not used in any terrain_override, which is not necessary, just something you may want to do.
	"INCORRECT_TERRAIN": False, # ONLY CHANGE THIS TO TRUE IF THERE ARE NO MORE ERRORS RELATED TO THE MAP! In EU4 it does not matter if the terrain.bmp matches the province being continental or an ocean, however in V2 this is important, so you can choose to automatically generate both the terrain.bmp and rivers.bmp to match this. The new ones will be saved as terrain2.bmp and rivers2.bmp and the generation process for the terrain.bmp is to copy any correct pixel, while incorrect ones will be swapped to ocean or inland_ocean for lakes and the FORCE_INLAND_OCEAN terrains or the CONTINENTAL_INDEX for continental provinces. If you do not see an error message containing: "If no map issues are mentioned above this message you can create the terrain.bmp and rivers.bmp files with correct pixels." leave this option as False as it either means there are important errors that need to be fixed first or very unlikely, everything is already correct.
	"COAST_NOT_COASTAL": False, # If you want every coastal province to have coastal terrain, change this to True. There will be no exceptions, so don't use this if a mod made some terrain not coastal by choice.
	"WRONG_PICTURE_SIZE": True, # If you don't want to fix wrong picture sizes you can disable the warning, however depending on how wrong the size is the output could look really bad.
	"MISSING_FLAGS": False # If you want to know which tags that don't have flags set this to True.
}
I_READ_THE_INSTRUCTIONS = False # Set this to True after changing all the settings you need to change or want to change and that's it. Now you can run it, if you have a sufficiently new Python version installed. Maybe anything after 3.7 will work, as well as a new enough Pillow version (Python Imaging Library).

# TODO check if ocean/lake files are empty, if bmps have correct indexes.
# formats a text file when given the path.
def format_text_in_path(path):
	with open(path,'r',encoding=ENCODING,errors='replace') as file:
		text = []
		for line in file:
			text.append(line.split('#',maxsplit=1)[0])
		text = " ".join(text)
		text = text.replace("{"," { ").replace("}"," } ").replace("="," = ")
		text = " " + " ".join(text.split()) + " "
		if text.__contains__("�"):
			counter = text.count("�")
			index = text.find("�")
			mindex = max(0,index - 50)
			print(f"{counter} character{'s' * (counter != 1)} with wrong encoding found in file: {file.name} specifically � in:")
			print(text[mindex:index + 50])
		if text.count("{") != text.count("}"): # TODO go through every character and count the bracketvalue
			print(f"DONT IGNORE THIS: The number of opening and closing brackets in {path} is not equal.")
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

# Remove everything between all occurances of a given string ending with a {, including that string, until the brackets close again and return the new string or "#" if an error occurs. Due to the formatting adding an empty space before and after any } there will still be an empty space between the now connected parts.
def remove_text_between_brackets(text,sub_string,path):
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
		else:
			print(f"In {path} the brackets are wrong.")
			return "#"
		text = prior_text + leftover
	text = " " + text.strip() + " "
	return text

# Will return the string between the first occurance starting substring and the closing bracket. Any additional occurances of the same subtring will be ignored.
def get_text_between_brackets(text,sub_string,path):
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
	else:
		print(f"In {path} the brackets are wrong.")
		return "#"
	return text

# creates a set of all cultures and a dictionary {culture_group:{culture:{male_names:" ",female_names:" ",dynasty_names:" "}}}
def get_cultures():
	culture_dictionary = dict()
	for root, dirs, files in os.walk("common\\cultures\\"):
		for file in files:
			path = os.path.join(root, file)
			text = format_text_in_path(path)
			if text == "  ":
				print(f"The file {path} is either empty or has only comments in it, why not remove it?")
				continue
			male_names_count = text.count(" male_names = {")
			female_names_count = text.count(" female_names = {")
			dynasty_names_count = text.count(" dynasty_names = {")
			text = remove_text_between_brackets(text," country = {",path)
			text = remove_text_between_brackets(text," province = {",path)
			if male_names_count != text.count(" male_names = {"):
				print('Some male_names list was between " country = {" or " province = {" and the closing bracket "}" and was therefore removed')
			if female_names_count != text.count(" female_names = {"):
				print('Some female_names list was between " country = {" or " province = {" and the closing bracket "}" and was therefore removed')
			if dynasty_names_count != text.count(" dynasty_names = {"):
				print('Some dynasty_names list was between " country = {" or " province = {" and the closing bracket "}" and was therefore removed')
			counter = 0
			culture_group = ""
			culture = ""
			while text.__contains__(" = {"):
				if text.startswith(" = {"):
					print(f'Correct the brackets in {path}. The file ended up starting with " = {{" while being evaluated: {text[:99]}')
					return [dict(),set()]
				[prior_text,leftover] = text.split(" = {",maxsplit=1)
				counter = 1 + counter + prior_text.count("{") - prior_text.count("}") # TODO let it count per character to see if the counter ever gets completely wrong
				new_entry = prior_text.rsplit(" ",maxsplit=1)[1]
				if counter < 1 or counter > 3:
					print(f"Correct the brackets in {path}")
					return [dict(),set()]
				elif counter == 1:
					if new_entry == "male_names" or new_entry == "female_names" or new_entry == "dynasty_names":
						print(f'Culture groups can not be called "male_names", "female_names" or "dynasty_names" or the brackets in {path} are wrong.')
						return [dict(),set()]
					culture_group = new_entry
					if culture_group in culture_dictionary:
						print(f"{culture_group} found a second time in {path}")
					else:
						culture_dictionary[culture_group] = dict()
						culture_dictionary[culture_group]["standard_names"] = dict()
				elif counter == 2:
					if new_entry == "male_names" or new_entry == "female_names" or new_entry == "dynasty_names":
						if new_entry in culture_dictionary[culture_group]["standard_names"]:
							print(f"{new_entry} was already added as standard name list for {culture_group}, but got added again, which replaces the names added before.")
						[name_string,leftover] = leftover.split("}",maxsplit=1)
						if name_string.__contains__("{"):
							print(f'In the culture group {culture_group} for the standard names between "{new_entry} =" and the opening and closing bracket was another opening bracket in {path}')
							return [dict(),set()]
						counter -= 1
						name_list = []
						name_tuple = ()
						if name_string == " ":
							print(f"There are no {new_entry} for the standard names in {culture_group} in {path}")
							name_string = ""
						elif name_string.count('"')%2 != 0:
							print(f'Uneven number of " found for standard names {new_entry} in culture group {culture_group} in {path}')
							return [dict(),set()]
						elif name_string.count('"') == 0:
							name_list = name_string.split()
							name_tuple = sorted(tuple(set(name_list)),key=str.lower)
						else:
							while name_string.count('"') > 1:
								[first_part,name,second_part] = name_string.split('"',maxsplit=2)
								if DONT_IGNORE_ISSUE["LONG_NAMES"] and name.count(" ") > 4 or len(name) > 50:
									print(f"The name {name} seems to be rather long, is this intended?")
								name_list.append('"' + name.strip() + '"')
								name_string = first_part + " " + second_part
							name_list += name_string.split()
							name_tuple = sorted(tuple(set(name_list)),key=str.lower)
						if DONT_IGNORE_ISSUE["DUPLICATE_NAMES"] and len(name_tuple) != len(name_list):
							for name in name_tuple:
								name_list.remove(name)
							print(f"The culture {culture} has the following {new_entry} multiple times: {name_list}")
						if name_tuple:
							culture_dictionary[culture_group]["standard_names"][new_entry] = " "
					else:
						if new_entry in culture_dictionary[culture_group]:
							print(f"{new_entry} was already added as culture for {culture_group}, but got added again in {path}, which removes male, female and dynasty_names if they were added before.")
						culture = new_entry
						culture_dictionary[culture_group][culture] = dict()
				elif counter == 3:
					if new_entry != "male_names" and new_entry != "female_names" and new_entry != "dynasty_names":
						print(f"{new_entry} is neither male_names nor female_names nor dynasty_names so it can't be added as name list for the culture {culture} in culture group {culture_group}, check the brackets in {path}")
						return [dict(),set()]
					if new_entry in culture_dictionary[culture_group][culture]:
						print(f"{new_entry} were already added for culture {culture} in culture group {culture_group}, but got added again, which removes the {new_entry} added before.")
					[name_string,leftover] = leftover.split("}",maxsplit=1)
					if name_string.__contains__("{"):
						print(f'In the culture group {culture_group} for the culture {culture} between "{new_entry} =" and the opening and closing bracket was another opening bracket in {path}')
						return [dict(),set()]
					counter -= 1
					name_list = []
					name_tuple = ()
					if name_string == " ":
						print(f"There are no {new_entry} for the culture {culture} in {culture_group} in {path}")
						name_string = ""
					elif name_string.count('"')%2 != 0:
						print(f'Uneven number of " found for {new_entry} in culture {culture} in culture group {culture_group} in {path}')
						return [dict(),set()]
					elif name_string.count('"') == 0:
						name_list = name_string.split()
						name_tuple = sorted(tuple(set(name_list)),key=str.lower)
					else:
						while name_string.count('"') > 1:
							[first_part,name,second_part] = name_string.split('"',maxsplit=2)
							if DONT_IGNORE_ISSUE["LONG_NAMES"] and name.count(" ") > 4 or len(name) > 50:
								print(f"The name {name} seems to be rather long, is this intended?")
							name_list.append('"' + name.strip() + '"')
							name_string = first_part + " " + second_part
						name_list += name_string.split()
						name_tuple = sorted(tuple(set(name_list)),key=str.lower)
					if DONT_IGNORE_ISSUE["DUPLICATE_NAMES"] and len(name_tuple) != len(name_list):
						for name in name_tuple:
							name_list.remove(name)
						print(f"The culture {culture} has the following {new_entry} multiple times: {name_list}")
					if name_tuple:
						culture_dictionary[culture_group][culture][new_entry] = " "
				text = leftover
		# TODO maybe check the rest to see if brackets close properly and there is also nothing left otherwise.
	culture_set = set()
	for culture_group in culture_dictionary:
		if len(culture_dictionary[culture_group]) < 2: # standard_names is always added.
			print(f"The culture group {culture_group} has no cultures in it.")
		for culture in culture_dictionary[culture_group]:
			if culture != "standard_names":
				if culture in culture_set:
					print(f'The culture {culture} is in at least 2 different culture groups.')
				else:
					culture_set.add(culture)
				for name_type in ["male_names","female_names","dynasty_names"]:
					if name_type not in culture_dictionary[culture_group][culture] and name_type not in culture_dictionary[culture_group]["standard_names"]:
						print(f"Culture {culture} in culture group {culture_group} has neither a {name_type} list nor does the culture group have a default {name_type} list.")
	return culture_set

# Creates a set and a dictionary of the religions from all files in the common\religions folder.
def get_religions():
	religion_dictionary = dict()
	religion_set = set()
	COLOR_STRUCTURE = re.compile(r' color = \{ [0-1][.][0-9]{1,3} [0-1][.][0-9]{1,3} [0-1][.][0-9]{1,3} \}')
	OPTIONAL_COLOR_STRUCTURE = re.compile(r' color = \{ [0-9]{1,3} [0-9]{1,3} [0-9]{1,3} \}')
	MIXED_COLOR_STRUCTURE = re.compile(r'(?: color = \{ [0-1][.][0-9]{1,3} [0-1][.][0-9]{1,3} [0-1][.][0-9]{1,3} \})|(?: color = \{ [0-9]{1,3} [0-9]{1,3} [0-9]{1,3} \})')
	ICON_STRUCTURE = re.compile(r'(?=( icon = [0-9]{1,3} ))')
	for root, dirs, files in os.walk("common\\religions\\"):
		for file in files:
			path = os.path.join(root, file)
			text = format_text_in_path(path)
			if text == "  ":
				print(f"The file {path} is either empty or has only comments in it, why not remove it?")
				continue
			colors = re.findall(COLOR_STRUCTURE,text)
			optional_colors = re.findall(OPTIONAL_COLOR_STRUCTURE,text)
			mixed_colors = set()
			icons = re.findall(ICON_STRUCTURE,text)
			if len(colors) != len(icons) and len(optional_colors) != len(icons):
				if len(optional_colors) == 0:
					print('A different number of "icon = ?" and " color = { ? ? ? }" strings has been found in ' + f"{path}, specifically the icons:\n{icons}\nand colors:\n{colors}")
					return set()
				elif len(colors) == 0:
					print('A different number of "icon = ?" and " color = { ? ? ? }" strings has been found in ' + f"{path}, specifically the icons:\n{icons}\nand colors:\n{optional_colors}")
					return set()
				elif len(colors) + len(optional_colors) == len(icons):
					print(f"The color scheme is mixed, so some colors use the range from 0 to 1, while others are from 0 to 255 in {path}, you need to choose one scheme and convert the other:\n{colors}\nand:\n{optional_colors}")
					mixed_colors = re.findall(MIXED_COLOR_STRUCTURE,text)
					if len(mixed_colors) != len(icons):
						print(f"Please report that the mixed regex for religion colors is wrong, either as github issue or in the OpenVic discord.")
						return set()
					else:
						colors = mixed_colors
				else:
					print(f"The color scheme is mixed and the number of found icons does not match the colors as well in {path}, specifically the icons:\n{icons}\nand colors:\n{colors}\nand:\n{optional_colors}")
					return set()
			elif colors and optional_colors:
				print(f"When the colors for one scheme fit the number of icons, there should be none for the other in {path}:\n{colors}\nand:\n{optional_colors}")
				if len(optional_colors) == len(icons):
					colors = optional_colors
			elif optional_colors:
				colors = optional_colors
			if text.find("{") < 5:
				print(f"{path} should start with a religious group, but the first bracket comes too soon.")
				return set()
			last_closing_bracket = -1
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
							if ( k - last_closing_bracket ) < 6:
								print(f"When not inside brackets the first thing afterwards should be a religious group, but the first opening bracket in {path} comes too soon.")
								return set()
							if text[k-3:k] == " = ":
								religion_group = text[:k-3].rsplit(" ",maxsplit=1)[1]
								if religion_group in religion_dictionary:
									print(f"Duplicate religious group {religion_group} found in {path}")
								else:
									religion_dictionary[religion_group] = dict()
						elif counter == 1:
							if text[k-3:k] == " = ":
								religion = text[:k-3].rsplit(" ",maxsplit=1)[1]
						counter += 1
					elif text[k] == "}":
						counter -= 1
						last_closing_bracket = k
						if counter == 0:
							if religion_dictionary[religion_group] == dict():
								print(f"Religion group {religion_group} has no religions.")
							religion_group = ""
						elif counter == 1:
							religion = ""
						elif counter < 0:
							print(f"Brackets are wrong in {path} specifically around {text[max(k-20,0):min(k+20,len(text))]}")
				for k in range(mindex + 7,maxdex):
					if text[k] == "{":
						counter += 1
					elif text[k] == "}":
						counter -= 1
						if counter < 2:
							print(f"The religion {religion} lacks a color or an icon.")
							return set()
				if religion in religion_dictionary[religion_group]:
					print(f"Duplicate religion {religion} in religious group {religion_group} in {path}")
				else:
					icon = icons[i].split(" ")[3]
					color = tuple(colors[i].split(" ")[4:7])
					religion_dictionary[religion_group][religion] = dict()
					religion_dictionary[religion_group][religion]["icon"] = icon
					if len(optional_colors) == len(icons):
						if not all(0 <= int(RGB) < 256 for RGB in color):
							print(f"The color {color} for religion {religion} in {path} is not valid.")
					elif not mixed_colors:
						if not all(0 <= float(RGB) <= 1 for RGB in color):
							print(f"The color {color} for religion {religion} in {path} is not valid.")
					if religion in religion_set:
						print(f"Religion {religion} is in two different religious groups.")
					else:
						religion_set.add(religion)
				text = text[maxdex:]
			for k in range(len(text)):
				if text[k] == "{":
					if counter == 0:
						print(f"After the last icon and color another opening bracket exists in {path}")
					counter += 1
				elif text[k] == "}":
					counter -= 1
					if counter < 0:
						print(f"Brackets are wrong in {path} specifically around {text[max(k-20,0):min(k+20,len(text))]}")
			if counter != 0:
				print(f"Brackets are wrong and don't close properly at the end in {path}.")
	return religion_set

def get_governments():
	government_set = set()
	for root, dirs, files in os.walk("common\\governments\\"):
		for file in files:
			path = os.path.join(root, file)
			text = format_text_in_path(path)
			if text == "  ":
				print(f"The file {path} is either empty or has only comments in it, why not remove it?")
				continue
			while text.__contains__(" = {"):
				if text.startswith(" = {"):
					print(f'{path} ended up starting with " = {{" while being evaluated: {text[:99]}')
					return set()
				next_government = text.split(" = {",maxsplit=1)[0].rsplit(" ",maxsplit=1)[1]
				text = remove_text_between_brackets(text," " + next_government + " = {",path)
				if next_government != "pre_dharma_mapping":
					if next_government in government_set:
						print(f"The government {next_government} exists at least twice in the common\\governments files.")
					government_set.add(next_government)
			if text != "  ":
				print(f"After evaluating {path} there should be nothing left, but this is: {text[:99]}")
				return set()
	return government_set

def get_tech_groups():
	tech_group_set = set()
	if os.path.exists("common\\technology.txt"):
		text = format_text_in_path("common\\technology.txt")
		if text.count(" groups = {") != 1:
			print(f'There was more than one " groups = {{" string in the common\\technology.txt file.')
			return set()
		counter = 1
		text = text.split(" groups = {",maxsplit=1)[1]
		for i in range(len(text)):
			if text[i] == "{":
				counter += 1
				if counter == 2:
					technology_group = text[:i].rsplit(" =",maxsplit=1)[0].rsplit(" ",maxsplit=1)[1]
					if technology_group in tech_group_set:
						print(f"The technology group {technology_group} occurs twice in common\\technology.txt.")
					else:
						tech_group_set.add(technology_group)
			elif text[i] == "}":
				counter -= 1
				if counter == 0:
					break
	else:
		print(f"There is no technology.txt file in the common folder.")
	return tech_group_set

def check_definition_csv():
	not_more_than_once = True
	definitions_dictionary = dict()
	RGB_dictionary = dict()
	with open("map\\definition.csv",'r',encoding=ENCODING,errors='replace') as file:
		for line in file:
			if re.fullmatch("[1-9]",line[0]):
				[provinceID,red,green,blue] = line.split(";",maxsplit=4)[0:4]
				if not re.fullmatch("[0-9]+",provinceID):
					print(f"The province ID {provinceID} is not a valid number in map\\definition.csv")
				elif provinceID in definitions_dictionary:
					print(f"At least 2 lines start with the same number {provinceID} in map\\definition.csv")
				elif not (re.fullmatch("[0-9]+",red) and re.fullmatch("[0-9]+",green) and re.fullmatch("[0-9]+",blue)):
					print(f"One of the red, green or blue values is not a number in line {line.strip()} in map\\definition.csv")
				elif not ((int(red) < 256) and (int(green) < 256) and (int(blue) < 256)):
					print(f"The red, green and blue values have to be numbers from 0 to 255 in line {line.strip()} in map\\definition.csv")
				else:
					RGB = tuple((int(red),int(green),int(blue)))
					if RGB in RGB_dictionary:
						print(f"Another province was already assigned the same RGB value {RGB} as {provinceID} in map\\definition.csv")
					else:
						definitions_dictionary[provinceID] = RGB
						RGB_dictionary[RGB] = int(provinceID)
			elif not_more_than_once and (line[0] == "p"):
				not_more_than_once = False
			elif line[0] == "#":
				pass
			else:
				print(f"In map\\definition.csv this line has to change or be removed: {line.strip()}")
	image = Image.open("map\\provinces.bmp")
	pixel_set = set(color for count, color in image.getcolors(65536))
	provinces_on_the_map = { RGB_dictionary[RGB] for RGB in pixel_set if RGB in RGB_dictionary }
	return [definitions_dictionary,RGB_dictionary,pixel_set,provinces_on_the_map]

# gets all the text from ?.?.? = { text } for a specified date, including further occurances of it and returns them, but adds " # " between them or returns "#" if either the date entry is empty or none is found or an error occurs.
def get_date_text(text,date,path):
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
		else:
			print(f"There was no closing bracket after the date {date} in {path}")
			return "#"
		next_date = re.search(r'[^-0-9]' + date + " = {",text)
	date_text = " " + " ".join(date_text.split()) + " "
	if date_text == "  ":
		return "#"
	return date_text

# Removes all date entries from a file and replaces dates with " ## " so for example "text ?.?.? = { .{}{.}. } more text" will be turned into "text ## more text" or if an error is found into "#". This should work with any number of valid dates, including duplicates, as long as the brackets are correct.
def get_base_date_text(text,sorted_list,path):
	if not text.__contains__("{"):
		if text.__contains__("}"):
			print(f"There was no opening, but a closing bracket in {path}")
			return "#"
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
			else:
				print(f"There was no closing bracket after the date {date} in {path}")
				return "#"
			text = prior_text + " ## " + leftover
			next_date = re.search(r'[^-0-9]' + date + " = {",text)
	text = " " + " ".join(text.split()) + " "
	if text == "  ":
		return "#"
	return text

# Adds all valid dates of the form "years.months.days = {" from the text to the date_list, if they are not yet in it, which includes multiple functionally identical dates like 1.1.1 and 01.01.01 to use them for searching. While the 29th February does not exist in OpenVic and will be replaced with 28th February in the output files, it will still be added to the list, but a warning will be given. Then the dates get sorted, with the exception of functionally identical dates like 1.1.1 and 01.01.01 which stay in whatever order they happen to be found first.
def get_sorted_dates(text,path):
	date_list = []
	next_date = DATE_STRUCTURE.search(text)
	while "None" != str(next_date):
		date = next_date.group()[1:].split(" ")[0]
		[years,months,days] = date.split(".")
		text = text[next_date.end():]
		next_date = DATE_STRUCTURE.search(text)
		if "None" != str(next_date):
			counter = 1
			for i in range(len(text)):
				if text[i] == "{":
					counter += 1
				elif text[i] == "}":
					counter -= 1
					if counter == 0:
						if next_date.end() < i:
							print(f"There was a date within the date {date} in {path}")
							return "#"
						break
		if int(years) < 1 or int(years) > 65535:
			print(f"{date} is not a valid date as OpenVic does not support years beyond 1 to 65535 or 1 to 2^16 - 1: {path}")
			continue
		if int(months) < 1 or int(months) > 12 or int(days) < 1 or int(days) > 31:
			print(f"{date} is not a valid date in: {path}")
			continue
		if int(days) == 31:
			if int(months) == 4 or int(months) == 6 or int(months) == 9 or int(months) == 11:
				print(f"{date} is not a valid date in: {path}")
				continue
		if int(months) == 2:
			if int(days) == 29:
				if str(int(years)) + "." + str(int(months)) + ".28" == START_DATE:
					print(f"29th February is not a valid date in OpenVic, so if {date} is identical to the START_DATE you entered, which was changed to {START_DATE} instead, the date entry will not be applied. Found in: {path}")
				else:
					print(f"29th February is not a valid date in OpenVic, though {date} will still be applied. Found in: {path}")
			elif int(days) == 30 or int(days) == 31:
				print(f'{days}th February? Really? This "date" will be ignored, however this means whatever is within it will be applied with the other province entries not within a date. Found in: {path}')
				continue
		if date not in date_list:
			date_list.append(date)
		elif DONT_IGNORE_ISSUE["IDENTICAL_DATES"]:
			print(f"identical date: {date} found multiple times in: {path}")
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
			elif DONT_IGNORE_ISSUE["DUPLICATE_DATES"] and int(y) == int(Y) and int(m) == int(M) and int(d) == int(D) and (y != Y or m != M or d != D):
				print(f"The dates {entry} and {prior_date} are in the same file, which can cause problems as their history is applied in whatever order the dates are found, instead of together, found in: {path}")
		date_list.remove(prior_date)
		sorted_list.append(prior_date)
	sorted_list.reverse()
	sorted_list[sorted_list.index(START_DATE)] = "START_DATE"
	sorted_list.reverse()
	sorted_list.insert(0,"BASE_DATE")
	return sorted_list

# Checks country files in history\countries, their paths in common\country_tags and the files in common\countries.
def check_country_files():
	tag_dictionary = dict()
	path_dictionary = dict()
	capital_dictionary = dict()
	for root, dirs, files in os.walk("history\\countries\\"):
		for file in files:
			tag = file[:3]
			if re.fullmatch('[0-9A-Z]{3}',tag):
				if tag in tag_dictionary:
					print(f"Duplicate tag found in history\\countries: {tag}")
				else:
					tag_dictionary[tag] = "No path"
					if tag in ["REB","NAT","PIR"]:
						continue
			else:
				print(f"Filename does not start with a valid country tag: {file}")
				continue
			path = os.path.join(root, file)
			text = format_text_in_path(path)
			for character in [" monarch = {"," monarch_consort = {"," monarch_heir = {"," monarch_foreign_heir = {"," queen = {"," heir = {"," define_advisor = {"," leader = {"]:
				text = remove_text_between_brackets(text,character,path)
			sorted_list = get_sorted_dates(text,path)
			uniques = [[" government = ",""],[" primary_culture = ",""],[" religion = ",""],[" capital = ",""],[" technology_group = ",""]]
			accepted_culture_list = []
			added_accepted_culture_list = []
			removed_accepted_culture_list = []
			capital_dictionary[tag] = []
			for date in sorted_list:
				if date == "BASE_DATE":
					date_text = get_base_date_text(text,sorted_list,path)
				elif date == "START_DATE":
					for index in range(len(uniques)):
						if uniques[index][1] == "":
							print(f'No valid " {uniques[index][0].strip()}" string was found until the start date in {path}')
					if DONT_IGNORE_ISSUE["DATES_AFTER_START_DATE"]:
						continue
					break
				else:
					date_text = get_date_text(text,date,path)
				if date_text == "#":
					continue
				for index in range(len(uniques)):
					if DONT_IGNORE_ISSUE["MISSING_EMPTY_SPACE"] and str(re.search(r'[^ _a-zA-Z]' + uniques[index][0].strip(),date_text)) != "None":
						print(f'"{uniques[index][0].strip()}" entry may not be recognised as it does not have an empty space in front of it in {path}')
					counter = date_text.count(uniques[index][0])
					if counter > 1:
						print(f"{uniques[index][0].strip()} found {counter} times for date {date} in {path}")
						uniques[index][1] = ""
					if counter > 0:
						uniques[index][1] = date_text.split(uniques[index][0],maxsplit=1)[1].split(" ",maxsplit=1)[0]
						if index == 0:
							if uniques[index][1] not in GOVERNMENT_SET:
								print(f"Government {uniques[index][1]} in {path} was not found in the common\\governments files")
								uniques[index][1] = ""
						elif index == 1:
							if uniques[index][1] not in CULTURE_SET:
								print(f"Culture {uniques[index][1]} in {path} was not found in the common\\cultures files")
								uniques[index][1] = ""
						elif index == 2:
							if uniques[index][1] not in RELIGION_SET:
								print(f"Religion {uniques[index][1]} in {path} was not found in the common\\religions files")
								uniques[index][1] = ""
						elif index == 3:
							if re.fullmatch("[0-9]+",uniques[index][1]):
								capital_dictionary[tag].append(int(uniques[index][1]))
							else:
								print(f"The capital {uniques[index][1]} in {path} is not a number.")
						elif index == 4:
							if uniques[index][1] not in TECH_GROUP_SET:
								print(f"Technology group {uniques[index][1]} in {path} was not found in common\\technology.txt")
								uniques[index][1] = ""
				added_accepted_culture_list = []
				removed_accepted_culture_list = []
				add_culture_text = date_text # TODO maybe mention if an accepted culture is the primary culture
				while add_culture_text.__contains__(" add_accepted_culture = "):
					add_culture_text = add_culture_text.split(" add_accepted_culture = ",maxsplit=1)[1]
					[culture,add_culture_text] = add_culture_text.split(" ",maxsplit=1)
					add_culture_text = " " + add_culture_text
					if culture in CULTURE_SET:
						if culture in accepted_culture_list:
							if DONT_IGNORE_ISSUE["DUPLICATE_CULTURES"] and (culture not in added_accepted_culture_list):
								print(f"{culture} was already present as accepted culture for {date}, but added again in {path}")
						else:
							accepted_culture_list.append(culture)
						if culture in added_accepted_culture_list:
							if DONT_IGNORE_ISSUE["DUPLICATE_CULTURES"]:
								print(f"{culture} was already added as accepted culture for {date}, but added again in {path}")
						else:
							added_accepted_culture_list.append(culture)
					else:
						print(f"Invalid add_accepted_culture = {culture} found in {path}")
				remove_culture_text = date_text
				while remove_culture_text.__contains__(" remove_accepted_culture = "):
					remove_culture_text = remove_culture_text.split(" remove_accepted_culture = ",maxsplit=1)[1]
					[culture,remove_culture_text] = remove_culture_text.split(" ",maxsplit=1)
					remove_culture_text = " " + remove_culture_text
					if culture in CULTURE_SET:
						if culture in accepted_culture_list:
							accepted_culture_list.remove(culture)
						else:
							if DONT_IGNORE_ISSUE["REMOVE_NON_EXISTANT_CULTURE"] and (culture not in removed_accepted_culture_list):
								print(f"{culture} is not an accepted culture for {date}, but removed in {path}")
						if culture in removed_accepted_culture_list:
							if DONT_IGNORE_ISSUE["DUPLICATE_REMOVAL_CULTURE"]:
								print(f"{culture} was already removed as accepted culture for {date}, but removed again in {path}")
						else:
							removed_accepted_culture_list.append(culture)
						if culture in added_accepted_culture_list:
							print(f"{culture} is added and removed as accepted culture for {date} in {path}")
							added_accepted_culture_list.remove(culture)
					else:
						print(f"Invalid remove_accepted_culture = {culture} found for {date} in {path}")
	for root, dirs, files in os.walk("common\\country_tags\\"):
		for file in files:
			path = os.path.join(root, file)
			text = format_text_in_path(path)
			if text == "  ":
				print(f"The file {path} is either empty or has only comments in it, why not remove it?")
				continue
			for tag in tag_dictionary.keys():
				while text.__contains__(tag + ' = "countries/'):
					if tag_dictionary[tag] != "No path":
						print(f'{tag} = "countries/ is at least twice in the files in the common\\country_tags folder')
					[first,second] = text.split(tag + ' = "countries/',maxsplit=1)
					[country_path,second] = second.split('"',maxsplit=1)
					if country_path not in path_dictionary:
						tag_dictionary[tag] = country_path
						path_dictionary[country_path] = tag
					else:
						print(f"In common\\country_tags a path is used twice: {country_path}")
					text = first + second
			if "" != text.strip():
				print(f"There is no tag in history\\countries for some paths in {path} specifically the following are left: {text.strip()}")
	if "No path" in tag_dictionary.values():
		tags_without_path = []
		for tag in tag_dictionary:
			if tag_dictionary[tag] == "No path":
				tags_without_path.append(tag)
		print(f"No path has been set in common\\country_tags for these tags from history\\countries: {tags_without_path}")
	COLOR_STRUCTURE = re.compile(r" color = \{ (-?\d+) (-?\d+) (-?\d+) \}")
	for root, dirs, files in os.walk("common\\countries\\"):
		for file in files:
			if file not in path_dictionary:
				print(f"{file} in common\\countries is not used as path in common\\country_tags by any of the tags in history\\countries or some other error occured")
			path = os.path.join(root, file)
			text = format_text_in_path(path)
			colors = re.findall(COLOR_STRUCTURE,text)
			if len(colors) != 1:
				print(f"The country in {path} has either no color or multiple.")
			elif not all(0 <= int(RGB) < 256 for RGB in colors[0]):
				print(f"The color for country in {path} is invalid {colors[0]}.")
			if text.count(" graphical_culture =") != 1:
				print(f"The country in {path} has either no graphical culture or multiple.")
	missing_paths = []
	for path in tag_dictionary.values():
		if path != "No path" and not os.path.exists("common\\countries\\" + path):
			missing_paths.append(path)
	if missing_paths:
		print(f"These paths have not been found: {missing_paths}")
	tag_set = set(tag_dictionary.keys())
	return [tag_set,capital_dictionary]

def check_terrain():
	text = format_text_in_path("map\\terrain.txt")
	if text.count(" categories = {") != 1:
		print(f'In map\\terrain.txt are either no or multiple occurances of " categories = {{".')
		return [dict(),set()]
	if text.count(" terrain = {") != 1:
		print(f'In map\\terrain.txt are either no or multiple occurances of " terrain = {{".')
		return [dict(),set()]
	terrain = get_text_between_brackets(text," categories = {","map\\terrain.txt")
	terrain_index = get_text_between_brackets(text," terrain = {","map\\terrain.txt")
	terrain_index_list = terrain_index.split()
	if terrain.count(" pti = { type = pti } ") == 1:
		terrain = " ".join(terrain.split(" pti = { type = pti } ",maxsplit=1))
	else:
		print(f'The " pti = {{ type = pti }} " part does not exist exactly once in map\\terrain.txt.')
		return [dict(),set()]
	terrain_list = terrain.split(" = {")
	province_terrain_dictionary = dict()
	terrain_override_provinces = set()
	while len(terrain_list) > 1:
		current_terrain = terrain_list[0].rsplit(" ",maxsplit=1)[1]
		province_terrain_dictionary[current_terrain] = dict()
		terrain_list.remove(terrain_list[0])
		current_terrain_text_list = []
		while terrain_list[0].rsplit(" ",maxsplit=1)[1] in ["color","terrain_override"]:
			if terrain_list[0].rsplit(" ",maxsplit=1)[1] == "color":
				if "color" in province_terrain_dictionary[current_terrain]:
					print(f"The terrain {current_terrain} has at least 2 colors.")
				province_terrain_dictionary[current_terrain]["color"] = terrain_list[1].split("}",maxsplit=1)[0]
			else:
				if "terrain_override" in province_terrain_dictionary[current_terrain]:
					print(f"The terrain {current_terrain} has at least 2 terrain_override parts.")
				additional_override = set(map(int,terrain_list[1].split("}",maxsplit=1)[0].split())) & PROVINCES_ON_THE_MAP
				province_terrain_dictionary[current_terrain]["terrain_override"] = additional_override
				for prov in additional_override:
					if prov in terrain_override_provinces:
						print(f"The province {prov} in the terrain override of {current_terrain} is already used in another terrain override.")
				terrain_override_provinces = terrain_override_provinces.union(additional_override)
			current_terrain_text_list.append(terrain_list[0].strip())
			terrain_list.remove(terrain_list[0])
		if "color" not in province_terrain_dictionary[current_terrain]:
			print(f"The terrain {current_terrain} has no color.")
		current_terrain_text = " " + " ".join(current_terrain_text_list) + " "
		for terrain_modifier in [" supply_limit = "," movement_cost = "," combat_width = "," defence = "]:
			if current_terrain_text.count(terrain_modifier) == 1:
				terrain_modifier_value = current_terrain_text.split(terrain_modifier,maxsplit=1)[1].split(" ",maxsplit=1)[0]
				if terrain_modifier == " supply_limit = ":
					if not (re.fullmatch("[1-9][0-9]?",terrain_modifier_value) or re.fullmatch("[1-9][0-9]?[.][0-9]{0,2}",terrain_modifier_value)):
						print(f"The{terrain_modifier}{terrain_modifier_value} for the terrain {current_terrain} might be incorrect.")
				elif terrain_modifier == " movement_cost = ":
					if not (re.fullmatch("[1-9]",terrain_modifier_value) or re.fullmatch("[0-9][.][0-9]{0,3}",terrain_modifier_value)):
						print(f"The{terrain_modifier}{terrain_modifier_value} for the terrain {current_terrain} might be incorrect.")
					elif float(terrain_modifier_value) == 0:
						print(f"The{terrain_modifier}{terrain_modifier_value} for the terrain {current_terrain} should not be 0.")
				elif terrain_modifier == " combat_width = ":
					if not re.fullmatch("-[0][.][0-9]{0,2}",terrain_modifier_value):
						print(f"The{terrain_modifier}{terrain_modifier_value} for the terrain {current_terrain} might be incorrect.")
					elif float(terrain_modifier_value) < -0.8:
						print(f"The{terrain_modifier}{terrain_modifier_value} for the terrain {current_terrain} is very small.")
				elif terrain_modifier == " defence = ":
					if not re.fullmatch("-?[0-6]",terrain_modifier_value):
						print(f"The{terrain_modifier}{terrain_modifier_value} for the terrain {current_terrain} might be incorrect.")
			elif current_terrain_text.count(terrain_modifier) > 1:
				print(f"The terrain {current_terrain} has multiple{terrain_modifier}occurances.")
			elif DONT_IGNORE_ISSUE["MISSING_TERRAIN_MODIFIER"] and (current_terrain not in ["ocean","inland_ocean"] and current_terrain not in TERRAIN_DICTIONARY["FORCE_INLAND_OCEAN"]):
				print(f"The terrain {current_terrain} does not have the terrain modifier {terrain_modifier.strip().split()[0]}.")
	if len(terrain_index_list) % 12 != 0:
		print(f"There seems to be a mistake in map\\terrain.txt in the terrain = {{ part:")
		for i in range(0,len(terrain_index_list),12):
			print(f"{" ".join(terrain_index_list[i:i+12])}")
	else:
		index_set = set()
		terrain_pixel_set = set(color for count, color in Image.open("map\\terrain.bmp").getcolors())
		for i in range(0,len(terrain_index_list),12):
			wrong_structure = False
			if terrain_index_list[i + 1] != "=": wrong_structure = True
			elif terrain_index_list[i + 2] != "{": wrong_structure = True
			elif terrain_index_list[i + 3] != "type": wrong_structure = True
			elif terrain_index_list[i + 4] != "=" : wrong_structure = True
			elif terrain_index_list[i + 6] != "color": wrong_structure = True
			elif terrain_index_list[i + 7] != "=" : wrong_structure = True
			elif terrain_index_list[i + 8] != "{": wrong_structure = True
			elif terrain_index_list[i + 10] != "}": wrong_structure = True
			elif terrain_index_list[i + 11] != "}": wrong_structure = True
			if wrong_structure:
				print(f"There is an error in map\\terrain.txt in the terrain = {{ part, specifically here: {" ".join(terrain_index_list[i:i+12])}")
				break
			if terrain_index_list[i + 5] not in province_terrain_dictionary:
				print(f"In map\\terrain.txt in the terrain = {{ part a terrain type is not specified in the terrain categories, specifically here: {" ".join(terrain_index_list[i:i+12])}")
			if terrain_index_list[i + 5] == "ocean":
				if str(TERRAIN_DICTIONARY["OCEAN_INDEX"]) != terrain_index_list[i + 9]:
					print(f"The terrain index {terrain_index_list[i + 9]} is type = ocean, but you entered the index: {TERRAIN_DICTIONARY["OCEAN_INDEX"]}")
			if terrain_index_list[i + 5] == "inland_ocean":
				if str(TERRAIN_DICTIONARY["INLAND_OCEAN_INDEX"]) != terrain_index_list[i + 9]:
					print(f"The terrain index {terrain_index_list[i + 9]} is type = inland_ocean, but you entered the index: {TERRAIN_DICTIONARY["INLAND_OCEAN_INDEX"]}")
			if not re.fullmatch("[0-9]{1,3}",terrain_index_list[i + 9]):
				print(f"The index {terrain_index_list[i + 9]} for terrain {terrain_index_list[i + 5]} is not a valid integer value")
			elif int(terrain_index_list[i + 9]) in index_set:
				print(f"In map\\terrain.txt in the terrain = {{ part, the color index {terrain_index_list[i + 9]} is used twice, specifically here: {" ".join(terrain_index_list[i:i+12])}")
			elif int(terrain_index_list[i + 9]) in terrain_pixel_set and int(terrain_index_list[i + 9]) >= max(2, min(8, ATLAS_SIZE[0])) * max(2, min(8, ATLAS_SIZE[1])) and terrain_index_list[i + 5] not in ["ocean","inland_ocean"]:
				print(f'You need to either add {terrain_index_list[i + 9]} to the ATLAS_DICTIONARY in the mod converter with an "atlas_index" value below {max(2, min(8, ATLAS_SIZE[0])) * max(2, min(8, ATLAS_SIZE[1]))} as there is no square for the terrain {terrain_index_list[i + 5]} in the map\\terrain\\atlas0.dds file or change the texturesheet.tga after the conversion.')
				index_set.add(int(terrain_index_list[i + 9]))
			else:
				index_set.add(int(terrain_index_list[i + 9]))
		if terrain_pixel_set - index_set:
			print(f"At least one index is in the terrain image, but not in the map\\terrain.txt terrain = {{ part,specifically: {terrain_pixel_set - index_set}.")
	return [province_terrain_dictionary,terrain_override_provinces]

def check_province_files():
	province_set = set()
	empty_province_files_set = set()
	for root, dirs, files in os.walk("history\\provinces\\"):
		for file in files:
			path = os.path.join(root, file)
			if not re.fullmatch("[1-9]",file[0]):
				print(f"Province file name does not start with a number from 1 to 9 in {path}")
				continue
			province_ID = int(re.match("[0-9]+", file).group())
			if province_ID not in province_set:
				province_set.add(province_ID)
			else:
				print(f'At least 2 files have the same province ID "{province_ID}" in history\\provinces.')
			text = format_text_in_path(path)
			if text == "  ":
				empty_province_files_set.add(province_ID)
				continue
			sorted_list = get_sorted_dates(text,path)
			province_is_empty = check_date_entries(text,sorted_list,path)
			if province_is_empty:
				empty_province_files_set.add(province_ID)
	province_tuple = tuple(sorted(province_set, key=int))
	counter = 0
	for province in province_tuple:
		counter += 1
		if province != counter:
			if DONT_IGNORE_ISSUE["MISSING_PROVINCE_ID"]:
				print(f"No province file found for: {counter} until {province}")
			for index in range(counter,province):
				empty_province_files_set.add(index)
			counter = province
	return [province_set,empty_province_files_set]

# Checks if dates contain obvious mistakes like cultures that don't exist in the culture files.
def check_date_entries(text,sorted_list,path):
	unique_dictionary = {" culture = ":0," religion = ":0," owner = ":0," controller = ":0," trade_goods = ":0," base_tax = ":0," base_production = ":0," base_manpower = ":0}
	current_cores = []
	added_cores = []
	removed_cores = []
	is_empty = True
	for date in sorted_list:
		if date == "BASE_DATE":
			date_text = get_base_date_text(text,sorted_list,path)
		elif date == "START_DATE":
			if unique_dictionary[" culture = "] != unique_dictionary[" religion = "]:
				print(f"Only the culture or religion, but not both are present for the start date in {path}")
			if unique_dictionary[" owner = "] != unique_dictionary[" controller = "]:
				print(f"Province has only an owner or a controller, but not both at the start date in {path}")
			if (unique_dictionary[" owner = "] == 1) and (unique_dictionary[" trade_goods = "] == 0):
				print(f"Province has an owner, but no trade good at the start date in {path}")
			if not (unique_dictionary[" base_tax = "] == unique_dictionary[" base_production = "] == unique_dictionary[" base_manpower = "]):
				print(f"The province lacks 1 or 2 of the base tax, production or manpower at the start date in {path}")
			if DONT_IGNORE_ISSUE["DATES_AFTER_START_DATE"]:
				continue
			break
		else:
			date_text = get_date_text(text,date,path)
		if date_text == "#":
			continue
		for unique_entry in unique_dictionary:
			counter = date_text.count(unique_entry)
			if counter > 1:
				is_empty = False
				print(f'"{unique_entry}" found {counter} times for date {date} in {path}')
				unique_dictionary[unique_entry] = 1
			elif counter == 1:
				is_empty = False
				unique_dictionary[unique_entry] = 1
				if unique_entry != " trade_goods = ":
					unique = date_text.split(unique_entry,maxsplit=1)[1].split(" ",maxsplit=1)[0]
					if unique_entry == " culture = ":
						if unique == "no_culture":
							print(f"culture = no_culture will not generate pops. Found for date {date} in {path}")
						elif unique not in CULTURE_SET:
							print(f"Culture {unique} in {path} was not found in the common\\cultures files")
					elif unique_entry == " religion = ":
						if unique == "no_religion":
							print(f"religion = no_religion will not generate pops. Found for date {date} in {path}")
						elif unique not in RELIGION_SET:
							print(f"Religion {unique} in {path} was not found in the common\\religions files")
					elif unique_entry in [" owner = "," controller = "]:
						if unique not in TAG_SET and unique != "---":
							print(f"The tag for {unique_entry.strip()} {unique} in {path} was not found in the history\\countries files")
					elif unique_entry in [" base_tax = "," base_production = "," base_manpower = "]:
						if not re.fullmatch("[0-9]+",unique):
							print(f"{unique_entry.strip()} {unique} in {path} is not an integer")
			if DONT_IGNORE_ISSUE["MISSING_EMPTY_SPACE"] and str(re.search(r'[^ _a-zA-Z]' + unique_entry.strip(),date_text)) != "None":
				print(f"{unique_entry.strip()} entry may not be recognised as it does not have an empty space in front of it in {path}")
		added_cores = []
		removed_cores = []
		core_text = date_text
		while core_text.__contains__(" add_core = "):
			is_empty = False
			core_text = core_text.split(" add_core = ",maxsplit=1)[1]
			tag = str(core_text)[:3]
			if tag in TAG_SET:
				if tag in current_cores:
					if DONT_IGNORE_ISSUE["DUPLICATE_CORES"] and (tag not in added_cores):
						print(f"{tag} core is already present for {date}, but added again in {path}")
				else:
					current_cores.append(tag)
				if tag in added_cores:
					if DONT_IGNORE_ISSUE["DUPLICATE_CORES"]:
						print(f"{tag} core was already added for {date}, but added again in {path}")
				else:
					added_cores.append(tag)
			else:
				print(f"Invalid add_core = {tag} found in {path}")
		remove_core_text = date_text
		while remove_core_text.__contains__(" remove_core = "):
			is_empty = False
			remove_core_text = remove_core_text.split(" remove_core = ",maxsplit=1)[1]
			tag = str(remove_core_text)[:3]
			if tag in TAG_SET:
				if tag in current_cores:
					current_cores.remove(tag)
				else:
					if DONT_IGNORE_ISSUE["REMOVE_NON_EXISTANT_CORE"] and (tag not in removed_cores):
						print(f"{tag} core is not present for {date}, but removed in {path}")
				if tag in added_cores:
					print(f"{tag} is added and removed for {date} in {path}")
				if tag in removed_cores and (tag not in removed_cores):
					if DONT_IGNORE_ISSUE["DUPLICATE_REMOVAL_CORE"]:
						print(f"{tag} core was already removed for {date}, but removed again in {path}")
				else:
					removed_cores.append(tag)
			else:
				print(f"Invalid remove_core = {tag} found for {date} in {path}")
	return is_empty

def check_continents():
	text = format_text_in_path("map\\continent.txt")
	continent_list = []
	continent_name_set = set()
	while text.__contains__("= {"):
		[continent_name,text] = text.split("= {",maxsplit=1)
		[provinces,text] = text.split("}",maxsplit=1)
		provinces = set(map(int,provinces.split())) & PROVINCES_ON_THE_MAP
		continent_name = continent_name.strip()
		if (not provinces) or continent_name == "island_check_provinces":
			continue
		continent_name_set.add(continent_name)
		continent_list.append([continent_name,provinces])
		for entry in provinces:
			if DONT_IGNORE_ISSUE["MISSING_PROVINCE_FILE"] and entry not in PROVINCE_SET:
				print(f"No province file with the ID {entry} exists, but the province is on the continent: {continent_name}")
			for i in range(len(continent_list) - 1):
				if entry in continent_list[i][1]:
					print(f"Province {entry} is already on the continent {continent_list[i][0]}, but also on the continent {continent_name}")
	combined_continent_set = set().union(*(provinces for continent_name, provinces in continent_list))
	if len(continent_list) > 6:
		print("OpenVic only supports 6 continents in the UI, so while it will work when there are more, there wont be any functional buttons for them in some windows. Until support for this gets added, you will have to combine continents. Of course you can just generate the output and merge the continents there instead or ignore this problem.")
	text = format_text_in_path("map\\default.map")
	ocean = text.split("sea_starts = {",maxsplit=1)[1].split("}",maxsplit=1)[0]
	ocean = set(map(int,ocean.split())) & PROVINCES_ON_THE_MAP
	for entry in ocean:
		if DONT_IGNORE_ISSUE["MISSING_PROVINCE_FILE"] and entry not in PROVINCE_SET:
			print(f"No province file with the ID {entry} exists, but the province is an ocean province.")
		if entry in combined_continent_set:
			print(f"Province {entry} is already on a continent, but also an ocean.")
	lakes = text.split("lakes = {",maxsplit=1)[1].split("}",maxsplit=1)[0]
	lakes = set(map(int,lakes.split())) & PROVINCES_ON_THE_MAP
	water_provinces = ocean.union(lakes)
	for entry in lakes:
		if DONT_IGNORE_ISSUE["MISSING_PROVINCE_FILE"] and entry not in PROVINCE_SET:
			print(f"No province file with the ID {entry} exists, but the province is a lake province.")
		if entry in combined_continent_set:
			print(f"Province {entry} is already on a continent, but also a lake.")
		if entry in ocean:
			print(f"Province {entry} is already an ocean, but also a lake.")
	leftover_provinces = (PROVINCE_SET & PROVINCES_ON_THE_MAP) - combined_continent_set - ocean - lakes
	if leftover_provinces:
		print(f"Some provinces are neither a part of a continent, ocean or lake: {leftover_provinces}")
	inland_ocean = lakes.copy()
	for terrain in TERRAIN_DICTIONARY["FORCE_INLAND_OCEAN"]:
		if "terrain_override" in PROVINCE_TERRAIN_DICTIONARY[terrain]:
			inland_ocean = inland_ocean.union(PROVINCE_TERRAIN_DICTIONARY[terrain]["terrain_override"])
			water_provinces = water_provinces.union(PROVINCE_TERRAIN_DICTIONARY[terrain]["terrain_override"])
			combined_continent_set = combined_continent_set.difference(PROVINCE_TERRAIN_DICTIONARY[terrain]["terrain_override"])
	for terrain in PROVINCE_TERRAIN_DICTIONARY:
		if "terrain_override" in PROVINCE_TERRAIN_DICTIONARY[terrain]:
			if terrain in ["ocean","inland_ocean"] or terrain in TERRAIN_DICTIONARY["FORCE_INLAND_OCEAN"]:
				if PROVINCE_TERRAIN_DICTIONARY[terrain]["terrain_override"] - water_provinces:
					print(f"Some provinces are neither ocean, lake or forced ocean, but in the override of terrain {terrain}, specifically: {PROVINCE_TERRAIN_DICTIONARY[terrain]["terrain_override"] - water_provinces}")
			elif PROVINCE_TERRAIN_DICTIONARY[terrain]["terrain_override"] - combined_continent_set:
				print(f"Some provinces are not continental, but in the override of terrain {terrain}, which is supposed to be continental, specifically: {PROVINCE_TERRAIN_DICTIONARY[terrain]["terrain_override"] - combined_continent_set}")
	if {capital for capital_list in CAPITAL_DICTIONARY.values() for capital in capital_list}.difference(combined_continent_set):
		for tag in TAG_SET:
			if tag in CAPITAL_DICTIONARY:
				if set(CAPITAL_DICTIONARY[tag]) - combined_continent_set:
					print(f"At least one capital in the history of tag {tag} is not continental or the province simply does not exist on the map, for example due to a wrong RGB value: {set(CAPITAL_DICTIONARY[tag]) - combined_continent_set}.")
	if water_provinces - EMPTY_PROVINCE_FILES_SET:
		print(f"These water provinces have some entries in their files: {water_provinces - EMPTY_PROVINCE_FILES_SET}")
	image = Image.open("map\\provinces.bmp")
	w,h = image.size
	load_province_bmp = image.load()
	if text.count(" max_provinces = ") != 1:
		print('Either " max_provinces = " does not exist in the map\\default.map file or it appears multiple times.')
	else:
		max_provinces = text.split(" max_provinces = ",maxsplit=1)[1].split(" ",maxsplit=1)[0]
		if not re.fullmatch("[0-9]+",max_provinces):
			print(f"In map\\default.map max_provinces = {max_provinces} is not an integer value.")
		elif len(PIXEL_SET) >= int(max_provinces):
			print(f"The max_provinces value {max_provinces} in the map\\default.map should be at least 1 higher than the number of different colors in the province.bmp {len(PIXEL_SET)}.")
		elif int(max_provinces) >= 65536:
			print(f"OpenVic does not yet support more than 65536 provinces and this script will mention a lot of false positives, if there are more unique colors in the province.bmp.")
	tiny_province_color_set = set()
	for count, color in image.getcolors(65536):
		if MIN_PROVINCE_SIZE > count:
			tiny_province_color_set.add(color)
			print(f"The province with color {color} has only {count} pixel{'s' * (count != 1)}.")
		if MAX_PROVINCE_SIZE < count:
			print(f"The province with color {color} has {count} pixels, which could cause problems in V2, though feel free to ignore this until you actually see it cause problems at which point the province simply needs to be split into multiple smaller ones.")
	if tiny_province_color_set:
		for x in range(w):
			for y in range(h):
				if load_province_bmp[x,y] in tiny_province_color_set:
					print(f"The pixel {x},{y} with color {load_province_bmp[x,y]} belongs to a tiny province.")
	province_colors_are_in_definition_csv = True
	if PIXEL_SET.difference(RGB_DICTIONARY.keys()):
		province_colors_are_in_definition_csv = False
		print(f"These colors are in the provinces.bmp, but not in the defintion.csv {PIXEL_SET.difference(RGB_DICTIONARY.keys())}")
		for x in range(w):
			for y in range(h):
				if load_province_bmp[x,y] not in RGB_DICTIONARY:
					print(f"The color at {x},{y} in the provinces.bmp is not in the map\\definition.csv")
	adjacency_dictionary = defaultdict(set)
	terrain = Image.open("map\\terrain.bmp").copy()
	terrain_w,terrain_h = terrain.size
	if terrain_w != w or terrain_h != h:
		print(f"The width and/or height of the provinces.bmp {w},{h} and terrain.bmp {terrain_w},{terrain_h} are not equal, which also means it wont be checked whether some terrain pixels are ocean or not while the province itself is continental or not.")
	else:
		wrong_water_terrain = set()
		wrong_land_terrain = set()
		WATER_INDEX = {TERRAIN_DICTIONARY["OCEAN_INDEX"],TERRAIN_DICTIONARY["INLAND_OCEAN_INDEX"]}
		if province_colors_are_in_definition_csv:
			for x in range(w):
				for y in range(h):
					for dx, dy in [(0,1),(1,0)]:
						nx, ny = x + dx, y + dy
						if 0 <= nx < w and 0 <= ny < h:
							if load_province_bmp[x,y] != load_province_bmp[nx,ny]:
								adjacency_dictionary[RGB_DICTIONARY[load_province_bmp[x,y]]].add(RGB_DICTIONARY[load_province_bmp[nx,ny]])
								adjacency_dictionary[RGB_DICTIONARY[load_province_bmp[nx,ny]]].add(RGB_DICTIONARY[load_province_bmp[x,y]])
			load_terrain_image = terrain.load()
			for x in range(w):
				for y in range(h):
					if load_terrain_image[x,y] in WATER_INDEX:
						if RGB_DICTIONARY[load_province_bmp[x,y]] not in water_provinces:
							if DONT_IGNORE_ISSUE["INDIVIDUAL_PIXELS"]:
								print(f"The color {load_province_bmp[x,y]} at {x},{y} is for a province on a continent, but the terrain is water.")
							if DONT_IGNORE_ISSUE["INCORRECT_TERRAIN"]:
								load_terrain_image[x,y] = TERRAIN_DICTIONARY["CONTINENTAL_INDEX"]
							wrong_water_terrain.add(RGB_DICTIONARY[load_province_bmp[x,y]])
						elif DONT_IGNORE_ISSUE["INCORRECT_TERRAIN"]:
							if TERRAIN_DICTIONARY["FORCE_INLAND_OCEAN"]:
								if RGB_DICTIONARY[load_province_bmp[x,y]] in inland_ocean:
									load_terrain_image[x,y] = TERRAIN_DICTIONARY["INLAND_OCEAN_INDEX"]
								else:
									load_terrain_image[x,y] = TERRAIN_DICTIONARY["OCEAN_INDEX"]
					else:
						if RGB_DICTIONARY[load_province_bmp[x,y]] in water_provinces:
							if DONT_IGNORE_ISSUE["INDIVIDUAL_PIXELS"]:
								print(f"The color {load_province_bmp[x,y]} at {x},{y} is for a province in an ocean or lake, but the terrain is not.")
							if DONT_IGNORE_ISSUE["INCORRECT_TERRAIN"]:
								if RGB_DICTIONARY[load_province_bmp[x,y]] in ocean and RGB_DICTIONARY[load_province_bmp[x,y]] not in inland_ocean:
									load_terrain_image[x,y] = TERRAIN_DICTIONARY["OCEAN_INDEX"]
								else:
									load_terrain_image[x,y] = TERRAIN_DICTIONARY["INLAND_OCEAN_INDEX"]
							wrong_land_terrain.add(RGB_DICTIONARY[load_province_bmp[x,y]])
			rivers = Image.open("map\\rivers.bmp").copy()
			rivers_w,rivers_h = rivers.size
			if w != rivers_w or h != rivers_h:
				print(f"The width and/or height of the provinces.bmp and the rivers.bmp are different.")
			elif DONT_IGNORE_ISSUE["INCORRECT_TERRAIN"]:
				load_rivers_bmp = rivers.load()
				for x in range(w):
					for y in range(h):
						if load_rivers_bmp[x,y] > 253:
							if load_terrain_image[x,y] in WATER_INDEX:
								load_rivers_bmp[x,y] = 254
							else:
								load_rivers_bmp[x,y] = 255
				rivers.save("map\\rivers2.bmp")
				if DONT_IGNORE_ISSUE["COAST_NOT_COASTAL"]:
					for x in range(w):
						for y in range(h):
							if load_terrain_image[x,y] not in WATER_INDEX:
								is_coastal = False
								for a in [-1,0,1]:
									for b in [-1,0,1]:
										if 0 <= x + a < w and 0 <= y + b < h:
											if load_terrain_image[x+a,y+b] in WATER_INDEX:
												is_coastal = True
								if is_coastal:
									load_terrain_image[x,y] = TERRAIN_DICTIONARY["COASTAL_INDEX"]
								elif load_terrain_image[x,y] == TERRAIN_DICTIONARY["COASTAL_INDEX"]:
									load_terrain_image[x,y] = TERRAIN_DICTIONARY["CONTINENTAL_INDEX"]
				terrain.save("map\\terrain2.bmp")
			if wrong_water_terrain:
				print(f"If no map issues are mentioned above this message you can create the terrain.bmp and rivers.bmp files with correct pixels. Some terrain.bmp pixels are water, but their provinces are not ocean or lakes: {wrong_water_terrain}")
			if wrong_land_terrain:
				print(f"If no map issues are mentioned above this message you can create the terrain.bmp and rivers.bmp files with correct pixels. Some terrain.bmp pixels are not water, but their provinces are ocean or lakes: {wrong_land_terrain}")
		else:
			print("Whether some Terrain pixels are water or not, while the province it belongs to is the other could not be checked due to colors in the provinces.bmp that are not in the definition.csv and many adjacency issues will also not give a warning.")
	text = format_text_in_path("map\\climate.txt")
	impassable = set()
	while text.__contains__(" = {"):
		[climate_name,text] = text.split(" = {",maxsplit=1)
		[provinces,text] = text.split("}",maxsplit=1)
		if provinces == " ":
			continue
		climate_name = climate_name.rsplit(" ",maxsplit=1)[1]
		provinces = set(map(int,provinces.split())) & PROVINCES_ON_THE_MAP
		for entry in provinces:
			if DONT_IGNORE_ISSUE["MISSING_PROVINCE_FILE"] and entry not in PROVINCE_SET:
				print(f"No province file with the ID {entry} exists, but the province has the climate: {climate_name}")
			if DONT_IGNORE_ISSUE["OCEAN_AND_LAKE_CLIMATE"] and entry in ocean:
				print(f"Province {entry} is an ocean, but also has the climate {climate_name}.")
			if DONT_IGNORE_ISSUE["OCEAN_AND_LAKE_CLIMATE"] and entry in lakes:
				print(f"Province {entry} is a lake, but also has the climate {climate_name}.")
		if climate_name == "impassable":
			impassable = provinces
	if impassable:
		for tag in TAG_SET:
			if tag in CAPITAL_DICTIONARY:
				if not set(CAPITAL_DICTIONARY[tag]).isdisjoint(impassable):
					print(f"At least one capital in the history of tag {tag} is impassable: {set(CAPITAL_DICTIONARY[tag]).intersection(impassable)}.")
	if DONT_IGNORE_ISSUE["NO_TERRAIN_OVERRIDE"]:
		leftover_provinces = combined_continent_set - TERRAIN_OVERRIDE_PROVINCES - ocean - lakes
		if leftover_provinces:
			print(f"The following provinces are continental and don't use terrain_override: {leftover_provinces}")
	if impassable - EMPTY_PROVINCE_FILES_SET:
		print(f"The following impassable provinces do not have empty province files: {impassable - EMPTY_PROVINCE_FILES_SET}")
	return [continent_name_set,combined_continent_set,ocean,lakes,impassable,water_provinces,adjacency_dictionary]

def check_adjacencies():
	csv_adjacency_dictionary = defaultdict(set)
	with open("map\\adjacencies.csv",'r',encoding=ENCODING,errors='replace') as file:
		for line in file:
			if re.fullmatch("[1-9]",line[0]):
				[From,To,Type,Through] = line.split(";",maxsplit=4)[0:4]
				if not (re.fullmatch("[0-9]+",From) and re.fullmatch("[0-9]+",To) and (re.fullmatch("[0-9]+",Through) or Through == "-1")):
					print(f"At least one of the province IDs {From} or {To} or {Through} contains something else than numbers, for example empty spaces are not allowed by my script, in map\\adjacencies.csv: {line.strip()}")
					continue
				From,To,Through = map(int,(From,To,Through))
				if (From == To) or (From not in PROVINCES_ON_THE_MAP) or (To not in PROVINCES_ON_THE_MAP):
					print(f"From and To are equal or at least one is not on the map in map\\adjacencies.csv: {line.strip()}")
					continue
				if Type not in ["sea","","canal","land","lake","river"]:
					print(f"Invalid adjacency type {Type}: {line.strip()}.")
				elif Type == "sea":
					if From not in COMBINED_CONTINENT_SET or To not in COMBINED_CONTINENT_SET:
						print(f"The adjaceny type is sea, but {From} or {To} or both are not continental in map\\adjacencies.csv: {line.strip()}")
					elif DONT_IGNORE_ISSUE["THROUGH_NOT_IN_OCEAN"] and (Through not in OCEAN_SET and Through != -1):
						print((f"The adjaceny type is sea, but {Through} is neither an ocean nor -1 in map\\adjacencies.csv: {line.strip()}"))
				elif Type == "land":
					if From not in COMBINED_CONTINENT_SET or To not in COMBINED_CONTINENT_SET:
						print(f"The adjaceny type is land, but {From} or {To} or both are not continental in map\\adjacencies.csv: {line.strip()}")
					elif not(Through in COMBINED_CONTINENT_SET or Through in IMPASSABLE_SET) and Through != -1:
						print((f"The adjaceny type is land, but {Through} is not continental or impassable in map\\adjacencies.csv: {line.strip()}"))
				elif Type != "canal":
					if From not in COMBINED_CONTINENT_SET or To not in COMBINED_CONTINENT_SET:
						print(f"The adjaceny type isn't canal, but {From} or {To} or both are not continental in map\\adjacencies.csv: {line.strip()}")
				if From in IMPASSABLE_SET or From in LAKES_SET or To in IMPASSABLE_SET or To in LAKES_SET:
					print(f"Either {From} or {To} or both are impassable/lake provinces in map\\adjacencies.csv: {line.strip()}")
				elif (From not in COMBINED_CONTINENT_SET and From not in OCEAN_SET) or (To not in COMBINED_CONTINENT_SET and To not in OCEAN_SET):
					print(f"Either {From} or {To} or both are neither continental nor ocean nor impassbable nor lake, in map\\adjacencies.csv: {line.strip()}")
				elif (From in OCEAN_SET) != (To in OCEAN_SET):
					print(f"{From} or {To} is ocean, but the other is not in map\\adjacencies.csv: {line.strip()}")
				elif (From in COMBINED_CONTINENT_SET) != (To in COMBINED_CONTINENT_SET):
					print(f"{From} or {To} is continental, but the other is not in map\\adjacencies.csv: {line.strip()}")
				elif ADJACENCY_DICTIONARY:
					if Through != -1 and not(From in ADJACENCY_DICTIONARY[Through] and To in ADJACENCY_DICTIONARY[Through]):
						if Type != "canal" or DONT_IGNORE_ISSUE["CANAL_NOT_MUTUAL_NEIGHBOUR"]:
							print(f"{From} or {To} or both are not next to {Through} in map\\provinces.bmp, if there are mutual neighbours they are {ADJACENCY_DICTIONARY[From].intersection(ADJACENCY_DICTIONARY[To])}: {line.strip()}")
					if From in ADJACENCY_DICTIONARY[To]:
						print(f"The provinces {From} and {To} are already adjacent due to neighbouring pixels: {line.strip()}")
					if From in csv_adjacency_dictionary[To]:
						print(f"The adjacency between {From} and {To} is added at least twice in map\\adjacencies.csv: {line.strip()}")
					else:
						csv_adjacency_dictionary[From].add(To)
						csv_adjacency_dictionary[To].add(From)
			elif line.strip() == "" or line.strip()[0] == "#" or line[0:6] == "-1;-1;" or line[0:8] == "From;To;":
				pass
			else:
				print(f"In map\\adjacencies.csv this line has to change or will be ignored by the mod converter, as the first character is not a number from 1 to 9: {line.strip()}")
	return

def check_area():
	combined_area_province_set = set()
	area_set = set()
	text = format_text_in_path("map\\area.txt")
	text_list = text.split(" = {")
	area_name = text_list[0].strip()
	text_list.remove(text_list[0])
	for entry in text_list:
		area_province_set = set(map(int,entry.split("}",maxsplit=1)[0].split())) & PROVINCES_ON_THE_MAP
		if area_name in area_set:
			print(f"At least 2 areas have the same name: {area_name}")
		elif area_province_set:
			area_set.add(area_name)
		for province in area_province_set:
			if province in combined_area_province_set:
				print(f"The province {province} is already in another area.")
			elif province in IMPASSABLE_SET:
				print(f"The province {province} is impassable and should not be in an area.")
			elif province in LAKES_SET:
				print(f"The province {province} is a lake and should not be in an area.")
			else:
				combined_area_province_set.add(province)
		area_name = entry.split("}",maxsplit=1)[1].strip()
	if COMBINED_CONTINENT_SET - combined_area_province_set - IMPASSABLE_SET:
		print(f"Some continental provinces are not in an area: {COMBINED_CONTINENT_SET - combined_area_province_set - IMPASSABLE_SET}")
	return area_set

def check_positions():
	unimportant = (0,0,0)
	if unimportant in PIXEL_SET:
		for b in range(256):
			for g in range(256):
				for r in range(6,256):
					if (r,g,b) not in PIXEL_SET:
						unimportant = (r,g,b)
						break
				if unimportant not in PIXEL_SET:
					break
			if unimportant not in PIXEL_SET:
				break
	ocean = (0,0,1)
	if ocean in PIXEL_SET:
		for r in range(4):
			for g in range(256):
				for b in range(2,256):
					if (r,g,b) not in PIXEL_SET:
						ocean = (r,g,b)
						break
				if ocean not in PIXEL_SET:
					break
			if ocean not in PIXEL_SET:
				break
	if unimportant == ocean or ocean in PIXEL_SET or unimportant in PIXEL_SET:
		print(f'A mod with over 65536 Provinces wont work.')
		return
	OCEAN_RGB_SET = set()
	for provinceID in OCEAN_SET:
		if str(provinceID) in DEFINITIONS_DICTIONARY:
			OCEAN_RGB_SET.add(DEFINITIONS_DICTIONARY[str(provinceID)])
		else:
			print(f"The province ID {provinceID} is not found in the map\\definition.csv file or it's color is already used by another province, but it is an ocean.")
	UNIMPORTANT_RGB_SET = set()
	for provinceID in LAKES_SET:
		if str(provinceID) in DEFINITIONS_DICTIONARY:
			UNIMPORTANT_RGB_SET.add(DEFINITIONS_DICTIONARY[str(provinceID)])
		else:
			print(f"The province ID {provinceID} is not found in the map\\definition.csv file or it's color is already used by another province, but it is a lake.")
	for provinceID in IMPASSABLE_SET:
		if str(provinceID) in DEFINITIONS_DICTIONARY:
			UNIMPORTANT_RGB_SET.add(DEFINITIONS_DICTIONARY[str(provinceID)])
		else:
			print(f"The province ID {provinceID} is not found in the map\\definition.csv file or it's color is already used by another province, but it is impassable.")
	positions = format_text_in_path("map\\positions.txt")
	image_load_original = Image.open("map\\provinces.bmp").load()
	image = Image.open("map\\provinces.bmp").copy()
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
	coastal_pixel_set = set(color for count, color in image.getcolors(65536))
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
		else:
			print(f"Due to the brackets being wrong no province ID could be found in {provinceID}")
			continue
		if int(provinceID) in IMPASSABLE_SET or int(provinceID) in LAKES_SET or int(provinceID) in OCEAN_SET or int(provinceID) not in PROVINCES_ON_THE_MAP:
			continue
		[city_x,city_y,unit_x,unit_y,name_x,name_y,port_x,port_y,positions] = positions.split(" ",maxsplit=8)
		if int(float(city_x)) < 0 or int(float(city_y)) < 0 or int(float(city_x)) >= w or int(float(city_y)) >= h:
			if DONT_IGNORE_ISSUE["CITY_POSITION_OUTSIDE_BMP"]:
				print(f"The city position {city_x},{city_y} for province {provinceID} is outside the provinces.bmp with size {w},{h}.")
			city_x = city_y = -1
		if int(float(unit_x)) < 0 or int(float(unit_y)) < 0 or int(float(unit_x)) >= w or int(float(unit_y)) >= h:
			if DONT_IGNORE_ISSUE["UNIT_POSITION_OUTSIDE_BMP"]:
				print(f"The unit position {unit_x},{unit_y} for province {provinceID} is outside the provinces.bmp with size {w},{h}.")
			unit_x = unit_y = -1
		if int(float(name_x)) < 0 or int(float(name_y)) < 0 or int(float(name_x)) >= w or int(float(name_y)) >= h:
			if DONT_IGNORE_ISSUE["NAME_POSITION_OUTSIDE_BMP"]:
				print(f"The name position {name_x},{name_y} for province {provinceID} is outside the provinces.bmp with size {w},{h}.")
			name_x = name_y = -1
		if int(float(port_x)) < 0 or int(float(port_y)) < 0 or int(float(port_x)) >= w or int(float(port_y)) >= h:
			print(f"The port position {port_x},{port_y} for province {provinceID} is outside the provinces.bmp with size {w},{h}.")
			continue
		if provinceID not in DEFINITIONS_DICTIONARY:
			print(f"The province ID {provinceID} is not found in the map\\definition.csv file or it's color is already used by another province, but a position for it exists.")
			continue
		if DONT_IGNORE_ISSUE["CITY_POSITION"] and city_x != -1 and city_y != -1:
			if image_load_original[int(float(city_x)),int(h-1 - float(city_y))] != DEFINITIONS_DICTIONARY[provinceID]:
				print(f"The rounded position {int(float(city_x))},{int(float(city_y))} of the city model, which is {int(float(city_x))},{int(h-1 - float(city_y))} when opening the bmp with GIMP, for province {provinceID} is not within the province itself.")
		if DONT_IGNORE_ISSUE["UNIT_POSITION"] and unit_x != -1 and unit_y != -1:
			if image_load_original[int(float(unit_x)),int(h-1 - float(unit_y))] != DEFINITIONS_DICTIONARY[provinceID]:
				print(f"The rounded position {int(float(unit_x))},{int(float(unit_y))} of the unit model, which is {int(float(unit_x))},{int(h-1 - float(unit_y))} when opening the bmp with GIMP, for province {provinceID} is not within the province itself.")
		if DONT_IGNORE_ISSUE["NAME_POSITION"] and name_x != -1 and name_y != -1:
			if image_load_original[int(float(name_x)),int(h-1 - float(name_y))] != DEFINITIONS_DICTIONARY[provinceID]:
				print(f"The rounded position {int(float(name_x))},{int(float(name_y))} of the province name, which is {int(float(name_x))},{int(h-1 - float(name_y))} when opening the bmp with GIMP, for province {provinceID} is not within the province itself.")
		if DEFINITIONS_DICTIONARY[provinceID] not in coastal_pixel_set:
			continue
		port_x = int(float(port_x))
		port_y = int(h-1 - float(port_y))
		coastal_nearby = False
		ocean_nearby = False
		for x in range(-2,3):
			for y in range(-2,3):
				if image_load[max(0,min(w-1,port_x+x)),max(0,min(h-1,port_y+y))] == DEFINITIONS_DICTIONARY[provinceID]:
					coastal_nearby = True
				if image_load[max(0,min(w-1,port_x+x)),max(0,min(h-1,port_y+y))] == ocean:
					ocean_nearby = True
				if coastal_nearby and ocean_nearby:
					break
			if coastal_nearby and ocean_nearby:
				break
		if not coastal_nearby and ocean_nearby:
			print(f"There is no coastal province pixel within a 2 pixel radius of the rounded port position {port_x},{h-1-port_y} for province {provinceID}, which would be {port_x},{port_y} in GIMP, if the province is not supposed to have a port, some stray pixel is somewhere next to an ocean.")
		if coastal_nearby and not ocean_nearby:
			print(f"There is no ocean province pixel within a 2 pixel radius of the rounded port position {port_x},{h-1-port_y} for province {provinceID}, which would be {port_x},{port_y} in GIMP, if the province is not supposed to have a port, some stray pixel is somewhere next to an ocean.")
		if not coastal_nearby and not ocean_nearby:
			print(f"There is neither a coastal nor an ocean province pixel within a 2 pixel radius of the rounded port position {port_x},{h-1-port_y} for province {provinceID}, which would be {port_x},{port_y} in GIMP, if the province is not supposed to have a port, some stray pixel is somewhere next to an ocean.")
		if coastal_nearby and ocean_nearby:
			if image_load[port_x,port_y] not in {DEFINITIONS_DICTIONARY[provinceID],ocean}:
				print(f"The rounded port position {port_x},{h-1-port_y} for province {provinceID}, which would be {port_x},{port_y} in GIMP is neither a coastal nor an ocean pixel, if the province is not supposed to have a port, some stray pixel is somewhere next to an ocean.")
	return

def check_localisation():
	localisation_dictionary = dict()
	for tag in TAG_SET:
		if tag not in {"REB","NAT","PIR"}:
			localisation_dictionary[tag] = 0
			localisation_dictionary[tag + "_ADJ"] = 0
	for area in AREA_SET:
		if area in localisation_dictionary:
			print(f"Both an area and a tag or tag adjective are called {area}.")
		else:
			localisation_dictionary[area] = 0
	for province in (PROVINCE_SET & PROVINCES_ON_THE_MAP):
		if "PROV" + str(province) in localisation_dictionary:
			print(f"Both an area and a province are called {province}.")
		else:
			localisation_dictionary["PROV" + str(province)] = 0
	for culture in CULTURE_SET:
		if culture in localisation_dictionary:
			print(f"The culture {culture} is already used for other localisation, likely an area, less likely a TAG, TAG_ADJ or PROV?.")
		else:
			localisation_dictionary[culture] = 0
	for religion in RELIGION_SET:
		if religion in localisation_dictionary:
			print(f"The religion {religion} is already used for other localisation, likely a culture or area, less likely a TAG, TAG_ADJ or PROV?.")
		else:
			localisation_dictionary[religion] = 0
	for government in GOVERNMENT_SET:
		if government + "_name" in localisation_dictionary:
			print(f"The government {government + "_name"} is already used for other localisation, maybe a culture, religion or area already has the same name.")
		else:
			localisation_dictionary[government + "_name"] = 0
	for continent in CONTINENT_NAME_SET:
		if continent in localisation_dictionary:
			print(f"The continent {continent} is already used for other localisation, maybe a culture, religion or area already has the same name.")
		else:
			localisation_dictionary[continent] = 0
	for tech_group in TECH_GROUP_SET:
		if tech_group in localisation_dictionary:
			print(f"The technology group {tech_group} is already used for other localisation, maybe a culture, religion, area, government, continent or less likely a TAG, TAG_ADJ or PROV? already has the same name.")
		else:
			localisation_dictionary[tech_group] = 0
	for terrain in set(PROVINCE_TERRAIN_DICTIONARY.keys()) - {"ocean","inland_ocean"}:
		if terrain in localisation_dictionary:
			print(f"The terrain {terrain} is already used for other localisation, maybe a culture, religion, area, government, continent, technology group or less likely a TAG, TAG_ADJ or PROV? already has the same name.")
		else:
			localisation_dictionary[terrain] = 0
		if terrain + "_desc" in localisation_dictionary:
			print(f"The terrain description {terrain}_desc is already used for other localisation, maybe a culture, religion, area, government, continent, technology group or less likely a TAG, TAG_ADJ or PROV? already has the same name.")
		else:
			localisation_dictionary[terrain + "_desc"] = 0
	THESE_KEYS_CAN_MISS = {"monarchy_name","theocracy_name","republic_name","native_name","tribal_name","europe","asia","africa","north_america","south_america","oceania","new_world"}
	for language in LANGUAGES:
		l_language_yml = "_l_" + language + ".yml"
		typo_language_yml = "_I_" + language + ".yml"
		language_dictionary = localisation_dictionary.copy()
		for root, dirs, files in os.walk("localisation\\"):
			for file in files:
				if file.__contains__(l_language_yml):
					with open(os.path.join(root, file),'r',encoding="utf-8-sig",errors='replace') as loc:
						for line in loc:
							if line.__contains__("�"):
								print(f"A character with wrong encoding was found in line {line} in file {os.path.join(root, file)}")
							if line.__contains__(':'):
								[key,value] = line.split(':',maxsplit=1)
								if not value.__contains__('"'):
									continue
								if value.count('"') < 2:
									print(f'There is only one " behind the : in the line ({line.strip()}) in file {os.path.join(root, file)}')
									continue
								if key.strip() in language_dictionary:
									language_dictionary[key.strip()] += 1
									value = value.split('"',maxsplit=1)[1].rsplit('"',maxsplit=1)[0].replace('\\"','"')
									if not value:
										print(f"The localisation is empty in the line ({line.strip()}) in file {os.path.join(root, file)}.")
									if key.__contains__(";"):
										print(f'Victoria 2 separates localisation with ";" so this character can not be used in the line ({line.strip()}) in file {os.path.join(root, file)}.')
									elif value.__contains__(";"):
										print(f'Victoria 2 separates localisation with ";" so this character can not be used in the line ({line.strip()}) in file {os.path.join(root, file)}.')
									if value.__contains__("§"):
										print(f'Victoria 2 may allow this, but my script wont check "§" colors yet, in the line ({line.strip()}) in file {os.path.join(root, file)}.')
									if "$" in value or "[" in value or "]" in value or "£" in value or "\\" in value:
										print(f"The special meaning of some characters may not be preserved in Victoria 2 in the line ({line.strip()}) in file {os.path.join(root, file)}.")
									# TODO find out if there are more EU4 specific localisation functions.
				elif file.__contains__(typo_language_yml):
					print(f"The file name should contain a lower L not an upper i in file {os.path.join(root, file)}")
		for key in language_dictionary:
			if language_dictionary[key] != 1:
				if language_dictionary[key] == 0 and (key not in THESE_KEYS_CAN_MISS or language not in {"english","french","german","polish","spanish"}):
					print(f"The language {language} has no localisation for {key} in the localisation folder.")
				elif language_dictionary[key] > 1:
					print(f"The language {language} has {language_dictionary[key]} localisations for {key} in the localisation folder.")
	if not LANGUAGES:
		print(f"No languages were entered, so no checks were made.")
	return

def check_rivers():
	image = Image.open("map\\rivers.bmp").copy()
	w,h = image.size
	load_bmp = image.load()
	for x in range(w):
		for y in range(h):
			if load_bmp[x,y] == 0:
				started_from_index = 0
				current_river_pixel = (x,y)
				river_source = current_river_pixel
				check_for_more = True
				tributary_rivers = []
				while check_for_more:
					if 14 < load_bmp[current_river_pixel] < 254:
						print(f'You need to add "{load_bmp[current_river_pixel]}:22" to the RIVER_DICTIONARY when using the mod converter or change the pixel at {current_river_pixel} to another index')
					load_bmp[current_river_pixel] = 255
					(a,b) = current_river_pixel
					counter = 0
					tributary_rivers_counter = 0
					for dx, dy in [(0,-1),(0,1),(-1,0),(1,0)]:
						nx, ny = a + dx, b + dy
						if 0 <= nx < w and 0 <= ny < h:
							if 2 < load_bmp[nx,ny] < 254:
								counter += 1
								current_river_pixel = (nx,ny)
							elif 0 < load_bmp[nx,ny] < 3:
								tributary_rivers.append((nx,ny))
								tributary_rivers_counter += 1
								if river_source == (a,b):
									print(f"{a},{b} a tributary or distributary river starts right next to another tributary or distributary river or a river source.")
							elif 0 == load_bmp[nx,ny]:
								print(f"{nx},{ny} the river starting here is connected to another starting point.")
					if counter == 1:
						pass
					elif counter > 1:
						if started_from_index != 0 and (abs(river_source[0]-a) + abs(river_source[1]-b)) <= 1:
							print(f"{a},{b} a river should only have a single source/green pixel attached to it, all the rivers merging into it should not have one, but one of the rivers here seems to have this problem.")
							if (abs(river_source[0]-a) + abs(river_source[1]-b)) == 1:
								load_bmp[a,b] = 3 # Going in from a tributary or distributary river would cut a river in half, so it has to be reconnected again.
							if tributary_rivers:
								current_river_pixel = tributary_rivers[0]
								river_source = current_river_pixel
								started_from_index = load_bmp[current_river_pixel]
								tributary_rivers.remove(tributary_rivers[0])
							else:
								check_for_more = False
						else:
							print(f"{current_river_pixel} has 3 nearby river pixels or 2 and a green start position.")
							tributary_rivers.append((a,b))
					else:
						for tr_counter in range(tributary_rivers_counter):
							if 1 == started_from_index == (load_bmp[tributary_rivers[len(tributary_rivers) - 1 - tr_counter]]):
								print(f"{tributary_rivers[len(tributary_rivers) - 1 - tr_counter]} both the start and end point of the tributary river are merged into another river.")
							elif 2 == started_from_index == (load_bmp[tributary_rivers[len(tributary_rivers) - 1 - tr_counter]]):
								print(f"{tributary_rivers[len(tributary_rivers) - 1 - tr_counter]} both the start and end point of the distributary river are split from another river.")
						if tributary_rivers:
							current_river_pixel = tributary_rivers[0]
							river_source = current_river_pixel
							started_from_index = load_bmp[current_river_pixel]
							tributary_rivers.remove(tributary_rivers[0])
						else:
							check_for_more = False
	for x in range(w):
		for y in range(h):
			if load_bmp[x,y] < 254:
				print(f"{x},{y} is part of a river that either lacks a source or is not properly connected with the main river, the pixel could be very far away from the actually intended source and the river itself will not be properly checked either due to the possibility of generating a lot of false positive issues, so you need to run the script again after fixing it.")
				if 14 < load_bmp[x,y]:
					print(f'You need to add ",{load_bmp[x,y]}:22" to the RIVER_DICTIONARY when using the mod converter or change the pixel at {x},{y} to another index')
				check_for_more = True
				current_river_pixel = (x,y)
				tributary_rivers = []
				while check_for_more:
					if 14 < load_bmp[current_river_pixel] < 254:
						print(f'You need to add ",{load_bmp[current_river_pixel]}:22" to the RIVER_DICTIONARY when using the mod converter or change the pixel at {current_river_pixel} to another index')
					load_bmp[current_river_pixel] = 255
					(a,b) = current_river_pixel
					counter = 0
					for dx, dy in [(0,-1),(0,1),(-1,0),(1,0)]:
						nx, ny = a + dx, b + dy
						if 0 <= nx < w and 0 <= ny < h:
							if load_bmp[nx,ny] < 254:
								counter += 1
								current_river_pixel = (nx,ny)
					if counter == 1:
						pass
					elif counter > 1:
						tributary_rivers.append((a,b))
					elif tributary_rivers:
						current_river_pixel = tributary_rivers[0]
						tributary_rivers.remove(tributary_rivers[0])
					else:
						check_for_more = False
	return

def check_gfx():
	terrain_w,terrain_h = Image.open("map\\terrain.bmp").size
	if os.path.exists("map\\terrain\\colormap_spring.dds"):
		w,h = Image.open("map\\terrain\\colormap_spring.dds").size
		if terrain_w % w != 0:
			print(f"The width of the terrain.bmp is not a multiple of the width of the colormap_spring.dds, while not necessary the result will probably look worse than if it was.")
		if terrain_h % h != 0:
			print(f"The height of the terrain.bmp is not a multiple of the height of the colormap_spring.dds, while not necessary the result will probably look worse than if it was.")
	else:
		print(f"There is no map\\terrain\\colormap_spring.dds image.")
	if os.path.exists("map\\terrain\\colormap_water.dds"):
		w,h = Image.open("map\\terrain\\colormap_water.dds").size
		if terrain_w % w != 0:
			print(f"The width of the terrain.bmp is not a multiple of the width of the colormap_water.dds, while not necessary the result will probably look worse than if it was.")
		if terrain_h % h != 0:
			print(f"The height of the terrain.bmp is not a multiple of the height of the colormap_water.dds, while not necessary the result will probably look worse than if it was.")
	else:
		print(f"There is no map\\terrain\\colormap_water.dds image.")
	if os.path.exists("gfx\\interface\\icon_religion_small.dds"):
		religion_dds = Image.open("gfx\\interface\\icon_religion_small.dds")
		w,h = religion_dds.size
		if h != 32:
			print(f"The height of the icon_religion_small.dds is not 32.")
		if w % h != 0:
			print(f"The width of the icon_religion_small.dds is not a multiple of the height.")
	else:
		print(f"There is no icon_religion_small.dds in gfx\\interface\\.")
	for tag in TAG_SET - {"REB","NAT","PIR"}:
		if os.path.exists("gfx\\flags\\" + tag + ".tga"):
			w,h = Image.open("gfx\\flags\\" + tag + ".tga").size
			if DONT_IGNORE_ISSUE["WRONG_PICTURE_SIZE"] and not 128 == w == h:
				print(f"The flag {tag}.tga does not have the size 128 x 128.")
		elif DONT_IGNORE_ISSUE["MISSING_FLAGS"]:
			print(f"There is no flag for {tag}.")
	w,h = Image.open(ATLAS_PATH).size
	if not (ATLAS_SIZE[0] in [2,3,4,5,6,7,8] and ATLAS_SIZE[1] in [2,3,4,5,6,7,8]):
		print(f"The ATLAS_SIZE {ATLAS_SIZE} you entered is not within the accepted limit.")
	elif w % ATLAS_SIZE[0] != 0 or h % ATLAS_SIZE[1] != 0 or w % ATLAS_SIZE[0] != h % ATLAS_SIZE[1]:
		print(f"The size {w},{h} of {ATLAS_PATH} is either not a multiple of the size {ATLAS_SIZE} you entered or the ratio is not equal.")
	terrain_set = set(PROVINCE_TERRAIN_DICTIONARY.keys())
	picture_set = set()
	for root, dirs, files in os.walk("gfx\\interface\\"):
		for file in files:
			if file.startswith("colony_terrain_"):
				w,h = Image.open(os.path.join(root, file)).size
				if DONT_IGNORE_ISSUE["WRONG_PICTURE_SIZE"] and (w,h) != (330,85):
					print(f"{os.path.join(root, file)} does not have the size 330,85")
				if not file.endswith(".dds"):
					print(f"{os.path.join(root, file)} is not a .dds file")
					continue
				terrain = file.split("colony_terrain_",maxsplit=1)[1].rsplit(".dds",maxsplit=1)[0]
				if terrain in terrain_set:
					terrain_set.remove(terrain)
				elif terrain in PROVINCE_TERRAIN_DICTIONARY:
					print(f"I am aware that terrain and pictures are connected in the interface files, but for now i simply match them through their name. There are at least 2 pictures named after terrain {terrain}, one at {os.path.join(root, file)}")
				else:
					picture_set.add(terrain)
	if terrain_set - {"ocean","inland_ocean"} - set(TERRAIN_DICTIONARY["FORCE_INLAND_OCEAN"]):
		print(f"I am aware that terrain and pictures are connected in the interface files, but for now i simply match them through their name. Some terrain does not have a picture with an identical name in the gfx\\interface folder, so for conversion to function you need to COPY AND rename the intended picture, do NOT just rename it, the old picture is required for EU4 after all, specifically: {terrain_set - {"ocean","inland_ocean"} - set(TERRAIN_DICTIONARY["FORCE_INLAND_OCEAN"])}")
	if picture_set and terrain_set - {"ocean","inland_ocean"} - set(TERRAIN_DICTIONARY["FORCE_INLAND_OCEAN"]):
		print(f"There are pictures for at least one terrain without an identically named terrain in map\\terrain.txt, specifically: {picture_set}. You can ignore this warning, but it is mentioned in case a terrain misses a picture due to using one with a slightly different name, so you can easily find the likely intended ones that you have to copy and rename.")
	return

if not I_READ_THE_INSTRUCTIONS:
	print("READ AND FOLLOW THE INSTRUCTIONS AT THE START OF THE FILE! For some mods you still have to make minimal changes yourself.")
else:
	START_DATE = verify_date(START_DATE)
	CULTURE_SET = get_cultures()
	RELIGION_SET = get_religions()
	GOVERNMENT_SET = get_governments()
	TECH_GROUP_SET = get_tech_groups()
	[DEFINITIONS_DICTIONARY,RGB_DICTIONARY,PIXEL_SET,PROVINCES_ON_THE_MAP] = check_definition_csv()
	if CULTURE_SET and RELIGION_SET and GOVERNMENT_SET and TECH_GROUP_SET:
		DATE_STRUCTURE = re.compile(r'[^-0-9]-?[0-9]{1,5}[.][0-9]{1,2}[.][0-9]{1,2} = {')
		[TAG_SET,CAPITAL_DICTIONARY] = check_country_files()
		[PROVINCE_TERRAIN_DICTIONARY, TERRAIN_OVERRIDE_PROVINCES] = check_terrain()
		[PROVINCE_SET,EMPTY_PROVINCE_FILES_SET] = check_province_files()
		[CONTINENT_NAME_SET,COMBINED_CONTINENT_SET,OCEAN_SET,LAKES_SET,IMPASSABLE_SET,WATER_PROVINCES_SET,ADJACENCY_DICTIONARY] = check_continents()
		check_adjacencies()
		AREA_SET = check_area()
		check_positions()
		PROVINCE_SET = PROVINCE_SET.union(COMBINED_CONTINENT_SET,WATER_PROVINCES_SET)
		check_localisation()
		check_rivers()
		check_gfx()
	else:
		if not CULTURE_SET:
			print(f"No cultures could be found in the common\\cultures folder.")
		if not RELIGION_SET:
			print(f"No religions could be found in the common\\religions folder.")
		if not GOVERNMENT_SET:
			print(f"No governments could be found in the common\\governments folder.")
		if not TECH_GROUP_SET and os.path.exists("common\\technology.txt"):
			print(f"No technology groups could be found in common\\technology.txt.")
#%%
