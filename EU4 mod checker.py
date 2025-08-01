#%%
# Place this Python script into whatever mod folder you want to check. The mod needs to have the common/countries, common/country_tags, common/cultures, common/religions, common/governments, history/countries and history/provinces folders and map/area.txt, map/climate.txt, map/continent.txt, map/definition.csv and map/default.map files as well as the provinces.bmp, rivers.bmp and terrain.bmp. If those are not present, either because the mod uses the base game files or relies on another mod you have to copy them or can't use this script.
from PIL import Image
import re
import os
# This mod_specific_values function is the only parts of the script you might need to change, just follow the instructions.
def mod_specific_values():
	START_DATE = "1444.11.11" # Replace 1444.11.11 with the intended start date in the form years.months.days, unless it would either be a 29th February as those do neither exist in OpenVic nor Victoria 2 and will be replaced with 28th February and for OpenVic it must be a date within the range -32768.1.1 to 32767.12.31 or if the output is intended for Victoria 2, i assume dates must be after 1.1.1 or even later, but i am not sure about the exact details. Any input that is not valid will be replaced with 1444.11.11. The history will be applied until the start date, including identical dates like 01444.11.11 and error messages will be shown, for example if the province has only a religion or culture, but not both at the start date.
	ENCODING = "utf-8" # Change this to whatever the encoding of the mod is, most likely it is either "utf-8" or "windows-1252". If it is mixed and you want to be able to automatically convert the mod to an OpenVic mod, you currently would have to pick one and convert the files with the other encoding.
	WATER_INDEX = {15,17} # Replace these numbers, if the mod changes the default EU4 index values for the ocean and inland ocean, which can be found in the map/terrain.txt by looking at the type = ocean/inland_ocean { color = { ?? } } at the end of the file or map/terrain.bmp for example by using GIMP and selecting an ocean/inland_ocean pixel with the color picker which will show the index.
	DONT_IGNORE_ISSUE = { # Not all issues cause trouble when generating output files, so you can choose to ignore them, though in some cases you really should check them.
		"INDIVIDUAL_PIXELS":False, # Some provinces will be assigned to a continent, while some of their pixels in the terrain.bmp are for oceans/in the WATER_INDEX, while other provinces are assigned as ocean or lake in the default.map file, but have pixels that are continental/not in the WATER_INDEX. The province IDs with such wrong pixels will be shown regardless of whether this option is False or True, but setting this option to True will also show all individual wrong pixels, which can easily cause tens of thousands of lines mentioning wrong pixels.
		"DATES_AFTER_START_DATE":True, # If you only care about mistakes that happen until the START_DATE, set this to False.
		"MISSING_EMPTY_SPACE":True, # For example "add_core =" is searched as " add_core =" instead, as if it always had an empty space in front of it, which the formatting also inserts before and after "=", "{", "}" and the at the start and end of the text itself, as well as any time some parts get removed like date entries or put together like duplicate date entries. However there could be situations where EU4 does not actually require an empty space in front of it, for example 'capital = "?"add_core', which this script would not recognise as a core being added, so you should check all these warnings.
		"IDENTICAL_DATES":True, # This mentions if one date appears multiple times in the same file, but their entries get combined anyway, so you can ignore this, if you don't want to combine the entries.
		"DUPLICATE_DATES":True, # 1.1.1 and 01.01.01 entries do not get combined and are applied in whatever order they are found first, so you have to check those.
		"DUPLICATE_NAMES":True, # Sometimes the male, female or dynasty names lists can contain duplicates, which does nothing, so you can ignore this, if you don't want to remove them.
		"DUPLICATE_CORES":True, # Sometimes cores that already exist are added again, which does nothing, so you can ignore this, if you don't want to remove such duplicates.
		"DUPLICATE_REMOVAL_CORE":True, # Cores may be removed twice for the same date, which does nothing, so you can ignore this.
		"REMOVE_NON_EXISTANT_CORE":True, # Sometimes cores are removed even though they were not present at this date. So maybe some other core was actually supposed to be removed.
		"DUPLICATE_CULTURES":True, # Sometimes accepted cultures are added again, which does nothing, so you can ignore this.
		"DUPLICATE_REMOVAL_CULTURE":True, # Cultures may be removed twice for the same date, which does nothing, so you can ignore this.
		"REMOVE_NON_EXISTANT_CULTURE":True, # Sometimes cultures are removed as accepted cultures, even though they were not accepted at this date. So maybe some other culture was actually supposed to be removed.
		"MISSING_PROVINCE_FILE":True, # Some provinces may be placed on a continent or such, but lack a province file, can be ignored as an empty "provinceID.txt" file will simply be generated anyway for the output.
		"MISSING_PROVINCE_ID":True, # While it is not necessary to use all numbers between 1 and the number of provinces as IDs, maybe you still want to add empty files for such cases, if not you can set it to False.
		"NAME_POSITION":False # The position of the name could be outside of the province, though this currently does not matter for conversion to a Victoria 2 mod.
	}
	I_READ_THE_INSTRUCTIONS = False # Set this to True after changing all the settings you need to change or want to change and that's it. Now you can run it, if you have a sufficiently new Python version installed. Maybe anything after 3.7 will work, as well as a new enough Pillow version (Python Imaging Library).
	return [START_DATE,ENCODING,WATER_INDEX,DONT_IGNORE_ISSUE,I_READ_THE_INSTRUCTIONS]

# TODO check if ocean/lake files are empty, if bmps have correct indexes.
# formats a text file when given the path.
def format_text_in_path(path,ENCODING):
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
			if counter == 1:
				print(f"1 character with wrong encoding found in file: {file.name} specifically � in:")
			else:
				print(f"{counter} characters with wrong encoding found in file: {file.name} specifically � for example in:")
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
	if years < -32768 or years > 32767:
		print(f"{date} is not a valid date as OpenVic does not support years beyond -32768 to 32767 or -2^15 to 2^15 - 1. Sucks for Warhammer 40k fans.")
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
	text = " " + " ".join(text.split()) + " "
	return text

# creates a set of all cultures and a dictionary {culture_group:{culture:{male_names:" ",female_names:" ",dynasty_names:" "}}}
def get_cultures(ENCODING,DONT_IGNORE_ISSUE):
	culture_dictionary = dict()
	for root, dirs, files in os.walk("common/cultures"):
		for file in files:
			text = format_text_in_path(os.path.join(root, file),ENCODING)
			if text == "  ":
				print(f"The file common/cultures/{file} is either empty or has only comments in it, why not remove it?")
				continue
			male_names_count = text.count(" male_names = {")
			female_names_count = text.count(" female_names = {")
			dynasty_names_count = text.count(" dynasty_names = {")
			text = remove_text_between_brackets(text," country = {","common/cultures/" + file)
			text = remove_text_between_brackets(text," province = {","common/cultures/" + file)
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
					print(f'Correct the brackets in common/cultures/{file}. The file ended up starting with " = {{" while being evaluated: {text[:99]}')
					return [dict(),set()]
				[prior_text,leftover] = text.split(" = {",maxsplit=1)
				counter = 1 + counter + prior_text.count("{") - prior_text.count("}") # TODO let it count per character to see if the counter ever gets completely wrong
				new_entry = prior_text.rsplit(" ",maxsplit=1)[1]
				if counter < 1 or counter > 3:
					print(f"Correct the brackets in common/cultures/{file}")
					return [dict(),set()]
				elif counter == 1:
					if new_entry == "male_names" or new_entry == "female_names" or new_entry == "dynasty_names":
						print(f'Culture groups can not be called "male_names", "female_names" or "dynasty_names" or the brackets in common/cultures/{file} are wrong.')
						return [dict(),set()]
					culture_group = new_entry
					if culture_group in culture_dictionary:
						print(f"{culture_group} found a second time in common/cultures/{file}")
					else:
						culture_dictionary[culture_group] = dict()
						culture_dictionary[culture_group]["standard_names"] = dict()
				elif counter == 2:
					if new_entry == "male_names" or new_entry == "female_names" or new_entry == "dynasty_names":
						if new_entry in culture_dictionary[culture_group]["standard_names"]:
							print(f"{new_entry} was already added as standard name list for {culture_group}, but got added again, which replaces the names added before.")
						[name_string,leftover] = leftover.split("}",maxsplit=1)
						if name_string.__contains__("{"):
							print(f'In the culture group {culture_group} for the standard names between "{new_entry} =" and the opening and closing bracket was another opening bracket in common/cultures/{file}')
							return [dict(),set()]
						counter -= 1
						name_list = []
						name_tuple = ()
						if name_string == " ":
							print(f"There are no {new_entry} for the standard names in {culture_group} in common/cultures/{file}")
							name_string = ""
						elif name_string.count('"')%2 != 0:
							print(f'Uneven number of " found for standard names {new_entry} in culture group {culture_group} in common/cultures/{file}')
							return [dict(),set()]
						elif name_string.count('"') == 0:
							name_list = name_string.split()
							name_tuple = sorted(tuple(set(name_list)),key=str.lower)
						else:
							while name_string.count('"') > 1:
								[first_part,name,second_part] = name_string.split('"',maxsplit=2)
								if name.count(" ") > 4 or len(name) > 50:
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
							print(f"{new_entry} was already added as culture for {culture_group}, but got added again in common/cultures/{file}, which removes male, female and dynasty_names if they were added before.")
						culture = new_entry
						culture_dictionary[culture_group][culture] = dict()
				elif counter == 3:
					if new_entry != "male_names" and new_entry != "female_names" and new_entry != "dynasty_names":
						print(f"{new_entry} is neither male_names nor female_names nor dynasty_names so it can't be added as name list for the culture {culture} in culture group {culture_group}, check the brackets in common/cultures/{file}")
						return [dict(),set()]
					if new_entry in culture_dictionary[culture_group][culture]:
						print(f"{new_entry} were already added for culture {culture} in culture group {culture_group}, but got added again, which removes the {new_entry} added before.")
					[name_string,leftover] = leftover.split("}",maxsplit=1)
					if name_string.__contains__("{"):
						print(f'In the culture group {culture_group} for the culture {culture} between "{new_entry} =" and the opening and closing bracket was another opening bracket in common/cultures/{file}')
						return [dict(),set()]
					counter -= 1
					name_list = []
					name_tuple = ()
					if name_string == " ":
						print(f"There are no {new_entry} for the culture {culture} in {culture_group} in common/cultures/{file}")
						name_string = ""
					elif name_string.count('"')%2 != 0:
						print(f'Uneven number of " found for {new_entry} in culture {culture} in culture group {culture_group} in common/cultures/{file}')
						return [dict(),set()]
					elif name_string.count('"') == 0:
						name_list = name_string.split()
						name_tuple = sorted(tuple(set(name_list)),key=str.lower)
					else:
						while name_string.count('"') > 1:
							[first_part,name,second_part] = name_string.split('"',maxsplit=2)
							if name.count(" ") > 4 or len(name) > 50:
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
				if "male_names" not in culture_dictionary[culture_group][culture] and "male_names" not in culture_dictionary[culture_group]["standard_names"]:
					print(f"Culture {culture} in culture group {culture_group} has neither a male names list nor does the culture group have a default male names list.")
				if "female_names" not in culture_dictionary[culture_group][culture] and "female_names" not in culture_dictionary[culture_group]["standard_names"]:
					print(f"Culture {culture} in culture group {culture_group} has neither a female names list nor does the culture group have a default female names list.")
				if "dynasty_names" not in culture_dictionary[culture_group][culture] and "dynasty_names" not in culture_dictionary[culture_group]["standard_names"]:
					print(f"Culture {culture} in culture group {culture_group} has neither a dynasty names list nor does the culture group have a default dynasty names list.")
	return [culture_dictionary, culture_set]

# Creates a set and a dictionary of the religions from all files in the common/religions folder.
def get_religions(ENCODING):
	religion_dictionary = dict()
	religion_set = set()
	COLOR_STRUCTURE = re.compile(r'(?=( color = \{ [0-1]{0,1}["."]{0,1}[0-9]{1,3} [0-1]{0,1}["."]{0,1}[0-9]{1,3} [0-1]{0,1}["."]{0,1}[0-9]{1,3} \} ))')
	ICON_STRUCTURE = re.compile(r'(?=( icon = [0-9]{1,3} ))')
	for root, dirs, files in os.walk("common/religions"):
		for file in files:
			text = format_text_in_path(os.path.join(root, file),ENCODING)
			if text == "  ":
				print(f"The file common/religions/{file} is either empty or has only comments in it, why not remove it?")
				continue
			colors = re.findall(COLOR_STRUCTURE,text)
			icons = re.findall(ICON_STRUCTURE,text)
			if len(colors) != len(icons):
				print('A different number of "icon = ?" and " color = { ? ? ? }" strings has been found in ' + f"common/religions/{file}, specifically the icons:\n{icons}\nand colors:\n{colors}")
				return [dict(),set()]
			if text.find("{") < 5:
				print(f"common/religions/{file} should start with a religious group, but the first bracket comes too soon.")
				return [dict(),set()]
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
								print(f"When not inside brackets the first thing afterwards should be a religious group, but the first opening bracket in common/religions/{file} comes too soon.")
								return [dict(),set()]
							if text[k-3:k] == " = ":
								religion_group = text[:k-3].rsplit(" ",maxsplit=1)[1]
								if religion_group in religion_dictionary:
									print(f"Duplicate religious group {religion_group} found in common/religions/{file}")
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
							print(f"Brackets are wrong in common/religions/{file} specifically around {text[max(k-20,0):min(k+20,len(text))]}")
				for k in range(mindex + 7,maxdex):
					if text[k] == "{":
						counter += 1
					elif text[k] == "}":
						counter -= 1
						if counter < 2:
							print(f"The religion {religion} lacks a color or an icon.")
							return [dict(),set()]
				if religion in religion_dictionary[religion_group]:
					print(f"Duplicate religion {religion} in religious group {religion_group} in common/religions/{file}")
				else:
					icon = icons[i].split(" ")[3]
					color = tuple(colors[i].split(" ")[4:7]) #TODO divide by 255, if values above 1
					religion_dictionary[religion_group][religion] = dict()
					religion_dictionary[religion_group][religion]["icon"] = icon
					religion_dictionary[religion_group][religion]["color"] = color
					if religion in religion_set:
						print(f"Religion {religion} is in two different religious groups.")
					else:
						religion_set.add(religion)
				text = text[maxdex:]
			for k in range(len(text)):
				if text[k] == "{":
					if counter == 0:
						print(f"After the last icon and color another opening bracket exists in common/religions/{file}")
					counter += 1
				elif text[k] == "}":
					counter -= 1
					if counter < 0:
						print(f"Brackets are wrong in common/religions/{file} specifically around {text[max(k-20,0):min(k+20,len(text))]}")
			if counter != 0:
				print(f"Brackets are wrong and don't close properly at the end in common/religions/{file}.")
	return [religion_dictionary,religion_set]

def get_governments(ENCODING):
	government_set = set()
	for root, dirs, files in os.walk("common/governments"):
		for file in files:
			text = format_text_in_path(os.path.join(root, file),ENCODING)
			if text == "  ":
				print(f"The file common/governments/{file} is either empty or has only comments in it, why not remove it?")
				continue
			while text.__contains__(" = {"):
				if text.startswith(" = {"):
					print(f'common/governments/{file} ended up starting with " = {{" while being evaluated: {text[:99]}')
					return set()
				next_government = text.split(" = {",maxsplit=1)[0].rsplit(" ",maxsplit=1)[1]
				text = remove_text_between_brackets(text,next_government + " = {","common/governments/" + file)
				if next_government != "pre_dharma_mapping":
					government_set.add(next_government)
			if text != "  ":
				print(f"After evaluating common/governments/{file} there should be nothing left, but this is: {text[:99]}")
				return set()
	return government_set

# gets all the text from ?.?.? = { text } for a specified date, including further occurances of it and returns them, but adds " # " between them or returns "#" if either the date entry is empty or none is found or an error occurs.
def get_date_text(text,date,path):
	date_text = " "
	next_date = re.search(r'[^-0-9]{1}' + date + " = {",text)
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
		next_date = re.search(r'[^-0-9]{1}' + date + " = {",text)
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
		next_date = re.search(r'[^-0-9]{1}' + date + " = {",text)
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
			next_date = re.search(r'[^-0-9]{1}' + date + " = {",text)
	text = " " + " ".join(text.split()) + " "
	if text == "  ":
		return "#"
	return text

# Adds all valid dates of the form "years.months.days = {" from the text to the date_list, if they are not yet in it, which includes multiple functionally identical dates like 1.1.1 and 01.01.01 to use them for searching. While the 29th February does not exist in OpenVic and will be replaced with 28th February in the output files, it will still be added to the list, but a warning will be given. Then the dates get sorted, with the exception of functionally identical dates like 1.1.1 and 01.01.01 which stay in whatever order they happen to be found first.
def get_sorted_dates(text,START_DATE,DATE_STRUCTURE,path,DONT_IGNORE_ISSUE):
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
		if int(years) < -32768 or int(years) > 32767:
			print(f"{date} is not a valid date as OpenVic does not support years beyond -32768 to 32767 or -2^15 to 2^15 - 1. Sucks for Warhammer 40k fans in: {path}")
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
				print(f"29th February is not a valid date in OpenVic, so {date} will be changed to {int(years)}.{int(months)}.28 instead in the output files. Found in: {path}")
			elif int(days) == 30 or int(days) == 31:
				print(f'{days}th February? Really? This "date" will be ignored. Found in: {path}')
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

# Checks country files in history/countries, their paths in common/country_tags and the files in common/countries.
def check_country_files(CULTURE_SET,RELIGION_SET,GOVERNMENT_SET,START_DATE,ENCODING,DATE_STRUCTURE,DONT_IGNORE_ISSUE):
	tag_dictionary = dict()
	path_dictionary = dict()
	for root, dirs, files in os.walk("history/countries"):
		for file in files:
			tag = file[:3]
			if re.fullmatch('[0-9A-Z]{3}',tag):
				if tag in tag_dictionary:
					print(f"Duplicate tag found in history/countries: {tag}")
				else:
					tag_dictionary[tag] = "No path"
					if tag == "REB" or tag == "NAT" or tag == "PIR":
						continue
			else:
				print(f"Filename does not start with a valid country tag: {file}")
				continue
			path = os.path.join(root, file)
			text = format_text_in_path(path,ENCODING)
			sorted_list = get_sorted_dates(text,START_DATE,DATE_STRUCTURE,path,DONT_IGNORE_ISSUE)
			uniques = [[" government = ",""],[" primary_culture = ",""],[" religion = ",""],[" capital = ",""],[" technology_group = ",""]]
			accepted_culture_list = []
			added_accepted_culture_list = []
			removed_accepted_culture_list = []
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
					if DONT_IGNORE_ISSUE["MISSING_EMPTY_SPACE"] and str(re.search(r'[^ _a-zA-Z]{1}' + uniques[index][0].strip(),date_text)) != "None":
						print(f'"{uniques[index][0].strip()}" entry may not be recognised as it does not have an empty space in front of it in {path}')
					counter = date_text.count(uniques[index][0])
					if counter > 1:
						print(f"{uniques[index][0].strip()} found {counter} times for date {date} in {path}")
						uniques[index][1] = ""
					if counter > 0:
						uniques[index][1] = date_text.split(uniques[index][0],maxsplit=1)[1].split(" ",maxsplit=1)[0]
						if index < 3:
							if index == 0:
								if uniques[index][1] not in GOVERNMENT_SET:
									print(f"Government {uniques[index][1]} in {path} was not found in the common/governments files")
									uniques[index][1] = ""
							elif index == 1:
								if uniques[index][1] not in CULTURE_SET:
									print(f"Culture {uniques[index][1]} in {path} was not found in the common/cultures files")
									uniques[index][1] = ""
							elif index == 2:
								if uniques[index][1] not in RELIGION_SET:
									print(f"Religion {uniques[index][1]} in {path} was not found in the common/religions files")
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
	for root, dirs, files in os.walk("common/country_tags"):
		for file in files:
			text = format_text_in_path(os.path.join(root, file),ENCODING)
			if text == "  ":
				print(f"The file common/country_tags/{file} is either empty or has only comments in it, why not remove it?")
				continue
			for tag in tag_dictionary.keys():
				while text.__contains__(tag + ' = "countries/'):
					if tag_dictionary[tag] != "No path":
						print(f'{tag} = "countries/ is at least twice in the files in the common/country_tags folder')
					[first,second] = text.split(tag + ' = "countries/',maxsplit=1)
					[country_path,second] = second.split('"',maxsplit=1)
					if country_path not in path_dictionary:
						tag_dictionary[tag] = country_path
						path_dictionary[country_path] = tag
					else:
						print(f"In common/country_tags a path is used twice: {country_path}")
					text = first + second
			if "" != text.strip():
				print(f"Not all paths have been used by a tag in {os.path.join(root, file)} specifically the following are left: {text.strip()}")
	if "No path" in tag_dictionary.values():
		tags_without_path = []
		for tag in tag_dictionary:
			if tag_dictionary[tag] == "No path":
				tags_without_path.append(tag)
		print(f"No path has been set in common/country_tags for these tags from history/countries: {tags_without_path}")
	COLOR_STRUCTURE = re.compile(r'(?=( color = \{ [0-9]{1,3} [0-9]{1,3} [0-9]{1,3} \} ))')
	for root, dirs, files in os.walk("common/countries"):
		for file in files:
			if file not in path_dictionary:
				print(f"{file} in common/countries is not used as path in common/country_tags by any of the tags in history/countries or some other error occured")
			text = format_text_in_path(os.path.join(root, file),ENCODING)
			colors = re.findall(COLOR_STRUCTURE,text)
			if len(colors) != 1:
				print(f"The country in common/countries/{file} has either no color or multiple.")
			if text.count(" graphical_culture =") != 1:
				print(f"The country in common/countries/{file} has either no graphical culture or multiple.")
	missing_paths = []
	for path in tag_dictionary.values():
		if path != "No path" and not os.path.exists("common/countries/" + path):
			missing_paths.append(path)
	if missing_paths:
		print(f"These paths have not been found: {missing_paths}")
	tag_set = set(tag_dictionary.keys())
	return [tag_set,tag_dictionary]

def check_province_files(CULTURE_SET,RELIGION_SET,TAG_SET,START_DATE,ENCODING,DATE_STRUCTURE,WATER_INDEX,DONT_IGNORE_ISSUE):
	province_set = set()
	for root, dirs, files in os.walk("history/provinces"):
		for file in files:
			if not re.fullmatch("[1-9]",file[0]):
				print(f"Province file name does not start with a number from 1 to 9 in history/provinces/{file}")
				continue
			path = os.path.join(root, file)
			text = format_text_in_path(path,ENCODING)
			sorted_list = get_sorted_dates(text,START_DATE,DATE_STRUCTURE,path,DONT_IGNORE_ISSUE)
			check_date_entries(text,sorted_list,path,CULTURE_SET,RELIGION_SET,TAG_SET,DONT_IGNORE_ISSUE)
			province_ID = ""
			while re.fullmatch("[0-9]",file[0]): 
				province_ID += file[0]
				file = file[1:]
			if int(province_ID) not in province_set:
				province_set.add(int(province_ID))
			else:
				print(f'At least 2 files have the same province ID "{province_ID}" in history/provinces.')
	province_tuple = tuple(sorted(province_set, key=int))
	counter = 0
	if DONT_IGNORE_ISSUE["MISSING_PROVINCE_ID"]:
		for province in province_tuple:
			counter += 1
			if province != counter:
				print(f"No province file found for: {counter} until {province}")
				counter = province
	check_continents(province_set,ENCODING,WATER_INDEX,DONT_IGNORE_ISSUE)
	return

# Checks if dates contain obvious mistakes like cultures that don't exist in the culture files.
def check_date_entries(text,sorted_list,path,CULTURE_SET,RELIGION_SET,TAG_SET,DONT_IGNORE_ISSUE):
	uniques = [[" culture = ",0],[" religion = ",0],[" owner = ",0],[" controller = ",0],[" trade_goods = ",0],[" base_tax = ",0],[" base_production = ",0],[" base_manpower = ",0]]
	current_cores = []
	added_cores = []
	removed_cores = []
	for date in sorted_list:
		if date == "BASE_DATE":
			date_text = get_base_date_text(text,sorted_list,path)
		elif date == "START_DATE":
			if uniques[0][1] != uniques[1][1]:
				print(f"Only the culture or religion, but not both are present for the start date in {path}")
			if uniques[2][1] != uniques[3][1]:
				print(f"Province has only an owner or a controller, but not both at the start date in {path}")
			if (uniques[2][1] == 1) and (uniques[4][1] == 0):
				print(f"Province has an owner, but no trade good at the start date in {path}")
			if (uniques[5][1] != uniques[6][1]) or (uniques[6][1] != uniques[7][1]):
				print(f"The province lacks 1 or 2 of the base tax, production or manpower at the start date in {path}")
			if DONT_IGNORE_ISSUE["DATES_AFTER_START_DATE"]:
				continue
			break
		else:
			date_text = get_date_text(text,date,path)
		if date_text == "#":
			continue
		for index in range(len(uniques)):
			counter = date_text.count(uniques[index][0])
			if counter > 1:
				print(f'"{uniques[index][0]}" found {counter} times for date {date} in {path}')
				uniques[index][1] = 1
			elif counter == 1:
				uniques[index][1] = 1
				if index != 4:
					unique = date_text.split(uniques[index][0],maxsplit=1)[1].split(" ",maxsplit=1)[0]
					if index == 0:
						if unique == "no_culture":
							print(f"culture = no_culture will not generate pops. Found for date {date} in {path}")
						elif unique not in CULTURE_SET:
							print(f"Culture {unique} in {path} was not found in the common/cultures files")
					elif index == 1:
						if unique == "no_religion":
								print(f"religion = no_religion will not generate pops. Found for date {date} in {path}")
						elif unique not in RELIGION_SET:
							print(f"Religion {unique} in {path} was not found in the common/religions files")
					elif index < 4:
						if unique not in TAG_SET and unique != "---":
							if index == 2:
								print(f"Owner {unique} in {path} was not found in the history/countries files")
							else:
								print(f"Controller {unique} in {path} was not found in the history/countries files")
					elif index > 4:
						if not re.fullmatch("[0-9]+",unique):
							if index == 5:
								print(f"base_tax {unique} in {path} is not an integer")
							if index == 6:
								print(f"base_production {unique} in {path} is not an integer")
							if index == 7:
								print(f"base_manpower {unique} in {path} is not an integer")
			if DONT_IGNORE_ISSUE["MISSING_EMPTY_SPACE"] and str(re.search(r'[^ _a-zA-Z]{1}' + uniques[index][0].strip(),date_text)) != "None":
				print(f"{uniques[index][0].strip()} entry may not be recognised as it does not have an empty space in front of it in {path}")
		added_cores = []
		removed_cores = []
		core_text = date_text
		while core_text.__contains__(" add_core = "):
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
	return

def check_continents(province_set,ENCODING,WATER_INDEX,DONT_IGNORE_ISSUE):
	text = format_text_in_path("map/continent.txt",ENCODING)
	continent_list = []
	while text.__contains__("= {"):
		[continent_name,text] = text.split("= {",maxsplit=1)
		[provinces,text] = text.split("}",maxsplit=1)
		if provinces == " ":
			provinces = set()
			continue
		continent_name = continent_name.strip()
		provinces = set(map(int,provinces.split()))
		continent_list.append([continent_name,provinces])
		for entry in provinces:
			if DONT_IGNORE_ISSUE["MISSING_PROVINCE_FILE"] and entry not in province_set:
				print(f"No province file with the ID {entry} exists, but the province is on the continent: {continent_name}")
			for i in range(len(continent_list) - 1):
				if entry in continent_list[i][1]:
					print(f"Province {entry} is already on the continent {continent_list[i][0]}, but also on the continent {continent_name}")
	combined_continent_set = provinces.copy()
	for i in range(len(continent_list) - 1):
		combined_continent_set = combined_continent_set.union(continent_list[i][1])
	if len(continent_list) > 6:
		print("OpenVic only supports 6 continents in the UI, so while it will work when there are more, there wont be any functional buttons for them in some windows. Until support for this gets added, you will have to combine continents. Of course you can just generate the output and merge the continents there instead or ignore this problem.")
	text = format_text_in_path("map/default.map",ENCODING)
	ocean = text.split("sea_starts = {",maxsplit=1)[1].split("}",maxsplit=1)[0]
	ocean = set(map(int,ocean.split()))
	for entry in ocean:
		if DONT_IGNORE_ISSUE["MISSING_PROVINCE_FILE"] and entry not in province_set:
			print(f"No province file with the ID {entry} exists, but the province is an ocean province.")
		if entry in combined_continent_set:
			print(f"Province {entry} is already on a continent, but also an ocean.")
	lakes = text.split("lakes = {",maxsplit=1)[1].split("}",maxsplit=1)[0]
	lakes = set(map(int,lakes.split()))
	water_provinces = ocean.union(lakes)
	for entry in lakes:
		if DONT_IGNORE_ISSUE["MISSING_PROVINCE_FILE"] and entry not in province_set:
			print(f"No province file with the ID {entry} exists, but the province is a lake province.")
		if entry in combined_continent_set:
			print(f"Province {entry} is already on a continent, but also a lake.")
		if entry in ocean:
			print(f"Province {entry} is already an ocean, but also a lake.")
	leftover_provinces = province_set - combined_continent_set - ocean - lakes
	if leftover_provinces:
		print(f"Some provinces are neither a part of a continent, ocean or lake: {leftover_provinces}")
	image = Image.open("map/provinces.bmp")
	w,h = image.size
	load_province_bmp = image.load()
	pixel_set = set()
	for x in range(w):
		for y in range(h):
			pixel_set.add(load_province_bmp[x,y])
	if text.count(" max_provinces = ") != 1:
		print('Either " max_provinces = " does not exist in the map/default.map file or it appears multiple times.')
	else:
		max_provinces = text.split(" max_provinces = ",maxsplit=1)[1].split(" ",maxsplit=1)[0]
		if not re.fullmatch("[0-9]+",max_provinces):
			print(f"In map/default.map max_provinces = {max_provinces} is not an integer value.")
		elif len(pixel_set) + 1 != int(max_provinces):
			print(f"The max_provinces value {max_provinces} in the map/default.map should be 1 higher than the number of different colors in the province.bmp {len(pixel_set)}.")
	[DEFINITIONS_DICTIONARY,RGB_DICTIONARY] = check_definition_csv(ENCODING)
	province_colors_are_in_definition_csv = True
	if pixel_set.difference(RGB_DICTIONARY.keys()):
		province_colors_are_in_definition_csv = False
		print(f"These colors are in the provinces.bmp, but not in the defintion.csv {pixel_set.difference(RGB_DICTIONARY.keys())}")
		for x in range(w):
			for y in range(h):
				if load_province_bmp[x,y] not in RGB_DICTIONARY:
					print(f"The color at {x},{y} in the provinces.bmp is not in the map/definition.csv")
	terrain = Image.open("map/terrain.bmp")
	terrain_w,terrain_h = terrain.size
	if terrain_w != w or terrain_h != h:
		print(f"The width and/or height of the provinces.bmp {w},{h} and terrain.bmp {terrain_w},{terrain_h} are not equal, which also means it wont be checked whether some terrain pixels are ocean or not while the province itself is continental or not.")
	else:
		load_terrain_image = terrain.load()
		wrong_water_terrain = set()
		wrong_land_terrain = set()
		if province_colors_are_in_definition_csv:
			for x in range(w):
				for y in range(h):
					if load_terrain_image[x,y] in WATER_INDEX:
						if RGB_DICTIONARY[load_province_bmp[x,y]] not in water_provinces:
							if DONT_IGNORE_ISSUE["INDIVIDUAL_PIXELS"]:
								print(f"The color {load_province_bmp[x,y]} at {x},{y} is for a province on a continent, but the terrain is water.")
							wrong_water_terrain.add(RGB_DICTIONARY[load_province_bmp[x,y]])
					else:
						if RGB_DICTIONARY[load_province_bmp[x,y]] in water_provinces:
							if DONT_IGNORE_ISSUE["INDIVIDUAL_PIXELS"]:
								print(f"The color {load_province_bmp[x,y]} at {x},{y} is for a province in an ocean or lake, but the terrain is not.")
							wrong_land_terrain.add(RGB_DICTIONARY[load_province_bmp[x,y]])
			if wrong_water_terrain:
				print(f"Some terrain.bmp pixels are water, but their provinces are not ocean or lakes: {wrong_water_terrain}")
			if wrong_land_terrain:
				print(f"Some terrain.bmp pixels are not water, but their provinces are ocean or lakes: {wrong_land_terrain}")
		else:
			print("Whether some Terrain pixels are water or not, while the province it belongs to is the other could not be checked due to colors in the provinces.bmp that are not in the definition.csv")
	text = format_text_in_path("map/climate.txt",ENCODING)
	impassable = set()
	while text.__contains__(" = {"):
		[climate_name,text] = text.split(" = {",maxsplit=1)
		[provinces,text] = text.split("}",maxsplit=1)
		if provinces == " ":
			continue
		climate_name = climate_name.rsplit(" ",maxsplit=1)[1]
		provinces = set(map(int,provinces.split()))
		for entry in provinces:
			if DONT_IGNORE_ISSUE["MISSING_PROVINCE_FILE"] and entry not in province_set:
				print(f"No province file with the ID {entry} exists, but the province has the climate: {climate_name}")
			if entry in ocean:
				print(f"Province {entry} is an ocean, but also has the climate {climate_name}.")
			if entry in lakes:
				print(f"Province {entry} is a lake, but also has the climate {climate_name}.")
		if climate_name == "impassable":
			impassable = provinces
	check_area(combined_continent_set,lakes,impassable,ENCODING)
	check_positions(ocean,lakes,impassable,pixel_set,DEFINITIONS_DICTIONARY,ENCODING,DONT_IGNORE_ISSUE)
	return

def check_area(combined_continent_set,lakes,impassable,ENCODING):
	area_province_set = set()
	area_set = set()
	text = format_text_in_path("map/area.txt",ENCODING)
	text_list = text.split(" = {")
	area_name = text_list[0].strip()
	area_set.add(area_name)
	text_list.remove(text_list[0])
	for entry in text_list:
		for province in set(map(int,entry.split("}",maxsplit=1)[0].split())):
			if province in area_province_set:
				print(f"The province {province} is already in another area.")
			elif province in impassable:
				print(f"The province {province} is impassable and should not be in an area.")
			elif province in lakes:
				print(f"The province {province} is a lake and should not be in an area.")
			else:
				area_province_set.add(province)
		area_name = entry.split("}",maxsplit=1)[1].strip()
		if area_name in area_set:
			print(f"At least 2 areas have the same name: {area_name}")
		else:
			area_set.add(area_name)
	if combined_continent_set - area_province_set - impassable:
		print(f"Some continental provinces are not in an area: {combined_continent_set - area_province_set - impassable}")
	return

def check_definition_csv(ENCODING):
	not_more_than_once = True
	definitions_dictionary = dict()
	RGB_dictionary = dict()
	with open("map/definition.csv",'r',encoding=ENCODING,errors='replace') as file:
		for line in file:
			if re.fullmatch("[1-9]",line[0]):
				[provinceID,red,green,blue] = line.split(";",maxsplit=4)[0:4]
				if not re.fullmatch("[0-9]+",provinceID):
					print(f"The province ID {provinceID} is not a valid number in map/definition.csv")
				elif provinceID in definitions_dictionary:
					print(f"At least 2 lines start with the same number {provinceID} in map/definition.csv")
				elif not (re.fullmatch("[0-9]+",red) and re.fullmatch("[0-9]+",green) and re.fullmatch("[0-9]+",blue)):
					print(f"One of the red, green or blue values is not a number in line {line.strip()} in map/definition.csv")
				elif not ((int(red) < 256) and (int(green) < 256) and (int(blue) < 256)):
					print(f"The red, green and blue values have to be numbers from 0 to 255 in line {line.strip()} in map/definition.csv")
				else:
					RGB = tuple((int(red),int(green),int(blue)))
					if RGB in RGB_dictionary:
						print(f"Another province was already assigned the same RGB value {RGB} as {provinceID} in map/definition.csv")
					else:
						definitions_dictionary[provinceID] = RGB
						RGB_dictionary[RGB] = int(provinceID)
			elif not_more_than_once and (line[0] == "p"):
				not_more_than_once = False
			elif line[0] == "#":
				pass
			else:
				print(f"In map/definition.csv this line has to change or be removed: {line.strip()}")
	return [definitions_dictionary,RGB_dictionary]

def check_positions(OCEAN_SET,LAKES_SET,IMPASSABLE_SET,pixel_set,DEFINITIONS_DICTIONARY,ENCODING,DONT_IGNORE_ISSUE):
	unimportant = (0,0,0)
	if unimportant in pixel_set:
		for b in range(256):
			for g in range(256):
				for r in range(6,256):
					if (r,g,b) not in pixel_set:
						unimportant = (r,g,b)
						break
				if unimportant not in pixel_set:
					break
			if unimportant not in pixel_set:
				break
	ocean = (0,0,1)
	if ocean in pixel_set:
		for r in range(4):
			for g in range(256):
				for b in range(2,256):
					if (r,g,b) not in pixel_set:
						ocean = (r,g,b)
						break
				if ocean not in pixel_set:
					break
			if ocean not in pixel_set:
				break
	if unimportant == ocean or ocean in pixel_set or unimportant in pixel_set:
		print(f'A mod with over 65536 Provinces wont work.')
		return
	OCEAN_RGB_SET = set()
	for provinceID in OCEAN_SET:
		if str(provinceID) in DEFINITIONS_DICTIONARY:
			OCEAN_RGB_SET.add(DEFINITIONS_DICTIONARY[str(provinceID)])
		else:
			print(f"The province ID {provinceID} is not found in the map/definition.csv file, but it is an ocean.")
	UNIMPORTANT_RGB_SET = set()
	for provinceID in LAKES_SET:
		if str(provinceID) in DEFINITIONS_DICTIONARY:
			UNIMPORTANT_RGB_SET.add(DEFINITIONS_DICTIONARY[str(provinceID)])
		else:
			print(f"The province ID {provinceID} is not found in the map/definition.csv file, but it is a lake.")
	for provinceID in IMPASSABLE_SET:
		if str(provinceID) in DEFINITIONS_DICTIONARY:
			UNIMPORTANT_RGB_SET.add(DEFINITIONS_DICTIONARY[str(provinceID)])
		else:
			print(f"The province ID {provinceID} is not found in the map/definition.csv file, but it is impassable.")
	positions = format_text_in_path("map/positions.txt",ENCODING)
	image_load_original = Image.open("map/provinces.bmp").load()
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
	coastal_pixel_set = set()
	for x in range(w):
		for y in range(h):
			coastal_pixel_set.add(image_load[x,y])
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
		if int(provinceID) in IMPASSABLE_SET or int(provinceID) in LAKES_SET or int(provinceID) in OCEAN_SET:
			continue
		[city_x,city_y,unit_x,unit_y,name_x,name_y,port_x,port_y,positions] = positions.split(" ",maxsplit=8)
		if int(float(city_x)) < 0 or int(float(city_y)) < 0 or int(float(city_x)) >= w or int(float(city_y)) >= h:
			print(f"The city position {city_x},{city_y} for province {provinceID} is outside the provinces.bmp with size {w},{h}.")
			city_x = city_y = -1
		if int(float(unit_x)) < 0 or int(float(unit_y)) < 0 or int(float(unit_x)) >= w or int(float(unit_y)) >= h:
			print(f"The unit position {unit_x},{unit_y} for province {provinceID} is outside the provinces.bmp with size {w},{h}.")
			unit_x = unit_y = -1
		if int(float(name_x)) < 0 or int(float(name_y)) < 0 or int(float(name_x)) >= w or int(float(name_y)) >= h:
			print(f"The name position {name_x},{name_y} for province {provinceID} is outside the provinces.bmp with size {w},{h}.")
			name_x = name_y = -1
		if int(float(port_x)) < 0 or int(float(port_y)) < 0 or int(float(port_x)) >= w or int(float(port_y)) >= h:
			print(f"The port position {port_x},{port_y} for province {provinceID} is outside the provinces.bmp with size {w},{h}.")
			continue
		if provinceID not in DEFINITIONS_DICTIONARY:
			print(f"The province ID {provinceID} is not found in the map/definition.csv file, but a position for it exists.")
			continue
		if city_x != -1 and city_y != -1:
			if image_load_original[int(float(city_x)),int(h-1 - float(city_y))] != DEFINITIONS_DICTIONARY[provinceID]:
				print(f"The rounded position {int(float(city_x))},{int(float(city_y))} of the city model, which is {int(float(city_x))},{int(h-1 - float(city_y))} when opening the bmp with GIMP, for province {provinceID} is not within the province itself.")
		if unit_x != -1 and unit_y != -1:
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
		for x in range(-2,2):
			for y in range(-2,2):
				if image_load_original[max(0,min(w-1,port_x+x)),max(0,min(h-1,port_y+y))] == DEFINITIONS_DICTIONARY[provinceID]:
					coastal_nearby = True
					break
			if coastal_nearby:
				break
		if not coastal_nearby:
			print(f"There is no coastal province within a 2 pixel radius of the rounded port position {port_x},{h-port_y} for province {provinceID}, which would be {port_x},{port_y} in GIMP")
	return

[START_DATE,ENCODING,WATER_INDEX,DONT_IGNORE_ISSUE,I_READ_THE_INSTRUCTIONS] = mod_specific_values()
if not  I_READ_THE_INSTRUCTIONS:
	print("READ AND FOLLOW THE INSTRUCTIONS AT THE START OF THE FILE! For some mods you still have to make minimal changes yourself.")
else:
	START_DATE = verify_date(START_DATE)
	[CULTURE_DICTIONARY,CULTURE_SET] = get_cultures(ENCODING,DONT_IGNORE_ISSUE)
	[RELIGION_DICTIONARY,RELIGION_SET] = get_religions(ENCODING)
	GOVERNMENT_SET = get_governments(ENCODING)
	if CULTURE_SET and RELIGION_SET and GOVERNMENT_SET:
		DATE_STRUCTURE = re.compile(r'[^-0-9]{1}[-]{0,1}[0-9]{1,5}["."][0-9]{1,2}["."][0-9]{1,2} = {')
		[TAG_SET,TAG_DICTIONARY] = check_country_files(CULTURE_SET,RELIGION_SET,GOVERNMENT_SET,START_DATE,ENCODING,DATE_STRUCTURE,DONT_IGNORE_ISSUE)
		check_province_files(CULTURE_SET,RELIGION_SET,TAG_SET,START_DATE,ENCODING,DATE_STRUCTURE,WATER_INDEX,DONT_IGNORE_ISSUE)
	else:
		if not CULTURE_SET:
			print(f"No cultures could be found in the common/cultures folder.")
		if not RELIGION_SET:
			print(f"No religions could be found in the common/religions folder.")
		if not GOVERNMENT_SET:
			print(f"No governments could be found in the common/governments folder.")
#%%
