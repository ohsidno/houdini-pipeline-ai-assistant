# Houdini AI Pipeline Assistant (Self-Healing & RAG) 🚀

**A locally-hosted, context-aware PySide tool for Houdini 19.0+, featuring an autonomous error-catching loop and lightweight RAG database.**

🎬 **Watch the Demo:** [https://youtu.be/6U-HeKIKkeY]

## Overview

Integrating Large Language Models (LLMs) into VFX pipelines presents two major challenges: 
1. **NDA/Security risks** from sending proprietary scene data to cloud-based models.
2. **API Hallucinations** that execute bad code and crash DCC environments. 

This project is a proof-of-concept Pipeline Assistant built to solve both. Running entirely locally via Ollama (`qwen2.5-coder`), it ensures absolute data privacy. More importantly, it features an **Autonomous Self-Healing Loop** that intercepts `hou.OperationFailed` crashes caused by AI hallucinations, preventing scene corruption and forcing the model to autonomously debug its own traceback errors.

## Core Architecture & Features

### 1. Dynamic Context Injection (`hou.selectedNodes()`)
Standard LLMs lack scene awareness. This tool dynamically parses the artist's current Houdini network state and injects the active node paths, types, and parent directories into the system prompt before generation, allowing for precise, relative node creation and manipulation.

### 2. Autonomous Self-Healing Loop
AI models frequently guess wrong arguments (e.g., trying to create object-level containers inside SOP networks). Instead of allowing the script to crash Houdini:
* The tool executes the generated code within a secure `try/except` loop.
* If a Houdini API error is thrown, the tool intercepts the exact traceback stack.
* The error is packaged and sent back to the LLM with a strict prompt to debug its own logic.
* The tool will attempt this healing cycle up to 3 times before safely aborting to prevent "script garbage" buildup in the artist's scene.

### 3. Lightweight RAG (Retrieval-Augmented Generation)
To ensure the AI adheres to strict studio naming conventions and network logic, a lightweight RAG database intercepts the artist's prompt. If specific keywords are detected (e.g., "transform" or "merge"), the tool dynamically injects immutable studio rules into the AI's system prompt (e.g., forcing the use of the `auto_` prefix or specific connection API calls).

## Prerequisites
* **SideFX Houdini:** 19.0 or higher (Tested with Python 3 / PySide2)
* **Ollama:** Installed and running locally on port `11434`.
* **LLM Model:** `qwen2.5-coder` (or any fast local coding model).

## Installation & Usage

1. Download or clone this repository.
2. Place `ai_assistant.py` into your Houdini Python scripts folder:
   * Windows: `Documents/houdini19.0/scripts/python`
3. Launch Houdini, create a new Shelf Tool, and add the following Python code to the **Script** tab to launch the UI:

```python
import ai_assistant
from importlib import reload

# Reload ensures Houdini reads fresh changes to the script
reload(ai_assistant)

# Launch the PySide UI
ai_assistant.launch()
