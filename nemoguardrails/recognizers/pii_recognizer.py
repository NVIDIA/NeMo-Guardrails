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
from nemoguardrails.rails.llm.config import RailsConfig

#TODO remove this and infer from recognizers' supported entities
pii_entities_dict = {
    "name" : "PERSON",
    "ssn" : "US_SSN",
    "credit_card" : "CREDIT_CARD",
    "phone_number" : "PHONE_NUMBER",
    "email": "EMAIL_ADDRESS",
    "driver_license": "US_DRIVER_LICENSE"
}

class PIIRecognizer:
    """Main class that enables integration of third party
       PII recognizers"""
    
    def __init__(self, config : RailsConfig, load_predefined: bool = False, redact: bool = False):
        
        self.config_path = config.config_path
        if config.redact_pii:
            self.redact = config.redact_pii.enable_pii_redaction
            self.load_predefined = config.redact_pii.load_predefined
             #required entities to be redacted from config.yml file
            if config.redact_pii.entities:
                self._map_pii_entities_from_config(config.redact_pii.entities)
        else:
            self.redact = redact
            self.load_predefined = load_predefined
            self.pii_entities = []
       
        # predefined recognizers use spacy module 
        if not spacy.util.is_package('en_core_web_lg'):
            spacy.cli.download('en_core_web_lg')
        
        #TODO make the decorator generic 
        self.allowed_actions = ["retrieve_relevant_chunks"]
        
        # load predefined recognizers in registry
        self.registry = RecognizerRegistry()
        if self.load_predefined:
            self.registry.load_predefined_recognizers()

        if self.config_path: 
            if os.path.exists(self.config_path):
                # load ad-hoc recognizers
                recognizer_path = os.path.join(self.config_path, "recognizers.yaml")
                if os.path.exists(recognizer_path):
                    self.recognizer_path = recognizer_path
                    self.registry.add_recognizers_from_yaml(self.recognizer_path)
                    self._add_custom_entities_from_yaml()

                # load additional recognizers:
                #  1. cloud hosted PII recognizers, 2. custom recognizers
                self.load_recognizers_from_path(self.config_path)
        
        # Analyzer object 
        self.analyzer = AnalyzerEngine(registry=self.registry)

        # Anonymizer object
        self.anonymizer = AnonymizerEngine()
        
        
    def _map_pii_entities_from_config(self, config_entities):
        """Mapping entities mentioned config file to the ones accepted
           by the reconigzers"""
        #TODO change the hardcoded mapping to match recognizer supported entities 
        # with config ones
        self.pii_entities = []
        for entity in config_entities:
            if entity in pii_entities_dict:
                self.pii_entities.append(pii_entities_dict[entity])


    def _add_custom_entities_from_yaml(self):
        """Discovers entities supported by ad-hoc PII recogniers"""

        with open(self.recognizer_path, "r") as stream:
            contents = yaml.safe_load(stream)
            for recognizer in contents["recognizers"]:
                custom_entity = recognizer["supported_entity"]
                if self.pii_entities:
                    if custom_entity in self.pii_entities:
                        pass
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

        def decorator(*args, **kwargs):
            # check for actions
            if inspect.isfunction(fn) and hasattr(fn, "action_meta"): 
                if fn.action_meta["name"] in self.allowed_actions and self.redact:
                    async def anonymized_fn():
                        context_updates_anonymized = {}
                        context_updates_anonymized["relevant_chunks"] = "" 
                        result = fn(*args, **kwargs)
                        if isinstance(result, ActionResult):
                            context_updates = result.context_updates
                            if context_updates and "relevant_chunks" in context_updates:
                                context_updates_anonymized["relevant_chunks"] = self._anonymize_text(context_updates["relevant_chunks"])
                                return ActionResult(
                                    return_value=context_updates_anonymized["relevant_chunks"],
                                    context_updates=context_updates_anonymized,
                                )
                        return result
                    return anonymized_fn
            return fn
            
        return decorator