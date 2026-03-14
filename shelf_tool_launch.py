import ai_assistant
from importlib import reload

# Reload ensures that if the Python file is updated, Houdini reads the fresh version
reload(ai_assistant)

# Launch the PySide UI
ai_assistant.launch()