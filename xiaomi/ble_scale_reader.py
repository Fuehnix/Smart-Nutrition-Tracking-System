import asyncio
import binascii
from bleak import BleakClient
import binascii

SCALE_MAC_ADDRESS = "5C:CA:D3:6F:25:2D"
SERVICE_UUID = "0000181b-0000-1000-8000-00805f9b34fb"
WEIGHT_CHARACTERISTIC_UUID = "00002a9c-0000-1000-8000-00805f9b34fb"

HEIGHT_OF_THIS_PERSON = 166
SEX_OF_THIS_PERSON = "Female"
AGE_OF_THIS_PERSON = 51
INCOME_OF_THIS_PERSON = 100000
EDUDATION_OF_THIS_PERSON = 18
COUNTRY_OF_THIS_PERSON = 'Korea'

def check_value_overflow(value, min_val, max_val):
    return max(min_val, min(max_val, value))

def getBMI(weight):
    return weight / ((HEIGHT_OF_THIS_PERSON / 100) ** 2)   

def get_ideal_weight():
    if SEX_OF_THIS_PERSON == "Female":
        return (HEIGHT_OF_THIS_PERSON - 70) * 0.6
    else:
        return (HEIGHT_OF_THIS_PERSON - 80) * 0.7


def get_metabolic_age(weight, impedance):
    if SEX_OF_THIS_PERSON == "Female":
        return HEIGHT_OF_THIS_PERSON * -1.1165 + weight * 1.5784 + AGE_OF_THIS_PERSON * 0.4615 + impedance * 0.0415 + 83.2548
    else:
        return HEIGHT_OF_THIS_PERSON * -0.7471 + weight * 0.9161 + AGE_OF_THIS_PERSON * 0.4184 + impedance * 0.0517 + 54.2267


def get_LBM_Coefficient(weight, impedance):
    lbm = (HEIGHT_OF_THIS_PERSON * 9.058 / 100) * (HEIGHT_OF_THIS_PERSON / 100)
    lbm += weight * 0.32 + 12.226
    lbm -= impedance * 0.0068
    lbm -= AGE_OF_THIS_PERSON * 0.0542
    return lbm


def get_fat_percentage(weight, impedance):
    value = 0.8
    if SEX_OF_THIS_PERSON == "Female" and AGE_OF_THIS_PERSON <= 49:
        value = 9.25
    elif SEX_OF_THIS_PERSON == "Female":
        value = 7.25

    LBM = get_LBM_Coefficient(weight, impedance)
    coefficient = 1.0

    if SEX_OF_THIS_PERSON == "Male" and weight < 61:
        coefficient = 0.98
    elif SEX_OF_THIS_PERSON == "Female" and weight > 60:
        coefficient *= 1.03 if HEIGHT_OF_THIS_PERSON > 160 else 0.96
    elif SEX_OF_THIS_PERSON == "Female" and weight < 50:
        coefficient *= 1.03 if HEIGHT_OF_THIS_PERSON > 160 else 1.02

    fatPercentage = (1.0 - (((LBM - value) * coefficient) / weight)) * 100
    if fatPercentage > 63:
        fatPercentage = 75
    return fatPercentage


def get_bone_mass(weight, impedance):
    base = 0.245691014 if SEX_OF_THIS_PERSON == "Female" else 0.18016894
    boneMass = (base - (get_LBM_Coefficient(weight, impedance) * 0.05158)) * -1
    boneMass += 0.1 if boneMass > 2.2 else -0.1
    if (SEX_OF_THIS_PERSON == "Female" and boneMass > 5.1) or (SEX_OF_THIS_PERSON == "Male" and boneMass > 5.2):
        boneMass = 8
    return boneMass
    


def get_muscle_mass(weight, impedance):
    fat = get_fat_percentage(weight, impedance)
    bone = get_bone_mass(weight, impedance)
    muscleMass = weight - ((fat / 100) * weight) - bone
    if (SEX_OF_THIS_PERSON == "Female" and muscleMass >= 84) or (SEX_OF_THIS_PERSON == "Male" and muscleMass > 93.5):
        muscleMass = 120
    return muscleMass


def get_water_percentage(weight, impedance):
    fat = get_fat_percentage(weight, impedance)
    waterPercentage = (100 - fat) * 0.7
    coefficient = 1.02 if waterPercentage <= 50 else 0.98
    if waterPercentage * coefficient >= 65:
        waterPercentage = 75
    return waterPercentage * coefficient


def get_protein_percentage(weight, impedance):
    muscle = get_muscle_mass(weight, impedance)
    water = get_water_percentage(weight, impedance)
    return (muscle / weight) * 100 - water


def get_BMR(weight):
    if SEX_OF_THIS_PERSON == "Female":
        bmr = 864.6 + weight * 10.2036 - HEIGHT_OF_THIS_PERSON * 0.39336 - AGE_OF_THIS_PERSON * 6.204
        if bmr > 2996:
            bmr = 5000
    else:
        bmr = 877.8 + weight * 14.916 - HEIGHT_OF_THIS_PERSON * 0.726 - AGE_OF_THIS_PERSON * 8.976
        if bmr > 2322:
            bmr = 5000
    return bmr


def estimate_visceral_fat(weight, impedance):
    fat_percentage = get_fat_percentage(weight, impedance)
    muscle_mass = get_muscle_mass(weight, impedance)    
    height = HEIGHT_OF_THIS_PERSON
    age = AGE_OF_THIS_PERSON
    sex = SEX_OF_THIS_PERSON    

    bmi = weight / ((height / 100) ** 2)

    if sex.lower() == 'female':
        vfat = (
            0.082 * bmi +
            0.062 * age +
            0.14 * fat_percentage +
            (-0.08) * muscle_mass / weight * 100 +
            0.05 * (impedance / (height ** 2)) +
            2.0
        )
    else:
        vfat = (
            0.091 * bmi +
            0.071 * age +
            0.10 * fat_percentage +
            (-0.07) * muscle_mass / weight * 100 +
            0.06 * (impedance / (height ** 2)) +
            1.5
        )

    return max(1, round(vfat, 1))

def predict_life_expectancy(bmi, fat_percentage):
    
    age = AGE_OF_THIS_PERSON
    sex = SEX_OF_THIS_PERSON
    income = INCOME_OF_THIS_PERSON
    education_years = EDUDATION_OF_THIS_PERSON
    country = COUNTRY_OF_THIS_PERSON

    base_life_expectancy = {
        'USA': {'male': 76, 'female': 81},
        'Korea': {'male': 80, 'female': 86},
        'Japan': {'male': 81, 'female': 87},
        'UK': {'male': 79, 'female': 83},
        'Germany': {'male': 78, 'female': 83},
        'France': {'male': 79, 'female': 85},
        'Canada': {'male': 80, 'female': 84},
        'Australia': {'male': 81, 'female': 85},
        'China': {'male': 75, 'female': 78},
        'India': {'male': 68, 'female': 70},
        'Brazil': {'male': 72, 'female': 79},
        'South Africa': {'male': 63, 'female': 67}
    }

    country = country.strip().title()
    sex = sex.strip().lower()

    if country in base_life_expectancy and sex in base_life_expectancy[country]:
        life_expectancy = base_life_expectancy[country][sex]
    else:
        life_expectancy = 72  # world average life expectancy

    # BMI adjustment (sex-specific)
    if sex == 'Female':
        if bmi < 18.5:
            life_expectancy -= 2
        elif 18.5 <= bmi <= 24.9:
            life_expectancy += 2
        elif 25.0 <= bmi <= 29.9:
            life_expectancy += 0  
        else:  # BMI ≥ 30
            life_expectancy -= 3
    else:  # male
        if bmi < 18.5:
            life_expectancy -= 2
        elif 18.5 <= bmi <= 24.9:
            life_expectancy += 2
        elif 25.0 <= bmi <= 29.9:
            life_expectancy += 1  
        else:  # BMI ≥ 30
            life_expectancy -= 2

    # fat percentage adjustment
    if sex == 'Female':
        if fat_percentage < 21:
            life_expectancy -= 1
        elif 21 <= fat_percentage <= 33:
            life_expectancy += 1
        elif 33 < fat_percentage <= 39:
            life_expectancy += 0
        else:  # fat_percentage > 39
            life_expectancy -= 2
    else:  # male
        if fat_percentage < 8:
            life_expectancy -= 1
        elif 8 <= fat_percentage <= 20:
            life_expectancy += 1
        elif 20 < fat_percentage <= 25:
            life_expectancy += 0
        else:  # fat_percentage > 25
            life_expectancy -= 2

    # income adjustment
    if income < 20000:
        life_expectancy -= 2
    elif 20000 <= income < 50000:
        life_expectancy += 0
    elif 50000 <= income < 100000:
        life_expectancy += 1
    else:  # income ≥ 100000
        life_expectancy += 2

    # education adjustment
    if education_years < 12:
        life_expectancy -= 2
    elif 12 <= education_years < 16:
        life_expectancy += 0
    else:  # education_years ≥ 16
        life_expectancy += 2

    # age adjustment
    if age < 0 or age > 120:
        return "Invalid Age."

    # live at least one year more than age
    if life_expectancy < age:
        life_expectancy = age + 1  

    return round(life_expectancy, 1)



def calculate_body_metrics(weight, impedance):
    metrics = {
        "BMI": getBMI(weight),
        "Ideal Weight": get_ideal_weight(),
        "Metabolic Age": get_metabolic_age(weight, impedance),
        "Fat Percentage": get_fat_percentage(weight, impedance),
        "Muscle Mass": get_muscle_mass(weight, impedance),
        "Bone Mass": get_bone_mass(weight, impedance),
        "Water Percentage": get_water_percentage(weight, impedance),
        "Protein Percentage": get_protein_percentage(weight, impedance),
        "BMR": get_BMR(weight),
        "Visceral Fat": estimate_visceral_fat(weight, impedance)
    }

    print("\n🔍 Body Metrics Summary:")
    for key, value in metrics.items():
        print(f" - {key:20}: {value:.2f}")

    # Predict life expectancy
    life_expectancy = predict_life_expectancy(
        bmi = metrics["BMI"],
        fat_percentage=metrics["Fat Percentage"]
    )

    print(f"\n🎯 Predicted Life Expectancy in 2025: {life_expectancy:.1f} years")
    print(f"\n🎯 Predicted Life Expectancy in 2055: {life_expectancy + 30*0.2:.1f} years") # increase by 0.2 years each year
    print(f"\n🎯 Predicted Healthy Life Expectancy in 2055: {life_expectancy + 30*0.2 - 7:.1f} years") # 7 years remaining unhealthy life



def parse_mi_scale_data(sender, data):
    try:
        data = binascii.b2a_hex(data).decode('ascii')
#        print(f"[Notification] {sender} -> data: {data}")

        ctrlByte1 = int(data[2:4], 16)
        isStabilized = ctrlByte1 & (1 << 5)
        hasImpedance = ctrlByte1 & (1 << 1)

        year = int((data[6:8] + data[4:6]), 16)
        month = int(data[8:10], 16)
        day = int(data[10:12], 16)
        date_str = f"{year}-{month:02d}-{day:02d}"

        measunit = int(data[0:2], 16)
        if len(data) >= 20:
            weight = int((data[24:26] + data[22:24]), 16) * 0.01
#            print(f"Extracted weight hex: {data[24:26]} {data[22:24]}")
        else:
            weight = 0

        unit = ''
        if measunit == 0x03: 
            unit = 'lbs'
        elif measunit == 0x02: 
            unit = 'kg' 
            weight = weight / 2

        miimpedance = "N/A"
        if hasImpedance:
            miimpedance = str(int((data[20:22] + data[18:20]), 16))            

        print(f"Date: {date_str}, Weight: {weight:.2f} {unit}, Stabilized: {bool(isStabilized)}, Impedance: {miimpedance}")
        if miimpedance != "N/A":
            try:
                impedance_value = float(miimpedance)
                weight_value = float(weight)
                calculate_body_metrics(weight_value, impedance_value)
            except ValueError:
                print("Invalid impedance")

    except Exception as e:
        print(f"Error parsing data: {e}")

async def read_weight():
    async with BleakClient(SCALE_MAC_ADDRESS) as client:
        try:
            print("Connecting to scale...")

            if client.is_connected:
                print("Already connected.  Disconnecting first...")
                await client.disconnect()
                await asyncio.sleep(1)


            await client.connect()  # try connecting again

            if not client.is_connected:
                print("Failed to connect!")
                return
            
            print("Connected to scale. Fetching services...")

            services = await client.get_services()
            if SERVICE_UUID not in [s.uuid for s in services]:
                print(f"Service {SERVICE_UUID} not found!")
                return

            print("Service found. Enabling notifications...")

            await client.start_notify(WEIGHT_CHARACTERISTIC_UUID, parse_mi_scale_data)
            await asyncio.sleep(10)
            await client.stop_notify(WEIGHT_CHARACTERISTIC_UUID)

        except Exception as e:
            print(f"Error: {e}")
        finally:
            if client.is_connected:
                await client.disconnect()
            print("Disconnected from scale")

asyncio.run(read_weight())