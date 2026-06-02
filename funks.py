import numpy as np
import cv2
import random
import adbutils
import time

# Глобальные переменные вынесены в константы
ADB_HOST = "127.0.0.1"
ADB_PORT = 5037
INPUT_DEVICE = "/dev/input/event4"  # Примечание: может отличаться в зависимости от модели устройства

# Безопасная инициализация глобальной переменной во избежание NameError
adb = None

try:
    adb = adbutils.AdbClient(host=ADB_HOST, port=ADB_PORT)
except Exception as e:
    print(f"Error initializing ADB client: {e}")

def get_device(numb_device):
    """Получение устройства с проверкой подключения"""
    if not adb:
        print("ADB client is not initialized")
        return None
    try:
        current_devices = adb.device_list()
        if not current_devices or numb_device >= len(current_devices):
            print(f"Device {numb_device} not available")
            return None
        return current_devices[numb_device]
    except Exception as e:
        print(f"Error retrieving devices: {e}")
        return None


def install_apk(numb_device, path_apk):
    device = get_device(numb_device)
    if not device:
        return None
    try:
        device.install(path_apk)
        return device
    except Exception as e:
        print(f"Error installing APK: {e}")
        return None


def list_apps(numb_device, all=True):
    device = get_device(numb_device)
    if not device:
        return []
    
    try:
        cmd = "pm list packages" if all else "pm list packages -3"
        get_all_apps = device.shell(cmd)
        if not get_all_apps:
            return []
        
        all_apps = [line.replace("package:", "").strip() for line in get_all_apps.split('\n') if line]
        return all_apps
    except Exception as e:
        print(f"Error listing apps: {e}")
        return []


def uninstall_app(numb_device, app):
    device = get_device(numb_device)
    if not device:
        return
    try:
        device.uninstall(app)
    except Exception as e:
        print(f"Error uninstalling app: {e}")


def get_devices():
    if not adb:
        return 0
    try:
        return len(adb.device_list())
    except Exception as e:
        print(f"Error getting device count: {e}")
        return 0


def get_device_info(numb_device):
    device = get_device(numb_device)
    # Возвращаем стандартное разрешение в качестве фолбека
    fallback_info = {"width": 1080, "height": 2400, "dpi": 440}
    if not device:
        return fallback_info
    
    try:
        # wm size может возвращать несколько строк при наличии Override size
        size_output = device.shell("wm size").strip()
        resolution_str = size_output.split()[-1]
        width, height = map(int, resolution_str.split('x'))
        
        density_output = device.shell("wm density").strip()
        dpi_str = density_output.split()[-1]
        
        return {"width": width, "height": height, "dpi": int(dpi_str)}
    except Exception as e:
        print(f"Error getting device info: {e}")
        return fallback_info
    
    

def app_activity(numb_device):
    device = get_device(numb_device)
    if device:
        try:
            return device.app_current()
        except Exception as e:
            print(f"Error getting app activity: {e}")
    return None


def _execute_device_command(numb_device, command):
    """Общая функция для выполнения команд на устройстве"""
    device = get_device(numb_device)
    if device:
        try:
            return device.shell(command)
        except Exception as e:
            print(f"Command execution error: {e}")
    return None


def app_activity_stop(numb_device, package_activity):
    _execute_device_command(numb_device, f"am force-stop {package_activity}")


def app_activity_clearcache(numb_device, package_activity):
    _execute_device_command(numb_device, f"pm clear {package_activity}")


def app_activity_start(numb_device, package_activity):
    _execute_device_command(numb_device, f"am start {package_activity}")


def screenshot(numb_device, grayscale=False):
    device = get_device(numb_device)
    if not device:
        return None
    
    try:
        # В adbutils метод называется screenshot(), он возвращает объект PIL Image
        pil_image = device.screenshot()
        if pil_image is None:
            return None
            
        # Конвертация PIL Image (RGB) в формат OpenCV
        image = np.array(pil_image)
        if grayscale:
            return cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        return cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
        
    except AttributeError:
        # Резервный вариант на случай старых версий adbutils или специфических ограничений устройства
        try:
            raw_bytes = device.shell("screencap -p", encoding=None)
            if not raw_bytes:
                return None
            image = cv2.imdecode(np.frombuffer(raw_bytes, np.uint8), cv2.IMREAD_COLOR)
            if image is None:
                return None
            return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if grayscale else image
        except Exception as fallback_err:
            print(f"Fallback screenshot error: {fallback_err}")
            return None
            
    except Exception as e:
        print(f"Screenshot error: {e}")
        return None

def _send_event(device, *args):
    """Отправка события на устройство"""
    command = f"sendevent {INPUT_DEVICE} {' '.join(map(str, args))}"
    device.shell(command)


def _micro_movements(device, x_cord, y_cord, min_steps=1, max_steps=3, delay=0.0025):
    """Микродвижения для реалистичности клика"""
    for _ in range(random.randint(min_steps, max_steps)):
        touch_major = random.uniform(10, 50)
        new_x = x_cord + random.randint(-2, 2)
        new_y = y_cord + random.randint(-2, 2)
        
        _send_event(device, 3, 53, new_x)
        _send_event(device, 3, 54, new_y)
        _send_event(device, 3, 48, touch_major)
        _send_event(device, 3, 58, 10)
        _send_event(device, 0, 0, 0)
        time.sleep(delay)


def click_physical(numb_device, x_cord, y_cord):
    device = get_device(numb_device)
    if not device:
        return
    
    touch_major = random.uniform(10, 50)
    
    # Начало касания
    _send_event(device, 1, 330, 1)
    _send_event(device, 1, 325, 1)
    _send_event(device, 3, 57, 10)
    _send_event(device, 3, 53, x_cord)
    _send_event(device, 3, 54, y_cord)
    _send_event(device, 3, 48, touch_major)
    _send_event(device, 0, 0, 0)
    
    # Микродвижения
    _micro_movements(device, x_cord, y_cord)
    
    # Завершение касания
    _send_event(device, 1, 330, 0)
    _send_event(device, 1, 325, 0)
    _send_event(device, 3, 57, 4294967295)
    _send_event(device, 0, 0, 0)


def click(numb_device, x_cord, y_cord, type_click=None, timedelay=0.1):
    device = get_device(numb_device)
    if not device:
        return    
    if type_click == "tap":
        time.sleep(timedelay)
        device.shell(f"input touchscreen tap {x_cord} {y_cord}")
    elif type_click == "long":
        device.shell(f"input touchscreen swipe {x_cord} {x_cord} {y_cord} {y_cord} {int(timedelay)}")
    elif type_click == "sdl":
        click_physical(numb_device, x_cord, y_cord)


def swipe(numb_device, x_cord1, x_cord2, y_cord1, y_cord2, timedelay):
    device = get_device(numb_device)
    if not device:
        return    
    device.shell(f"input touchscreen swipe {x_cord1} {x_cord2} {y_cord1} {y_cord2} {int(timedelay)}")


def home(numb_device):
    _execute_device_command(numb_device, "input keyevent 3")


def back(numb_device):
    _execute_device_command(numb_device, "input keyevent 4")


def send_text(numb_device, text, clear_field=None):
    if clear_field:
        # KEYCODE_MOVE_END (123) — перемещает курсор в самый конец текста
        # KEYCODE_DEL (67) — код удаления символа (Backspace)
        # Объединяем их в одну команду, чтобы удаление выполнилось мгновенно без циклов
        clear_cmd = "input keyevent 123 " + " ".join(["67"] * 1000)
        _execute_device_command(numb_device, clear_cmd)
        time.sleep(0.05)
    
    replacement_sequence = [
        ('\\', '\\\\'),
        (' ', '%s'),
        ('%', '%%'),
        ('&', '\\&'),
        ('(', '\\('),
        (')', '\\)'),
        ('<', '\\<'),
        ('>', '\\>'),
        (';', '\\;'),
        ('*', '\\*'),
        ('?', '\\?'),
        ('[', '\\['),
        (']', '\\]'),
        ('#', '\\#'),
        ('|', '\\|'),
        ('^', '\\^'),
        ('`', '\\`'),
        ('$', '\\$'),
        ('"', '\\"'),
        ("'", "\\'"),
        ('!', '\\!'),
        ('\n', '%s')
    ]
    
    escaped_text = text
    for char, replacement in replacement_sequence:
        escaped_text = escaped_text.replace(char, replacement)
    
    _execute_device_command(numb_device, f"input text {escaped_text}")