def autoCap(name):
	name = name.lower()
	if (name.find("city") != -1):
		name = name[:name.find("city")]
	if (name[-1] == " "):
		name = name[:-1]
	print(name)
	space = False
	ans = ""
	ind = 0
	for i in name:
		if (i == " "):
			space = True
			ans += i
		elif ((name.index(i) == 0 and ind == 0) or space == True):
			ind +=1
			ans += i.upper()
			space = False;
		else:
			ans += i
	return ans
