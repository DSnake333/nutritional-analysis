from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.utils import secure_filename
import os
import cv2
import easyocr
import re
import requests
from difflib import SequenceMatcher
from itertools import groupby

app = Flask(__name__)

# Set the secret key for the application
app.secret_key = 'dharshak12345'

# Configure the upload folder
UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
edited_ingredients = {}
# Allowed file extensions
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}


def remove_consecutive_duplicates(text):
    # Split the text into words and use groupby to remove consecutive duplicates
    words = text.split()
    return ' '.join(key for key, _ in groupby(words))


def similar(a, b):
    return SequenceMatcher(None, a, b).ratio()
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
def extract_text(image_path):
    # Initialize the EasyOCR Reader with English language
    reader = easyocr.Reader(['en'])

    # Load the image using OpenCV
    image = cv2.imread(image_path)

    # Convert the image to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Apply Adaptive Thresholding to binarize the image
    _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    # Use EasyOCR to extract text from the binarized image
    results = reader.readtext(binary)

    # Concatenate all the detected text into a single string
    extracted_text = ' '.join([result[1] for result in results])

    # Remove all non-alphabetic characters except commas and correct words close to "Ingredients"
    extracted_text = ' '.join(['INGREDIENTS' if similar(word.lower(), 'ingredients') > 0.75 else word
                               for word in re.sub('[^A-Za-z ,]+', '', extracted_text).split()])

    # Further clean the text to remove any stray numbers that may have been missed
    extracted_text = re.sub(r'\b\d+\b', '', extracted_text)
    extracted_text = remove_consecutive_duplicates(extracted_text)

    return extracted_text.strip()


def extract_ingredients(text):
    # Define patterns to match potential ingredient phrases
    ingredient_patterns = [
        r'\b(?:Ingredients?|INGREDIENTS?|Ingredients\s*:\s*|INGREDIENTS\s*:)\s*(.*)',
        # Additional patterns can be added based on common ingredient list formats
    ]

    # Initialize an empty list to store extracted ingredients
    ingredients = []

    # Iterate over each pattern and search for matches in the text
    for pattern in ingredient_patterns:
        matches = re.findall(pattern, text)
        if matches:
            # Append all matches found for this pattern to the list of ingredients
            for match in matches:
                # Handling ingredients with parentheses
                potential_ingredients = re.split(r'(?<!\d)[;,]', match)
                for ingredient in potential_ingredients:
                    # Remove content within parentheses and leading/trailing whitespaces
                    ingredient = re.sub(r"\(.*?\)", "", ingredient).strip()
                    # Filter out non-ingredient phrases and unwanted numbers
                    if ingredient and not re.match(r'^[A-Za-z]+:|\d+$', ingredient):
                        # Handling multi-word ingredients
                        if ' ' in ingredient:
                            ingredients.append({'name': ingredient, 'quantity': 1})  # Default quantity set to 1
                        else:
                            ingredients.append({'name': ingredient, 'quantity': 1})  # Default quantity set to 1
    return ingredients


@app.route('/update-ingredients', methods=['POST'])
def update_ingredients():
    global edited_ingredients  # Access the global variable

    if request.method == 'POST':
        ingredients = request.form.getlist('ingredients[]')
        quantities = request.form.getlist('quantities[]')

        # Update the edited ingredients dictionary
        edited_ingredients = {}
        nutritional_info_list = []  # List to store nutritional info for each ingredient

        for ingredient, quantity in zip(ingredients, quantities):
            edited_ingredients[ingredient] = int(quantity)
            # Get nutritional information for the ingredient
            nutritional_info = get_nutritional_info(ingredient, quantity, edited_ingredients)
            if nutritional_info:
                nutritional_info_list.append(nutritional_info)

        # Store the nutritional info list and edited ingredients in session variables
        session['nutritional_info_list'] = nutritional_info_list
        session['edited_ingredients'] = edited_ingredients

        # Redirect back to the index page
        return redirect(url_for('index'))

def get_nutritional_info(ingredient, quantity, edited_ingredients):
    url = "https://api.edamam.com/api/nutrition-data"
    app_id = "079b8f09"  # Replace with your app ID
    app_key = "8b25577c1d51b8b55861cd3e6d0b06d5"  # Replace with your app key
    ingr_with_quantity = f"{quantity} {ingredient}"  # Use the provided quantity
    params = {
        "app_id": app_id,
        "app_key": app_key,
        "ingr": ingr_with_quantity
    }

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()  # Raise an exception for bad response status
        nutritional_info = response.json()
        return nutritional_info
    except requests.exceptions.RequestException as e:
        print("Request failed:", e)
        return None

def extract_required_fields(nutritional_info):
    required_fields = {
        'uri': nutritional_info.get('uri'),
        'calories': nutritional_info.get('calories'),
        'totalCO2Emissions': nutritional_info.get('totalCO2Emissions'),
        'co2EmissionsClass': nutritional_info.get('co2EmissionsClass'),
        'totalWeight': nutritional_info.get('totalWeight'),
        'dietLabels': nutritional_info.get('dietLabels'),
        'healthLabels': nutritional_info.get('healthLabels'),
        'cautions': nutritional_info.get('cautions'),
        'totalNutrients': nutritional_info.get('totalNutrients', {}),
        'totalDaily': nutritional_info.get('totalDaily', {}),
        'totalNutrientsKCal': nutritional_info.get('totalNutrientsKCal', {}),
        'ingredients': nutritional_info.get('ingredients'),
    }
    return required_fields

def perform_comprehensive_analysis(ingredients_info):
    total_calories = 0
    total_protein = 0
    total_fat = 0
    total_carbohydrates = 0
    total_fiber = 0

    # Iterate over each ingredient's information
    for ingredient_info in ingredients_info:
        total_calories += ingredient_info.get('calories', 0)
        if ingredient_info.get('totalNutrients'):
            total_protein += ingredient_info['totalNutrients'].get('PROCNT', {}).get('quantity', 0)
            total_fat += ingredient_info['totalNutrients'].get('FAT', {}).get('quantity', 0)
            total_carbohydrates += ingredient_info['totalNutrients'].get('CHOCDF', {}).get('quantity', 0)
            total_fiber += ingredient_info['totalNutrients'].get('FIBTG', {}).get('quantity', 0)

    # Create a dictionary to hold the analysis results
    analysis_result = {
        'total_calories': total_calories,
        'total_protein': total_protein,
        'total_fat': total_fat,
        'total_carbohydrates': total_carbohydrates,
        'total_fiber': total_fiber,
        # Add more metrics as needed
    }

    return analysis_result


def assess_healthiness(analysis_result):
    # Define thresholds for assessment
    CALORIES_THRESHOLD = 2000
    PROTEIN_RATIO_MIN = 0.15
    FAT_RATIO_MAX = 0.35
    FIBER_MIN = 3
    FIBER_GOOD = 5

    # Initialize the assessment and reasons
    assessment = "Healthy"
    reasons = []
    unhealthy_ingredients = []
    recommendations = []

    # Extract relevant values from the analysis_result
    total_calories = analysis_result.get('total_calories', 0)
    total_protein = analysis_result.get('total_protein', 0)
    total_fat = analysis_result.get('total_fat', 0)
    total_fiber = analysis_result.get('total_fiber', 0)
    ingredients = analysis_result.get('ingredients', [])

    # Check if total calories are zero
    if total_calories == 0:
        assessment = "Unknown"
        reasons.append("Total calories are zero, unable to determine healthiness.")
        return assessment, reasons, unhealthy_ingredients, recommendations

    # Assess based on calorie threshold
    if total_calories > CALORIES_THRESHOLD:
        assessment = "Unhealthy"
        reasons.append(f"Total calories ({total_calories}) exceed threshold ({CALORIES_THRESHOLD}).")

    # Calculate nutrient ratios
    protein_calories_ratio = total_protein / total_calories if total_calories > 0 else 0
    fat_calories_ratio = total_fat / total_calories if total_calories > 0 else 0

    # Assess protein-to-calories ratio
    if protein_calories_ratio < PROTEIN_RATIO_MIN:
        assessment = "Unhealthy"
        reasons.append(f"Protein to calories ratio ({protein_calories_ratio:.4f}) is less than {PROTEIN_RATIO_MIN}.")
        unhealthy_ingredients.append("Low protein content")
        recommendations.append("Increase protein intake with lean meats, beans, or legumes.")

    # Assess fat-to-calories ratio
    if fat_calories_ratio > FAT_RATIO_MAX:
        assessment = "Unhealthy"
        reasons.append(f"Fat to calories ratio ({fat_calories_ratio:.4f}) is greater than {FAT_RATIO_MAX}.")
        unhealthy_ingredients.append("High fat content")
        recommendations.append("Reduce fat intake by choosing lower-fat alternatives like grilled chicken or fish.")

    # Assess based on fiber content
    if total_fiber < FIBER_MIN:
        assessment = "Moderate"
        reasons.append(f"Total fiber ({total_fiber}) is less than {FIBER_MIN}.")
        unhealthy_ingredients.append("Low fiber content")
        recommendations.append("Increase fiber intake with fruits, vegetables, or whole grains.")
    elif total_fiber < FIBER_GOOD:
        previous_assessment = assessment
        assessment = "Healthy" if assessment == "Healthy" else "Moderate"
        reasons.append(f"Total fiber ({total_fiber}) is between {FIBER_MIN} and {FIBER_GOOD}.")
        unhealthy_ingredients.append("Moderate fiber content")
        recommendations.append("Increase fiber intake with high-fiber foods such as legumes, nuts, and seeds.")
    else:
        if assessment == "Healthy":
            assessment = "Very Healthy"
        reasons.append(f"Total fiber ({total_fiber}) is {FIBER_GOOD} or more.")

    # Ingredient-based assessment
    known_unhealthy_ingredients = ["sugar", "high fructose corn syrup", "trans fats", "saturated fats"]
    for ingredient in ingredients:
        if ingredient.lower() in known_unhealthy_ingredients:
            assessment = "Unhealthy"
            reasons.append(f"Contains unhealthy ingredient: {ingredient}")
            unhealthy_ingredients.append(ingredient)
            if ingredient.lower() in ["sugar", "high fructose corn syrup"]:
                recommendations.append("Reduce sugar intake by choosing products with natural sweeteners or no added sugars.")
            elif ingredient.lower() in ["trans fats", "saturated fats"]:
                recommendations.append("Avoid trans fats and saturated fats by opting for healthier fats like those found in olive oil or avocados.")

    return assessment, reasons, unhealthy_ingredients, recommendations


@app.route('/')
def index():
    global edited_ingredients  # Access the global variable

    # Retrieve the edited ingredients and nutritional information
    ingredients = edited_ingredients.keys()
    nutritional_info = []

    for ingredient in ingredients:
        quantity = edited_ingredients[ingredient]
        info = get_nutritional_info(ingredient, quantity, edited_ingredients)
        if info:
            # Extract required fields for each ingredient
            required_info = extract_required_fields(info)
            nutritional_info.append(required_info)

    # Perform comprehensive analysis
    analysis_result = perform_comprehensive_analysis(nutritional_info)

    # Assess the healthiness based on key metrics
    healthiness_assessment, reasons, unhealthy_ingredients, recommendations = assess_healthiness(analysis_result)

    # Pass the edited ingredients, processed nutritional information, analysis result, and healthiness assessment to the template
    return render_template('index.html', edited_ingredients=edited_ingredients,
                           nutritional_info=nutritional_info, analysis_result=analysis_result,
                           healthiness_assessment=healthiness_assessment, reasons=reasons,
                           unhealthy_ingredients=unhealthy_ingredients, recommendations=recommendations)



@app.route('/upload', methods=['POST'])
def upload():
    if 'image' not in request.files:
        flash('No file part')
        return redirect(request.url)

    file = request.files['image']

    if file.filename == '':
        flash('No selected file')
        return redirect(request.url)

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        # Process the uploaded image
        if os.path.exists(filepath):
            # Extract text from the processed image
            extracted_text = extract_text(filepath)
            # Extract ingredients from the extracted text
            ingredients = extract_ingredients(extracted_text)
            return render_template('index.html', ingredients=ingredients)
        else:
            flash('Failed to process the uploaded image')

        return redirect(url_for('index'))
    else:
        flash('Invalid file format')
        return redirect(request.url)


if __name__ == '__main__':
    app.run(debug=True)
