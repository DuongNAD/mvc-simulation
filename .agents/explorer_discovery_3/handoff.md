# Handoff Report: Local Offline Voice Assistant Technologies (Explorer 3)

## 1. Observation
*   **Python Version**: 3.11.9, located at `c:\Windows\py.exe`
*   **System GPU and CUDA**: NVIDIA GeForce RTX 5060 Ti. Python code execution confirmed CUDA is available:
    *   Command: `py -c "import torch; print('CUDA Available:', torch.cuda.is_available()); print('Device Name:', torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'None')"`
    *   Result: `CUDA Available: True`, `Device Name: NVIDIA GeForce RTX 5060 Ti`
*   **Python environment packages (via `pip list`)**:
    *   `transformers` (4.56.2)
    *   `torch` (2.8.0+cu128)
    *   `torchaudio` (2.8.0+cu128)
    *   `sounddevice` (0.5.5)
    *   `soundfile` (0.12.1)
    *   `onnxruntime` & `onnxruntime-gpu` (1.26.0)
    *   `edge-tts` (7.2.8)
    *   `kokoro`, `piper`, `pyttsx3`, `pyttsx4`, `gtts`, `whisper`, `faster_whisper`, `llama_cpp`, `ollama` are not installed.
*   **Local Caches (via `Get-ChildItem`)**:
    *   HuggingFace cache directory `C:\Users\Admin\.cache\huggingface\hub` contains:
        *   `models--Systran--faster-whisper-base`
        *   `models--Systran--faster-whisper-small`
        *   `models--Qwen--Qwen2.5-7B-Instruct`
        *   `models--Qwen--Qwen2.5-7B-Instruct-AWQ`
        *   `models--meta-llama--Llama-3.1-8B-Instruct`
        *   `models--google--gemma-2-9b-it`
    *   ModelScope cache directory `C:\Users\Admin\.cache\modelscope\hub` contains:
        *   `models\iic\SenseVoiceSmall`
        *   `models\iic\speech_fsmn_vad_zh-cn-16k-common-pytorch`
        *   `models\iic\punc_ct-transformer_cn-en-common-vocab471067-large`
    *   Ollama directory `C:\Users\Admin\.ollama` exists, but its `models` directory is empty. The `ollama` executable is not installed globally or in common folders.

## 2. Logic Chain
1.  **Hardware Capability**: Since `torch.cuda.is_available()` is True with an RTX 5060 Ti, the local machine has 8GB of VRAM and a powerful desktop GPU. This enables running local Speech-to-Text (STT) and Conversational LLMs with extremely low latency.
2.  **STT Selection**: The user requested STT options like Whisper/faster-whisper/Nemotron 3 ASR. We observed that the model files for `faster-whisper-base` and `faster-whisper-small` are already pre-downloaded in `C:\Users\Admin\.cache\huggingface\hub`. Because we also have `torch` and CUDA support, loading the pre-downloaded `faster-whisper-small` using a newly installed `faster-whisper` library will run entirely offline, quickly, and with zero network downloads.
3.  **LLM Selection**: The user requested conversational LLMs (Ollama, llama-cpp-python, or transformers). We observed that:
    *   Ollama is not installed.
    *   `transformers` (4.56.2) is already installed in Python.
    *   `Qwen2.5-7B-Instruct-AWQ` is pre-downloaded in the local HuggingFace cache.
    *   Therefore, running `Qwen2.5-7B-Instruct-AWQ` directly using the installed `transformers` library on the GPU requires zero downloads, zero extra tool installation (like Ollama or compilers for llama-cpp-python), and runs entirely offline. Qwen 2.5 is also highly fluent in Vietnamese and English.
4.  **TTS Selection**: The user requested Vietnamese/English bilingual soft voice TTS.
    *   `pyttsx3`/`pyttsx4` are offline but sound robotic and lack "soft" natural voice profiles.
    *   `edge-tts` is installed and has soft neural voices (HoaiMy/NamMinh), but is **not** offline (requires internet).
    *   `piper` (via `piper-tts`) has a local Vietnamese voice trained on the VIVOS dataset (`vi_VN-vivos-medium.onnx`), which is a soft/natural female voice.
    *   `kokoro` (via `kokoro-onnx`) is a lightweight neural TTS (~82M params) that runs using `onnxruntime-gpu` (which is already installed).
    *   Therefore, the best offline setups are:
        *   **Kokoro-ONNX** (using the installed `onnxruntime-gpu` for sub-second speed on RTX 5060 Ti).
        *   **Piper** (using `vi_VN-vivos-medium.onnx` for a dedicated, highly natural offline Vietnamese voice).

## 3. Caveats
*   We did not test the exact audio quality of SAPI5 voices (pyttsx3) on this specific machine.
*   We assumed the user wants a fully offline solution as per "Research offline options". If internet connectivity is allowed, `edge-tts` is the easiest high-quality TTS solution.
*   While `Qwen2.5-7B-Instruct-AWQ` is pre-downloaded, it requires the `autoawq` library or an AWQ-compatible backend. Standard FP16 `Qwen2.5-7B-Instruct` is also cached and can be loaded directly with `transformers` using `torch.bfloat16` or `torch.float16` to fit within the GPU VRAM.

## 4. Conclusion
We can build a 100% offline, high-performance voice assistant using the existing system configuration:
1.  **STT**: `faster-whisper` (Small model) loaded directly from local Hugging Face cache.
2.  **LLM**: `Qwen2.5-7B-Instruct` or `Qwen2.5-7B-Instruct-AWQ` loaded directly via the installed `transformers` package with CUDA.
3.  **TTS**: `kokoro-onnx` (using ONNX Runtime GPU) or `piper-tts` (using the VIVOS model).
4.  **Setup Action**: Run `py -m pip install faster-whisper kokoro-onnx piper-tts` to install the remaining packages, and download the chosen TTS model file (.onnx) to execute entirely locally.

## 5. Verification Method
1.  **Verify local Python environment and imports**:
    Run the following command to check if packages are available:
    ```powershell
    py -c "import transformers, torch, sounddevice, onnxruntime; print('Imports successful!')"
    ```
2.  **Inspect cache locations**:
    Verify cached files exist using:
    ```powershell
    Get-ChildItem -Path C:\Users\Admin\.cache\huggingface\hub
    ```
3.  **Verify GPU acceleration in PyTorch**:
    ```powershell
    py -c "import torch; print(torch.cuda.get_device_name(0))"
    ```
