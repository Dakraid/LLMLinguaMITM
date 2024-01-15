# LLMLinguaMITM
This is a proof of concept of a small server that sits inbetween your frontend and LLM backend and compresses prompts using [LLMLingua](https://github.com/microsoft/LLMLingua).

Right now the tested environment is intercepting communication between SillyTavern and oobabooga's Text Generation WebUI.

# Disclaimer
This was whipped up within a few hours, there are no guarantees that it will work as expected, work at all, or not explode your PC.

I take no responsibility for what happens and have only conducted a limited amount of testing after I got it to work.

## Requirements
By default, this software requires:
```
Nvidia GPU with at least 6 GB VRAM (as it runs CUDA using TheBloke/Llama-2-7b-Chat-GPTQ)
```

Other methods have not been tested yet. For further information go here: [LLMLingua Docs](https://github.com/microsoft/LLMLingua/blob/main/DOCUMENT.md)

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
pip install torch --index-url https://download.pytorch.org/whl/cu121
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
pip install torch --index-url https://download.pytorch.org/whl/cu121
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
ratio: 0.5 # Compression ratio for the prompt
```

## Running
Simply run the command:
```
python -m uvicorn main:app --host 0.0.0.0 --port 8080 
```
Within SillyTavern, set this as your target API: 
```
Text Completion
Default (oobabooga)
```
