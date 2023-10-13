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
import logging

log = logging.getLogger(__name__)

class PIIRecognizer:
    
    def __init__(self, config: RailsConfig, 
                 load_predefined: bool = False, 
                 redact: bool = False):

        # predefined recognizers use spacy module 
        if not spacy.util.is_package('en_core_web_lg'):
            spacy.cli.download('en_core_web_lg')
        
        self.config_path = config.config_path
        if config.sensitive_data_detection:
            self.redact = config.sensitive_data_detection.enable_detection
            if not config.sensitive_data_detection.provider:
                self.load_predefined = True
                self.pii_entities = ["PERSON", "US_SSN", 
                                     "CREDIT_CARD","PHONE_NUMBER",
                                     "EMAIL_ADDRESS","US_DRIVER_LICENSE"]
            elif config.sensitive_data_detection.provider=="presidio":
                self.load_predefined = True
                self.default_pii_entities = ["PERSON", "US_SSN", 
                                             "CREDIT_CARD","PHONE_NUMBER",
                                             "EMAIL_ADDRESS","US_DRIVER_LICENSE"]
                if config.sensitive_data_detection.entities:
                    self._map_pii_entities_from_config(config.sensitive_data_detection.entities)
                else:
                    self.pii_entities = self.default_entities
        else:
            self.redact = redact
            self.load_predefined = load_predefined
            self.pii_entities = []

        if config.sensitive_data_detection.mask_token:
            self.mask_token = config.sensitive_data_detection.mask_token
        else:
            self.mask_token = None
                    
        self.registry = RecognizerRegistry()
        if self.load_predefined:
            self.registry.load_predefined_recognizers()
                
        #ad-hoc recognizers
        if os.path.exists(self.config_path):
            recognizer_path = os.path.join(self.config_path, "recognizers.yaml")
            if os.path.exists(recognizer_path):
                self.recognizer_path = recognizer_path
                self.registry.add_recognizers_from_yaml(self.recognizer_path)
                self._add_custom_entities_from_yaml()

            self.load_recognizers_from_path(self.config_path)

        self.analyzer = AnalyzerEngine(registry=self.registry)
        self.anonymizer = AnonymizerEngine()

        log.info(f"PII entities to be redacted: {self.pii_entities}")
        

    def _map_pii_entities_from_config(self, config_entities):
        """Mapping entities mentioned config file to the ones accepted
           by the reconigzers"""
        #TODO change the hardcoded mapping to match recognizer supported entities 
        # with config ones
        self.pii_entities = []
        for entity in config_entities:
            if entity in self.default_pii_entities:
                self.pii_entities.append(entity)

    
    def _add_custom_entities_from_yaml(self):
        
        with open(self.recognizer_path, "r") as stream:
            contents = yaml.safe_load(stream)
            for recognizer in contents["recognizers"]:
                custom_entity = recognizer["supported_entity"]
                if self.pii_entities:
                    if custom_entity in self.pii_entities:
                        pass
                self.pii_entities.append(custom_entity)


    def load_recognizers_from_path(self, path: str):

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
                        log.info("failed to add recognizer to registry of analyzer engine")


    def _detect_sensitive_data(self, text: str) -> bool:
        analyzer_results = self.analyzer.analyze(text=text, language='en', entities=self.pii_entities)
        for result in analyzer_results:
            if result.entity_type in self.pii_entities:
                log.info(f"{result.entity_type} detected")
                return True
        return False
    
    
    def _anonymize_text(self, text: str) -> str:
        
        analyzer_results = self.analyzer.analyze(text=text, language='en', entities=self.pii_entities)
    
        #find length of characters to anonymize
        operators = {}
        for entity in analyzer_results:
            if entity.entity_type in self.pii_entities:
                #TODO function to obfuscate
                if self.mask_token:
                    if len(self.mask_token) == 1:
                        mask_string = self.mask_token * len(entity.entity_type)
                    else:
                        mask_string = self.mask_token    
                    operators[entity.entity_type] = OperatorConfig("replace", {"new_value": mask_string})
                else:
                    operators[entity.entity_type] = OperatorConfig("replace")
                    
        anonymized_results = self.anonymizer.anonymize(
            text=text,
            analyzer_results=analyzer_results,    
            operators=operators)
        
        return anonymized_results.text