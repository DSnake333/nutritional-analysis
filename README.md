# Food Product Nutrition Analyzer

This project is aimed at assisting users in analyzing the nutritional content of food products by uploading images of the ingredient lists from the back of food packaging. The system utilizes Optical Character Recognition (OCR) to extract the ingredients as text, retrieves their nutritional information through the EDAMAM API, and then processes this data to provide users with insightful analysis, including text summaries and graphical representations. Additionally, the system explains why a particular product may be considered healthy or unhealthy and offers basic recommendations for dietary adjustments.

## Features

- **Image Upload**: Users can upload images containing the list of ingredients from the packaging of food products.
- **OCR Processing**: Optical Character Recognition (OCR) technology is used to extract text from the uploaded images.
- **Nutritional Information Retrieval**: The system queries the EDAMAM API with the extracted ingredients to obtain their nutritional information.
- **Analysis and Insights**: The retrieved nutritional data is analyzed to provide users with detailed insights into the healthiness of the product.
- **Graphical Representation**: The system generates graphical representations of the nutritional data for better visualization.
- **Explanation and Recommendations**: Users receive explanations on why a product is deemed healthy or unhealthy, along with basic dietary recommendations.

## Installation

1. Clone the repository to your local machine:

  ```bash
  git clone https://github.com/your-username/food-product-nutrition-analyzer.git
  ```
2. Install the required dependencies:

  ```bash
  pip install -r requirements.txt
  ```

3. Set up the necessary API keys:

4. Obtain API credentials from EDAMAM.
5. Update app_id and app_key variables in the code with your credentials.
6. Run the Flask application:

  ```bash
  python app.py
  ```
7. Access the application via http://localhost:5000 in your web browser.

Usage
Upload Image: Navigate to the application and upload an image containing the ingredient list from the packaging.
View Analysis: After processing, the system will display detailed nutritional analysis, including healthiness assessment, reasons, and recommendations.
Technologies Used
Python: Programming language used for backend development.
Flask: Micro web framework used for building the web application.
OpenCV: Library used for image processing.
EasyOCR: Optical Character Recognition (OCR) library for text extraction.
EDAMAM API: API used for retrieving nutritional information.
HTML/CSS: Frontend markup and styling.
Contributing
Contributions to the project are welcome! Feel free to open issues for bug fixes or feature requests, or submit pull requests for enhancements.

License
This project is licensed under the MIT License.
