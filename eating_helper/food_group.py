from enum import Enum, unique


@unique
class FoodGroup(str, Enum):
    """
    Food groups I use to make it easier to shop groceries.
    """

    BREAD = "bread"
    PANTRY = "pantry"
    DAIRY = "dairy"
    FROZEN = "frozen"
    PRODUCE = "produce"
    MEAT = "meat"
    INDIAN = "indian"  # Go to an indian store
    ASIAN = "asian"  # Go to an asian store


USDA_TO_CUSTOM_FOOD_GROUP = {
    "Baked Products": FoodGroup.BREAD,
    "Cereal Grains and Pasta": FoodGroup.PANTRY,
    "Dairy and Egg Products": FoodGroup.DAIRY,
    "Frozen": FoodGroup.FROZEN,
    "Fruits and Fruit Juices": FoodGroup.PRODUCE,
    "Legumes and Legume Products": FoodGroup.PANTRY,
    "Nut and Seed Products": FoodGroup.PRODUCE,
    "Pantry": FoodGroup.PANTRY,
    "Poultry Products": FoodGroup.MEAT,
    "Seafood": FoodGroup.MEAT,
    "Soups, Sauces, and Gravies": FoodGroup.PANTRY,
    "Vegetables and Vegetable Products": FoodGroup.PRODUCE,
}

# Some ID/names do not have groups already associated with them.
# I manually associate them here.
INGREDIENT_TO_CUSTOM_FOOD_GROUP = {
    "1949692": FoodGroup.PANTRY,
    "1859997": FoodGroup.PANTRY,
    "1864648": FoodGroup.PRODUCE,
    "1889879": FoodGroup.BREAD,
    "1932883": FoodGroup.DAIRY,
    "2024576": FoodGroup.PANTRY,
    "2080001": FoodGroup.PANTRY,
    "2099245": FoodGroup.MEAT,
    "2113885": FoodGroup.PANTRY,
    "2272524": FoodGroup.FROZEN,
    "2273669": FoodGroup.PANTRY,
    "2341777": FoodGroup.MEAT,
    "2343304": FoodGroup.BREAD,
    "2344719": FoodGroup.PRODUCE,
    "2345725": FoodGroup.PANTRY,
    "2345739": FoodGroup.PANTRY,
    "386410": FoodGroup.PANTRY,
    "562738": FoodGroup.PANTRY,
    "577489": FoodGroup.PANTRY,
    "595770": FoodGroup.PANTRY,
    "981101": FoodGroup.PANTRY,
    "bay leaf": FoodGroup.PANTRY,
    "black pepper": FoodGroup.PANTRY,
    "cacao powder": FoodGroup.PANTRY,
    "cajun": FoodGroup.PANTRY,
    "cherry tomato": FoodGroup.PRODUCE,
    "chili powder": FoodGroup.PANTRY,
    "chipotle in adobo sauce": FoodGroup.PANTRY,
    "cilantro": FoodGroup.PRODUCE,
    "cucumber": FoodGroup.PRODUCE,
    "cumin": FoodGroup.PANTRY,
    "dill": FoodGroup.PANTRY,
    "five spice": FoodGroup.PANTRY,
    "garlic powder": FoodGroup.PANTRY,
    "garlic": FoodGroup.PRODUCE,
    "ginger garlic paste": FoodGroup.INDIAN,
    "sichuan peppercorn": FoodGroup.ASAIN,
    "chinese dried red chili": FoodGroup.ASAIN,
    "green onion": FoodGroup.PRODUCE,
    "indian spices": FoodGroup.INDIAN,
    "jalapeno": FoodGroup.PRODUCE,
    "ketchup": FoodGroup.PANTRY,
    "lemon": FoodGroup.PRODUCE,
    "lettuce": FoodGroup.PRODUCE,
    "lime": FoodGroup.PRODUCE,
    "long green chili": FoodGroup.INDIAN,
    "onion powder": FoodGroup.PANTRY,
    "paprika": FoodGroup.PANTRY,
    "parsley": FoodGroup.PRODUCE,
    "pico de gallo": FoodGroup.PRODUCE,
    "poblano": FoodGroup.PRODUCE,
    "red onion": FoodGroup.PRODUCE,
    "salsa": FoodGroup.PRODUCE,
    "salt": FoodGroup.PANTRY,
    "sambal oelek": FoodGroup.PANTRY,
    "shallot": FoodGroup.PRODUCE,
    "soy sauce": FoodGroup.PANTRY,
    "spinach": FoodGroup.PRODUCE,
    "sugar": FoodGroup.PANTRY,
    "tomato": FoodGroup.PRODUCE,
    "vinegar": FoodGroup.PANTRY,
    "water": FoodGroup.PANTRY,
    "white vinegar": FoodGroup.PANTRY,
}
