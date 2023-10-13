import logging
from typing import List, Optional
import requests
from nemoguardrails.actions.actions import ActionResult, action
from nemoguardrails.rails.llm.config import RailsConfig


def recognizer(name: Optional[str] = None):
    """Decorator that sets the meta data
       for identification of PII recognizers
       in modules"""
    
    def decorator(fn_or_cls):
        fn_or_cls.recognizer_meta = {
            "name": name or fn_or_cls.__name__
        }
        return fn_or_cls
    
    return decorator