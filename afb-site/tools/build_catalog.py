import json, re

# (item, name, category, format, caseQty, unitOz, organic)
R = []

def add(rows, cat, fmt):
    for r in rows:
        item, name, qty, oz = r[0], r[1], r[2], r[3]
        org = name.upper().startswith("ORGANIC")
        R.append(dict(item=str(item), name=name.title(), category=cat, format=fmt,
                      caseQty=qty, unitOz=oz, organic=org))

# ---------- 16 OZ CONTAINERS ----------
add([
 ("2800516C","Marcona Almonds Salted",12,10),
 ("2800520C","Marcona Almonds with Truffle",12,10),
 ("2800521","Marcona Almonds with Lemon & Pepper",12,10),
 ("2810520","Cashews with Truffle",12,9),
 ("2810521","Peanuts with Truffle",12,9),
 ("2800522","Valencia Almonds with Rosemary",12,10),
 ("2820515C","Walnuts Caramelized",12,7),
 ("2840515C","Pecans Caramelized",12,8),
], "Flavored Gourmet Nuts", "16 oz Container")

add([
 ("6000501","Organic Almonds Raw",12,9.5),
 ("6000502","Organic Almonds Roasted Salted",12,9.5),
 ("6000503","Organic Almonds Roasted Unsalted",12,9.5),
 ("6010503","Organic Cashews Raw",12,9),
 ("6010504","Organic Cashews Roasted Salted",12,9),
 ("6010505","Organic Cashews Roasted Unsalted",12,9),
 ("6050501","Organic Hazelnuts Oregon",12,9),
 ("6080505","Organic Mixed Nuts Salted",12,9),
 ("6080506","Organic Mixed Nuts Unsalted",12,10),
 ("6070504","Organic Peanuts Roasted Salted",12,10),
 ("6040501","Organic Pecans",12,7),
 ("6020502","Organic Walnuts",12,7),
 ("2800505","Almonds Blanched Sliced",12,6),
 ("2800414","Almonds Jordanian Assorted",16,10),
 ("2800506","Almonds Natural Sliced",12,6),
 ("2800501","Almonds Raw",12,8),
 ("2800502","Almonds Roasted Salted",12,8),
 ("2800503","Almonds Roasted Unsalted",12,8),
 ("2800507","Almonds Slivered Blanched",12,8),
 ("2800512","Almonds Tamari",12,8),
 ("2800504","Almonds Whole Blanched",16,7),
 ("2800408","Almonds Roasted Honey",16,6),
 ("2860401","Brazil Nuts Raw",16,6),
 ("2810500","Cashews Raw",12,8),
 ("2810501","Cashews Roasted Salted",12,8),
 ("2810502","Cashews Roasted Unsalted",12,8),
 ("2810407","Cashews Roasted Honey",16,6),
 ("2880507","Corn Nuts Roasted Salted",12,6),
 ("2880510","Green Peas Whole",12,6.5),
 ("2850401","Hazelnuts (Filberts) Turkish",16,6),
 ("2860407","Macadamia Nuts",16,6),
 ("3180502","Mixed Nuts Salted (with Peanuts)",12,8),
 ("3180503","Mixed Nuts Unsalted (with Peanuts)",12,8),
 ("3180505","Mixed Nuts Salted Supreme",12,8),
 ("3180506","Mixed Nuts Unsalted Supreme",12,8),
 ("2870504","Peanuts Roasted Salted",12,9),
 ("2870503","Peanuts Blanched Raw",12,9),
 ("2870509","Peanuts Cajun",12,9),
 ("2870411","Peanuts Honey Roasted",16,6.5),
 ("2870505","Peanuts Roasted Unsalted",12,9),
 ("2840501","Pecans Light Halves",12,6.5),
 ("2860310","Pine Nuts (Pignolias) Raw",24,4),
 ("2830501","Pistachios In-Shell Salted",12,7),
 ("2830502","Pistachios In-Shell Unsalted",12,7),
 ("2830405","Pistachio Kernels Raw",16,6),
 ("2830404","Pistachios Turkish",16,6.5),
 ("2820502","Walnuts Light Halves & Pieces",12,6),
 ("2880511","Wasabi Green Peas",12,6),
], "Nuts", "16 oz Container")

add([
 ("2890400","Pepitas Raw",16,6),
 ("2890401","Pepitas Roasted Salted",16,6),
 ("2890402","Pepitas Roasted Unsalted",16,6),
 ("2890505","Pumpkin Seeds In-Shell Salted",12,6),
 ("2890506","Pumpkin Seeds In-Shell Unsalted",12,6),
 ("2890507","Sunflower In-Shell Salted",12,5),
 ("2890508","Sunflower In-Shell Unsalted",12,5),
 ("2890511","Sunflower Kernels Unsalted",12,9),
 ("2890509","Sunflower Kernels Raw",12,9),
 ("2890510","Sunflower Kernels Salted",12,9),
], "Seeds", "16 oz Container")

add([
 ("3000503","All Natural Healthy Mix",12,9),
 ("3000541","Antioxidant Mix",12,8),
 ("3000514","Berry Nutty Mix",12,10),
 ("3000427","Cajun Hot Mix",16,5),
 ("3000517","California Aloha Mix",12,8),
 ("3000513","Cherry Berry Mix",12,8),
 ("3000542","Choco N Nut Mix",12,10),
 ("3000535","Cranberry Craze",12,8),
 ("3000509","Cranberry Gold Mix",12,9),
 ("3000536","Cranberry Healthy Mix",12,9),
 ("3000506","Dieter's Delight Mix",12,9),
 ("3000504","Energy Mix",12,10),
 ("3000533","Fanatic Fruit Mix",12,8),
 ("3000505","Fitness Mix",12,8),
 ("3000415","Goji Berry Mix",16,7),
 ("3000507","Hiker Trail Mix",12,8),
 ("3000511","Hippie Mix",12,10),
 ("3000523","Honey and Milk Medley Mix",12,10),
 ("3000502","Omega 3 Mix",12,8),
 ("3000528","Oriental Party Mix",12,5),
 ("3000516","Pacific Almond Mix",12,10),
 ("3000524","Rainbow Delight Mix",12,10),
 ("3000519","Raisin Nuts Mix",12,9),
 ("3000518","Rocky Mountain Mix",12,8),
 ("3000501","Salad Topping Mix",12,8),
 ("3000525","Simple Trek Mix",12,8),
 ("3000540","Sweet & Salty Mix",12,9),
 ("3000531","Sweet Sea Salt Sensation Mix",12,9),
 ("3000529","Wasabi Wow Mix",12,8),
 ("3000522","Yogurt Deluxe Trail Mix",12,10),
], "Trail Mixes", "16 oz Container")

add([
 ("2910529","Apple Rings",12,4.5),
 ("2910415","Apricots Turkish",12,11),
 ("2910513","Apricots Californian",12,11),
 ("2910553","Coconut Chips",12,6),
 ("2910555","Coconut Flakes",12,4),
 ("2910501","Cranberries",12,8),
 ("2910519","Dates Medjool",12,9),
 ("2910520","Dates Pitted",12,8),
 ("2910416","Figs Black Mission",16,6),
 ("2910418","Figs Turkish",16,6),
 ("2910441","Ginger Crystallized",16,6),
 ("2910517","Kalamata Figs",16,11),
 ("2910546","Kiwi Slices",12,6),
 ("2910532","Mango Slices",12,6),
 ("2910535","Papaya Chunks",12,10),
 ("2910534","Papaya Spears",12,8),
 ("2910443","Peach Slices",16,6),
 ("2910444","Pear Slices",16,6),
 ("2910539","Pineapple Chunks",12,9),
 ("2910538","Pineapple Rings",12,8),
 ("2910423","Prunes Pitted",16,8),
 ("2910525","Raisins Black",12,10),
 ("2910527","Raisins Golden",12,9),
 ("6110415","Organic Apricots",12,8),
 ("6110402","Organic Cherries Sour",16,6.5),
 ("6110401","Organic Cranberries",12,6),
 ("6110419","Organic Dates Medjool",16,6),
 ("6110420","Organic Dates Pitted",16,6),
 ("6110418","Organic Figs Turkish",16,6),
 ("6110432","Organic Mango Slices",16,4),
 ("6110425","Organic Raisins Black",16,6.5),
], "Dried Fruits", "16 oz Container")

add([
 ("2112008","Blackeyed Peas",20,16),
 ("2150513","Chia Seeds",12,11),
 ("2112012","Chick Peas / Garbanzos",20,16),
 ("2120539","Couscous Israeli",12,10),
 ("2122038","Couscous Medium",20,16),
 ("2112004","Dark Red Kidney Beans",20,16),
 ("2122020","Dunya Red Quinoa",20,16),
 ("2150514","Flax Seeds",12,10.5),
 ("2132010","Green Split Peas",20,16),
 ("2112005","Light Red Kidney Beans",20,16),
 ("2112006","Navy Beans",20,16),
 ("2112007","Pinto Beans",20,16),
 ("2120519","Quinoa White",12,11),
 ("2132002","Red Lentils",20,16),
 ("2150516","Sesame Seeds Hulled",12,7),
 ("2132011","Yellow Split Peas",20,16),
], "Grains, Beans & Lentils", "16 oz Container")

add([
 ("3140407","Graham Crackers Dark Chocolate Covered",12,5),
 ("3140406","Graham Crackers Milk Chocolate Covered",12,5),
 ("3200501","Nonpareils Dark Chocolate",12,10.5),
 ("3210402","Almonds Dark Chocolate Covered",12,10),
 ("3210401","Almonds Milk Chocolate Covered",12,10),
 ("3210403","Almonds Yogurt Covered",12,10),
 ("3210405","Cashews Dark Chocolate Covered",12,10),
 ("3210404","Cashews Milk Chocolate Covered",12,10),
 ("3220404","Cherries Dark Chocolate",12,11),
 ("3200405","Chocolate Sprinkles",12,10),
 ("3220405","Cranberries Dark Chocolate",12,11),
 ("3220407","Cranberries Milk Chocolate",12,11),
 ("3210413","Espresso Beans Dark Chocolate",12,10),
 ("3200403","Jelly Rings Dark Chocolate",12,12),
 ("3200402","Malt Balls Milk Chocolate Covered",12,9),
 ("3210411","Peanuts Dark Chocolate Covered",12,12),
 ("3210410","Peanuts Milk Chocolate Covered",12,12),
 ("3210412","Peanuts Yogurt Covered",12,12),
 ("3220402","Raisins Dark Chocolate Covered",12,12),
 ("3220401","Raisins Milk Chocolate Covered",12,12),
 ("3220403","Raisins Yogurt Covered",12,12),
 ("3130506","Pretzels Blueberry Covered",12,7),
 ("3130502","Pretzels Dark Chocolate",12,7),
 ("3130501","Pretzels Milk Chocolate",12,7),
 ("3130505","Pretzels Strawberry Covered",12,7),
 ("3130504","Pretzels Toffee Covered",12,7),
 ("3130503","Pretzels Yogurt Covered",12,7),
], "Chocolate Covered", "16 oz Container")

add([
 ("3360614","Gummy Worms Sour",12,10),
 ("3310604","Jelly Beans",12,10),
 ("3310605","Raspberries Red & Black",12,9),
 ("3370602","Red Fish",12,10),
 ("3360606","Sour Patch Kids",12,12),
 ("3370601","Swedish Fish",12,12),
], "Candy & Gummies", "16 oz Container")

add([
 ("3110501","Banana Chips Sweetened",12,5),
 ("3110703","Plantain Chips Garlic",12,7),
 ("3110702","Plantain Chips Salted",12,7),
 ("3110704","Plantain Chips Spicy",12,7),
 ("3110706","Plantain Chips Sweet",12,7),
 ("3110507","Vegetable Chips",12,4),
], "Plantain Chips", "16 oz Container")

add([
 ("3100503","Honey Nut & Seed Crunch",12,8),
 ("3100501","Honey Peanut Crunch",12,8),
 ("3100502","Honey Sesame Crunch",12,7),
 ("3190502","Oat Bran Sticks",12,5.5),
 ("3190505","Oriental Rice Snack",12,4),
 ("3190503","Sesame Sticks",12,9),
 ("3190504","Sesame Sticks Honey Roasted",12,7),
], "Granolas & Crunches", "16 oz Container")

# ---------- TASTY BRAND SCREW TOP ----------
add([
 ("6801901","Organic Almonds Raw",14,10),
 ("6801902","Organic Almonds Salted",14,10),
 ("6801903","Organic Almonds Unsalted",14,10),
 ("2801908","Almonds Honey Roasted",14,9),
 ("2801958","Almonds Sliced",14,8),
 ("6811900","Organic Cashews Raw",14,10),
 ("6811901","Organic Cashews Salted",14,10),
 ("6811902","Organic Cashews Unsalted",14,10),
 ("2801901","Almonds Raw",14,10),
 ("2801902","Almonds Salted",14,10),
 ("2801903","Almonds Unsalted",14,10),
 ("2811900","Cashews Raw",14,10),
 ("2811901","Cashews Salted",14,10),
 ("2811902","Cashews Unsalted",14,10),
 ("5811902","Truffle Cashews",14,10),
 ("2811907","Cashews Honey Roasted",14,9),
 ("2811977","Organic Hazelnuts",14,9),
 ("6181902","Organic Mixed Nuts Salted",14,8),
 ("6181903","Organic Mixed Nuts Unsalted",14,8),
 ("2831901","Pistachios In-Shell Salted",14,10),
 ("2831902","Pistachios In-Shell Unsalted",14,8),
 ("2831962","Truffle Peanuts",14,8),
 ("2871904","Peanuts Salted",14,10),
 ("2871905","Peanuts Unsalted",14,10),
 ("2871911","Peanuts Honey Roasted",14,10),
 ("2891906","Pumpkin Seeds Unsalted",14,9),
 ("2891901","Pumpkin Seeds Salted",14,11),
 ("2891900","Pumpkin Seeds Raw",14,11),
 ("6841901","Organic Pecan Halves",14,8),
 ("6821902","Organic Walnuts Light Halves & Pieces",14,7),
 ("2801920","Truffle Marcona Almonds",14,10),
 ("2801916","Marcona Almonds Salted",14,10),
 ("2801922","Marcona Almonds with Rosemary",14,10),
 ("2801921","Marcona Almonds with Lemon & Pepper",14,10),
 ("2821915","Walnuts Caramelized",14,7),
 ("2841915","Pecans Caramelized",14,9),
 ("2841947","Macadamia Nuts",14,10),
], "Nuts", "Screw Top")

add([
 ("3001903","Healthy Mix",14,8),
 ("3001941","Antioxidant Mix",14,10),
 ("3001904","Energy Mix",14,9),
 ("3001902","Omega-3 Mix",14,9),
 ("6001903","Organic Omega-3 Mix",14,9),
], "Trail Mixes", "Screw Top")

add([
 ("6911901","Organic Cranberries",14,9),
 ("2911920","Organic Dates Pitted",14,10),
 ("2911927","Raisins Golden",14,10),
 ("2911925","Raisins Black",14,10),
 ("6911926","Organic Raisins Black",14,10),
 ("2910539","Pineapple Chunks",14,10),
 ("2910540","Pineapple Rings",14,8),
 ("2910423","Prunes Pitted",14,12),
 ("6910424","Organic Prunes Pitted",14,12),
 ("2911915","Apricots Turkish",14,11),
 ("2911913","Apricots Californian",14,10),
 ("2911932","Mango Slices",14,9),
 ("6911933","Organic Mango Slices",14,6),
 ("5181945","Peach Slices",14,9),
 ("5181946","Pear Slices",14,10),
 ("2841945","Kiwi Slices",14,9),
 ("2841946","Sour Cherries",14,10),
], "Dried Fruits", "Screw Top")

# ---------- SMALL SIZE CONTAINER ----------
add([
 ("3211902","Almonds Dark Chocolate",18,8),
 ("3211901","Almonds Milk Chocolate",18,8),
 ("3221905","Cranberries Dark Chocolate",18,9),
 ("3221907","Cranberries Milk Chocolate",18,9),
 ("3211905","Cashews Dark Chocolate",18,8),
 ("3211906","Cashews Milk Chocolate",18,8),
 ("3211911","Peanuts Dark Chocolate",18,8),
 ("3211910","Peanuts Milk Chocolate",18,8),
 ("3221902","Raisins Dark Chocolate",18,9),
 ("3221901","Raisins Milk Chocolate",18,9),
 ("3201901","Nonpareils Dark Chocolate",18,7),
 ("3201909","Nonpareils Milk Chocolate",18,7),
], "Chocolate Covered", "Small Container")

add([
 ("3361910","Gummy Watermelon Slices",18,6),
 ("3361902","Gummy Bears Sour",18,8),
 ("3361901","Gummy Bears",18,8),
 ("3361908","Gummy Peach Rings",18,6),
 ("3361905","Gummy Worms Sour",18,6),
 ("3361904","Gummy Worms",18,8),
 ("2801914","Jordan Almonds",18,9),
 ("3311905","Raspberry Gummies Black & Red",18,8),
], "Candy & Gummies", "Small Container")

# ---------- GRANOLA & PLANTAIN CUPS ----------
add([
 ("2040718","Granola Cranberry & Pecan",12,15),
 ("2040720","Granola Walnut",12,15),
 ("2040719","Granola Walnut & Date",12,15),
 ("2040725","Granola Almond & Raisin",12,15),
 ("2040726","Granola Apple & Cinnamon",12,15),
 ("2040727","Granola Cashew & Coconut",12,15),
 ("2040703","Granola Crispy",12,15),
 ("2040728","Granola Dark Chocolate",12,15),
 ("2040704","Granola French Vanilla",12,15),
 ("2040721","Granola Fruit & Nut",12,15),
 ("2040705","Granola Honey Nut",12,15),
 ("2040723","Granola Mango & Coconut",12,15),
 ("2040724","Granola Omega-3",12,15),
 ("2040722","Granola Pina Colada",12,15),
 ("2040729","Granola Raisins",12,15),
], "Granolas & Crunches", "Granola Cup")

add([
 ("3110705","Plantain Chips Lemon",12,7),
 ("3110703G","Plantain Chips Garlic",12,7),
 ("3110702G","Plantain Chips Salted",12,7),
 ("3110704G","Plantain Chips Spicy",12,7),
 ("3110706G","Plantain Chips Sweet",12,7),
], "Plantain Chips", "Granola Cup")

# ---------- NUTS TO GO CUPS ----------
add([
 ("2802901","Almonds Raw",18,7),
 ("2802902","Almonds Roasted Salted",18,7),
 ("2802903","Almonds Roasted Unsalted",18,7),
 ("2812900","Cashews Raw",18,5.5),
 ("2812901","Cashews Roasted Salted",18,5.5),
 ("2812902","Cashews Roasted Unsalted",18,5.5),
 ("3182905","Mixed Nuts Roasted Salted Supreme",18,5),
 ("3182906","Mixed Nuts Roasted Unsalted Supreme",18,5),
 ("2872911","Peanuts Roasted Honey",18,6),
 ("2872904","Peanuts Roasted Salted",18,7),
 ("2872905","Peanuts Roasted Unsalted",18,7),
 ("2842901","Pecans Light Halves",18,4.5),
 ("2832901","Pistachios In-Shell Salted",18,5),
 ("2832902","Pistachios In-Shell Unsalted",18,5),
 ("2829203","Walnuts Light Halves & Pieces",18,4.5),
 ("2882911","Wasabi Peas",18,5.5),
], "Nuts", "To-Go Cup")

add([
 ("3002927","Cajun Hot Mix",18,5),
 ("3002936","Cranberry Healthy Mix",18,6),
 ("3002904","Energy Mix",18,6),
 ("3002933","Fanatic Fruit Mix",18,6),
 ("3002905","Fitness Mix",18,6),
 ("3002903","Healthy Mix",18,5),
 ("3002909","Heart Healthy Mix",18,6),
 ("3002907","Hiker Trail Mix",18,7),
 ("3002902","Omega 3 Mix",18,6),
 ("3002914","Berry Nutty Mix",18,7),
], "Trail Mixes", "To-Go Cup")

add([
 ("2912915","Apricots",18,8),
 ("2912901","Cranberries Dried",18,6),
 ("2912920","Dates Pitted",18,6),
 ("2912932","Mango Diced",18,6),
 ("2912935","Papaya Diced",18,7),
 ("2912939","Pineapple Diced",18,6),
 ("2912923","Prunes Pitted",18,7),
 ("2912925","Raisins Black",18,6),
 ("3112901","Banana Chips Sweetened",18,4),
], "Dried Fruits", "To-Go Cup")

add([
 ("3212902","Almonds Dark Chocolate Covered",18,8),
 ("3212901","Almonds Milk Chocolate Covered",18,8),
 ("3212911","Peanuts Dark Chocolate Covered",18,8),
 ("3212910","Peanuts Milk Chocolate Covered",18,8),
], "Chocolate Covered", "To-Go Cup")

add([
 ("3362901","Gummy Bears",18,8),
 ("3362915","Gummy Mini Worms Neon Sour",18,6),
 ("3362904","Gummy Worms",18,7),
 ("3362906","Sour Patch Kids",18,7),
 ("3372901","Swedish Fish",18,7),
 ("3372902","Red Fish",18,7),
], "Candy & Gummies", "To-Go Cup")

# ---------- BIG PRESENTATION CONTAINERS ----------
add([
 ("2800701","Almonds Raw",16,16),
 ("2800702","Almonds Roasted Salted",16,16),
 ("2800703","Almonds Roasted Unsalted",16,16),
 ("2810700","Cashews Raw",16,14),
 ("2810701","Cashews Roasted Salted",16,14),
 ("2810702","Cashews Roasted Unsalted",16,14),
 ("2820702","Walnuts Light Halves",16,10),
 ("2830701","Pistachios In-Shell Salted",16,12),
 ("2830702","Pistachios In-Shell Unsalted",16,12),
 ("2830705","Pistachio Kernels Raw",16,16),
 ("2840701","Pecans Light Halves",16,12),
 ("2860701","Brazil Nuts Raw",16,16),
 ("2870704","Peanuts Roasted Salted",16,16),
 ("2870705","Peanuts Roasted Unsalted",16,16),
 ("2870709","Peanuts Cajun",16,16),
 ("2870711","Peanuts Roasted Honey",16,16),
 ("2880709","Edamame Roasted Salted",16,12),
], "Nuts", "Presentation Container")

add([
 ("2890700","Pepitas Raw",16,16),
 ("2890701","Pepitas Roasted Salted",16,16),
 ("2890702","Pepitas Roasted Unsalted",16,16),
 ("2890705","Pumpkin Seeds In-Shell Salted",16,12),
 ("2890706","Pumpkin Seeds In-Shell Unsalted",16,10),
 ("2890707","Sunflower In-Shell Salted",16,10),
 ("2890708","Sunflower In-Shell Unsalted",16,10),
], "Seeds", "Presentation Container")

# ---------- BULK CASES ----------
add([
 ("B-2910529","Apple Rings Bulk",1,705),
 ("B-2910415","Apricots #1 Turkish Bulk",1,448),
 ("B-2910519","Dates Medjool Jumbo Bulk",1,176),
 ("B-2910501","Cranberries Bulk",1,400),
 ("B-2910532","Mango Slices Bulk",1,352),
 ("B-2910423","Prunes Pitted Bulk",1,400),
], "Dried Fruits", "Bulk Case")

add([
 ("B-2800501","Almonds Raw Bulk",1,800),
 ("B-2810500","Cashews Raw Bulk",1,800),
 ("B-2820502","Walnuts Light Halves & Pieces Bulk",1,400),
 ("B-2830404","Pistachios Turkish Bulk",1,400),
 ("B-2870504","Peanuts Roasted Salted Bulk",1,480),
], "Nuts", "Bulk Case")

add([
 ("B-3000503","All Natural Healthy Mix Bulk",1,320),
 ("B-3000504","Energy Mix Bulk",1,320),
 ("B-3000502","Omega 3 Mix Bulk",1,320),
], "Trail Mixes", "Bulk Case")

# --- derived fields ---
BASE = {  # indicative $/oz retail
 "Nuts":0.62,"Flavored Gourmet Nuts":1.05,"Seeds":0.42,"Trail Mixes":0.55,
 "Dried Fruits":0.48,"Granolas & Crunches":0.38,"Plantain Chips":0.34,
 "Chocolate Covered":0.58,"Candy & Gummies":0.36,"Grains, Beans & Lentils":0.22,
}
FORMAT_MULT = {"16 oz Container":1.0,"Screw Top":1.15,"Small Container":1.05,
 "To-Go Cup":1.2,"Presentation Container":0.95,"Granola Cup":1.0,"Bulk Case":0.55}

BLURB = {
 "Nuts":"Roasted and packed in Paterson, in our own kitchen, in small batches.",
 "Flavored Gourmet Nuts":"Slow-roasted and hand-finished with real seasoning, not coating.",
 "Seeds":"Cleaned, roasted and packed the same week they're received.",
 "Trail Mixes":"Blended to a fixed recipe by weight, so every scoop is the same.",
 "Dried Fruits":"Sourced direct from growers and packers, no added sulfites unless noted.",
 "Granolas & Crunches":"Baked in sheet trays, broken by hand, never dust at the bottom.",
 "Plantain Chips":"Sliced thin, fried crisp, seasoned while still warm.",
 "Chocolate Covered":"Panned in a rotating drum for an even, glossy shell.",
 "Candy & Gummies":"Packed to order so they arrive soft, not stuck together.",
 "Grains, Beans & Lentils":"Cleaned, sorted and packed for kitchens that go through volume.",
}

MOQ = {"16 oz Container":1,"Screw Top":1,"Small Container":2,"To-Go Cup":2,
       "Presentation Container":1,"Granola Cup":1,"Bulk Case":1}

seen = {}
out = []
for r in R:
    key = r["item"]
    if key in seen:
        continue
    seen[key] = 1
    oz = r["unitOz"]
    price = round(oz * BASE[r["category"]] * FORMAT_MULT[r["format"]] * 1.0 + 1.2, 2)
    if r["organic"]:
        price = round(price * 1.22, 2)
    r["price"] = price
    r["caseWeightOz"] = round(oz * r["caseQty"], 2)
    r["moq"] = MOQ[r["format"]]
    r["kosher"] = True
    r["blurb"] = BLURB[r["category"]]
    r["slug"] = re.sub(r"[^a-z0-9]+","-", r["name"].lower()).strip("-") + "-" + r["item"].lower()
    out.append(r)

cats = sorted({r["category"] for r in out})
fmts = ["16 oz Container","Screw Top","Small Container","To-Go Cup",
        "Presentation Container","Granola Cup","Bulk Case"]

data = dict(
  company=dict(
    name="American Food & Beverage",
    dba="Premium Food Distributors — DBA Grassland",
    address="PO Box 533, Paterson NJ 07543",
    phone="(908) 345-6345",
    salesEmail="sales@americanfoodbeverage.com",
    ordersEmail="orders@grasslandfoods.com",
    site="americanfoodbeverage.com",
  ),
  minimums=dict(
    retail=dict(orderSubtotal=35.00, freeShippingAt=75.00, shippingFlat=9.95, taxRate=0.06625),
    wholesale=dict(orderCases=20, orderWeightLb=250, rule="either")
  ),
  categories=cats, formats=fmts, products=out)

json.dump(data, open("catalog.json","w"), indent=1)
print(len(out), "SKUs")
print(cats)
