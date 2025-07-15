#latency_handler.py

import time
from langchain_core.callbacks import BaseCallbackHandler # type: ignore

class LatencyCallbackHandler(BaseCallbackHandler):
    def __init__(self):
        self.times = {}
    
    def _start_timer(self, key):
        self.times[key] = {"start": time.time(), "end": None}
    
    def _end_timer(self, key):
        if key in self.times:
            self.times[key]["end"] = time.time()

    def on_chain_start(self, serialized, inputs, **kwargs):
        self._start_timer("chain")

    def on_chain_end(self, outputs, **kwargs):
        self._end_timer("chain")

    def on_tool_start(self, serialized, input_str, **kwargs):
        self._start_timer("Query Execution")

    def on_tool_end(self, output, **kwargs):
        self._end_timer("Query Execution")

    def on_llm_start(self, serialized, prompts, **kwargs):
        self._start_timer("llm")

    def on_llm_end(self, response, **kwargs):
        self._end_timer("llm")

    def get_latencies(self):
        result = {}
        for k, v in self.times.items():
            if v["start"] and v["end"]:
                result[k] = round(v["end"] - v["start"], 3)
        return result
