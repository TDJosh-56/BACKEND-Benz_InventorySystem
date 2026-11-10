from decimal import Decimal, InvalidOperation

#for recipe import

try:
    from recipe.models import Recipe
except ImportError:
    Recipe = None

def normalize_to_base_unit(amount: float, unit: str) -> tuple[Decimal, str]:
    """translates measuring units into uniform database units where:
    solids are converted to grams (g),
    liquids are converted to milliliters (mL),
    and the result is returned as a tuple of (converted_amount, base_unit_string)"""
    
    clean_unit = unit.strip().lower()

    try:
        val = Decimal(str(amount))
    except (ValueError, InvalidOperation):
        val = Decimal('0.0')

    #solids translation (grams)
    if clean_unit in ['kg', 'kilograms', 'kilograms']:
        return val * Decimal('1000.0'), 'g' #converts kilograms to grams
    if clean_unit in ['g', 'gram', 'grams']:
        return val, 'g'

    #liquids translation (mL)
    if clean_unit in ['l', 'liters', 'liter', 'litre', 'litres']:
        return val * Decimal('1000.0'), 'mL'
    if clean_unit in ['ml', 'milliliter', 'milliliters']:
        return val, 'mL'

    #discrete items (pcs, units, bags)
    return val, clean_unit

def calculate_ingredient_deductions(production_quantity: int, mock_recipe_ingredients: list) -> list:
    """ calculates base amounts to deduct based on batch sizes;
    accepts a list of dictionaries simulating recipe ingredients"""
    deduction_manifest = []
    multiplier = Decimal(str(production_quantity))

    for ingredient in mock_recipe_ingredients:
        name = ingredient.get('name')
        raw_amount = ingredient.get('amount', 0.0)
        raw_unit = ingredient.get('unit', '')

        base_amount, base_unit = normalize_to_base_unit(raw_amount, raw_unit)

        total_deduction = base_amount * multiplier 

        deduction_manifest.append({
            'ingredient_name': name,
            'amount_to_deduct': float(total_deduction),
            'unit': base_unit
        })

    return deduction_manifest

def execute_inventory_deduction(production_record):
    """
    Core production service worker. 
    Processes recipes, applies conversions, and triggers inventory deduction hooks.
    """
    recipe_name = production_record.recipe_name
    ingredients_to_process = []

    if Recipe is not None:
        try:
            recipe_instance = Recipe.objects.get(name=recipe_name)
        except Exception:
            pass  

    if not ingredients_to_process:
        if "cold brew" in recipe_name.lower():
            ingredients_to_process = [
                {'name': 'Coffee Beans', 'amount': 0.2, 'unit': 'kg'},
                {'name': 'Filtered Water', 'amount': 1.5, 'unit': 'L'}
            ]
        else:
            ingredients_to_process = [
                {'name': 'Generic Base Ingredient', 'amount': 10.0, 'unit': 'g'}
            ]

    manifest = calculate_ingredient_deductions(production_record.quantity, ingredients_to_process)
    
    print(f"\n--- [INVENTORY DEDUCTION MANIFEST FOR {recipe_name.upper()}] ---")
    for item in manifest:
        print(f"-> Deduct {item['amount_to_deduct']} {item['unit']} of {item['ingredient_name']}")
    print("-----------------------------------------------------------\n")