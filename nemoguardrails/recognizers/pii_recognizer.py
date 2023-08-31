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
import spacy


class PIIRecognizer:
    """Main class that enables integration of third party
       PII recognizers"""
    
    def __init__(self, config_path: str, load_predefined: bool = True, redact: bool = False):
        
        self.redact = redact
        self.load_predefined = load_predefined

        # predefined recognizers use spacy module 
        if not spacy.util.is_package('en_core_web_lg'):
            spacy.cli.download('en_core_web_lg')
        
        #TODO make the decorator generic 
        self.allowed_actions = ["retrieve_relevant_chunks"]
        
        #TODO read config.yml to find out required entities to be redacted
        self.pii_entities = ["CREDIT_CARD",
                            "PHONE_NUMBER",
                            "US_SSN",
                            "US_PASSPORT",
                            "LOCATION",
                            "EMAIL_ADDRESS",
                            "US_DRIVER_LICENSE"]

        # load predefined recognizers in registry
        self.registry = RecognizerRegistry()
        if self.load_predefined:
            self.registry.load_predefined_recognizers()

        # load ad-hoc recognizers 
        if os.path.exists(config_path):
            recognizer_path = os.path.join(config_path, "recognizers.yaml")
            if os.path.exists(recognizer_path):
                self.recognizer_path = recognizer_path
                self.registry.add_recognizers_from_yaml(self.recognizer_path)
                self._add_custom_entities_from_yaml()

        # load additional recognizers:
        #  1. cloud hosted PII recognizers, 2. custom recognizers
        self.load_recognizers_from_path(config_path)
        
        # Analyzer object 
        self.analyzer = AnalyzerEngine(registry=self.registry)

        # Anonymizer object
        self.anonymizer = AnonymizerEngine()
        
        
    def _add_custom_entities_from_yaml(self):
        """Discovers entities supported by ad-hoc PII recogniers"""

        with open(self.recognizer_path, "r") as stream:
            contents = yaml.safe_load(stream)
            for recognizer in contents["recognizers"]:
                custom_entity = recognizer["supported_entity"]
                if custom_entity not in self.pii_entities:
                    self.pii_entities.append(custom_entity)


    def load_recognizers_from_path(self, path: str):
        """helper function that loads custom recognizers
           recognizers that wrap cloud hosted PII recognizers"""
        
        recognizers_py_path = os.path.join(path, "recognizers.py")
        if os.path.exists(recognizers_py_path):
            file_name = os.path.basename(recognizers_py_path)
            spec = importlib.util.spec_from_file_location(file_name, recognizers_py_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # custom recognizers need to be decorated with @recognizer
            for name, obj in inspect.getmembers(module):
                if inspect.isclass(obj) and hasattr(obj, "recognizer_meta"):
                    try:
                        recognizer = obj()
                        self.registry.add_recognizer(recognizer)
                    except Exception as e:
                        #TODO need to log
                        print("failed to add recognizer to registry of analyzer engine")

    
    def _anonymize_text(self, text: str) -> str:
        """function to recognize PII entities and redact"""

        # analyzer tags entities with labels
        analyzer_results = self.analyzer.analyze(text=text, language='en', entities=self.pii_entities)
    
        # config for anonymization
        operators = {}
        for entity in analyzer_results:
            if entity.entity_type in self.pii_entities:
                operators[entity.entity_type] = OperatorConfig("replace", {"new_value": "<ANONYMIZED>"})
      
        # redact or anonymize
        anonymized_results = self.anonymizer.anonymize(
            text=text,
            analyzer_results=analyzer_results,    
            operators=operators)
        
        return anonymized_results.text
    

    def anonymize_fn(self, fn):
        """decorator that anonymizes
           output from retrieve_relevant_chunks action"""        

        async def decorator(*args, **kwargs):
            context_updates_anonymized = {}
            context_updates_anonymized["relevant_chunks"] = "" 
            
            # check for actions
            if inspect.isfunction(fn) and hasattr(fn, "action_meta"): 
                if fn.action_meta["name"] in self.allowed_actions and self.redact:
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