from flask import Flask, render_template, request

app = Flask(__name__)


def convert_units(from_unit, to_unit, value):
    try:
        from_unit = str(from_unit).lower()
        to_unit = str(to_unit).lower()
        value = float(value)

        if from_unit == to_unit:
            return value

        if from_unit == "meter" and to_unit == "kilometer":
            converted_value = value / 1000
            return converted_value
        elif from_unit == "kilometer" and to_unit == "meter":
            converted_value = value * 1000
            return converted_value

        if from_unit == "mile" and to_unit == "kilometer":
            converted_value = value * 1.60934
            return converted_value
        elif from_unit == "kilometer" and to_unit == "mile":
            converted_value = value / 1.60934
            return converted_value

        if from_unit == "kilometer" and to_unit == "meter":
            converted_value = value * 1000
            return converted_value
        elif from_unit == "meter" and to_unit == "kilometer":
            converted_value = value / 1000
            return converted_value

        if from_unit == "mile" and to_unit == "meter":
            converted_value = value * 1609.34
            return converted_value
        elif from_unit == "meter" and to_unit == "mile":
            converted_value = value / 1609.34
            return converted_value

        return None
    except ValueError:
        return None


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/unit_converter', methods=['POST'])
def unit_converter():
    converted_value = None
    error_message = None
    if request.method == 'POST':
        from_unit = request.form['from_unit']
        to_unit = request.form['to_unit']
        value = request.form['value']

        try:
            value = float(value)
            converted_value = convert_units(from_unit, to_unit, value)
            if converted_value is None:
                error_message = "😡"
        except ValueError:
            error_message = "Введи по человечески 😡"

    return render_template('index.html', converted_value=converted_value, error_message=error_message)

if __name__ == "__main__":
    app.run(debug=True)
