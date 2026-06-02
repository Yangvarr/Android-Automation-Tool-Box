from screeninfo import get_monitors
import flet as ft
import base64
import cv2
import json
import asyncio
import time
from datetime import datetime

# Импорт словаря локализации
try:
    from locales import LOCALIZATION
except ImportError:
    print("Error: locales.py not found. Please ensure locales.py exists in the same directory.")
    LOCALIZATION = {"en": {}}

# Импорты пользовательских модулей
try:
    from funks import screenshot, home, back, app_activity, get_device_info, app_activity_start, app_activity_stop, app_activity_clearcache, click, send_text, get_devices, swipe, install_apk, uninstall_app, list_apps
    from click_on_image import click_on_image
    from theme import BACKGROUND_COLOR, PRIMARY_COLOR, PRIMARY_COLOR2, SECONDARY_COLOR, ACCENT_COLOR, TEXT_PRIMARY, TEXT_SECONDARY
except ImportError as e:
    print(f"Error importing modules: {e}")

# --- COLOR CONSTANTS ---
COLOR_BLOCK_CLICK = ft.Colors.TEAL_900
COLOR_BLOCK_LOOP = ft.Colors.INDIGO_900
COLOR_BLOCK_CHECK = ft.Colors.PURPLE_900
COLOR_BLOCK_SYSTEM = ft.Colors.BLUE_GREY_900
COLOR_BLOCK_DELAY = ft.Colors.ORANGE_900
COLOR_BLOCK_BREAK = ft.Colors.RED_800
COLOR_BLOCK_TEXT = ft.Colors.GREEN_900
COLOR_BLOCK_SIMPLE_CLICK = ft.Colors.CYAN_900
COLOR_BLOCK_SWIPE = ft.Colors.AMBER_900
COLOR_BLOCK_INSTALL = ft.Colors.GREEN_900
COLOR_BLOCK_UNINSTALL = ft.Colors.RED_900
COLOR_BLOCK_LIST_APPS = ft.Colors.BLUE_900
COLOR_BLOCK_WAIT = ft.Colors.BLUE_900
COLOR_BLOCK_KEYBOARD = ft.Colors.GREY_900

def get_screen_resolution():
    monitor = get_monitors()[0]  # Get the first monitor
    return monitor.width, monitor.height

# Usage
DISPLAY_WIDTH, DISPLAY_HEIGHT = get_screen_resolution()

# --- CODE GENERATOR (TRANSPILER) ---
def generate_python_script(sequence, device_number=0):
    """Generates Python script text from the action sequence."""
    code_lines = []
    indent_step = "    "

    # Script Header
    code_lines.extend([
        "import asyncio",
        "import time",
        "import cv2",
        "try:",
        "    from funks import screenshot, home, back, app_activity, app_activity_start, app_activity_stop, app_activity_clearcache, click, send_text, swipe, install_apk, uninstall_app, list_apps",
        "    from click_on_image import click_on_image",
        "except ImportError:",
        "    print('Error: funks.py or click_on_image.py not found')",
        "",
        "# --- CONFIG ---",
        f"DEVICE_NUMBER = {device_number}",
        "",
        "async def main():",
        f"{indent_step}print('>>> Script Started')",
        ""
    ])

    def parse_actions(actions, level=1):
        """Recursive parser"""
        indent = indent_step * level
        
        for action in actions:
            atype = action.get("type")
            
            # 1. DELAY
            if atype == "delay":
                sec = action.get("delay", 1.0)
                code_lines.append(f"{indent}print(f'Waiting {sec}s...')")
                code_lines.append(f"{indent}await asyncio.sleep({sec})")

            # 2. CLICK / FIND
            elif atype == "click":
                img = action.get("image_path", "")
                conf = action.get("confidence", 0.9)
                clk = action.get("click", True)
                td = action.get("timedelay", 0.1)
                cx = action.get("custom_x")
                cy = action.get("custom_y")
                
                params = f"path_on_template='{img}', clicked={clk}, confidence={conf}, numb_device=DEVICE_NUMBER, timedelay={td}"
                if cx: params += f", custom_x={cx}"
                if cy: params += f", custom_y={cy}"
                
                code_lines.append(f"{indent}print(f'Find/Click: {img}')")
                code_lines.append(f"{indent}if click_on_image({params}):")
                
                # THEN
                if action.get("children"):
                    parse_actions(action["children"], level + 1)
                else:
                    code_lines.append(f"{indent}{indent_step}pass")
                
                # ELSE
                if action.get("else_actions"):
                    code_lines.append(f"{indent}else:")
                    parse_actions(action["else_actions"], level + 1)

            # 3. ACTIVITY CHECK
            elif atype == "activity_check":
                pkg = action.get("target_package")
                act = action.get("target_activity")
                
                code_lines.append(f"{indent}curr = app_activity(DEVICE_NUMBER)")
                conditions = []
                if pkg: conditions.append(f"curr.package == '{pkg}'")
                if act: conditions.append(f"curr.activity == '{act}'")
                cond_str = " and ".join(conditions) if conditions else "True"
                
                code_lines.append(f"{indent}if curr and {cond_str}:")
                if action.get("children"):
                    parse_actions(action["children"], level + 1)
                else:
                    code_lines.append(f"{indent}{indent_step}pass")
                if action.get("else_actions"):
                    code_lines.append(f"{indent}else:")
                    parse_actions(action["else_actions"], level + 1)

            # 4. WHILE LOOP
            elif atype == "while_loop":
                max_iter = int(action.get("max_iterations", 0))
                code_lines.append(f"{indent}loop_iter = 0")
                code_lines.append(f"{indent}loop_start = time.time()")
                code_lines.append(f"{indent}print('Entering Loop...')")
                code_lines.append(f"{indent}while True:")
                
                lvl_loop = level + 1
                ind_loop = indent_step * lvl_loop
                
                if max_iter > 0:
                    code_lines.append(f"{ind_loop}if loop_iter >= {max_iter}: break")
                
                # Exit conditions
                for cond in action.get("break_conditions", []):
                    ctype = cond.get("type")
                    if ctype == "click":
                        img = cond["image_path"]
                        conf = cond.get("confidence", 0.9)
                        code_lines.append(f"{ind_loop}if click_on_image('{img}', clicked=False, confidence={conf}, numb_device=DEVICE_NUMBER):")
                        code_lines.append(f"{ind_loop}{indent_step}print('Break: Image found')")
                        code_lines.append(f"{ind_loop}{indent_step}break")
                    elif ctype == "activity_check":
                        pkg = cond.get("target_package")
                        code_lines.append(f"{ind_loop}c_app = app_activity(DEVICE_NUMBER)")
                        code_lines.append(f"{ind_loop}if c_app and c_app.package == '{pkg}':")
                        code_lines.append(f"{ind_loop}{indent_step}print('Break: Activity match')")
                        code_lines.append(f"{ind_loop}{indent_step}break")
                    elif ctype == "break_timer":
                        dur = cond.get("duration", 0)
                        code_lines.append(f"{ind_loop}if (time.time() - loop_start) > {dur}:")
                        code_lines.append(f"{ind_loop}{indent_step}print('Break: Timeout')")
                        code_lines.append(f"{ind_loop}{indent_step}break")

                # Loop body
                if action.get("actions"):
                    parse_actions(action["actions"], lvl_loop)
                else:
                    code_lines.append(f"{ind_loop}pass")
                
                code_lines.append(f"{ind_loop}loop_iter += 1")
                code_lines.append(f"{ind_loop}await asyncio.sleep(0.1)")

            # 5. SYSTEM
            elif atype == "app_start":
                code_lines.append(f"{indent}app_activity_start(DEVICE_NUMBER, '{action.get('package_name')}')")
            elif atype == "app_stop":
                code_lines.append(f"{indent}app_activity_stop(DEVICE_NUMBER, '{action.get('package_name')}')")
            elif atype == "app_clear_cache":
                code_lines.append(f"{indent}app_activity_clearcache(DEVICE_NUMBER, '{action.get('package_name')}')")
            elif atype == "home":
                code_lines.append(f"{indent}home(DEVICE_NUMBER)")
            elif atype == "back":
                code_lines.append(f"{indent}back(DEVICE_NUMBER)")

            # 6. SEND TEXT
            elif atype == "send_text":
                text = action.get("text", "")
                clear = action.get("clear_field", None)
                code_lines.append(f"{indent}print(f'Sending text: {text}')")
                if clear is not None:
                    code_lines.append(f"{indent}send_text(DEVICE_NUMBER, '{text}', clear_field={clear})")
                else:
                    code_lines.append(f"{indent}send_text(DEVICE_NUMBER, '{text}')")

            # 7. SIMPLE CLICK
            elif atype == "simple_click":
                x = action.get("x", 0)
                y = action.get("y", 0)
                click_type = action.get("click_type", None)
                if click_type == "long":
                    td = float(action.get("timedelay", 70.0))    
                else:
                    td = float(action.get("timedelay", 0.1))
                
                params = f"DEVICE_NUMBER, {x}, {y}"
                if click_type: params += f", type_click='{click_type}'"
                params += f", timedelay={td}"
                
                code_lines.append(f"{indent}print(f'Clicking at ({x}, {y})')")
                code_lines.append(f"{indent}click({params})")

            # 8. SWIPE
            elif atype == "swipe":
                x1 = action.get("x1", 0)
                y1 = action.get("y1", 0)
                x2 = action.get("x2", 0)
                y2 = action.get("y2", 0)
                td = action.get("timedelay", 70.0)
                
                code_lines.append(f"{indent}print(f'Swipe from ({x1},{y1}) to ({x2},{y2})')")
                code_lines.append(f"{indent}swipe(DEVICE_NUMBER, {x1}, {y1}, {x2}, {y2}, {td})")

            # 9. INSTALL APK
            elif atype == "install_apk":
                path = action.get("path_apk", "")
                code_lines.append(f"{indent}print(f'Installing APK: {path}')")
                code_lines.append(f"{indent}install_apk(DEVICE_NUMBER, '{path}')")

            # 10. UNINSTALL APP
            elif atype == "uninstall_app":
                package = action.get("package", "")
                code_lines.append(f"{indent}print(f'Uninstalling app: {package}')")
                code_lines.append(f"{indent}uninstall_app(DEVICE_NUMBER, '{package}')")

            # 11. WAIT FOR IMAGE
            elif atype == "wait_for_image":
                img = action.get("image_path", "")
                conf = action.get("confidence", 0.9)
                timeout = action.get("timeout", 10.0)
                code_lines.append(f"{indent}print('Waiting for image {img} up to {timeout}s...')")
                code_lines.append(f"{indent}start_wait = time.time()")
                code_lines.append(f"{indent}found = False")
                code_lines.append(f"{indent}while (time.time() - start_wait) < {timeout}:")
                code_lines.append(f"{indent}    if click_on_image('{img}', clicked=False, confidence={conf}, numb_device=DEVICE_NUMBER):")
                code_lines.append(f"{indent}        found = True")
                code_lines.append(f"{indent}        break")
                code_lines.append(f"{indent}    await asyncio.sleep(0.5)")
                code_lines.append(f"{indent}if not found: print('Timeout waiting for image!')")


            code_lines.append("") 

    parse_actions(sequence, level=1)
    
    # Footer
    code_lines.extend([
        f"{indent_step}print('<<< Script Finished')",
        "",
        "if __name__ == '__main__':",
        f"{indent_step}asyncio.run(main())"
    ])
    
    return "\n".join(code_lines)

def main(page: ft.Page):
    # --- PAGE SETTINGS ---
    page.title = "Android Automation Tool Box v.0.0.0.1a"
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 10
    page.bgcolor = BACKGROUND_COLOR
    page.spacing = 0

    # --- GLOBAL SYSTEM CONFIG ---
    device_number = 0
    current_screenshot = None
    
    action_sequence = []
    is_running_sequence = False
    
    # Active localization language key
    current_lang = "en"

    def t(key):
        """Helper function to fetch localized text elements."""
        return LOCALIZATION.get(current_lang, {}).get(key, key)
    
    # Device dimensions
    device_info = get_device_info(numb_device=device_number) or {"width": 1080, "height": 2400}
    
    # Crop parameters
    is_selecting = False
    selection_start = None
    selection_end = None
    selection_rect = None
    
    # Preview operational mode
    image_mode = "crop"
    
    # UI references
    image_container_ref = ft.Ref[ft.Container]()
    
    # --- DYNAMIC SCALE COEFFICIENT ---
    def get_current_coef():
        """Returns scaling coefficient between actual screen resolution and frame preview."""
        if current_screenshot is not None and image_container.height:
            return current_screenshot.shape[0] / image_container.height
        return VIEW_COEF

    # --- FILE SELECTION EVENTS ---
    def select_json_result(e: ft.FilePickerResultEvent):
        if e.files:
            tf_filepath.value = e.files[0].path
            tf_filepath.update()
            load_json(None)

    def select_apk_result(e: ft.FilePickerResultEvent):
        if e.files:
            install_apk_field.value = e.files[0].path
            install_apk_field.update()

    json_picker = ft.FilePicker(on_result=select_json_result)
    apk_picker = ft.FilePicker(on_result=select_apk_result)
    page.overlay.extend([json_picker, apk_picker])

    # --- AUTOMATION ENGINE ---
    async def execute_sequence_recursive(actions_list, prefix=""):
        if not is_running_sequence: return

        for i, action in enumerate(actions_list):
            if not is_running_sequence: break
            
            act_type = action.get("type")
            log_prefix = f"{prefix}[{i+1}]"
            
            try:
                # 1. DELAY
                if act_type == "delay":
                    sec = float(action.get("delay", 1.0))
                    update_status(f"{log_prefix} Wait {sec} sec...")
                    await asyncio.sleep(sec)

                # 2. CLICK / FIND
                elif act_type == "click":
                    img_path = action.get("image_path", "")
                    do_click = action.get("click", True)
                    conf = float(action.get("confidence", 0.97))
                    
                    update_status(f"{log_prefix} Finding: {img_path}...")
                    
                    result = click_on_image(
                        path_on_template=img_path,
                        clicked=do_click,
                        confidence=conf,
                        numb_device=device_number,
                        timedelay=float(action.get("timedelay", 0.1)),
                        custom_x=action.get("custom_x"),
                        custom_y=action.get("custom_y")
                    )
                    
                    if result:
                        update_status(f"{log_prefix} Complete. Do THEN...")
                        if action.get("children"):
                            await execute_sequence_recursive(action["children"], prefix=f"{log_prefix}+")
                    else:
                        update_status(f"{log_prefix} Not Found. Do ELSE...")
                        if action.get("else_actions"):
                            await execute_sequence_recursive(action["else_actions"], prefix=f"{log_prefix}-")

                # 3. ACTIVITY CHECK
                elif act_type == "activity_check":
                    update_status(f"{log_prefix} Check Activity...")
                    current = app_activity(device_number)
                    match = False
                    
                    if current:
                        target_act = action.get("target_activity")
                        target_pkg = action.get("target_package")
                        
                        match = True
                        if target_act and target_act != current.activity: match = False
                        if target_pkg and target_pkg != current.package: match = False
                    
                    if match:
                        if action.get("children"): await execute_sequence_recursive(action["children"], prefix=f"{log_prefix}+")
                    else:
                        if action.get("else_actions"): await execute_sequence_recursive(action["else_actions"], prefix=f"{log_prefix}-")

                # 4. WHILE LOOP
                elif act_type == "while_loop":
                    max_iter = int(action.get("max_iterations", 0))
                    iteration = 0
                    loop_start_time = time.time()
                    
                    while is_running_sequence:
                        if max_iter > 0 and iteration >= max_iter:
                            update_status(f"{log_prefix} Loop complete (Max iteration).")
                            break
                        
                        should_break = False
                        break_reason = ""
                        
                        for cond in action.get("break_conditions", []):
                            c_type = cond.get("type")
                            
                            if c_type == "click":
                                res = click_on_image(
                                    path_on_template=cond["image_path"],
                                    clicked=False,
                                    confidence=float(cond.get("confidence", 0.9)),
                                    numb_device=device_number
                                )
                                if res:
                                    should_break = True
                                    break_reason = f"Finded image: {cond.get('image_path')}"
                                    break

                            elif c_type == "activity_check":
                                current = app_activity(device_number)
                                if current:
                                    t_pkg = cond.get("target_package")
                                    t_act = cond.get("target_activity")
                                    
                                    match_act = True
                                    if t_pkg and t_pkg != current.package: match_act = False
                                    if t_act and t_act != current.activity: match_act = False
                                    
                                    if match_act:
                                        should_break = True
                                        break_reason = f"Activity matched: {current.package}"
                                        break

                            elif c_type == "break_timer":
                                duration = float(cond.get("duration", 0))
                                elapsed = time.time() - loop_start_time
                                if elapsed > duration:
                                    should_break = True
                                    break_reason = f"Timeout ({elapsed:.1f}s > {duration}s)"
                                    break
                        
                        if should_break:
                            update_status(f"{log_prefix} BREAK: {break_reason}")
                            break

                        update_status(f"{log_prefix} Iteration {iteration+1}")
                        
                        if action.get("actions"):
                            await execute_sequence_recursive(action["actions"], prefix=f"{log_prefix}L")
                        
                        iteration += 1
                        await asyncio.sleep(0.1)

                # 5. SYSTEM ACTIONS
                elif act_type == "app_start":
                    app_activity_start(device_number, action.get('package_name'))
                elif act_type == "app_stop":
                    app_activity_stop(device_number, action.get('package_name'))
                elif act_type == "app_clear_cache":
                    app_activity_clearcache(device_number, action.get('package_name'))
                elif act_type == "home":
                    home(device_number)
                elif act_type == "back":
                    back(device_number)

                # 6. SEND TEXT
                elif act_type == "send_text":
                    text = action.get("text", "")
                    clear_field = action.get("clear_field", None)
                    update_status(f"{log_prefix} Sending text: {text}")
                    send_text(device_number, text, clear_field)

                # 7. SIMPLE CLICK
                elif act_type == "simple_click":
                    x = int(action.get("x", 0))
                    y = int(action.get("y", 0))
                    click_type = action.get("click_type", None)
                    timedelay = float(action.get("timedelay", 70.0))    
                    update_status(f"{log_prefix} Clicking at ({x}, {y})")
                    click(device_number, x, y, click_type, timedelay)

                # 8. SWIPE
                elif act_type == "swipe":
                    x1 = int(action.get("x1", 0))
                    y1 = int(action.get("y1", 0))
                    x2 = int(action.get("x2", 0))
                    y2 = int(action.get("y2", 0))
                    timedelay = float(action.get("timedelay", 70.0))
                    
                    update_status(f"{log_prefix} Swipe from ({x1},{y1}) to ({x2},{y2})")
                    swipe(device_number, x1, y1, x2, y2, timedelay)

                # 9. INSTALL APK
                elif act_type == "install_apk":
                    path = action.get("path_apk", "")
                    update_status(f"{log_prefix} Installing APK: {path}")
                    install_apk(device_number, path)

                # 10. UNINSTALL APP
                elif act_type == "uninstall_app":
                    package = action.get("package", "")
                    update_status(f"{log_prefix} Uninstalling app: {package}")
                    uninstall_app(device_number, package)

                # 11. WAIT FOR IMAGE
                elif act_type == "wait_for_image":
                    img_path = action.get("image_path", "")
                    conf = float(action.get("confidence", 0.97))
                    timeout = float(action.get("timeout", 10.0))
                    
                    update_status(f"{log_prefix} Waiting for image {img_path} (max {timeout}s)...")
                    start_time = time.time()
                    found = False
                    while is_running_sequence and (time.time() - start_time) < timeout:
                        res = click_on_image(
                            path_on_template=img_path,
                            clicked=False,
                            confidence=conf,
                            numb_device=device_number
                        )
                        if res:
                            found = True
                            break
                        await asyncio.sleep(0.5)
                    
                    if found:
                        update_status(f"{log_prefix} Image found.")
                    else:
                        update_status(f"{log_prefix} Timeout: Image not found.")


            except Exception as ex:
                update_status(f"Error in {act_type}: {ex}")
                print(f"Error executing action: {ex}")

    # --- UI INTERFACES ---
    log_listview = ft.ListView(expand=True, spacing=3, auto_scroll=True)

    def update_status(text):
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_listview.controls.append(ft.Text(f"[{timestamp}] {text}", size=11, font_family="monospace"))
        page.update()

    async def run_btn_click(e):
        nonlocal is_running_sequence
        if not action_sequence:
            update_status(t("status_list_empty"))
            return
        
        is_running_sequence = True
        btn_run.disabled = True
        btn_stop.disabled = False
        page.update()
        
        await execute_sequence_recursive(action_sequence)
        
        is_running_sequence = False
        btn_run.disabled = False
        btn_stop.disabled = True
        update_status("Complete.")
        page.update()


    def export_click(e):
        if not action_sequence:
            update_status(t("status_export_nothing"))
            return
        script_text = generate_python_script(action_sequence, device_number=device_number)
        
        tf_code = ft.TextField(value=script_text, multiline=True, min_lines=10, max_lines=40, read_only=True, text_size=12, expand=True)
        
        def copy_to_clipboard(e):
            page.set_clipboard(script_text)
            page.snack_bar = ft.SnackBar(ft.Text(t("status_copied_clipboard")))
            page.snack_bar.open = True
            page.update()

        def save_file(e):
            try:
                fname = f"script_{datetime.now().strftime('%Y%m%d_%H%M%S')}.py"
                with open(fname, "w", encoding="utf-8") as f:
                    f.write(script_text)
                page.snack_bar = ft.SnackBar(ft.Text(f"{t('status_saved')}: {fname}"))
                page.snack_bar.open = True
                page.update()
            except Exception as ex:
                print(ex)

        dlg = ft.AlertDialog(
            title=ft.Text("Export to Python"),
            content=ft.Container(tf_code, width=page.width, height=page.height),
            bgcolor=PRIMARY_COLOR2,
            actions=[
                ft.TextButton(icon=ft.Icons.COPY, icon_color=ACCENT_COLOR, on_click=copy_to_clipboard),
                ft.TextButton(icon=ft.Icons.SAVE, icon_color=ACCENT_COLOR, on_click=save_file),
                ft.TextButton(icon=ft.Icons.CLOSE, icon_color=ACCENT_COLOR, on_click=lambda e: page.close(dlg))
            ]
        )
        page.open(dlg)
    

    def stop_btn_click(e):
        nonlocal is_running_sequence
        is_running_sequence = False
        update_status("Stoping...")


    def clear_selection(e=None):
        """Clears crop selections"""
        nonlocal is_selecting, selection_start, selection_end
        is_selecting = False
        selection_start = None
        selection_end = None
        
        if selection_overlay in image_stack.controls:
            image_stack.controls.remove(selection_overlay)
        
        selection_buttons.visible = False
        pixel_info_text.value = t("pixel_info_default")
        image_stack.update()

    # --- ACTION CREATION MODAL ---
    def open_action_dialog(action_dict=None, parent_list=None, index=None, insert_mode=False):
        temp_data = action_dict.copy() if action_dict else {"type": "click"}
        
        dd_type = ft.Dropdown(
            label=t("type_doing"),
            value=temp_data.get("type", "click"),
            bgcolor=PRIMARY_COLOR2,
            options=[
                ft.dropdown.Option("click", "Find/Click"),
                ft.dropdown.Option("simple_click", "Simple Click"),
                ft.dropdown.Option("send_text", "Send Text"),
                ft.dropdown.Option("swipe", "Swipe"),
                ft.dropdown.Option("while_loop", "While"),
                ft.dropdown.Option("activity_check", "Check Activity"),
                ft.dropdown.Option("break_timer", "Timer (break)"),
                ft.dropdown.Option("delay", "Delay (Pause)"),
                ft.dropdown.Option("app_start", "Start App"),
                ft.dropdown.Option("app_stop", "Stop App"),
                ft.dropdown.Option("app_clear_cache", "Clear cache"),
                ft.dropdown.Option("home", "Home"),
                ft.dropdown.Option("back", "Back"),
                ft.dropdown.Option("install_apk", "Install APK"),
                ft.dropdown.Option("uninstall_app", "Uninstall App"),
                ft.dropdown.Option("wait_for_image", "Wait for Image"),
            ],
            disabled=not insert_mode
        )
        
        fields_container = ft.Column()
        
        tf_image = ft.TextField(label=t("path_image"), bgcolor=PRIMARY_COLOR2, value=temp_data.get("image_path", ""))
        tf_conf = ft.TextField(label=t("confidence"), bgcolor=PRIMARY_COLOR2, value=str(temp_data.get("confidence", 0.97)), width=150)
        sw_click = ft.Switch(label=t("click_or_not"), active_color=ACCENT_COLOR, value=temp_data.get("click", True))
        tf_delay = ft.TextField(label=t("pause_sec"), bgcolor=PRIMARY_COLOR2, value=str(temp_data.get("timedelay", 0.1)), width=150)
        tf_custom_x = ft.TextField(label=t("custom_x"), bgcolor=PRIMARY_COLOR2, value=str(temp_data.get("custom_x") or ""), width=100)
        tf_custom_y = ft.TextField(label=t("custom_y"), bgcolor=PRIMARY_COLOR2, value=str(temp_data.get("custom_y") or ""), width=100)
        
        tf_x = ft.TextField(label=t("x_coordinate"), bgcolor=PRIMARY_COLOR2, value=str(temp_data.get("x", "")), width=100)
        tf_y = ft.TextField(label=t("y_coordinate"), bgcolor=PRIMARY_COLOR2, value=str(temp_data.get("y", "")), width=100)
        dd_click_type = ft.Dropdown(
            label=t("click_type"),
            bgcolor=PRIMARY_COLOR2,
            value=temp_data.get("click_type", ""),
            options=[
                ft.dropdown.Option("tap", "Tap"),
                ft.dropdown.Option("long", "Long Press"),
                ft.dropdown.Option("sdl", "PhC"),
            ],
            width=150
        )
        
        tf_text = ft.TextField(label=t("text_to_send"), bgcolor=PRIMARY_COLOR2, value=temp_data.get("text", ""), multiline=True, min_lines=2, max_lines=4)
        sw_clear_field = ft.Switch(label=t("clear_field_first"), active_color=ACCENT_COLOR, value=temp_data.get("clear_field", False))
        
        tf_pkg = ft.TextField(label=t("package_name"), bgcolor=PRIMARY_COLOR2, value=temp_data.get("package_name") or temp_data.get("target_package") or "")
        tf_act = ft.TextField(label=t("target_activity"), bgcolor=PRIMARY_COLOR2, value=temp_data.get("target_activity", ""))
        
        tf_seconds = ft.TextField(label=t("sec"), bgcolor=PRIMARY_COLOR2, value=str(temp_data.get("delay", 1.0)))
        tf_iter = ft.TextField(label=t("max_iteration"), bgcolor=PRIMARY_COLOR2, value=str(temp_data.get("max_iterations", 0)))
        
        tf_break_duration = ft.TextField(label=t("limit_time"), bgcolor=PRIMARY_COLOR2, value=str(temp_data.get("duration", 30.0)))
        
        tf_swipe_x1 = ft.TextField(label="X1", bgcolor=PRIMARY_COLOR2, value=str(temp_data.get("x1", "")), width=80)
        tf_swipe_y1 = ft.TextField(label="Y1", bgcolor=PRIMARY_COLOR2, value=str(temp_data.get("y1", "")), width=80)
        tf_swipe_x2 = ft.TextField(label="X2", bgcolor=PRIMARY_COLOR2, value=str(temp_data.get("x2", "")), width=80)
        tf_swipe_y2 = ft.TextField(label="Y2", bgcolor=PRIMARY_COLOR2, value=str(temp_data.get("y2", "")), width=80)
        tf_swipe_delay = ft.TextField(label=t("delay_ms"), bgcolor=PRIMARY_COLOR2, value=str(temp_data.get("timedelay", 70.0)), width=100)
        
        tf_install_path = ft.TextField(label=t("path_to_apk"), bgcolor=PRIMARY_COLOR2, value=temp_data.get("path_apk", ""))
        tf_uninstall_package = ft.TextField(label=t("package_uninstall"), bgcolor=PRIMARY_COLOR2, value=temp_data.get("package", ""))
        sw_list_all = ft.Switch(label=t("all_apps"), active_color=ACCENT_COLOR, value=temp_data.get("all", False))

        # Wait fields
        tf_timeout = ft.TextField(label=t("timeout_sec"), bgcolor=PRIMARY_COLOR2, value=str(temp_data.get("timeout", 10.0)), width=150)

        dlg_ref = {"value": None}

        def update_fields(e=None):
            t_val = dd_type.value
            fields_container.controls.clear()
            
            if t_val == "click":
                fields_container.controls.extend([tf_image, ft.Row([tf_conf, tf_delay]), sw_click, ft.Row([tf_custom_x, tf_custom_y])])
            elif t_val == "simple_click":
                fields_container.controls.extend([
                    ft.Text(t("dialog_coordinates"), size=12, color="grey"),
                    ft.Row([tf_x, tf_y]),
                    dd_click_type,
                    tf_delay
                ])
            elif t_val == "send_text":
                fields_container.controls.extend([tf_text, sw_clear_field])
            elif t_val == "swipe":
                fields_container.controls.extend([
                    ft.Text(t("dialog_swipe_coordinates"), size=12, color="grey"),
                    ft.Row([tf_swipe_x1, tf_swipe_y1]),
                    ft.Row([tf_swipe_x2, tf_swipe_y2]),
                    tf_swipe_delay
                ])
            elif t_val == "activity_check":
                fields_container.controls.extend([tf_pkg, tf_act])
            elif t_val == "while_loop":
                fields_container.controls.extend([tf_iter, ft.Text(t("dialog_if_break"), size=12, color="grey")])
            elif t_val == "delay":
                fields_container.controls.extend([tf_seconds])
            elif t_val == "break_timer":
                fields_container.controls.extend([ft.Text(t("dialog_break_while"), size=12), tf_break_duration])
            elif t_val in ["app_start", "app_stop", "app_clear_cache"]:
                fields_container.controls.extend([tf_pkg])
            elif t_val == "install_apk":
                fields_container.controls.extend([tf_install_path])
            elif t_val == "uninstall_app":
                fields_container.controls.extend([tf_uninstall_package])
            elif t_val == "list_apps":
                fields_container.controls.extend([sw_list_all])
            elif t_val == "wait_for_image":
                fields_container.controls.extend([tf_image, ft.Row([tf_conf, tf_timeout])])
            
            if dlg_ref["value"]: page.update()

        dd_type.on_change = update_fields
        update_fields()

        def save_close(e):
            t_val = dd_type.value
            new_action = {"type": t_val}
            
            if t_val == "click":
                new_action.update({
                    "image_path": tf_image.value,
                    "confidence": float(tf_conf.value or 0.97),
                    "click": sw_click.value,
                    "timedelay": float(tf_delay.value or 0.1),
                    "custom_x": int(tf_custom_x.value) if tf_custom_x.value else None,
                    "custom_y": int(tf_custom_y.value) if tf_custom_y.value else None,
                    "children": temp_data.get("children", []),
                    "else_actions": temp_data.get("else_actions", [])
                })
            elif t_val == "simple_click":
                new_action.update({
                    "x": int(tf_x.value) if tf_x.value else 0,
                    "y": int(tf_y.value) if tf_y.value else 0,
                    "click_type": dd_click_type.value if dd_click_type.value else None,
                    "timedelay": float(tf_delay.value or 0.1)
                })
            elif t_val == "send_text":
                new_action.update({
                    "text": tf_text.value,
                    "clear_field": sw_clear_field.value
                })
            elif t_val == "swipe":
                new_action.update({
                    "x1": int(tf_swipe_x1.value) if tf_swipe_x1.value else 0,
                    "y1": int(tf_swipe_y1.value) if tf_swipe_y1.value else 0,
                    "x2": int(tf_swipe_x2.value) if tf_swipe_x2.value else 0,
                    "y2": int(tf_swipe_y2.value) if tf_swipe_y2.value else 0,
                    "timedelay": float(tf_swipe_delay.value or 70.0)
                })
            elif t_val == "activity_check":
                new_action.update({
                    "target_package": tf_pkg.value,
                    "target_activity": tf_act.value,
                    "children": temp_data.get("children", []),
                    "else_actions": temp_data.get("else_actions", [])
                })
            elif t_val == "while_loop":
                new_action.update({
                    "max_iterations": int(tf_iter.value or 0),
                    "actions": temp_data.get("actions", []),
                    "break_conditions": temp_data.get("break_conditions", [])
                })
            elif t_val == "break_timer":
                new_action["duration"] = float(tf_break_duration.value or 0)
            elif t_val == "delay":
                new_action["delay"] = float(tf_seconds.value or 1.0)
            elif t_val in ["app_start", "app_stop", "app_clear_cache"]:
                new_action["package_name"] = tf_pkg.value
            elif t_val == "install_apk":
                new_action["path_apk"] = tf_install_path.value
            elif t_val == "uninstall_app":
                new_action["package"] = tf_uninstall_package.value
            elif t_val == "list_apps":
                new_action["all"] = sw_list_all.value
            elif t_val == "wait_for_image":
                new_action.update({
                    "image_path": tf_image.value,
                    "confidence": float(tf_conf.value or 0.97),
                    "timeout": float(tf_timeout.value or 10.0)
                })

            if insert_mode:
                parent_list.append(new_action)
            else:
                action_dict.clear()
                action_dict.update(new_action)
            
            page.close(dlg_ref["value"])
            render_sequence_ui()
            page.update()

        dlg = ft.AlertDialog(
            title=ft.Text(t("dialog_title")),
            bgcolor=PRIMARY_COLOR2,
            content=ft.Container(content=ft.Column([dd_type, fields_container], tight=True), width=400),
            actions=[
                ft.ElevatedButton(t("dialog_cancel"), bgcolor=PRIMARY_COLOR, color=TEXT_SECONDARY, on_click=lambda e: page.close(dlg)),
                ft.ElevatedButton(t("dialog_save"), bgcolor=PRIMARY_COLOR, color=TEXT_SECONDARY, on_click=save_close),
            ]
        )
        dlg_ref["value"] = dlg
        page.open(dlg)

    # --- UI SEQUENCE RENDER ---
    sequence_container = ft.Column(scroll=ft.ScrollMode.ALWAYS, spacing=10)

    def render_sequence_ui():
        sequence_container.controls.clear()
        if not action_sequence:
            sequence_container.controls.append(
                ft.Container(ft.Text(t("no_actions"), color="grey"), alignment=ft.alignment.center, padding=20)
            )
        else:
            build_action_tree(action_sequence, sequence_container)
        
        sequence_container.update()

    def build_action_tree(actions_list, parent_control):
        for i, action in enumerate(actions_list):
            atype = action.get("type")
            
            card_color = SECONDARY_COLOR
            icon = ft.Icons.CIRCLE
            title_text = atype
            detail_text = ""
            
            if atype == "click":
                card_color = ft.Colors.with_opacity(0.05, COLOR_BLOCK_CLICK)
                border_side = COLOR_BLOCK_CLICK
                icon = ft.Icons.TOUCH_APP
                mode = "CLICK" if action.get("click") else "FIND"
                title_text = f"{mode}: {action.get('image_path')}"
                detail_text = f"Conf: {action.get('confidence')}"
            
            elif atype == "simple_click":
                card_color = ft.Colors.with_opacity(0.05, COLOR_BLOCK_SIMPLE_CLICK)
                border_side = COLOR_BLOCK_SIMPLE_CLICK
                icon = ft.Icons.MOUSE
                title_text = f"CLICK: ({action.get('x')}, {action.get('y')})"
                click_type = action.get("click_type")
                if click_type:
                    detail_text = f"Type: {click_type}"
            
            elif atype == "send_text":
                card_color = ft.Colors.with_opacity(0.05, COLOR_BLOCK_TEXT)
                border_side = COLOR_BLOCK_TEXT
                icon = ft.Icons.TEXT_FIELDS
                title_text = "SEND TEXT"
                text_preview = action.get("text", "")[:30] + "..." if len(action.get("text", "")) > 30 else action.get("text", "")
                detail_text = f"Text: {text_preview}"
                if action.get("clear_field"):
                    detail_text += " (clear)"
            
            elif atype == "swipe":
                card_color = ft.Colors.with_opacity(0.05, COLOR_BLOCK_SWIPE)
                border_side = COLOR_BLOCK_SWIPE
                icon = ft.Icons.SWIPE
                title_text = f"SWIPE: ({action.get('x1')},{action.get('y1')}) -> ({action.get('x2')},{action.get('y2')})"
                detail_text = f"Delay: {action.get('timedelay')}ms"
            
            elif atype == "while_loop":
                card_color = ft.Colors.with_opacity(0.05, COLOR_BLOCK_LOOP)
                border_side = COLOR_BLOCK_LOOP
                icon = ft.Icons.LOOP
                iters = action.get("max_iterations")
                title_text = "WHILE LOOP"
                detail_text = f"Max Iter: {'∞' if iters==0 else iters}"
            
            elif atype == "activity_check":
                card_color = ft.Colors.with_opacity(0.05, COLOR_BLOCK_CHECK)
                border_side = COLOR_BLOCK_CHECK
                icon = ft.Icons.APP_REGISTRATION
                title_text = "CHECK ACTIVITY"
                detail_text = f"{action.get('target_package')}"

            elif atype == "break_timer":
                card_color = ft.Colors.with_opacity(0.05, COLOR_BLOCK_BREAK)
                border_side = COLOR_BLOCK_BREAK
                icon = ft.Icons.TIMER_OFF
                title_text = "BREAK TIMER"
                detail_text = f"> {action.get('duration')} sec"
                
            elif atype == "delay":
                card_color = ft.Colors.with_opacity(0.05, COLOR_BLOCK_DELAY)
                border_side = COLOR_BLOCK_DELAY
                icon = ft.Icons.TIMER
                title_text = f"WAIT {action.get('delay')}s"
            
            elif atype == "install_apk":
                card_color = ft.Colors.with_opacity(0.05, COLOR_BLOCK_INSTALL)
                border_side = COLOR_BLOCK_INSTALL
                icon = ft.Icons.INSTALL_DESKTOP
                title_text = "INSTALL APK"
                detail_text = f"Path: {action.get('path_apk')}"
            
            elif atype == "uninstall_app":
                card_color = ft.Colors.with_opacity(0.05, COLOR_BLOCK_UNINSTALL)
                border_side = COLOR_BLOCK_UNINSTALL
                icon = ft.Icons.DELETE
                title_text = "UNINSTALL APP"
                detail_text = f"Package: {action.get('package')}"

            elif atype == "wait_for_image":
                card_color = ft.Colors.with_opacity(0.05, COLOR_BLOCK_WAIT)
                border_side = ft.Colors.BLUE_400
                icon = ft.Icons.HOURGLASS_EMPTY
                title_text = f"WAIT FOR IMAGE: {action.get('image_path')}"
                detail_text = f"Timeout: {action.get('timeout')}s | Conf: {action.get('confidence')}"
            
            else:
                card_color = ft.Colors.with_opacity(0.05, COLOR_BLOCK_SYSTEM)
                border_side = COLOR_BLOCK_SYSTEM
                icon = ft.Icons.SETTINGS
                title_text = f"{atype.upper()}"
                if "package_name" in action: detail_text = action["package_name"]

            header = ft.Row([
                ft.Icon(icon, size=16, color=border_side),
                ft.Column([
                    ft.Text(title_text, weight=ft.FontWeight.BOLD, size=13),
                    ft.Text(detail_text, size=10, color=TEXT_SECONDARY, visible=bool(detail_text))
                ], spacing=1, expand=True),
                ft.IconButton(ft.Icons.EDIT, tooltip="Edit Action", icon_color=ACCENT_COLOR, on_click=lambda e, a=action, l=actions_list, idx=i: open_action_dialog(a, l, idx, False)),
                ft.Column([
                    ft.IconButton(ft.Icons.KEYBOARD_ARROW_UP, tooltip="Move Up", icon_color=ACCENT_COLOR, on_click=lambda e, l=actions_list, idx=i: move_item(l, idx, -1)),
                    ft.IconButton(ft.Icons.KEYBOARD_ARROW_DOWN, tooltip="Move Down", icon_color=ACCENT_COLOR, on_click=lambda e, l=actions_list, idx=i: move_item(l, idx, 1)),
                ], spacing=0),
                ft.IconButton(ft.Icons.CLOSE, tooltip="Delete Action", icon_color=ft.Colors.RED_400, on_click=lambda e, l=actions_list, idx=i: delete_item(l, idx)),
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)

            card = ft.Container(
                content=ft.Column([header], spacing=0),
                bgcolor=card_color, border_radius=5, padding=5,
                border=ft.border.only(top=ft.BorderSide(1, border_side)),
                margin=ft.margin.only(bottom=1)
            )
            
            if atype in ["click", "activity_check"]:
                logic_col = ft.Column(spacing=2)
                
                then_cont = ft.Container(content=ft.Column([
                    ft.Row([
                        ft.Text("THEN:", size=10, color=ft.Colors.GREEN_400, weight=ft.FontWeight.BOLD),
                        ft.IconButton(ft.Icons.ADD_CIRCLE_OUTLINE, tooltip="Add action to THEN branch", icon_color=ft.Colors.GREEN_400, on_click=lambda e, a=action: open_action_dialog(parent_list=a.setdefault("children", []), insert_mode=True))
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    ft.Column(spacing=2)
                ]), padding=ft.padding.only(left=15, top=5))
                build_action_tree(action.get("children", []), then_cont.content.controls[1])
                logic_col.controls.append(then_cont)

                else_cont = ft.Container(content=ft.Column([
                    ft.Row([
                        ft.Text("ELSE:", size=10, color=ft.Colors.RED_400, weight=ft.FontWeight.BOLD),
                        ft.IconButton(ft.Icons.ADD_CIRCLE_OUTLINE, tooltip="Add action to ELSE branch", icon_color=ft.Colors.RED_400, on_click=lambda e, a=action: open_action_dialog(parent_list=a.setdefault("else_actions", []), insert_mode=True))
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    ft.Column(spacing=2)
                ]), padding=ft.padding.only(left=15, top=5))
                build_action_tree(action.get("else_actions", []), else_cont.content.controls[1])
                logic_col.controls.append(else_cont)
                
                card.content.controls.append(logic_col)

            elif atype == "while_loop":
                break_cont = ft.Container(content=ft.Column([
                    ft.Row([
                        ft.Text("(BREAK IF...):", size=10, color=ft.Colors.ORANGE_400, weight=ft.FontWeight.BOLD),
                        ft.IconButton(ft.Icons.ADD_CIRCLE_OUTLINE, icon_color=ft.Colors.ORANGE_400, 
                                      tooltip="Add break condition (Image, Activity, Timer)",
                                      on_click=lambda e, a=action: open_action_dialog(parent_list=a.setdefault("break_conditions", []), insert_mode=True))
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    ft.Column(spacing=2)
                ]), padding=ft.padding.only(left=15, top=5))
                
                build_action_tree(action.get("break_conditions", []), break_cont.content.controls[1])
                
                body_cont = ft.Container(content=ft.Column([
                    ft.Row([
                        ft.Text("List in (LOOP):", size=10, color=ft.Colors.BLUE_400, weight=ft.FontWeight.BOLD),
                        ft.IconButton(ft.Icons.ADD_CIRCLE_OUTLINE, icon_color=ft.Colors.BLUE_400,
                                      tooltip="Add action inside loop",
                                      on_click=lambda e, a=action: open_action_dialog(parent_list=a.setdefault("actions", []), insert_mode=True))
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    ft.Column(spacing=2)
                ]), padding=ft.padding.only(left=15, top=5, bottom=5))
                
                build_action_tree(action.get("actions", []), body_cont.content.controls[1])
                
                card.content.controls.extend([break_cont, body_cont])

            parent_control.controls.append(card)

    def delete_item(lst, idx):
        lst.pop(idx)
        render_sequence_ui()

    def move_item(lst, idx, direction):
        if 0 <= idx + direction < len(lst):
            lst[idx], lst[idx+direction] = lst[idx+direction], lst[idx]
            render_sequence_ui()

    # --- DEVICE SCREEN PREVIEW EVENTS ---
    async def screenshot_click(e):
        nonlocal current_screenshot
        update_status(t("status_screenshoting"))
        try:
            img = screenshot(device_number)
            if img is not None:
                current_screenshot = img
                _, buffer = cv2.imencode('.jpg', img)
                b64 = base64.b64encode(buffer).decode('utf-8')
                img_preview.src_base64 = b64
                img_preview.visible = True
                clear_selection()
                update_status(t("status_screenshot_ready"))
            else:
                update_status(t("status_no_screenshot"))
        except Exception as ex:
            update_status(f"Error screening: {ex}")
        page.update()

    def on_pan_start(e: ft.DragStartEvent):
        nonlocal selection_start, selection_end
        if image_mode == "click":
            return
        
        selection_start = (e.local_x, e.local_y)
        selection_end = (e.local_x, e.local_y)
        update_selection_rect()

    def on_pan_update(e: ft.DragUpdateEvent):
        nonlocal selection_end
        if image_mode == "click":
            return
        
        selection_end = (e.local_x, e.local_y)
        update_selection_rect()

    def on_tap(e: ft.HoverEvent):
        """Processes screen clicks inside Click Mode"""
        if image_mode != "click" or current_screenshot is None:
            return
        
        mx, my = e.local_x, e.local_y
        h, w = current_screenshot.shape[:2]
        
        coef = get_current_coef()
        real_x = int(mx * coef)
        real_y = int(my * coef)

        click(device_number, real_x, real_y, "tap", 0.1)
        
        if 0 <= real_x < w and 0 <= real_y < h:
            action_dict = {
                "type": "simple_click",
                "x": real_x,
                "y": real_y,
                "click_type": "tap",
                "timedelay": 0.1
            }
            
            def add_simple_click_dialog(e):
                open_action_dialog(action_dict=action_dict, parent_list=action_sequence, insert_mode=True)
                page.close(dlg)
            
            dlg = ft.AlertDialog(
                title=ft.Text(t("dialog_add_simple_click")),
                bgcolor=PRIMARY_COLOR,
                content=ft.Column([
                    ft.Text(f"{t('dialog_coordinates')} ({real_x}, {real_y})"),
                    ft.Text(t("dialog_click_add_prompt"))
                ], tight=True),
                actions=[
                    ft.ElevatedButton(t("dialog_cancel"), bgcolor=PRIMARY_COLOR, color=TEXT_SECONDARY, on_click=lambda e: page.close(dlg)),
                    ft.ElevatedButton(t("dialog_add_action"), bgcolor=PRIMARY_COLOR, color=TEXT_SECONDARY, on_click=add_simple_click_dialog),
                ]
            )
            page.open(dlg)
            
            update_status(f"Click at ({real_x}, {real_y})")
        else:
            update_status("Click outside image bounds")

    def update_selection_rect():
        if not selection_start or not selection_end:
            if selection_overlay in image_stack.controls:
                image_stack.controls.remove(selection_overlay)
        else:
            x = min(selection_start[0], selection_end[0])
            y = min(selection_start[1], selection_end[1])
            w = abs(selection_start[0] - selection_end[0])
            h = abs(selection_start[1] - selection_end[1])
            
            selection_overlay.left = x
            selection_overlay.top = y
            selection_overlay.width = w
            selection_overlay.height = h
            
            if selection_overlay not in image_stack.controls:
                image_stack.controls.append(selection_overlay)
        
        image_stack.update()
        return(x, y, w, h)

    def btn_crop_click(e):
        nonlocal selection_start, selection_end
        if current_screenshot is None: 
            update_status(t("status_crop_no_screenshot"))
            return
        if not selection_start or not selection_end:
            update_status(t("status_crop_no_selection"))
            return
            
        try:
            x, y, w, h = update_selection_rect()
            coef = get_current_coef()
            x = round(int(x) * coef)
            y = round(int(y) * coef)
            w = round(int(w) * coef)
            h = round(int(h) * coef)
            
            if w < 5 or h < 5:
                update_status(t("status_crop_small"))
                return

            crop = current_screenshot[y:y+h, x:x+w]
            
            def ask_filename(e):
                filename = filename_field.value
                if not filename:
                    filename = f"crop_{datetime.now().strftime('%H%M%S')}.png"
                
                cv2.imwrite(filename, crop)
                page.close(filename_dlg)
                
                def ask_add_to_sequence(e):
                    page.close(sequence_dlg)
                    action_dict = {
                        "type": "click",
                        "image_path": filename,
                        "confidence": 0.97,
                        "click": True,
                        "timedelay": 0.1,
                        "children": [],
                        "else_actions": []
                    }
                    open_action_dialog(action_dict=action_dict, parent_list=action_sequence, insert_mode=True)
                
                def skip_adding(e):
                    page.close(sequence_dlg)
                    update_status(f"Saved: {filename}")
                
                sequence_dlg = ft.AlertDialog(
                    title=ft.Text(t("dialog_add_seq_title")),
                    bgcolor=PRIMARY_COLOR,
                    content=ft.Column([
                        ft.Text(f"{t('dialog_file_saved')}: {filename}"),
                        ft.Text(t("dialog_add_action_prompt")),
                    ], tight=True),
                    actions=[
                        ft.ElevatedButton(t("dialog_skip"), bgcolor=PRIMARY_COLOR, color=TEXT_SECONDARY, on_click=skip_adding, tooltip=t("dialog_skip_tooltip")),
                        ft.ElevatedButton(t("dialog_add_action"), bgcolor=PRIMARY_COLOR, color=TEXT_SECONDARY, on_click=ask_add_to_sequence, tooltip=t("dialog_add_action_tooltip")),
                    ]
                )
                page.open(sequence_dlg)
            
            def cancel_crop(e):
                page.close(filename_dlg)
                update_status(t("status_crop_cancelled"))
            
            filename_field = ft.TextField(
                label=t("dialog_file_name_label"),
                value=f"crop_{datetime.now().strftime('%H%M%S')}.png",
                width=300,
                **text_field_style
            )
            
            filename_dlg = ft.AlertDialog(
                title=ft.Text(t("dialog_save_crop_title")),
                content=filename_field,
                bgcolor=PRIMARY_COLOR,
                actions=[
                    ft.ElevatedButton(t("dialog_cancel"), bgcolor=PRIMARY_COLOR, color=TEXT_SECONDARY, on_click=cancel_crop),
                    ft.ElevatedButton(t("dialog_save"), bgcolor=PRIMARY_COLOR, color=TEXT_SECONDARY, on_click=ask_filename),
                ]
            )
            
            page.open(filename_dlg)
            
        except Exception as ex:
            update_status(f"{t('status_crop_error')}: {ex}")

    def on_image_hover(e: ft.HoverEvent):
        if current_screenshot is None: return
        mx, my = e.local_x, e.local_y
        h, w = current_screenshot.shape[:2]
        
        coef = get_current_coef()
        real_x = int(mx * coef)
        real_y = int(my * coef)
        
        if 0 <= real_x < w and 0 <= real_y < h:
            pixel = current_screenshot[real_y, real_x]
            b, g, r = pixel
            pixel_info_text.value = f"X:{real_x} Y:{real_y} | RGB:({r},{g},{b})"
        else:
            pixel_info_text.value = f"X:{real_x} Y:{real_y} (Out of bounds)"
        
        pixel_info_text.update()

    def clear_all(e):
        action_sequence.clear()
        render_sequence_ui()
        update_status(t("status_list_cleaned"))
    
    def save_json(e):
        try:
            fname = f"seq_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(fname, "w", encoding="utf-8") as f:
                json.dump(action_sequence, f, indent=2, ensure_ascii=False)
            update_status(f"{t('status_saved')}: {fname}")
        except Exception as ex:
            update_status(f"Error save: {ex}")

    def load_json(e):
        try:
            if tf_filepath.value:
                with open(tf_filepath.value, "r", encoding="utf-8") as f:
                    action_sequence[:] = json.load(f)
                render_sequence_ui()
                update_status(t("status_loaded"))
        except Exception as ex:
            update_status(f"Error load: {ex}")

    def change_image_mode(e):
        nonlocal image_mode
        image_mode = mode_selector.value
        clear_selection()
        
        if image_mode == "crop":
            pixel_info_text.value = t("pixel_info_default")
            btn_crop.disabled = False
            btn_crop.icon_color = TEXT_SECONDARY
        else:
            pixel_info_text.value = "Click on image to add simple click"
            btn_crop.disabled = True
            btn_crop.icon_color = ft.Colors.GREY_700
        
        gesture_detector.mouse_cursor = ft.MouseCursor.CLICK if image_mode == "click" else ft.MouseCursor.MOVE
        page.update()

    VIEW_HEIGHT = device_info["height"]
    if device_info["height"] >= 2400:
        VIEW_COEF = 4.5
    elif device_info["height"] >= 1920:
        VIEW_COEF = 3.75
    else:
        VIEW_COEF = 3
    
    img_preview = ft.Image(src_base64="", visible=False, fit=ft.ImageFit.CONTAIN, border_radius=8)

    selection_overlay = ft.Container(
        bgcolor=ft.Colors.with_opacity(0.1, TEXT_SECONDARY),
        border=ft.border.all(1, ft.Colors.WHITE),
        border_radius=8,
        visible=True,
    )

    image_stack = ft.Stack(
        [img_preview, selection_overlay],
    )

    gesture_detector = ft.GestureDetector(
        content=image_stack,
        on_pan_start=on_pan_start,
        on_pan_update=on_pan_update,
        on_hover=on_image_hover,
        on_tap_down=on_tap,
        mouse_cursor=ft.MouseCursor.CLICK,
    )

    def zoom_in(e):
        nonlocal VIEW_COEF
        if device_info["height"] >= 2400:
            VIEW_COEF = 3
        elif device_info["height"] >= 1920:
            VIEW_COEF = 3.75
        else:
            VIEW_COEF = 1.85

        image_container.width = VIEW_HEIGHT/VIEW_COEF
        image_container.height = VIEW_HEIGHT/VIEW_COEF
        page.update()
    
    def zoom_out(e):
        nonlocal VIEW_COEF
        if device_info["height"] >= 2400:
            VIEW_COEF = 6
        elif device_info["height"] >= 1920:
            VIEW_COEF = 5
        else:
            VIEW_COEF = 4.2

        image_container.width = VIEW_HEIGHT/VIEW_COEF
        image_container.height = VIEW_HEIGHT/VIEW_COEF
        page.update()

    def reset_zoom(e):
        nonlocal VIEW_COEF
        if device_info["height"] >= 2400:
            VIEW_COEF = 4.5
        elif device_info["height"] >= 1920:
            VIEW_COEF = 3.75
        else:
            VIEW_COEF = 3
        
        image_container.width = VIEW_HEIGHT/VIEW_COEF
        image_container.height = VIEW_HEIGHT/VIEW_COEF
        page.update()

    # ========== APK AND PACKAGE CONTROL ACTIONS ==========
    def start_app_action(e):
        try:
            package_name = start_app_field.value.strip()
            if not package_name:
                update_status("Please enter a package name")
                return

            update_status(f"Starting app: {package_name}")
            result = app_activity_start(device_number, package_name)
            if result:
                update_status(f"App started successfully: {package_name}")
            else:
                update_status(f"Failed to start app: {package_name}")

        except Exception as ex:
            update_status(f"Error starting app: {str(ex)}")

    def stop_app_action(e):
        try:
            package_name = start_app_field.value.strip()
            if not package_name:
                update_status("Please enter a package name")
                return

            update_status(f"Stopping app: {package_name}")
            result = app_activity_stop(device_number, package_name)
            if result:
                update_status(f"App stopped successfully: {package_name}")
            else:
                update_status(f"Failed to stop app: {package_name}")

        except Exception as ex:
            update_status(f"Error stopping app: {str(ex)}")

    def clear_app_cache_action(e):
        try:
            package_name = start_app_field.value.strip()
            if not package_name:
                update_status("Please enter a package name")
                return

            update_status(f"Clearing cache for: {package_name}")
            result = app_activity_clearcache(device_number, package_name)
            if result:
                update_status(f"Cache cleared successfully: {package_name}")
            else:
                update_status(f"Failed to clear cache: {package_name}")

        except Exception as ex:
            update_status(f"Error clearing cache: {str(ex)}")

    def install_apk_action(e):
        try:
            path_apk = install_apk_field.value
            if not path_apk:
                update_status("Please enter APK path")
                return

            update_status(f"Installing APK: {path_apk}")
            result = install_apk(device_number, path_apk)
            if result:
                update_status(f"APK installed successfully: {path_apk}")
            else:
                update_status(f"Failed to install APK: {path_apk}")

        except Exception as ex:
            update_status(f"Error installing APK: {str(ex)}")

    def uninstall_app_action(e):
        try:
            package_name = uninstall_app_field.value
            if not package_name:
                update_status("Please enter package name")
                return

            update_status(f"Uninstalling app: {package_name}")
            result = uninstall_app(device_number, package_name)
            if result:
                update_status(f"App uninstalled successfully: {package_name}")
            else:
                update_status(f"Failed to uninstall app: {package_name}")

        except Exception as ex:
            update_status(f"Error uninstalling app: {str(ex)}")

    def list_apps_action(e):
        try:
            all_apps = list_all_switch.value
            update_status(f"Getting app list (all={all_apps})...")
            apps_list = list_apps(device_number, all_apps)
            
            if apps_list:
                show_apps_dialog(apps_list, all_apps)
                update_status(f"Found {len(apps_list)} apps (all={all_apps})")
            else:
                update_status(f"No apps found (all={all_apps})")

        except Exception as ex:
            update_status(f"Error listing apps: {str(ex)}")

    def show_apps_dialog(apps_list, all_apps=False):
        apps_text = "\n".join(apps_list)
        total_apps = len(apps_list)
        
        apps_listview = ft.ListView(
            controls=[],
            expand=True,
            spacing=2,
            padding=10,
        )
        
        def on_app_click(app_name):
            package = app_name
            if "package:" in app_name:
                package = app_name.split("package:")[-1].strip()
            if "(" in package:
                package = package.split("(")[0].strip()
            package = package.strip()
            
            page.set_clipboard(package)
            page.snack_bar = ft.SnackBar(ft.Text(f"Package copied: {package}"))
            page.snack_bar.open = True
            
            install_apk_field.value = ""
            uninstall_app_field.value = package
            start_app_field.value = package
            page.update()
        
        app_items = []
        for i, app in enumerate(apps_list, 1):
            app_items.append(
                ft.Container(
                    content=ft.ListTile(
                        title=ft.Text(app, size=12),
                        leading=ft.Text(f"{i}.", size=12, color=ACCENT_COLOR),
                        trailing=ft.Icon(ft.Icons.CONTENT_COPY, size=16, color=ACCENT_COLOR),
                        on_click=lambda e, a=app: on_app_click(a),
                    ),
                    bgcolor=ft.Colors.with_opacity(0.05, ACCENT_COLOR),
                    border_radius=5,
                    padding=2,
                    margin=1,
                )
            )
        apps_listview.controls = app_items

        def filter_apps(e):
            search_text = search_field.value.lower()
            filtered_items = []
            for i, app in enumerate(apps_list, 1):
                if search_text in app.lower():
                    filtered_items.append(
                        ft.Container(
                            content=ft.ListTile(
                                title=ft.Text(app, size=12),
                                leading=ft.Text(f"{i}.", size=12, color=ACCENT_COLOR),
                                trailing=ft.Icon(ft.Icons.CONTENT_COPY, size=16, color=ACCENT_COLOR),
                                on_click=lambda e, a=app: on_app_click(a),
                            ),
                            bgcolor=ft.Colors.with_opacity(0.05, ACCENT_COLOR),
                            border_radius=5,
                            padding=2,
                            margin=1,
                        )
                    )
            apps_listview.controls = filtered_items
            apps_listview.update()
        
        search_field = ft.TextField(
            label="Search apps...",
            on_change=filter_apps,
            expand=True,
            border_color=ACCENT_COLOR,
            bgcolor=PRIMARY_COLOR2,
            hint_text="Type to filter apps...",
        )
        
        dlg = ft.AlertDialog(
            title=ft.Text(f"Installed Apps ({total_apps} total)"),
            content=ft.Container(
                content=ft.Column([
                            ft.Row([
                                search_field,
                                ft.IconButton(ft.Icons.SEARCH, icon_color=ACCENT_COLOR)
                            ], alignment=ft.MainAxisAlignment.CENTER),
                            ft.Text("Click on app to copy package name", size=11, color=TEXT_SECONDARY, italic=True),
                            apps_listview,
                    ft.Row([
                        ft.Text(f"Total: {total_apps} apps", size=12, color=TEXT_SECONDARY),
                        ft.Text(f"Filter: {'All apps' if all_apps else 'User apps'}", size=12, color=TEXT_SECONDARY),
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
                ], height=400),
                width=600,
            ),
            actions=[
                ft.IconButton(icon=ft.Icons.CLEAR, icon_color=ACCENT_COLOR, on_click=lambda e: page.close(dlg)),
            ],
            bgcolor=PRIMARY_COLOR2,
        )
        page.open(dlg)

    
    btn_crop = ft.IconButton(icon=ft.Icons.CROP, bgcolor=PRIMARY_COLOR, icon_color=TEXT_SECONDARY, on_click=btn_crop_click, style=ft.ButtonStyle(padding=5), tooltip=t("btn_crop_tooltip"))
    pixel_info_text = ft.Text(t("pixel_info_default"), size=12, color=TEXT_SECONDARY, weight=ft.FontWeight.BOLD, tooltip=t("pixel_info_tooltip"))

    # Dynamic mode selection radios
    radio_crop = ft.Radio(value="crop", label=t("radio_crop_label"), fill_color=ACCENT_COLOR, tooltip=t("radio_crop_tooltip"))
    radio_click = ft.Radio(value="click", label=t("radio_click_label"), fill_color=ACCENT_COLOR, tooltip=t("radio_click_tooltip"))

    mode_selector = ft.RadioGroup(
        content=ft.Row([radio_crop, radio_click], spacing=10),
        value=image_mode,
        on_change=change_image_mode
    )

    def check_activity_action(e):
        try:
            update_status("Checking current activity...")
            current_activity = app_activity(device_number)
            if current_activity:
                activity_info = f"Activity: {current_activity.activity}, Package: {current_activity.package}"
                update_status(f"Current activity: {activity_info}")
                
                current_activity_field.value = current_activity.activity
                current_package_field.value = current_activity.package
                current_activity_field.update()
                current_package_field.update()
            else:
                update_status("Failed to get current activity")
        except Exception as ex:
            update_status(f"Error checking activity: {str(ex)}")

    text_field_style = {
        "border_color": ACCENT_COLOR,
        "focused_border_color": ACCENT_COLOR,
        "border_radius": 8,
        "border_width": 1,
        "expand": True,
    }

    start_app_field = ft.TextField(
        label=t("start_app_label"),
        value="",
        width=160,
        text_size=12,
        height=40,
        hint_text="com.example.app",
        tooltip=t("start_app_tooltip"),
        **text_field_style
    )

    current_activity_field = ft.TextField(
        label=t("current_activity_label"),
        value="",
        width=160,
        text_size=12,
        height=40,
        read_only=True,
        tooltip=t("current_activity_tooltip"),
        **text_field_style
    )

    current_package_field = ft.TextField(
        label=t("current_package_label"),
        value="",
        width=160,
        text_size=12,
        height=40,
        read_only=True,
        tooltip=t("current_package_tooltip"),
        **text_field_style
    )
    
    install_apk_field = ft.TextField(
        label=t("install_apk_label"),
        value="",
        width=160,
        text_size=12,
        height=40,
        hint_text="path/to/app.apk",
        tooltip=t("install_apk_tooltip"),
        **text_field_style
    )
    
    uninstall_app_field = ft.TextField(
        label=t("uninstall_app_label"),
        value="",
        width=160,
        text_size=12,
        height=40,
        hint_text="com.example.app",
        tooltip=t("uninstall_app_tooltip"),
        **text_field_style
    )
    
    def list_swith(e):
        if list_all_switch.value==False:
            list_all_switch.label = t("list_all_switch_user")
        else:
            list_all_switch.label = t("list_all_switch_all")
        list_all_switch.update()
    
    list_all_switch = ft.Switch(label=t("list_all_switch_user"), value=False, active_color=ACCENT_COLOR, expand=True, on_change=list_swith, tooltip=t("list_all_switch_tooltip"))

    check_activity_btn = ft.IconButton(
        icon=ft.Icons.APP_REGISTRATION,
        on_click=check_activity_action,
        height=36,
        icon_color=ACCENT_COLOR,
        tooltip=t("check_activity_tooltip")
    )
    
    install_apk_btn = ft.IconButton(
        icon=ft.Icons.INSTALL_DESKTOP,
        on_click=install_apk_action,
        height=36,
        icon_color=ACCENT_COLOR,
        tooltip=t("install_apk_btn_tooltip")
    )
    
    uninstall_app_btn = ft.IconButton(
        icon=ft.Icons.DELETE,
        on_click=uninstall_app_action,
        height=36,
        icon_color=ACCENT_COLOR,
        tooltip=t("uninstall_app_btn_tooltip")
    )
    
    list_apps_btn = ft.IconButton(
        icon=ft.Icons.PLAYLIST_ADD_CHECK_SHARP,
        on_click=list_apps_action,
        height=36,
        icon_color=ACCENT_COLOR,
        tooltip=t("list_apps_btn_tooltip")
    )
    
    selection_buttons = ft.Column(visible=False, spacing=5)

    image_container = ft.Container(
        ref=image_container_ref,
        content=gesture_detector, 
        bgcolor="black", 
        alignment=ft.alignment.center, 
        border_radius=8, 
        width=VIEW_HEIGHT/VIEW_COEF,
        height=VIEW_HEIGHT/VIEW_COEF,
        clip_behavior=ft.ClipBehavior.HARD_EDGE,
        border=ft.border.all(1, ACCENT_COLOR),
    )

    start_app_btn = ft.IconButton(
        icon=ft.Icons.PLAY_ARROW,
        on_click=start_app_action,
        icon_color=ACCENT_COLOR,
        tooltip=t("start_app_btn_tooltip")
    )

    stop_app_btn = ft.IconButton(
        icon=ft.Icons.STOP,
        on_click=stop_app_action,
        icon_color=ACCENT_COLOR,
        tooltip=t("stop_app_btn_tooltip")
    )

    clear_app_btn = ft.IconButton(
        icon=ft.Icons.CLEAR_ALL,
        on_click=clear_app_cache_action,
        icon_color=ACCENT_COLOR,
        tooltip=t("clear_app_btn_tooltip")
    )

    device_dropdown = ft.Dropdown(
        label=t("device_dropdown_label"),
        options=[ft.dropdown.Option(str(i)) for i in range(get_devices())],
        value="0",
        tooltip=t("device_dropdown_tooltip"),
        **text_field_style
    )

    def refresh_device(e):
        nonlocal device_number
        device_number = int(device_dropdown.value) if device_dropdown.value else 0
        update_status(f"Device set to: {device_number}")
        device_dropdown.options=[ft.dropdown.Option(str(i)) for i in range(get_devices())]
        page.update()
    
    refresh_device_btn = ft.IconButton(
        icon=ft.Icons.SMARTPHONE,
        on_click=refresh_device,
        icon_color=ACCENT_COLOR,
        tooltip=t("refresh_device_tooltip")
    )

    # --- File Picking Control Buttons ---
    apk_select_btn = ft.IconButton(
        icon=ft.Icons.FOLDER_OPEN,
        on_click=lambda _: apk_picker.pick_files(allowed_extensions=["apk"]),
        icon_color=ACCENT_COLOR,
        tooltip=t("apk_select_tooltip")
    )

    json_select_btn = ft.IconButton(
        icon=ft.Icons.FOLDER_OPEN,
        on_click=lambda _: json_picker.pick_files(allowed_extensions=["json"]),
        icon_color=ACCENT_COLOR,
        tooltip=t("json_select_tooltip")
    )

    # --- Screen Capture Auto Refresh Switch ---
    async def auto_refresh_toggle(e):
        if auto_refresh_switch.value:
            update_status("Auto-refresh active")
            while auto_refresh_switch.value:
                await screenshot_click(None)
                await asyncio.sleep(1)
        else:
            update_status("Auto-refresh stopped")

    auto_refresh_switch = ft.Switch(
        label=t("auto_refresh_label"), 
        value=False, 
        active_color=ACCENT_COLOR, 
        on_change=auto_refresh_toggle,
        tooltip=t("auto_refresh_tooltip")
    )

    image_container3 = ft.Container(
        content=ft.Column([
            ft.Row([device_dropdown, refresh_device_btn], alignment=ft.MainAxisAlignment.CENTER, spacing=10),
            ft.Row([current_package_field, current_activity_field, check_activity_btn], alignment=ft.MainAxisAlignment.CENTER, spacing=10),
            ft.Row([start_app_field, start_app_btn, stop_app_btn, clear_app_btn], alignment=ft.MainAxisAlignment.CENTER, spacing=10),
            ft.Row([install_apk_field, apk_select_btn, install_apk_btn], alignment=ft.MainAxisAlignment.CENTER, spacing=10),
            ft.Row([uninstall_app_field, uninstall_app_btn], alignment=ft.MainAxisAlignment.CENTER, spacing=10),
            ft.Row([list_all_switch, list_apps_btn], alignment=ft.MainAxisAlignment.CENTER, spacing=10),
        ]),
        alignment=ft.alignment.top_center,
        expand=True,
        padding=10,
        border_radius=8,
        bgcolor=PRIMARY_COLOR,
        border=ft.border.all(1, ACCENT_COLOR),
    )

    btn_screenshot = ft.IconButton(
        bgcolor=PRIMARY_COLOR, 
        icon_color=TEXT_SECONDARY, 
        icon=ft.Icons.CAMERA_ALT, 
        on_click=screenshot_click, 
        tooltip=t("screenshot_btn_tooltip")
    )

    btn_zoom_in = ft.IconButton(ft.Icons.ADD, bgcolor=PRIMARY_COLOR, icon_color=TEXT_SECONDARY, on_click=zoom_in, tooltip=t("zoom_in_tooltip"))
    btn_zoom_out = ft.IconButton(ft.Icons.REMOVE, bgcolor=PRIMARY_COLOR, icon_color=TEXT_SECONDARY, on_click=zoom_out, tooltip=t("zoom_out_tooltip"))
    btn_zoom_reset = ft.IconButton(ft.Icons.FULLSCREEN, bgcolor=PRIMARY_COLOR, icon_color=TEXT_SECONDARY, on_click=reset_zoom, tooltip=t("zoom_reset_tooltip"))

    panel_left = ft.Container(
        content=ft.Column([
            image_container,
            ft.Row([pixel_info_text, mode_selector], alignment=ft.MainAxisAlignment.CENTER),
            selection_buttons,
            ft.Row([
                btn_screenshot, 
                btn_crop,
                btn_zoom_in,
                btn_zoom_out,
                btn_zoom_reset,
            ], alignment=ft.alignment.center),
            ft.Row([auto_refresh_switch], alignment=ft.MainAxisAlignment.CENTER)
        ],
        alignment=ft.MainAxisAlignment.CENTER, 
        horizontal_alignment=ft.CrossAxisAlignment.CENTER),
        padding=10, 
        bgcolor=PRIMARY_COLOR,
        border_radius=8,
        border=ft.border.all(1, ACCENT_COLOR),
    )

    tf_filepath = ft.TextField(label=t("tf_filepath_label"), text_size=12, expand=True, border_color=ACCENT_COLOR, tooltip=t("tf_filepath_tooltip"))
    btn_run = ft.IconButton(icon=ft.Icons.PLAY_ARROW, on_click=run_btn_click, style=ft.ButtonStyle(bgcolor=ft.Colors.GREEN_ACCENT_700, color="white"), tooltip=t("btn_run_tooltip"))
    btn_stop = ft.IconButton(icon=ft.Icons.STOP, on_click=stop_btn_click, disabled=True, style=ft.ButtonStyle(bgcolor=ft.Colors.RED_ACCENT_700, color="white"), tooltip=t("btn_stop_tooltip"))
    btn_clear_all = ft.IconButton(ft.Icons.DELETE_SWEEP, icon_color=ACCENT_COLOR, on_click=clear_all, tooltip=t("clear_all_tooltip"))
    btn_save_json = ft.IconButton(ft.Icons.SAVE, icon_color=ACCENT_COLOR, on_click=save_json, tooltip=t("save_json_tooltip"))
    btn_load_json = ft.IconButton(ft.Icons.UPLOAD_FILE, icon_color=ACCENT_COLOR, on_click=load_json, tooltip=t("json_upload_tooltip"))
    btn_export_python = ft.IconButton(ft.Icons.CODE, icon_color=ACCENT_COLOR, tooltip=t("export_python_tooltip"), on_click=export_click)

    title_text_ctrl = ft.Text(t("app_title"), size=16, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY)

    toolbar = ft.Container(
        content=ft.Column([
            ft.Row([
                title_text_ctrl,
                ft.Icon(ft.Icons.ANDROID, size=24, color=ACCENT_COLOR),
                ft.Text("v.0.0.0.1a", size=12, color=TEXT_SECONDARY),
            ]),
            ft.Row([
                btn_run, 
                btn_stop, 
                btn_clear_all, 
                btn_save_json, 
                tf_filepath, 
                json_select_btn,
                btn_load_json, 
                btn_export_python
            ])
        ]), 
        padding=10, 
        bgcolor=PRIMARY_COLOR, 
        border_radius=8,
        border=ft.border.all(1, ACCENT_COLOR),
    )

    panel_right = ft.Container(
        content=sequence_container, 
        bgcolor=PRIMARY_COLOR, 
        expand=True, 
        width=625, 
        padding=10, 
        border_radius=8, 
        border=ft.border.all(1, ACCENT_COLOR), 
        alignment=ft.alignment.top_center
    )

    # --- LOGS PANEL ---
    log_panel_title = ft.Text(t("console_header"), size=11, color=TEXT_SECONDARY, weight=ft.FontWeight.BOLD)
    log_panel = ft.Container(
        content=ft.Column([
            log_panel_title,
            log_listview
        ]),
        height=160,
        bgcolor=PRIMARY_COLOR,
        border_radius=8,
        border=ft.border.all(1, ACCENT_COLOR),
        padding=8
    )

    TR = ft.Column([
        toolbar, 
        ft.Row([image_container3, panel_right], expand=True, vertical_alignment=ft.CrossAxisAlignment.CENTER),
        log_panel
    ], spacing=10, expand=True)
    
    page.add(ft.Row([panel_left, TR], spacing=10, expand=True))
    
    page.floating_action_button = ft.FloatingActionButton(
        icon=ft.Icons.ADD, 
        mini=True, 
        bgcolor=ACCENT_COLOR, 
        on_click=lambda e: open_action_dialog(parent_list=action_sequence, insert_mode=True),
        tooltip=t("fab_add_tooltip")
    )
    
    render_sequence_ui()
    
    def check_size(e):
        if page.window.width <= DISPLAY_WIDTH/2:
            zoom_out(e)
        elif page.window.width >= DISPLAY_WIDTH:
            zoom_in(e)
        else:
            reset_zoom(e)
        
    page.on_resized = check_size
    check_size(None)


if __name__ == "__main__":
    ft.app(target=main)