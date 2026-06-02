from funks import screenshot, click, cv2


def click_on_image(path_on_template, clicked=False, confidence=0.97, numb_device=None, custom_x=None, custom_y=None, timedelay=0.1, type_click="tap"):
    template = cv2.imread(path_on_template)
    template = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)
    h, w = template.shape[:2]
    method = cv2.TM_CCOEFF_NORMED
    result = cv2.matchTemplate(screenshot(numb_device=numb_device, grayscale=True), template, method)            
    _, max_val, _, max_loc = cv2.minMaxLoc(result)
    if max_val > confidence:
        location = max_loc
        if custom_x is None or custom_y is None:
            x = int(location[0] + w / 2)
            y = int(location[1] + h / 2)
        if clicked != False:
            if custom_x == None and custom_y == None:
                click(numb_device=numb_device, x_cord=x, y_cord=y, type_click=type_click, timedelay=0.1)#tap, swipe, sld
            else:
                click(numb_device=numb_device, x_cord=custom_x, y_cord=custom_y, type_click=type_click, timedelay=0.1)#tap, swipe, sld
        return max_val
    else:
        return None



