from presidio_analyzer import AnalyzerEngine, PatternRecognizer
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig
import json
from pprint import pprint
from presidio_analyzer import AnalyzerEngine, RecognizerRegistry
import os
import yaml
from nemoguardrails.actions.actions import ActionResult, action
import inspect
import importlib
import inspect


class PIIRecognizer:
    
    def __init__(self, config_path: str, load_predefined: bool = True, redact: bool = True):
        

        self.redact = redact
        self.load_predefined = load_predefined
        
        self.allowed_actions = ["retrieve_relevant_chunks"]
        
        #TODO read config.yml to find out required entities to be redacted
        self.pii_entities = ["CREDIT_CARD",
                            "PHONE_NUMBER",
                            "US_SSN",
                            "US_PASSPORT",
                            "LOCATION",
                            "EMAIL_ADDRESS",
                            "US_DRIVER_LICENSE"]

        self.registry = RecognizerRegistry()
        if self.load_predefined:
            self.registry.load_predefined_recognizers()

        #ad-hoc recognizers
        if os.path.exists(config_path):
            recognizer_path = os.path.join(config_path, "recognizers.yaml")
            if recognizer_path:
                self.recognizer_path = recognizer_path
                self.registry.add_recognizers_from_yaml(self.recognizer_path)
                self._add_custom_entities_from_yaml()

        self.load_actions_from_path(config_path)
        
        self.analyzer = AnalyzerEngine(registry=self.registry)
        self.anonymizer = AnonymizerEngine()
        
    
     
    def _add_custom_entities_from_yaml(self):
        
        with open(self.recognizer_path, "r") as stream:
            contents = yaml.safe_load(stream)
            for recognizer in contents["recognizers"]:
                custom_entity = recognizer["supported_entity"]
                if custom_entity not in self.pii_entities:
                    self.pii_entities.append(custom_entity)


    def load_actions_from_path(self, path: str):

        recognizers_py_path = os.path.join(path, "recognizers.py")
        if os.path.exists(recognizers_py_path):
            file_name = os.path.basename(recognizers_py_path)
            spec = importlib.util.spec_from_file_location(file_name, recognizers_py_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            for name, obj in inspect.getmembers(module):
                if inspect.isclass(obj) and hasattr(obj, "recognizer_meta"):
                    try:
                        recognizer = obj()
                        self.registry.add_recognizer(recognizer)
                    except Exception as e:
                        print("failed to add recognizer to registry of analyzer engine")

    
    
    def _anonymize_text(self, text: str) -> str:
        
        analyzer_results = self.analyzer.analyze(text=text, language='en', entities=self.pii_entities)
    
        #find length of characters to anonymize
        operators = {}
   
        for entity in analyzer_results:
            if entity.entity_type in self.pii_entities:
                operators[entity.entity_type] = OperatorConfig("replace", {"new_value": "<ANONYMIZED>"})
      
        anonymized_results = self.anonymizer.anonymize(
            text=text,
            analyzer_results=analyzer_results,    
            operators=operators)
        
        return anonymized_results.text
    
    def anonymize_fn(self, fn):
        
        async def decorator(*args, **kwargs):
            context_updates_anonymized = {}
            context_updates_anonymized["relevant_chunks"] = "" 
            
            if inspect.isfunction(fn) and hasattr(fn, "action_meta"): 
                if fn.action_meta["name"] in self.allowed_actions and self.redact:
                    print ('anonymizing relevant chunks...')
                    action_result = await fn(*args, **kwargs)
                    context_updates = action_result.context_updates
                    context_updates_anonymized["relevant_chunks"] = self._anonymize_text(context_updates["relevant_chunks"])
                    async def anonymized_fn():
                        return ActionResult(
                            return_value=context_updates_anonymized["relevant_chunks"],
                            context_updates=context_updates_anonymized,
                        )
                    
                    return anonymized_fn
                else:
                    return fn
            
        return decorator