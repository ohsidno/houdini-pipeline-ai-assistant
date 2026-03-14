import hou
import json
import urllib.request
import traceback

# Handle version differences 
try:
    from PySide2 import QtWidgets, QtCore, QtGui
except ImportError:
    from PySide6 import QtWidgets, QtCore, QtGui

class AdvancedHoudiniTDTool(QtWidgets.QWidget):
    def __init__(self):
        super(AdvancedHoudiniTDTool, self).__init__()
        self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
        self.setWindowTitle("Advanced AI TD - Self Healing & RAG")
        self.resize(600, 700)
        
        self.layout = QtWidgets.QVBoxLayout(self)
        
        # --- Lightweight RAG Database (Studio Rules) ---
        self.studio_knowledge_base = {
            "transform": "PIPELINE RULE: The internal Houdini node name for a Transform is 'xform'. Example: parent.createNode('xform')",
            "merge": "PIPELINE RULE: To connect nodes to a merge node, you MUST use merge_node.setNextInput(node_to_connect).",
            "naming": "PIPELINE RULE: All new nodes created by this tool MUST have the prefix 'auto_' in their name.",
            "color": "PIPELINE RULE: All new nodes MUST be colored red using node.setColor(hou.Color((1.0, 0.0, 0.0)))."
        }
        
        # UI: Input
        self.layout.addWidget(QtWidgets.QLabel("<b>Artist Request:</b>"))
        self.input_field = QtWidgets.QTextEdit()
        self.input_field.setMaximumHeight(60)
        self.input_field.setPlaceholderText("e.g., Create a transform node directly after my selected node, then add a merge node.")
        self.layout.addWidget(self.input_field)
        
        # UI: Generate Button
        self.btn_layout = QtWidgets.QHBoxLayout()
        self.generate_btn = QtWidgets.QPushButton("1. Generate Context-Aware Code")
        self.generate_btn.setStyleSheet("background-color: #2b6c9a; color: white; padding: 8px; font-weight: bold;")
        self.btn_layout.addWidget(self.generate_btn)
        self.layout.addLayout(self.btn_layout)
        
        # UI: Code Display
        self.layout.addWidget(QtWidgets.QLabel("<b>Generated Code (Review before execution):</b>"))
        self.code_output = QtWidgets.QTextEdit()
        font = QtGui.QFont("Courier")
        self.code_output.setFont(font)
        self.layout.addWidget(self.code_output)
        
        # UI: System Log
        self.layout.addWidget(QtWidgets.QLabel("<b>System Log (Auto-Healing Status):</b>"))
        self.log_output = QtWidgets.QTextEdit()
        self.log_output.setMaximumHeight(150)
        self.log_output.setReadOnly(True)
        self.log_output.setStyleSheet("background-color: #1e1e1e; color: #00ff00; font-family: Courier;")
        self.layout.addWidget(self.log_output)
        
        # UI: Execute Button
        self.execute_btn = QtWidgets.QPushButton("2. EXECUTE & AUTO-HEAL")
        self.execute_btn.setStyleSheet("background-color: #8b3a3a; color: white; padding: 12px; font-weight: bold;")
        self.layout.addWidget(self.execute_btn)
        
        # Connections
        self.generate_btn.clicked.connect(self.generate_initial_code)
        self.execute_btn.clicked.connect(self.execute_with_healing)
        
        self.log("System initialized. RAG Database loaded. Ready.")

    def log(self, message):
        """Updates the system log without freezing the UI."""
        self.log_output.append(message)
        QtWidgets.QApplication.processEvents()
        scrollbar = self.log_output.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def get_scene_context(self):
        """Grabs currently selected nodes to give the AI context."""
        selected = hou.selectedNodes()
        if not selected:
            return "Context: The user has no nodes selected. Assume object level (/obj) unless specified."
            
        context_str = "Context: The user has the following nodes selected:\n"
        for node in selected:
            context_str += f"- Name: '{node.name()}', Path: '{node.path()}', Type: '{node.type().name()}'\n"
        return context_str

    def retrieve_studio_rules(self, user_request):
        """Searches the database for rules matching the user's request (Lightweight RAG)."""
        retrieved_rules = []
        request_lower = user_request.lower()
        
        for keyword, rule in self.studio_knowledge_base.items():
            if keyword in request_lower:
                retrieved_rules.append(rule)
                self.log(f"RAG System: Injected studio rule for keyword '{keyword}'")
                
        if not retrieved_rules:
            return ""
            
        rules_context = "\nCRITICAL STUDIO PIPELINE RULES YOU MUST FOLLOW:\n" + "\n".join(retrieved_rules)
        return rules_context

    def call_ollama(self, prompt_text):
        """Handles the HTTP request to the local LLM."""
        url = "http://localhost:11434/api/generate"
        
        # Strict instructions to prevent chatty AI responses and force errors to surface
       
        system_prompt = (
            "You are a Senior Houdini Pipeline TD. "
            "Write ONLY raw, executable Python 3 code using the 'hou' module. "
            "Do not include markdown tags like ```python. Do not explain your code. "
            "CRITICAL RULES YOU MUST OBEY: "
            "1. DO NOT use try/except blocks. "
            "2. DO NOT use hou.pwd(). ALWAYS use hou.selectedNodes()[0] to get the user's current working node. "
            "3. DO NOT write silent 'if' checks that skip execution. Code must fail loudly if it doesn't work."
            "4. When using createNode(), DO NOT use any keyword arguments. Only pass the node type string and optionally the node name string."
            "5. DO NOT create 'geo' containers. Create SOP nodes (like 'sphere', 'merge') DIRECTLY using parent.createNode('type')."
        )
        
        full_prompt = f"{system_prompt}\n\n{prompt_text}"
        
        data = {
            "model": "qwen2.5-coder",
            "prompt": full_prompt,
            "stream": False
        }
        
        req = urllib.request.Request(url, data=json.dumps(data).encode('utf-8'), headers={'Content-Type': 'application/json'})
        try:
            response = urllib.request.urlopen(req)
            result = json.loads(response.read().decode('utf-8'))
            clean_code = result['response'].replace("```python", "").replace("```", "").strip()
            return clean_code
        except Exception as e:
            self.log(f"CRITICAL HTTP ERROR: Make sure Ollama is running. {str(e)}")
            return None

    def generate_initial_code(self):
        user_request = self.input_field.toPlainText()
        if not user_request:
            self.log("Error: Please enter a request.")
            return
            
        scene_context = self.get_scene_context()
        
        self.log("Querying studio database for pipeline rules...")
        pipeline_rules = self.retrieve_studio_rules(user_request)
        
        self.log("Sending context, rules, and prompt to local AI...")
        
        # Combine Context, Rules, and User Request
        combined_prompt = f"{scene_context}\n{pipeline_rules}\n\nArtist Request: {user_request}"
        
        ai_code = self.call_ollama(combined_prompt)
        if ai_code:
            self.code_output.setText(ai_code)
            self.log("Code generated successfully. Awaiting execution.")

    def execute_with_healing(self):
        """The Auto-Healing Loop: Tries to run code, catches errors, asks AI to fix it."""
        max_retries = 3
        current_attempt = 1
        
        while current_attempt <= max_retries:
            code_to_run = self.code_output.toPlainText()
            self.log(f"Execution Attempt {current_attempt}/{max_retries}...")
            
            try:
                # Attempt to execute the code
                exec(code_to_run, globals(), locals())
                self.log("SUCCESS: Code executed cleanly in Houdini!")
                break # Exit the loop if successful
                
            except Exception as e:
                # If it fails, we catch the exact error traceback
                error_trace = traceback.format_exc()
                self.log(f"FAILED: Houdini threw an error. Initiating Auto-Heal loop...")
                
                if current_attempt == max_retries:
                    self.log("CRITICAL: Auto-Heal failed after max retries. Manual intervention required.")
                    break
                    
                # Ask the AI to fix its own mistake
                self.log("Packaging error log and sending back to AI for debugging...")
                healing_prompt = (
                    f"The following Houdini Python code failed with this error:\n\n"
                    f"CODE:\n{code_to_run}\n\n"
                    f"ERROR TRACEBACK:\n{error_trace}\n\n"
                    f"Rewrite the code to fix this specific error. "
                    f"DO NOT use try/except blocks. Just fix the logic."
                )
                
                fixed_code = self.call_ollama(healing_prompt)
                if fixed_code:
                    self.code_output.setText(fixed_code) 
                    current_attempt += 1
                else:
                    self.log("Auto-Heal aborted: AI failed to respond.")
                    break

# --- Module Execution Wrapper ---
dialog = None 

def launch():
    global dialog
    if dialog is None:
        dialog = AdvancedHoudiniTDTool()
    dialog.show()