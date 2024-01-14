# LLMLinguaMITM
This is a proof of concept of a small server that sits inbetween your frontend and LLM backend and compresses prompts using LLMLingua.

Right now the tested environment is intercepting communication between SillyTavern and oobabooga's Text Generation WebUI.

## Installation

### Windows
To install you need first to set up a Python virtual environment:
```
python -m venv \path\to\venv
```
Afterward start up the venv:
```
# In cmd.exe
\path\to\venv\Scripts\activate.bat
# In PowerShell
\path\to\venv\Scripts\Activate.ps1
```
Within the virtual environment, install the requirements:
```
pip install -r requirements.txt
```
Now you can go onto Running

### Linux
To install you need first to set up a Python virtual environment:
```
python -m venv /path/to/venv
```
Afterward start up the venv:
```
source /path/to/venv/bin/activate
```
Within the virtual environment, install the requirements:
```
pip install -r requirements.txt
```
Now you can go onto Running

## Configuration
The application expects a config.yaml file next to the Python script:

```
base_url: 'url' # The target LLM backend
model_name: 'TheBloke/Llama-2-7b-Chat-GPTQ' # The model used to compress
branch: 'main' # Branch to use
device: 'cuda' # Device environment (e.g., 'cuda', 'cpu', 'mps')
target_token: 500 # What the target output length should be, might be changed to take it from the request
```

## Running
Simply run the command:
```
python -m uvicorn main:app --host 0.0.0.0 --port 8080 
```
Within SillyTavern, set this as your target API: Text Completion and Default (oobabooga)
