import os

def before_all(context):
    os.makedirs("screenshots", exist_ok=True)

def after_scenario(context, scenario):
    if hasattr(context, "driver"):
        if scenario.status == "failed":
            name = scenario.name.replace(" ", "_")
            context.driver.save_screenshot(f"screenshots/FAIL_{name}.png")
        context.driver.quit()
