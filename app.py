from flask import Flask, render_template, request

app = Flask(__name__)

LITERS_TO_GALLONS = 0.264172


def to_float(value, default=0.0):
    try:
        return float(str(value).replace(',', '').strip())
    except (ValueError, TypeError):
        return default


def split_delivery_pair(value: str):
    text = (value or '').strip()
    if '/' in text:
        left, right = text.split('/', 1)
        return left.strip(), right.strip()
    return text, ''


@app.route('/', methods=['GET', 'POST'])
def index():
    results = None
    error = None

    if request.method == 'POST':
        delivery_pairs = request.form.getlist('delivery_pair')
        mcu_liters_list = request.form.getlist('mcu_liters')
        total_freight = to_float(request.form.get('total_freight'))
        product_unit_cost = to_float(request.form.get('product_unit_cost'))

        rows = []
        total_liters = 0.0

        row_count = max(len(delivery_pairs), len(mcu_liters_list))

        for i in range(row_count):
            delivery_pair = delivery_pairs[i].strip() if i < len(delivery_pairs) else ''
            mcu_liters = to_float(mcu_liters_list[i]) if i < len(mcu_liters_list) else 0.0

            if not delivery_pair and mcu_liters == 0:
                continue

            mcu_delivery_number, moc_delivery_number = split_delivery_pair(delivery_pair)
            moc_gallons = mcu_liters * LITERS_TO_GALLONS

            row = {
                'delivery_pair': delivery_pair,
                'mcu_delivery_number': mcu_delivery_number,
                'moc_delivery_number': moc_delivery_number,
                'mcu_liters': mcu_liters,
                'moc_gallons': moc_gallons,
                'freight_total': 0.0,
                'mcu_cost_total': 0.0,
                'is_lynden': mcu_delivery_number.lower() == 'lynden',
                'lynden_freight_cost': None,
                'lynden_product_cost': None,
            }

            rows.append(row)
            total_liters += mcu_liters

        if not rows:
            error = 'Please enter at least one delivery row.'
            return render_template('index.html', results=results, error=error)

        freight_unit_cost = (total_freight / total_liters) if total_liters else 0.0
        total_freight_check = 0.0
        total_product_cost = 0.0

        for row in rows:
            row['freight_total'] = row['mcu_liters'] * freight_unit_cost
            row['mcu_cost_total'] = row['mcu_liters'] * product_unit_cost
            total_freight_check += row['freight_total']
            total_product_cost += row['mcu_cost_total']

            if row['is_lynden'] and row['moc_gallons'] > 0:
                row['lynden_freight_cost'] = row['freight_total'] / row['moc_gallons']
                row['lynden_product_cost'] = row['mcu_cost_total'] / row['moc_gallons']

        # collect MOC delivery numbers (only non-empty values) as comma-separated string
        moc_numbers = [r['moc_delivery_number'] for r in rows if r.get('moc_delivery_number')]
        moc_numbers_str = ','.join(moc_numbers)

        results = {
            'rows': rows,
            'total_liters': total_liters,
            'total_freight': total_freight,
            'freight_unit_cost': freight_unit_cost,
            'product_unit_cost': product_unit_cost,
            'total_freight_check': total_freight_check,
            'total_product_cost': total_product_cost,
            'liters_to_gallons': LITERS_TO_GALLONS,
            'moc_delivery_numbers': moc_numbers_str,
        }

    return render_template('index.html', results=results, error=error)


if __name__ == '__main__':
    app.run(debug=True)
