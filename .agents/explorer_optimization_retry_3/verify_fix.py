import os
import sys
import time
import threading
import unittest

# Configure environment and paths
os.environ["MOCK_ENGINES"] = "1"
tests_dir = r"e:\test\mvc-simulation\tests"
project_root = r"e:\test\mvc-simulation"
sys.path.insert(0, project_root)
sys.path.insert(0, tests_dir)

import mock_assistant

# --- Apply proposed fixes via monkeypatching ---

# 1. RLock and updated thread cleanup in TTSEngine
def patched_tts_init(self):
    self._is_speaking = False
    self._lock = threading.RLock() # Reentrant lock
    self._speak_thread = None
    self._stop_event = threading.Event()
    self._current_speak_id = 0

def patched_tts_speak(self, text: str, volume: float = 0.5):
    if not isinstance(volume, (int, float)):
        raise TypeError("Volume must be a number")
    if volume < 0.0 or volume > 1.0:
        raise ValueError("Volume must be between 0.0 and 1.0")
    if text is None:
        raise TypeError("Text cannot be None")
    
    if text == "":
        return

    with self._lock:
        if self._is_speaking:
            self.stop()
        
        self._current_speak_id += 1
        speak_id = self._current_speak_id
        self._is_speaking = True
        self._stop_event.clear()
        mock_assistant.history.tts_speak_calls.append((text, volume))
        
        t_ref = []
        def run_speak():
            duration = min(0.5, max(0.05, len(text) * 0.005))
            start_time = time.time()
            while time.time() - start_time < duration:
                with self._lock:
                    # Fix thread leak check condition
                    if self._stop_event.is_set() or self._current_speak_id != speak_id:
                        break
                time.sleep(0.01)
            with self._lock:
                if self._current_speak_id == speak_id:
                    self._is_speaking = False
        
        self._speak_thread = threading.Thread(target=run_speak)
        t_ref.append(self._speak_thread)
        self._speak_thread.daemon = True
        self._speak_thread.start()

mock_assistant.TTSEngine.__init__ = patched_tts_init
mock_assistant.TTSEngine.speak = patched_tts_speak

# 2. VRAM State Leak fixes in STTEngine and LLMEngine
def patched_stt_load_model(self):
    mock_assistant.history.stt_load_calls.append(True)
    try:
        import voice_assistant.config as config
        device = getattr(config, "STT_DEVICE", "cuda")
    except Exception:
        device = "cuda"
        
    if device == "cuda":
        mock_assistant.vram_manager.stt_loaded = True
        try:
            mock_assistant.vram_manager.check_safety()
        except Exception:
            mock_assistant.vram_manager.stt_loaded = False # Cleanup on failure
            raise
    self._model_loaded = True

def patched_llm_load_model(self):
    mock_assistant.history.llm_load_calls.append(True)
    try:
        import voice_assistant.config as config
        device = getattr(config, "LLM_DEVICE", "cuda")
    except Exception:
        device = "cuda"
        
    if device == "cuda":
        mock_assistant.vram_manager.llm_loaded = True
        try:
            mock_assistant.vram_manager.check_safety()
        except Exception:
            mock_assistant.vram_manager.llm_loaded = False # Cleanup on failure
            raise
    self._model_loaded = True

mock_assistant.STTEngine.load_model = patched_stt_load_model
mock_assistant.LLMEngine.load_model = patched_llm_load_model

# 3. Serialization Lock in AssistantController
def patched_controller_init(self, tts_engine=None, stt_engine=None, llm_engine=None, wiki_retriever=None):
    self.tts_engine = tts_engine if tts_engine else mock_assistant.TTSEngine()
    self.stt_engine = stt_engine if stt_engine else mock_assistant.STTEngine()
    self.llm_engine = llm_engine if llm_engine else mock_assistant.LLMEngine()
    self.wiki_retriever = wiki_retriever if wiki_retriever else mock_assistant.WikiRetriever()
    self.context = []
    self.is_running = False
    self.interrupted_flag = False
    self._lock = threading.Lock() # Lock to serialize handle_input

def patched_controller_handle_input(self, input_type: str, content) -> None:
    with self._lock: # Protect handle_input execution
        mock_assistant.history.controller_handle_input_calls.append((input_type, content))
        
        if self.tts_engine.is_speaking():
            self.tts_engine.stop()
            self.interrupted_flag = True
        else:
            self.interrupted_flag = False

        if content == "" or content is None:
            return

        try:
            import voice_assistant.config as config
            dynamic_loading = getattr(config, "DYNAMIC_MODEL_LOADING", False)
        except Exception:
            dynamic_loading = False

        prompt = None
        if input_type in ("voice", "audio"):
            if dynamic_loading:
                self.stt_engine.load_model()
                try:
                    prompt = self.stt_engine.transcribe(content)
                finally:
                    self.stt_engine.unload_model()
            else:
                prompt = self.stt_engine.transcribe(content)
        elif input_type == "text":
            prompt = content
        else:
            raise ValueError(f"Invalid input type: {input_type}")

        if not prompt:
            return

        retrieval_context = ""
        try:
            chunks = self.wiki_retriever.retrieve(prompt)
            retrieval_context = "\n".join(chunks)
        except Exception:
            retrieval_context = ""

        if dynamic_loading:
            self.llm_engine.load_model()
            try:
                response = self.llm_engine.generate_response(prompt, self.context, retrieval_context=retrieval_context)
            finally:
                self.llm_engine.unload_model()
        else:
            response = self.llm_engine.generate_response(prompt, self.context, retrieval_context=retrieval_context)
        
        self.context.append({"role": "user", "content": prompt})
        self.context.append({"role": "assistant", "content": response})

        volume = 0.5
        try:
            import voice_assistant.config as config
            volume = config.DEFAULT_VOLUME
        except Exception:
            pass
            
        self.tts_engine.speak(response, volume=volume)

mock_assistant.AssistantController.__init__ = patched_controller_init
mock_assistant.AssistantController.handle_input = patched_controller_handle_input

# --- Verification runner ---

class DummyTTSEngine:
    def speak(self, text, volume=0.5): pass
    def stop(self): pass
    def is_speaking(self): return False

def test_vram_concurrency():
    print("\n--- Verifying Concurrent VRAM Safety & State Leaks ---")
    mock_assistant.reset_history()
    import voice_assistant.config as config
    config.DYNAMIC_MODEL_LOADING = True
    config.STT_DEVICE = "cuda"
    config.LLM_DEVICE = "cuda"
    mock_assistant.vram_manager.enforce_always = True

    controller = mock_assistant.AssistantController(tts_engine=DummyTTSEngine())
    errors = []
    vram_readings = []

    original_stt_transcribe = controller.stt_engine.transcribe
    original_llm_generate = controller.llm_engine.generate_response

    def slow_transcribe(audio_path_or_data):
        time.sleep(0.05)
        return original_stt_transcribe(audio_path_or_data)

    def slow_generate(prompt, context=None, retrieval_context=""):
        time.sleep(0.05)
        return original_llm_generate(prompt, context, retrieval_context)

    controller.stt_engine.transcribe = slow_transcribe
    controller.llm_engine.generate_response = slow_generate

    def run_voice_input():
        try:
            controller.handle_input("voice", "audio_concurrency.wav")
        except Exception as e:
            errors.append(e)

    def monitor_vram():
        for _ in range(150):
            vram_readings.append(mock_assistant.vram_manager.current_vram)
            time.sleep(0.002)

    threads = [threading.Thread(target=run_voice_input) for _ in range(5)]
    monitor_t = threading.Thread(target=monitor_vram)

    for t in threads: t.start()
    monitor_t.start()
    for t in threads: t.join()
    monitor_t.join()

    print(f"Errors caught: {len(errors)}")
    for err in errors:
        print(f"  Error: {type(err).__name__}: {err}")
    
    max_vram = max(vram_readings) if vram_readings else 0.0
    print(f"Max VRAM observed: {max_vram} GB")
    print(f"VRAM Manager state 'loaded_in_vram': {mock_assistant.loaded_in_vram}")

    assert len(errors) == 0, f"Expected 0 errors, but got {len(errors)}"
    assert max_vram <= 6.0, f"Expected max VRAM <= 6.0, but observed {max_vram}"
    assert len(mock_assistant.loaded_in_vram) == 0, f"VRAM state leaked: {mock_assistant.loaded_in_vram}"
    print(">> CONCURRENT VRAM SAFETY & STATE LEAKS: FIXED!")

def test_tts_deadlock():
    print("\n--- Verifying TTS Deadlock ---")
    mock_assistant.reset_history()
    tts = mock_assistant.TTSEngine()
    
    tts.speak("First phrase which starts playback", volume=0.5)
    assert tts.is_speaking()
    
    def call_speak_again():
        tts.speak("Second phrase which interrupts", volume=0.5)
        
    t = threading.Thread(target=call_speak_again)
    t.daemon = True
    t.start()
    t.join(timeout=1.0)
    
    is_deadlocked = t.is_alive()
    print(f"Thread deadlocked (is_alive): {is_deadlocked}")
    assert not is_deadlocked, "TTS Engine deadlocked!"
    print(">> TTS DEADLOCK: FIXED!")

def test_tts_thread_leak():
    print("\n--- Verifying TTS Thread Leak ---")
    mock_assistant.reset_history()
    tts = mock_assistant.TTSEngine()
    initial_threads = threading.active_count()
    
    tts.speak("First phrase that is long enough to run for a bit", volume=0.5)
    time.sleep(0.02)
    
    tts.stop()
    tts.speak("Second phrase", volume=0.5)
    
    # Let threads process and exit
    time.sleep(0.6)
    final_threads = threading.active_count()
    leaked_threads = final_threads - initial_threads
    
    print(f"Initial threads: {initial_threads}")
    print(f"Final threads: {final_threads}")
    print(f"Estimated leaked threads: {leaked_threads}")
    assert leaked_threads <= 0, f"Leaked {leaked_threads} threads!"
    print(">> TTS THREAD LEAK: FIXED!")

def test_all_90_tests():
    print("\n--- Verifying all 90 standard E2E tests still pass ---")
    # Discover and run the main E2E test suite
    loader = unittest.TestLoader()
    suite_tier = loader.discover(start_dir=tests_dir, pattern="test_tier*.py")
    suite_rag = loader.discover(start_dir=tests_dir, pattern="test_rag.py")
    suite_opt = loader.discover(start_dir=tests_dir, pattern="test_optimization.py")
    suite = unittest.TestSuite([suite_tier, suite_rag, suite_opt])
    
    runner = unittest.TextTestRunner(verbosity=1)
    result = runner.run(suite)
    print(f"Tests run: {result.testsRun}, Failures: {len(result.failures)}, Errors: {len(result.errors)}")
    assert result.wasSuccessful(), "Standard test suite failed!"
    print(">> STANDARD E2E TEST SUITE: ALL PASSED!")

if __name__ == "__main__":
    try:
        test_vram_concurrency()
        test_tts_deadlock()
        test_tts_thread_leak()
        test_all_90_tests()
        print("\nALL FIXED BEHAVIORS SUCCESSFULLY VERIFIED!")
    except AssertionError as e:
        print(f"\nVERIFICATION FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\nUNEXPECTED EXCEPTION: {e}")
        sys.exit(1)
