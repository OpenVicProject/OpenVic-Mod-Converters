#%%
# Place this Python script into whatever mod folder you want to check. The mod needs to have the common/countries, common/country_tags, common/cultures, common/religions, common/governments, history/countries and history/provinces folders and map/default.map and map/continent.txt files. If those are not present, either because the mod uses the base game files or relies on another mod you have to copy them or can't use this script.
import re
import os
# This mod_specific_values function is the only parts of the script you might need to change, just follow the instructions.
def mod_specific_values():
	BASE_DATE = "1444.11.11" # Anything within a province file that is not set for a specific date will be treated as if it was set for this date. Replace 1444.11.11 with the intended base date in the form years.months.days, unless it would either be a 29th February as those currently do not exist in OpenVic and will be replaced with 28th February or a date outside the range -32768.1.1 to 32767.12.31. Any input that is not valid will be replaced with 1444.11.11.
	START_DATE = "1444.11.11" # The history will be applied until the start date, including identical dates like 01444.11.11 or not at all if the base date is set to a later date and no prior history entries exist and error messages will be shown, for example if the province has only a religion or culture, but not both at the start date. The same restrictions as for the base date apply.
	ENCODING = "utf-8" # Change this to whatever the encoding of the mod is, most likely it is either "utf-8" or "windows-1252". If it is mixed and you want to be able to automatically convert the mod to an OpenVic mod, you currently would have to pick one and convert the files with the other encoding.
	DONT_IGNORE_ISSUE = { # Not all issues cause trouble when generating output files, so you can choose to ignore them, though in some cases you really should check them.
		"BASE_DATE_EQUALS_DATE":True, # If you are certain that all existing date entries, with dates equal the BASE_DATE, should be applied after the BASE_DATE, you can set this to False.
		"DATES_AFTER_START_DATE":True, # If you only care about mistakes that happen until the START_DATE, set this to False.
		"MISSING_EMPTY_SPACE":True, # For example "add_core =" is searched as " add_core =" instead, as if it always had an empty space in front of it, which the formatting also inserts before and after "=", "{", "}" and the at the start and end of the text itself, as well as any time some parts get removed like date entries to evaluate the base date or put together like duplicate date entries. However there could be situations where EU4 does not actually require an empty space in front of it, for example 'capital = "?"add_core', which this script would not recognise as a core being added, so you should check all these warnings.
		"IDENTICAL_DATES":True, # This mentions if one date appears multiple times in the same file, but their entries get combined anyway, so you can ignore this, if you don't want to combine the entries.
		"DUPLICATE_DATES":True, # 1.1.1 and 01.01.01 entries do not get combined and are applied in whatever order they are found first, so you have to check those.
		"DUPLICATE_CORES":True, # Sometimes cores that already exist are added again, which does nothing, so you can ignore this, if you don't want to remove such duplicates.
		"DUPLICATE_REMOVAL_CORE":True, # Cores may be removed twice for the same date, which does nothing, so you can ignore this.
		"REMOVE_NON_EXISTANT_CORE":True, # Sometimes cores are removed even though they were not present at this date. So maybe some other core was actually supposed to be removed.
		"DUPLICATE_CULTURES":True, # Sometimes accepted cultures are added again, which does nothing, so you can ignore this.
		"DUPLICATE_REMOVAL_CULTURE":True, # Cultures may be removed twice for the same date, which does nothing, so you can ignore this.
		"REMOVE_NON_EXISTANT_CULTURE":True, # Sometimes cultures are removed as accepted cultures, even though they were not accepted at this date. So maybe some other culture was actually supposed to be removed.
		"MISSING_PROVINCE_FILE":True, # Some provinces may be placed on a continent or such, but lack a province file, can be ignored as an empty "provinceID.txt" file will simply be generated anyway for the output.
		"MISSING_PROVINCE_ID":True # While it is not necessary to use all numbers between 1 and the number of provinces as IDs, maybe you still want to add empty files for such cases, if not you can set it to False.
	} # That's it. Now you can run it, if you have a sufficiently new Python version installed. Maybe anything after 3.7 will work.
	return [BASE_DATE,START_DATE,ENCODING,DONT_IGNORE_ISSUE]

# formats a text file when given the path.
def format_text_in_path(path,ENCODING):
	with open(path,'r',encoding=ENCODING,errors='replace') as file:
		text = ' '
		for line in file:
			if line.__contains__("#"):
				text = text + re.split("#",line,maxsplit=1)[0] + " "
			else:
				text = text + line + " "
		text = re.sub("{",' { ',text)
		text = re.sub("}",' } ',text)
		text = re.sub("=",' = ',text)
		text = re.sub(r"\s+",' ',text)
		if text.__contains__("�"):
			counter = text.count("�")
			index = text.find("�")
			mindex = max(0,index - 50)
			if counter == 1:
				print(f"1 character with wrong encoding found in file: {file.name} specifically � in:")
			else:
				print(f"{counter} characters with wrong encoding found in file: {file.name} specifically � for example in:")
			print(text[mindex:index + 50])
		if text.count("{") != text.count("}"):
			print(f"DONT IGNORE THIS: The number of opening and closing brackets in {path} is not equal.")
	return(text)

# Makes sure that the base and start date are valid and removes any unnecessary zeros in front of the numbers.
def verify_date(date):
	if 2 != date.count("."):
		print(f"{date} Try again...")
		return("1444.11.11")
	[years,months,days] = date.split(".")
	years = int(years)
	months = int(months)
	days = int(days)
	if years < -32768 or years > 32767:
		print(f"{date} is not a valid date as OpenVic does not support years beyond -32768 to 32767 or -2^15 to 2^15 - 1. Sucks for Warhammer 40k fans.")
		return("1444.11.11")
	if months < 1 or months > 12 or days < 1 or days > 31:
		print(f"{date} is not a valid date")
		return("1444.11.11")
	if days == 31:
		if months == 4 or months == 6 or months == 9 or months == 11:
			print(f"{date} is not a valid date")
			return("1444.11.11")
	if months == 2:
		if days == 29:
			print(f"29th February is not a valid date in OpenVic, so {date} will be changed to {years}.{months}.28 instead.")
			return(f"{years}.{months}.28")
		elif days == 30 or days == 31:
			print(f"{days}th February? Really?")
			return("1444.11.11")
	return(f"{years}.{months}.{days}")

# replace everything with " " between all occurances of a given string ending with a {, including that string, until the brackets close again and return the new string or "#" if an error occurs.
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
		if counter > 0:
			print(f"In {path} the wrong number of brackets are in the text.")
			return "#"
		text = prior_text + " " + leftover
	text = " " + text + " "
	text = re.sub(r"\s+",' ',text)
	return text

# creates a set of all cultures and a dictionary {culture_group:{culture:{male_names:"names",female_names:"names",dynasty_names:"names"}}}
def get_cultures(ENCODING):
	culture_dictionary = dict()
	for files in os.listdir("common/cultures"):
		text = format_text_in_path("common/cultures/" + files,ENCODING)
		if text == " ":
			print(f"The file common/cultures/{files} is either empty or has only comments in it, why not remove it?")
			continue
		male_names_count = text.count(" male_names = {")
		female_names_count = text.count(" female_names = {")
		dynasty_names_count = text.count(" dynasty_names = {")
		text = remove_text_between_brackets(text," country = {","common/cultures/" + files)
		text = remove_text_between_brackets(text," province = {","common/cultures/" + files)
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
				print(f'DONT IGNORE THIS: common/cultures/{files} ended up starting with " = ' + '{" while being evaluated: ' + text[:99])
				return [dict(),set()]
			[prior_text,leftover] = text.split(" = {",maxsplit=1)
			counter = 1 + counter + prior_text.count("{") - prior_text.count("}")
			new_entry = prior_text.rsplit(" ",maxsplit=1)[1]
			if counter < 1 or counter > 3:
				print(f"Correct the brackets in common/cultures/{files}")
				return [dict(),set()]
			elif counter == 1:
				if new_entry == "male_names" or new_entry == "female_names" or new_entry == "dynasty_names":
					print(f'Culture groups can not be called "male_names", "female_names" or "dynasty_names" or the brackets in common/cultures/{files} are wrong.')
					return [dict(),set()]
				culture_group = new_entry
				if culture_group in culture_dictionary:
					print(f"{culture_group} found a second time in common/cultures/{files}")
				else:
					culture_dictionary[culture_group] = dict()
					culture_dictionary[culture_group]["standard_names"] = dict()
			elif counter == 2:
				if new_entry == "male_names" or new_entry == "female_names" or new_entry == "dynasty_names":
					if new_entry in culture_dictionary[culture_group]["standard_names"]:
						print(f"{new_entry} was already added as standard name list for {culture_group}, but got added again, which replaces the names added before.")
					[name_string,leftover] = leftover.split("}",maxsplit=1)
					if name_string.__contains__("{"):
						print(f'In the culture group {culture_group} for the standard names between "{new_entry} =" and the opening and closing bracket was another opening bracket in common/cultures/{files}')
						return [dict(),set()]
					counter -= 1
					name_list = []
					name_tuple = ()
					if name_string == " ":
						print(f"There are no {new_entry} for the standard names in {culture_group} in common/cultures/{files}")
						name_string = ""
					elif name_string.count('"')%2 != 0:
						print(f'Uneven number of " found for standard names {new_entry} in culture group {culture_group} in common/cultures/{files}')
						return [dict(),set()]
					elif name_string.count('"') == 0:
						name_tuple = sorted(tuple(set(name_string.split())),key=str.lower)
					else:
						while name_string.count('"') > 1:
							[first_part,name,second_part] = name_string.split('"',maxsplit=2)
							name_list.append('"' + name.strip() + '"')
							name_string = first_part + " " + second_part
						name_tuple = sorted(tuple(set(name_list + name_string.split())),key=str.lower)
					if name_tuple:
						for name in name_tuple:
							name_string += name + " "
					if name_string != "":
						culture_dictionary[culture_group]["standard_names"][new_entry] = name_string.strip()
				else:
					if new_entry in culture_dictionary[culture_group]:
						print(f"{new_entry} was already added as culture for {culture_group}, but got added again in common/cultures/{files}, which removes male, female and dynasty_names if they were added before.")
					culture = new_entry
					culture_dictionary[culture_group][culture] = dict()
			elif counter == 3:
				if new_entry != "male_names" and new_entry != "female_names" and new_entry != "dynasty_names":
					print(f"{new_entry} is neither male_names nor female_names nor dynasty_names so it can't be added as name list for the culture {culture} in culture group {culture_group}, check the brackets in common/cultures/{files}")
					return [dict(),set()]
				if new_entry in culture_dictionary[culture_group][culture]:
					print(f"{new_entry} were already added for culture {culture} in culture group {culture_group}, but got added again, which removes the {new_entry} added before.")
				[name_string,leftover] = leftover.split("}",maxsplit=1)
				if name_string.__contains__("{"):
					print(f'In the culture group {culture_group} for the culture {culture} between "{new_entry} =" and the opening and closing bracket was another opening bracket in common/cultures/{files}')
					return [dict(),set()]
				counter -= 1
				name_list = []
				name_tuple = ()
				if name_string == " ":
					print(f"There are no {new_entry} for the culture {culture} in {culture_group} in common/cultures/{files}")
					name_string = ""
				elif name_string.count('"')%2 != 0:
					print(f'Uneven number of " found for {new_entry} in culture {culture} in culture group {culture_group} in common/cultures/{files}')
					return [dict(),set()]
				elif name_string.count('"') == 0:
					name_tuple = sorted(tuple(set(name_string.split())),key=str.lower)
				else:
					while name_string.count('"') > 1:
						[first_part,name,second_part] = name_string.split('"',maxsplit=2)
						name_list.append('"' + name.strip() + '"')
						name_string = first_part + " " + second_part
					name_tuple = sorted(tuple(set(name_list + name_string.split())),key=str.lower)
				if name_tuple:
					for name in name_tuple:
						name_string += name + " "
				if name_string != "":
					culture_dictionary[culture_group][culture][new_entry] = name_string.strip()
			text = leftover
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
	for files in os.listdir("common/religions"):
		text = format_text_in_path("common/religions/" + files,ENCODING)
		if text == " ":
			print(f"The file common/religions/{files} is either empty or has only comments in it, why not remove it?")
			continue
		colors = re.findall(COLOR_STRUCTURE,text)
		icons = re.findall(ICON_STRUCTURE,text)
		if len(colors) != len(icons):
			print('A different number of "icon = ?" and " color = { ? ? ? }" strings has been found in ' + f"common/religions/{files}, specifically the icons:\n{icons}\nand colors:\n{colors}")
			return [dict(),set()]
		if text.find("{") < 5:
			print(f"common/religions/{files} should start with a religious group, but the first bracket comes too soon.")
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
							print(f"When not inside brackets the first thing afterwards should be a religious group, but the first opening bracket in common/religions/{files} comes too soon.")
							return [dict(),set()]
						if text[k-3:k] == " = ":
							religion_group = text[:k-3].rsplit(" ",maxsplit=1)[1]
							if religion_group in religion_dictionary:
								print(f"Duplicate religious group {religion_group} found in common/religions/{files}")
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
						print(f"Brackets are wrong in common/religions/{files} specifically around {text[max(k-20,0):min(k+20,len(text))]}")
			for k in range(mindex + 7,maxdex):
				if text[k] == "{":
					counter += 1
				elif text[k] == "}":
					counter -= 1
					if counter < 2:
						print(f"The religion {religion} lacks a color or an icon.")
						return [dict(),set()]
			if religion in religion_dictionary[religion_group]:
				print(f"Duplicate religion {religion} in religious group {religion_group} in common/religions/{files}")
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
					print(f"After the last icon and color another opening bracket exists in common/religions/{files}")
				counter += 1
			elif text[k] == "}":
				counter -= 1
				if counter < 0:
					print(f"Brackets are wrong in common/religions/{files} specifically around {text[max(k-20,0):min(k+20,len(text))]}")
		if counter != 0:
			print(f"Brackets are wrong and don't close properly at the end in common/religions/{files}.")
	return [religion_dictionary,religion_set]

def get_governments(ENCODING):
	government_set = set()
	for files in os.listdir("common/governments"):
		text = format_text_in_path("common/governments/" + files,ENCODING)
		if text == " ":
			print(f"The file common/governments/{files} is either empty or has only comments in it, why not remove it?")
			continue
		while text.__contains__(" = {"):
			if text.startswith(" = {"):
				print(f'common/governments/{files} ended up starting with " = ' + '{" while being evaluated: ' + text[:99])
				return set()
			next_government = text.split(" = {",maxsplit=1)[0].rsplit(" ",maxsplit=1)[1]
			text = remove_text_between_brackets(text,next_government + " = {","common/governments/" + files)
			if next_government != "pre_dharma_mapping":
				government_set.add(next_government)
		if text != " ":
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
	date_text = re.sub(r"\s+",' ',date_text)
	if date_text == " ":
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
	text = re.sub(r"\s+",' ',text)
	if text == " ":
		return "#"
	return(text)

# Adds all valid dates of the form "years.months.days = {" from the text to the date_list, if they are not yet in it, which includes multiple functionally identical dates like 1.1.1 and 01.01.01 to use them for searching. While the 29th February does not exist in OpenVic and will be replaced with 28th February in the output files, it will still be added to the list, but a warning will be given. Then the dates get sorted, with the exception of functionally identical dates like 1.1.1 and 01.01.01 which stay in whatever order they happen to be found first.
def get_sorted_dates(text,BASE_DATE,START_DATE,DATE_STRUCTURE,path,DONT_IGNORE_ISSUE):
	[YEARS,MONTHS,DAYS] = BASE_DATE.split(".")
	date_list = []
	next_date = DATE_STRUCTURE.search(text)
	while "None" != str(next_date):
		date = next_date.group()[1:].split(" ")[0]
		[years,months,days] = date.split(".")
		text = text[next_date.end():]
		next_date = DATE_STRUCTURE.search(text)
		counter = 1
		for i in range(len(text)):
			if text[i] == "{":
				counter += 1
			elif text[i] == "}":
				counter -= 1
				if counter == 0:
					if "None" != str(next_date):
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
		if DONT_IGNORE_ISSUE["BASE_DATE_EQUALS_DATE"] and int(YEARS) == int(years) and int(MONTHS) == int(months) and int(DAYS) == int(days):
			print(f"{date} is identical to the BASE_DATE you entered, which could lead to unintended results, as the BASE_DATE is always applied before an identical date in: {path}")
		if date not in date_list:
			date_list.append(date)
		elif DONT_IGNORE_ISSUE["IDENTICAL_DATES"]:
			print(f"identical date: {date} found multiple times in: {path}")
	date_list.insert(0,BASE_DATE)
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
	sorted_list[sorted_list.index(BASE_DATE)] = "BASE_DATE"
	sorted_list.reverse()
	sorted_list[sorted_list.index(START_DATE)] = "START_DATE"
	sorted_list.reverse()
	return(sorted_list)

# Checks country files in history/countries, their paths in common/country_tags and the files in common/countries.
def check_country_files(CULTURE_SET,RELIGION_SET,GOVERNMENT_SET,BASE_DATE,START_DATE,ENCODING,DATE_STRUCTURE,DONT_IGNORE_ISSUE):
	tag_dictionary = dict()
	path_dictionary = dict()
	for files in os.listdir("history/countries"):
		tag = files[:3]
		if re.fullmatch('[0-9A-Z]{3}',tag):
			if tag in tag_dictionary:
				print(f"Duplicate tag found in history/countries: {tag}")
			else:
				tag_dictionary[tag] = "No path"
				if tag == "REB" or tag == "NAT" or tag == "PIR":
					continue
		else:
			print(f"Filename does not start with a valid country tag: {files}")
			continue
		path = "history/countries/" + files
		text = format_text_in_path(path,ENCODING)
		sorted_list = get_sorted_dates(text,BASE_DATE,START_DATE,DATE_STRUCTURE,path,DONT_IGNORE_ISSUE)
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
	for files in os.listdir("common/country_tags"):
		path = "common/country_tags/" + files
		text = format_text_in_path(path,ENCODING)
		if text == " ":
			print(f"The file common/country_tags/{files} is either empty or has only comments in it, why not remove it?")
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
		text = re.sub(r"\s+",' ',text)
		if text != " ":
			print(f"Not all paths have been used by a tag in {path} specifically the following are left:{text}")
	if "No path" in tag_dictionary.values():
		tags_without_path = []
		for tag in tag_dictionary:
			if tag_dictionary[tag] == "No path":
				tags_without_path.append(tag)
		print(f"No path has been set in common/country_tags for these tags from history/countries: {tags_without_path}")
	COLOR_STRUCTURE = re.compile(r'(?=( color = \{ [0-9]{1,3} [0-9]{1,3} [0-9]{1,3} \} ))')
	for files in os.listdir("common/countries"):
		if files not in path_dictionary:
			print(f"{files} in common/countries is not used as path in common/country_tags by any of the tags in history/countries or some other error occured")
		text = format_text_in_path("common/countries/" + files,ENCODING)
		colors = re.findall(COLOR_STRUCTURE,text)
		if len(colors) != 1:
			print(f"The country in common/countries/{files} has either no color or multiple.")
		if text.count(" graphical_culture =") != 1:
			print(f"The country in common/countries/{files} has either no graphical culture or multiple.")
	missing_paths = []
	for path in tag_dictionary.values():
		if path != "No path" and not os.path.exists("common/countries/" + path):
			missing_paths.append(path)
	if missing_paths:
		print(f"These paths have not been found: {missing_paths}")
	tag_set = set(tag_dictionary.keys())
	return [tag_set,tag_dictionary]

def check_province_files(CULTURE_SET,RELIGION_SET,TAG_SET,BASE_DATE,START_DATE,ENCODING,DATE_STRUCTURE,DONT_IGNORE_ISSUE):
	province_set = set()
	for files in os.listdir("history/provinces"):
		if not re.fullmatch('[0-9]{1}',files[0]):
			print(f"Province file name does not start with a number in history/provinces/{files}")
			continue
		path = "history/provinces/" + files
		text = format_text_in_path(path,ENCODING)
		sorted_list = get_sorted_dates(text,BASE_DATE,START_DATE,DATE_STRUCTURE,path,DONT_IGNORE_ISSUE)
		check_date_entries(text,sorted_list,path,CULTURE_SET,RELIGION_SET,TAG_SET,DONT_IGNORE_ISSUE)
		province_ID = ""
		while re.fullmatch('[0-9]{1}',files[0]):
			province_ID += files[0]
			files = files[1:]
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
	check_continents(province_set,ENCODING,DONT_IGNORE_ISSUE)
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
						if unique not in CULTURE_SET:
							if unique != "no_culture":
								print(f"Culture {unique} in {path} was not found in the common/cultures files")
					elif index == 1:
						if unique not in RELIGION_SET:
							if unique != "no_religion":
								print(f"Religion {unique} in {path} was not found in the common/religions files")
					elif index < 4:
						if unique not in TAG_SET and unique != "---":
							if index == 2:
								print(f"Owner {unique} in {path} was not found in the history/countries files")
							else:
								print(f"Controller {unique} in {path} was not found in the history/countries files")
					elif index > 4:
						if not unique.isnumeric():
							if index == 4:
								print(f"base_tax {unique} in {path} is not an integer")
							if index == 5:
								print(f"base_production {unique} in {path} is not an integer")
							if index == 6:
								print(f"base_manpower {unique} in {path} is not an integer")
			if DONT_IGNORE_ISSUE["MISSING_EMPTY_SPACE"] and str(re.search(r'[^ _a-zA-Z]{1}' + uniques[index][0].strip(),date_text)) != "None":
				print(f"{uniques[index][0].strip()} entry may not be recognised as it does not have an empty space in front of it in {path}")
		if date_text.__contains__(" culture = no_culture"):
			print(f"culture = no_culture will not generate pops. Found for date {date} in {path}")
		if date_text.__contains__(" religion = no_religion"):
			print(f"religion = no_religion will not generate pops. Found for date {date} in {path}")
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

def check_continents(province_set,ENCODING,DONT_IGNORE_ISSUE):
	text = format_text_in_path("map/continent.txt",ENCODING)
	continent_list = []
	while text.__contains__("= {"):
		[continent_name,text] = text.split("= {",maxsplit=1)
		[provinces,text] = text.split("}",maxsplit=1)
		if provinces == " ":
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
	if len(continent_list) > 6:
		print("OpenVic only supports 6 continents in the UI, so while it will work when there are more, there wont be any functional buttons for them in some windows. Until support for this gets added, you will have to combine continents. Of course you can just generate the output and merge the continents there instead or ignore this problem.")
	text = format_text_in_path("map/default.map",ENCODING)
	text = text.split("sea_starts = {",maxsplit=1)[1]
	provinces = text.split("}",maxsplit=1)[0]
	provinces = set(map(int,provinces.split()))
	continent_list.append(["OpenVic_ocean",provinces])
	for entry in provinces:
		if DONT_IGNORE_ISSUE["MISSING_PROVINCE_FILE"] and entry not in province_set:
			print(f"No province file with the ID {entry} exists, but the province is an ocean province.")
		for i in range(len(continent_list) - 1):
			if entry in continent_list[i][1]:
				print(f"Province {entry} is already on the continent {continent_list[i][0]}, but also an ocean")
	text = format_text_in_path("map/default.map",ENCODING)
	text = text.split("lakes = {",maxsplit=1)[1]
	provinces = text.split("}",maxsplit=1)[0]
	provinces = set(map(int,provinces.split()))
	continent_list.append(["OpenVic_lakes",provinces])
	for entry in provinces:
		if DONT_IGNORE_ISSUE["MISSING_PROVINCE_FILE"] and entry not in province_set:
			print(f"No province file with the ID {entry} exists, but the province is a lake province.")
		for i in range(len(continent_list) - 2):
			if entry in continent_list[i][1]:
				print(f"Province {entry} is already on the continent {continent_list[i][0]}, but also a lake")
		if entry in continent_list[len(continent_list) - 2][1]:
			print(f"Province {entry} is already an ocean, but also a lake")
	combined_continent_set = provinces.copy()
	for i in range(len(continent_list) - 1):
		combined_continent_set = combined_continent_set.union(continent_list[i][1])
	leftover_provinces = province_set - combined_continent_set
	if leftover_provinces:
		print(f"Some provinces are neither a part of a continent, ocean or lake: {leftover_provinces}")
	return

[BASE_DATE,START_DATE,ENCODING,DONT_IGNORE_ISSUE] = mod_specific_values()
BASE_DATE = verify_date(BASE_DATE)
START_DATE = verify_date(START_DATE)
[CULTURE_DICTIONARY,CULTURE_SET] = get_cultures(ENCODING)
[RELIGION_DICTIONARY,RELIGION_SET] = get_religions(ENCODING)
GOVERNMENT_SET = get_governments(ENCODING)
if CULTURE_SET != set() and RELIGION_SET != set() and GOVERNMENT_SET != set():
	DATE_STRUCTURE = re.compile(r'[^-0-9]{1}[-]{0,1}[0-9]{1,5}["."][0-9]{1,2}["."][0-9]{1,2} = {')
	[TAG_SET,TAG_DICTIONARY] = check_country_files(CULTURE_SET,RELIGION_SET,GOVERNMENT_SET,BASE_DATE,START_DATE,ENCODING,DATE_STRUCTURE,DONT_IGNORE_ISSUE)
	check_province_files(CULTURE_SET,RELIGION_SET,TAG_SET,BASE_DATE,START_DATE,ENCODING,DATE_STRUCTURE,DONT_IGNORE_ISSUE)
else:
	if CULTURE_SET == set():
		print(f"No cultures could be found in the common/cultures folder.")
	if RELIGION_SET == set():
		print(f"No religions could be found in the common/religions folder.")
	if GOVERNMENT_SET == set():
		print(f"No governments could be found in the common/governments folder.")
#%%