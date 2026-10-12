import math
import re
from pathlib import Path
from PIL import Image, ImageChops

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / 'satellite_data'
IMAGE_EXTENSIONS = {'.png', '.jpg', '.jpeg'}


def year_from_filename(path):
    m = re.search(r'(?:^|[-_ ])(\d{4})(?:$|[-_ .])', Path(path).stem)
    return int(m.group(1)) if m else None


def image_files(folder):
    result = []
    folder = Path(folder)
    if not folder.is_dir():
        return result
    for p in folder.iterdir():
        if p.is_file() and p.suffix.lower() in IMAGE_EXTENSIONS:
            y = year_from_filename(p)
            if y is not None:
                result.append((y, p))
    return sorted(result, key=lambda x: (x[0], x[1].name.casefold()))


LOCATION_ORDER = [
    'BEAR, ALASKA',
    'Breiðamerkurjökull, Iceland',
    'Brunt Ice Shelf, Antarctica',
    'CULOMBIA',
    'Kilimanjaro,tanzania',
    'Petermann, greenland',
    'Svalbard, NORWAY',
    'VERDI,ANTARCTICA',
]

def discover_options():
    # Expose the actual folder names, including folders that currently contain
    # no dated images. This keeps the Location selector identical to the
    # server's satellite_data folder structure.
    options = {}
    if not DATA_DIR.is_dir():
        return options
    for disaster_dir in sorted(DATA_DIR.iterdir(), key=lambda p: p.name.casefold()):
        if not disaster_dir.is_dir():
            continue
        folders = [p for p in disaster_dir.iterdir() if p.is_dir()]
        by_name = {p.name: p.name for p in folders}
        ordered = [name for name in LOCATION_ORDER if name in by_name]
        ordered.extend(sorted((name for name in by_name if name not in LOCATION_ORDER), key=str.casefold))
        if ordered:
            options[disaster_dir.name] = ordered
    if 'GLACIER' in options:
        options = {'GLACIER': options['GLACIER'], **{k:v for k,v in options.items() if k != 'GLACIER'}}
    return options


def calculate_change(image_a, image_b):
    with Image.open(image_a).convert('RGB') as a, Image.open(image_b).convert('RGB') as b:
        a = a.resize(b.size)
        diff = ImageChops.difference(a, b)
        total_pixels = b.width * b.height
        # Per-pixel average difference > 20, matching the project's original threshold.
        significant = sum(1 for r,g,bb in diff.getdata() if (r+g+bb)/3.0 > 20)
    return round((significant / total_pixels) * 100.0, 2) if total_pixels else 0.0


def regression_rate(changes):
    """Fit a non-negative linear rate anchored at the latest image (0% change).

    Each observation is measured against the latest image. Constraining the
    fit through (latest_year, 0) keeps the forecast equation consistent with
    that baseline instead of allowing an unrelated regression intercept.
    """
    if len(changes) < 2:
        return 0.0, None
    latest_year = max(y for y, _ in changes)
    pairs = [(float(latest_year - y), float(change))
             for y, change in changes if y < latest_year]
    denominator = sum(elapsed ** 2 for elapsed, _ in pairs)
    if not pairs or denominator <= 0:
        return 0.0, None
    slope = sum(elapsed * change for elapsed, change in pairs) / denominator
    return max(0.0, slope), 0.0


def predict(changes, future_year, latest_year):
    rate, _ = regression_rate(changes)
    years_ahead = future_year - latest_year
    # Forecast is anchored at 0% in the latest observed year and bounded to
    # the valid percentage range. Callers validate that future_year is later.
    predicted = max(0.0, min(100.0, rate * years_ahead))
    if predicted >= 40:
        risk = 'HIGH'
    elif predicted >= 20:
        risk = 'MODERATE'
    else:
        risk = 'LOW'

    moderate_raw = latest_year + math.ceil(20.0 / rate) if rate > 0 else None
    high_raw = latest_year + math.ceil(40.0 / rate) if rate > 0 else None
    if rate <= 0:
        moderate_year = high_year = None
        window = 'No increasing trend can be estimated from the stored images'
        window_status = 'NO_INCREASING_TREND'
        message = 'The available observations do not support an increasing linear trend; no threshold year is estimated.'
    elif moderate_raw > 2100 or high_raw > 2100:
        moderate_year = moderate_raw if moderate_raw <= 2100 else None
        high_year = high_raw if high_raw <= 2100 else None
        window = f'{moderate_year or "Beyond 2100"} – {high_year or "Beyond 2100"}'
        window_status = 'PARTLY_BEYOND_HORIZON' if moderate_year else 'BEYOND_HORIZON'
        message = 'At least one modeled threshold falls beyond 2100, outside this tool’s supported forecast horizon.'
    else:
        moderate_year, high_year = moderate_raw, high_raw
        window = f'{moderate_year} – {high_year}'
        window_status = 'ESTIMATED_WINDOW'
        message = 'A linear extrapolation of the stored image-difference trend—not a guaranteed physical disaster date.'

    return {
        'future_year': future_year,
        'latest_historical_year': latest_year,
        'predicted_change': round(predicted, 2),
        'risk': risk,
        'annual_change_rate': round(rate, 4),
        'equation': f'change(t) = {rate:.4f} × (t - {latest_year}), bounded to 0–100%',
        'disaster_window': {
            'status': window_status,
            'estimated_from_year': moderate_year,
            'estimated_to_year': high_year,
            'moderate_risk_year': moderate_year,
            'high_risk_year': high_year,
            'estimated_disaster_year': high_year,
            'window': window,
            'message': message,
            'thresholds': {'moderate': 20, 'high': 40},
        },
    }


def analyze(disaster, location, future_year):
    options = discover_options()
    if disaster not in options or location not in options[disaster]:
        raise ValueError('The selected disaster/location is not available in the server dataset.')
    folder = DATA_DIR / disaster / location
    files = image_files(folder)
    if not files:
        raise ValueError(f'No dated satellite images are available for {location}.')
    latest_year, latest_image = files[-1]
    if future_year <= latest_year:
        raise ValueError(f'Enter a future year after {latest_year} for {location}.')
    changes = [[y, calculate_change(p, latest_image)] for y,p in files]
    prediction = predict(changes, future_year, latest_year)
    prediction['baseline_image'] = latest_image.name
    prediction['disaster'] = disaster
    prediction['location'] = location
    risk = prediction['risk']
    return {
        'future_year': future_year,
        'datasets_found': 1,
        'datasets_analyzed': 1,
        'overall': {'risk': risk, 'predicted_change': prediction['predicted_change'], 'location': location, 'disaster': disaster},
        'results': [{
            'disaster': disaster,
            'location': location,
            'status': 'OK',
            'baseline_image': latest_image.name,
            'changes': changes,
            'prediction': prediction,
        }],
        'model_note': 'The latest dated image in the selected server folder is the baseline; earlier images are compared against it.',
    }
