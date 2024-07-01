# Invoice Generator

This is a Flask-based web application that generates professional PDF invoices based on user input.

## Features

- Create customized invoices with business and client details
- Add multiple line items with descriptions, quantities, and prices
- Automatically calculate subtotals, taxes, and total amounts
- Upload and include a company logo
- Generate a downloadable PDF invoice

## Prerequisites

- Python 3.7+
- Flask
- ReportLab
- Werkzeug

## Installation

1. Clone this repository
2. Create a virtual environment and activate it: python -m venv env then go -> source env/bin/activate # On Windows, use env\Scripts\activate
3. Install the required packages: pip install flask reportlab werkzeug

## Usage

1. Run the Flask application: python app.py
   
2. Open a web browser and navigate to `http://localhost:5000`

3. Fill out the invoice form with the necessary details

4. Click "Generate Invoice" to create and download the PDF invoice

## File Structure

- `app.py`: Main Flask application file
- `templates/`: Directory containing HTML templates
- `home.html`: Homepage template
- `invoice.html`: Invoice form template
- `uploads/`: Directory for storing uploaded logo files

## Customization

You can customize the invoice design by modifying the `create_pdf()` function in `app.py`. The function uses ReportLab to generate the PDF, allowing for extensive customization of layout, colors, and styling.

## Security Considerations

- This application is set to run in debug mode (`app.run(debug=True)`). Make sure to disable debug mode in a production environment.
- Implement proper input validation and sanitization for all form fields to prevent security vulnerabilities.
- Consider adding user authentication and authorization for a production environment.

## License

This project is open-source and available under the [MIT License](LICENSE).

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
