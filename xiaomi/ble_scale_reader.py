import asyncio
import binascii
from bleak import BleakClient
import binascii

SCALE_MAC_ADDRESS = "5C:CA:D3:6F:25:2D"
SERVICE_UUID = "0000181b-0000-1000-8000-00805f9b34fb"
WEIGHT_CHARACTERISTIC_UUID = "00002a9c-0000-1000-8000-00805f9b34fb"

HEIGHT_OF_THIS_PERSON = 166
SEX_OF_THIS_PERSON = "Female"
AGE_OF_THIS_PERSON = 40


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


def get_visceral_fat(weight):
    height = HEIGHT_OF_THIS_PERSON
    age = AGE_OF_THIS_PERSON
    sex = SEX_OF_THIS_PERSON

    if sex == "Female":
        threshold = (height * 0.5) - 13
        if weight > threshold:
            subsubcalc = ((height * 1.45) + (height * 0.1158) * height) - 120
            subcalc = weight * 500 / subsubcalc
            vfal = (subcalc - 6) + (age * 0.07)
        else:
            subcalc = 0.691 + (height * -0.0024) * 2
            vfal = ((height * 0.027) - (subcalc * weight)) * -1 + (age * 0.07) - age
    elif height < weight * 1.6:
        subcalc = (height ** 2 * 0.0826) - (height * 0.4)
        vfal = (weight * 305) / (subcalc + 48) - 2.9 + (age * 0.15)
    else:
        subcalc = 0.765 - height * 0.0015
        vfal = (weight * subcalc - height * 0.143) + (age * 0.15) - 5.0

    return check_value_overflow(vfal, 1, 50)
        


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
        "Visceral Fat": get_visceral_fat(weight)
    }

    print("\n🔍 Body Metrics Summary:")
    for key, value in metrics.items():
        print(f" - {key:20}: {value:.2f}")


def parse_mi_scale_data(sender, data):
    try:
        data = binascii.b2a_hex(data).decode('ascii')
        print(f"[Notification] {sender} -> data: {data}")

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
            print(f"Extracted weight hex: {data[24:26]} {data[22:24]}")
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