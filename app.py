import base64
import hashlib
import random
import string
import uuid
import qrcode
from io import BytesIO
from flask import Flask, render_template, request, flash, redirect, url_for
import logging

app = Flask(__name__)
app.secret_key = ''.join(random.choices(string.ascii_letters + string.digits, k=16))

logging.basicConfig(level=logging.INFO)

@app.route('/', methods=['GET'])
def index():
    return render_template("index.html")

def generate_password(length=20, include_numbers=True, include_lowercase=True,
                       include_uppercase=True, include_symbols=True, begin_with_letter=False,
                       no_similar_characters=False, no_duplicate_characters=False,
                       no_sequential_characters=False, custom_symbols=''):
    characters = ''
    if include_numbers:
        characters += string.digits
    if include_lowercase:
        characters += string.ascii_lowercase
    if include_uppercase:
        characters += string.ascii_uppercase
    if include_symbols:
        characters += custom_symbols

    if begin_with_letter and not (include_numbers or include_symbols):
        characters = string.ascii_letters

    if no_similar_characters:
        characters = characters.translate(str.maketrans('', '', 'iloIO01'))

    password = ''.join(random.choice(characters) for _ in range(length))

    if no_duplicate_characters:
        while len(set(password)) != len(password):
            password = ''.join(random.choice(characters) for _ in range(length))

    if no_sequential_characters:
        for i in range(len(password) - 2):
            if password[i:i + 3] in string.ascii_letters + string.digits:
                return generate_password(length, include_numbers, include_lowercase,
                                         include_uppercase, include_symbols, begin_with_letter,
                                         no_similar_characters, no_duplicate_characters,
                                         no_sequential_characters, custom_symbols)
    return password

def generate_passwords(length, include_numbers, include_lowercase,
                       include_uppercase, include_symbols, begin_with_letter,
                       no_similar_characters, no_duplicate_characters,
                       no_sequential_characters, custom_symbols, quantity):
    return [generate_password(length, include_numbers, include_lowercase,
                              include_uppercase, include_symbols, begin_with_letter,
                              no_similar_characters, no_duplicate_characters,
                              no_sequential_characters, custom_symbols)
            for _ in range(quantity)]

@app.route('/password_generator', methods=['POST', 'GET'])
def password_generator_func():
    if request.method == "POST":
        form_data = request.form
        length = int(form_data.get('length', 20))
        quantity = int(form_data.get('quantity', 5))
        include_numbers = form_data.get('include_numbers') == 'on'
        include_lowercase = form_data.get('include_lowercase') == 'on'
        include_uppercase = form_data.get('include_uppercase') == 'on'
        include_symbols = form_data.get('include_symbols') == 'on'
        begin_with_letter = form_data.get('begin_with_letter') == 'on'
        no_similar_characters = form_data.get('no_similar_characters') == 'on'
        no_duplicate_characters = form_data.get('no_duplicate_characters') == 'on'
        no_sequential_characters = form_data.get('no_sequential_characters') == 'on'
        custom_symbols = form_data.get('custom_symbols', '')

        if include_symbols and not custom_symbols:
            flash("Custom symbols cannot be empty.")
            return render_template('password_generator.html')
        
        if not (include_numbers or include_lowercase or include_uppercase):
            flash("You must select at least one character set.")
            return render_template('password_generator.html')
        
        passwords = generate_passwords(length, include_numbers, include_lowercase,
                                        include_uppercase, include_symbols, begin_with_letter,
                                        no_similar_characters, no_duplicate_characters,
                                        no_sequential_characters, custom_symbols, quantity)
        return render_template('password_generator.html', passwords=passwords)
    return render_template("password_generator.html")

hash_algorithms = {
    'blake2b': hashlib.blake2b,
    'blake2s': hashlib.blake2s,
    'md5': hashlib.md5,
    'sha224': hashlib.sha224,
    'sha256': hashlib.sha256,
    'sha384': hashlib.sha384,
    'sha512': hashlib.sha512,
    'sha3': hashlib.sha3_256
}

hash_algorithm_input_types = {
    'blake2b': bytes,
    'blake2s': bytes,
    'md5': bytes,
    'sha224': bytes,
    'sha256': bytes,
    'sha384': bytes,
    'sha512': bytes,
    'sha3': bytes
}

@app.route('/hash_generator', methods=['GET', 'POST'])
def hash_generator_func():
    if request.method == 'POST':
        text = request.form['text']
        selected_algorithm = request.form['algorithm']

        if selected_algorithm not in hash_algorithms:
            flash("Invalid hash algorithm selected.")
            return render_template("hash_generator.html")

        try:
            hashed_text = hash_algorithms[selected_algorithm](text.encode()).hexdigest()
        except Exception as e:
            flash("Error while hashing: " + str(e))
            return render_template("hash_generator.html")

        return render_template('hash_generator.html', text=text, 
                            selected_algorithm=selected_algorithm,
                            generated_hash=hashed_text)
    
    return render_template("hash_generator.html")

@app.route('/uuid_generator', methods=['GET', 'POST'])
def uuid_generator_func():
    if request.method == 'POST':
        try:
            quantity = int(request.form['quantity'])
            if quantity <= 0:
                return "Quantity must be a positive integer."
            uuids = [str(uuid.uuid4()) for _ in range(quantity)]
            return render_template('uuid_generator.html', uuids=uuids)
        except ValueError:
            return "Invalid input. Quantity must be an integer."
        except Exception as e:
            return f"An error occurred: {e}"
    return render_template('uuid_generator.html')

import io
import base64
import logging
from flask import Flask, request, flash, redirect, url_for, render_template
import qrcode

def generate_qr_code(data):
    logging.info(f"Generating QR code for data: {data}")
    try:
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(data)
        qr.make(fit=True)

        img = qr.make_image(fill='black', back_color='white')
        buffered = io.BytesIO()
        img.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode('utf-8')

        logging.info("QR code generated successfully.")
        return f"data:image/png;base64,{img_str}"
    except Exception as e:
        logging.error(f"Error in generate_qr_code function: {e}", exc_info=True)
        raise e

@app.route('/qr_generator', methods=['GET', 'POST'])
def qr_generator_func():
    if request.method == 'POST':
        data = request.form['data']
        logging.info(f"Received data: {data}")

        if not data.strip():
            flash('Please enter some text to generate the QR code.', 'error')
            return redirect(url_for('qr_generator_func'))
        
        try:
            img_data = generate_qr_code(data)
            flash('QR code generated successfully!', 'success')
            return render_template("qr_code_generator.html", img_data=img_data)
        except Exception as e:
            logging.error(f"Error generating QR code: {e}", exc_info=True)
            flash('An error occurred while generating the QR code.', 'error')
            return redirect(url_for('qr_generator_func'))
    return render_template("qr_code_generator.html")

if __name__ == '__main__':
    app.run(debug=True)
