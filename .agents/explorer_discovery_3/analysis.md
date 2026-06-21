# Analysis Report: Local Offline Voice Assistant Technologies (TTS, STT, LLM)

This report details the offline options for Text-to-Speech (TTS), Speech-to-Text (STT), and Conversational AI (LLM) models that can run on Windows. It also includes the verification of local packages, pre-downloaded model caches, system resources, and step-by-step setup guides.

---

## 1. System Environment & Hardware Resources

We conducted a diagnostic on the system's Python environment and hardware. The results are highly favorable for local execution:

*   **Python Version**: 3.11.9 (64-bit)
*   **Graphics Processing Unit (GPU)**: **NVIDIA GeForce RTX 5060 Ti**
*   **CUDA Support**: **Enabled** (`torch.cuda.is_available() == True`, CUDA version `12.8`)
*   **ONNX GPU Acceleration**: **Installed** (`onnxruntime-gpu: 1.26.0` is available)

### Pre-installed Python Packages
*   `transformers` (4.56.2)
*   `torch` (2.8.0+cu128)
*   `torchaudio` (2.8.0+cu128)
*   `sounddevice` (0.5.5)
*   `soundfile` (0.12.1)
*   `onnxruntime` & `onnxruntime-gpu` (1.26.0)
*   `edge-tts` (7.2.8) (Requires internet connection; not suitable for offline mode, but installed)

---

## 2. Text-to-Speech (TTS) Offline Options

We researched local Text-to-Speech options with a focus on Vietnamese/English bilingual capacity and a "soft" natural voice profile.

| Model / Option | Description & Quality | Bilingual Capability | Resource Footprint | Windows Setup & Dependency | Local Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Kokoro-ONNX** | State-of-the-art 82M param neural TTS. Produces highly natural, soft, and expressive voices. | **Excellent**. Uses English voices natively; multilingual checkpoints support multiple languages, and Vietnamese can be supported via phone mapping or custom ONNX voice files. | Extremely low (~340MB model file). Generates audio in sub-second times on GPU/CPU. | Requires `kokoro-onnx` pip package. Runs using the already installed `onnxruntime-gpu`. | **Not Installed / Not Downloaded** |
| **Piper** | Fast, local neural TTS system optimized for CPU/low-resource environments. | **Good**. Requires separate models (e.g., VIVOS female voice for Vietnamese, Lessac for English) and a router in code. | Very low (~15MB to ~50MB per voice model). | Requires `piper-tts` pip package or downloading the static Windows CLI executable (`piper.exe`). | **Not Installed / Not Downloaded** |
| **pyttsx3 / pyttsx4** | Python wrapper for native OS speech engines (SAPI5 on Windows). | **Basic**. Uses whatever voices are installed in Windows settings (e.g., "Microsoft An" for Vietnamese, "Microsoft Zira" for English). | Negligible (uses built-in OS libraries). | Requires `pyttsx3` or `pyttsx4` pip package. No extra binaries or weights needed. | **Not Installed** |
| **gTTS-offline** | Typically redirects to pyttsx3 or requires internet (gTTS is fundamentally an API client). | **Poor**. | Negligible. | N/A (Online only; not recommended). | **Not Installed** |

### Recommendations for TTS Setup:
1.  **Primary Option: Kokoro-ONNX**. Since `onnxruntime-gpu` is already installed, Kokoro-ONNX can leverage the RTX 5060 Ti to synthesize speech almost instantaneously.
    *   *Setup*:
        ```powershell
        py -m pip install kokoro-onnx
        ```
        Download the model `kokoro-v0_19.onnx` and its configuration files from HuggingFace to a local folder.
2.  **Fallback Option: Piper**. If a fully unified Vietnamese voice model is required, Piper's model trained on the VIVOS dataset (`vi_VN-vivos-medium.onnx`) provides a soft, natural female Vietnamese voice.
    *   *Setup*:
        ```powershell
        py -m pip install piper-tts
        ```

---

## 3. Speech-to-Text (STT) Offline Options

We researched local Speech-to-Text models and checked the local cache. We discovered that **several models are already pre-downloaded** in the HuggingFace and ModelScope cache directories!

### Verification of Local Caches
*   **HuggingFace Cache (`C:\Users\Admin\.cache\huggingface\hub`)**:
    *   `models--Systran--faster-whisper-base` (Already downloaded!)
    *   `models--Systran--faster-whisper-small` (Already downloaded!)
*   **ModelScope Cache (`C:\Users\Admin\.cache\modelscope\hub`)**:
    *   `models\iic\SenseVoiceSmall` (Alibaba's low-latency multilingual ASR model - Already downloaded!)
    *   `models\iic\speech_fsmn_vad_zh-cn-16k-common-pytorch` (Voice Activity Detection model - Already downloaded!)
    *   `models\iic\punc_ct-transformer_cn-en-common-vocab471067-large` (Punctuation restoration - Already downloaded!)

### Evaluation of STT Options

| Model / Option | Vietnamese Support | Performance & Speed | Setup & Local Status |
| :--- | :--- | :--- | :--- |
| **faster-whisper (Base/Small)** | **Excellent**. Whisper is trained on 680,000 hours of multilingual data, including Vietnamese. | Up to 4x faster than standard PyTorch Whisper. Runs in float16 on the RTX 5060 Ti GPU. | **Highly Recommended**. The model weights are already cached locally. You only need to run: `py -m pip install faster-whisper` |
| **SenseVoice (SenseVoiceSmall)** | **Not Native**. Alibaba's model natively lists English, Chinese, Cantonese, Japanese, and Korean. | Extremely fast (sub-100ms latency), includes emotion and event detection (laughter, cough). | The model weights are already cached locally. Requires installing `funasr` and `modelscope` via pip. |
| **Nemotron 3 ASR** | **Basic**. Requires NVIDIA Riva server. | High performance but heavy resource footprint. | Not recommended for local lightweight Windows execution due to heavy dockerized setup. |

### Setup Guide for `faster-whisper`:
Since the model weights are already downloaded in the Hugging Face cache, setting up `faster-whisper` takes only one step:
```powershell
py -m pip install faster-whisper
```
Usage in Python (forces loading from local Hugging Face cache):
```python
from faster_whisper import WhisperModel

# Will load the pre-downloaded 'small' model from C:\Users\Admin\.cache\huggingface\hub
model = WhisperModel("small", device="cuda", compute_type="float16")
segments, info = model.transcribe("audio.wav", beam_size=5, language="vi")
for segment in segments:
    print("[%.2fs -> %.2fs] %s" % (segment.start, segment.end, segment.text))
```

---

## 4. Local Offline Conversational AI / LLMs

We researched offline Large Language Model options. We verified that **no local Ollama service is installed**, but **multiple highly capable LLMs are already cached** in the HuggingFace cache folder.

### Verification of Local Caches
The HuggingFace hub cache (`C:\Users\Admin\.cache\huggingface\hub`) contains the following pre-downloaded LLM weights:
1.  `models--Qwen--Qwen2.5-7B-Instruct` (~15GB FP16/BF16)
2.  `models--Qwen--Qwen2.5-7B-Instruct-AWQ` (~5.5GB 4-bit INT quantized)
3.  `models--meta-llama--Llama-3.1-8B-Instruct` (~16GB FP16/BF16)
4.  `models--google--gemma-2-9b-it` (~19GB FP16/BF16)

*Note: Qwen 2.5 has outstanding bilingual support (Vietnamese and English) and is highly optimized for chat interactions.*

### Comparison of Execution Backends

| Backend Option | System Status | Setup Method | Pros & Cons |
| :--- | :--- | :--- | :--- |
| **Hugging Face `transformers`** | **Installed & Ready** | None required (already installed). | **Highly Recommended**. Uses the pre-installed PyTorch with GPU support. Can load the cached `Qwen2.5-7B-Instruct-AWQ` or `Qwen2.5-7B-Instruct` directly. Zero extra dependencies. |
| **Ollama** | **Not Installed** | Download installer from `ollama.com`. Run `ollama run qwen2.5:7b` to download GGUF. | Excellent API server. However, it requires a separate installation step, and we would need to re-download the models in Ollama's GGUF format, which wastes storage. |
| **llama-cpp-python** | **Not Installed** | Install via pip with CUDA flags: `pip install llama-cpp-python` (requires MSVC compiler on Windows). | Extremely fast GGUF inference in Python. However, compiling from source on Windows is often error-prone due to compiler dependencies. |

### Setup Guide for Conversational AI (`transformers`):
Since `transformers` and `torch` with CUDA are already installed, and the models are cached, you can run the LLM immediately in Python:

```python
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

# Using the pre-downloaded Qwen 2.5 7B AWQ model (highly efficient on GPU)
model_id = "Qwen/Qwen2.5-7B-Instruct-AWQ"

tokenizer = AutoTokenizer.from_pretrained(model_id, local_files_only=True)
model = AutoModelForCausalLM.from_pretrained(
    model_id, 
    device_map="cuda", 
    local_files_only=True
)

messages = [
    {"role": "system", "content": "Bạn là trợ lý ảo 'Nàng thơ' hỗ trợ giải thích kiến thức lập trình."},
    {"role": "user", "content": "Giải thích vai trò của Controller trong kiến trúc MVC."}
]

text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
model_inputs = tokenizer([text], return_tensors="pt").to("cuda")

generated_ids = model.generate(**model_inputs, max_new_tokens=512)
generated_ids = [
    output_ids[len(input_ids):] for input_ids, output_ids in zip(model_inputs.input_ids, generated_ids)
]

response = tokenizer.batch_decode(generated_ids, skip_special_tokens=True)[0]
print(response)
```

---

## 5. Synthesis & Integrated Recommendation

To build a fully offline, high-performance Vietnamese/English voice assistant (code-named "Nàng thơ") on Windows, we recommend the following integrated architecture:

1.  **STT Engine**: **`faster-whisper`** (Small model)
    *   *Status*: Pre-downloaded in local cache.
    *   *Action*: Install `faster-whisper` and load from cache. Running on the RTX 5060 Ti GPU provides instantaneous transcription of spoken Vietnamese and English.
2.  **LLM Engine**: **Hugging Face `transformers`** loading **`Qwen2.5-7B-Instruct-AWQ`**
    *   *Status*: Installed library; model pre-downloaded.
    *   *Action*: Run directly via PyTorch (`device_map="cuda"`). The AWQ model uses only ~5.5GB VRAM (leaving plenty of VRAM on the 8GB RTX 5060 Ti for STT and TTS) and offers fast response times. Qwen 2.5 has excellent Vietnamese fluency.
3.  **TTS Engine**: **Kokoro-ONNX** OR **Piper**
    *   *Status*: Needs library installation and model download.
    *   *Action*: Install `kokoro-onnx` or `piper-tts`. Piper offers the most robust offline Vietnamese female voice trained on VIVOS, while Kokoro offers state-of-the-art natural voice generation via ONNX Runtime.

### Recommended Next Steps for Implementation:
1.  Run the following installation command to add missing libraries:
    ```powershell
    py -m pip install faster-whisper kokoro-onnx piper-tts
    ```
2.  Create a unified `VoiceAssistant` class coordinating:
    *   A recording loop that uses `sounddevice` to capture user speech.
    *   `faster-whisper` to transcribe the audio.
    *   `transformers` to generate a response from the local `Qwen2.5` cache.
    *   `kokoro-onnx` or `piper-tts` to synthesize the response.
    *   An interruption mechanism that stops audio playback if user voice activity is detected during TTS.
